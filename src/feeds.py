"""Feed output: RSS 2.0, JSON Feed 1.1, and the raw items dump.

Feed readers never load the HTML, so for a large part of the audience these
files *are* the site. The tag feeds exist so that someone who only cares about
breaking changes can subscribe to exactly that and nothing else — a full feed
they mostly ignore is a feed they eventually unsubscribe from.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape

from .models import Item
from .site import IMPACT_LABEL, OG_IMAGE, SITE_DESC, SITE_TAGLINE, SITE_TITLE, SITE_URL


def _is_claude_code(item: Item) -> bool:
    return item.category == "claude-code" or "claude-code" in item.source


# (filename, human label, predicate). The first entry is the main feed and is
# the one linked from every page's <head>.
FEEDS: list[tuple[str, str, object]] = [
    ("feed.xml", "", lambda i: True),
    ("feed-breaking.xml", "breaking changes", lambda i: i.impact == "breaking"),
    ("feed-claude-code.xml", "Claude Code", _is_claude_code),
    ("feed-releases.xml", "model releases", lambda i: i.category in ("model-release", "launch")),
]


def render_rss(items: list[Item], limit: int = 100, label: str = "", path: str = "feed.xml") -> str:
    title = f"{SITE_TITLE} — {label}" if label else SITE_TITLE
    desc = f"{SITE_TAGLINE}, {label} only." if label else f"{SITE_TAGLINE}."
    now = format_datetime(datetime.now(timezone.utc))
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        f"<title>{escape(title)}</title>",
        f"<link>{escape(SITE_URL)}</link>",
        f"<description>{escape(desc)} Unofficial; not affiliated with Anthropic.</description>",
        "<language>en</language>",
        f"<lastBuildDate>{now}</lastBuildDate>",
        f'<atom:link href="{escape(SITE_URL)}/{escape(path)}" rel="self" type="application/rss+xml"/>',
        "<docs>https://www.rssboard.org/rss-specification</docs>",
        f"<generator>{escape(SITE_TITLE)}</generator>",
        "<ttl>60</ttl>",
        "<image>",
        f"<url>{escape(OG_IMAGE)}</url>",
        f"<title>{escape(title)}</title>",
        f"<link>{escape(SITE_URL)}</link>",
        "</image>",
    ]
    for item in items[:limit]:
        tag = IMPACT_LABEL.get(item.impact, item.impact)
        headline = f"[{tag}] {item.title}" if item.impact == "breaking" else item.title
        parts += [
            "<item>",
            f"<title>{escape(headline)}</title>",
            f"<link>{escape(item.url)}</link>",
            f'<guid isPermaLink="false">frontierfeed:{item.uid}</guid>',
            f"<pubDate>{format_datetime(item.dt)}</pubDate>",
            f"<category>{escape(item.category)}</category>",
            f"<description>{escape(item.summary)}</description>",
            "</item>",
        ]
    parts += ["</channel>", "</rss>"]
    return "\n".join(parts)


def render_jsonfeed(items: list[Item], limit: int = 100) -> str:
    """JSON Feed 1.1 — https://jsonfeed.org/version/1.1

    items.json is this project's own dump and its shape is whatever the Item
    dataclass happens to be. This one is the standard a reader can subscribe to.
    """
    return json.dumps(
        {
            "version": "https://jsonfeed.org/version/1.1",
            "title": SITE_TITLE,
            "home_page_url": f"{SITE_URL}/",
            "feed_url": f"{SITE_URL}/feed.json",
            "description": SITE_DESC,
            "icon": OG_IMAGE,
            "favicon": OG_IMAGE,
            "language": "en",
            "items": [
                {
                    "id": f"frontierfeed:{i.uid}",
                    "url": i.url,
                    "title": i.title,
                    "summary": i.summary,
                    "content_text": i.summary,
                    "date_published": i.dt.isoformat(),
                    "tags": [i.category, i.impact, *i.tags],
                }
                for i in items[:limit]
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


def render_items_json(items: list[Item]) -> str:
    return json.dumps(
        {
            "title": SITE_TITLE,
            "description": SITE_TAGLINE,
            "generated": datetime.now(timezone.utc).isoformat(),
            "count": len(items),
            "items": [i.to_dict() for i in items],
        },
        indent=2,
    )
