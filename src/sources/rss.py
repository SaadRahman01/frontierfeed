"""Generic RSS / Atom reader.

Anthropic publishes a native feed for the Claude Code changelog. The news page
and engineering blog do not, so config.yaml points at community mirrors that
regenerate feeds on a schedule. Swap those entries the day an official feed
appears — that's the whole reason each feed is a config line and not code.
"""

from __future__ import annotations

import feedparser

from ..models import Item, iso


def _text(entry) -> str:
    for key in ("content", "summary_detail", "summary", "description"):
        val = entry.get(key)
        if isinstance(val, list) and val:
            return val[0].get("value", "")
        if isinstance(val, dict):
            return val.get("value", "")
        if isinstance(val, str):
            return val
    return ""


def _stamp(entry) -> str:
    for key in ("published", "updated", "created"):
        if entry.get(key):
            return iso(entry[key])
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            from datetime import datetime, timezone

            return iso(datetime(*parsed[:6], tzinfo=timezone.utc))
    return iso(None)


def fetch(fetcher, cfg) -> list[Item]:
    items: list[Item] = []
    for feed_cfg in cfg.get("feeds", []):
        url = feed_cfg["url"]
        name = feed_cfg.get("name", url)
        body, status = fetcher.get(url)
        if body is None:
            if status == "not-modified":
                print(f"  = {name}: unchanged since last run")
            continue
        parsed = feedparser.parse(body)
        for entry in parsed.entries[: feed_cfg.get("limit", 20)]:
            link = entry.get("link") or ""
            if not link:
                continue
            items.append(
                Item(
                    title=entry.get("title", "Untitled").strip(),
                    url=link,
                    source=name,
                    published=_stamp(entry),
                    body=_text(entry)[:8000],
                    tags=list(feed_cfg.get("tags", [])),
                )
            )
    return items
