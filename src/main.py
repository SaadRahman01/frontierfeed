"""Entry point: python -m src.main

Reads config.yaml, fetches every enabled source, drops anything already seen,
classifies what's left, and rewrites docs/. Designed to be idempotent — running
it twice in a row produces no second set of entries.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import summarize as summarizer
from .classify import classify
from .http import Fetcher
from .models import Item
from .render import write_all
from .sources import REGISTRY

CONFIG = Path("config.yaml")
STORE = Path("data/items.json")


def load_store() -> list[Item]:
    if not STORE.exists():
        return []
    try:
        raw = json.loads(STORE.read_text())
    except json.JSONDecodeError:
        print("! data/items.json is corrupt; starting from empty")
        return []
    return [Item.from_dict(d) for d in raw.get("items", [])]


def save_store(items: list[Item]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps({"items": [i.to_dict() for i in items]}, indent=2))


def collect(config: dict, fetcher: Fetcher) -> list[Item]:
    found: list[Item] = []
    for name, cfg in (config.get("sources") or {}).items():
        if not cfg or cfg.get("enabled") is False:
            continue
        fetch = REGISTRY.get(name)
        if fetch is None:
            print(f"! unknown source '{name}' in config.yaml — skipping")
            continue
        print(f"> {name}")
        try:
            items = fetch(fetcher, cfg)
        except Exception as exc:  # one bad source must not kill the run
            print(f"  ! {name} failed: {type(exc).__name__}: {exc}")
            continue
        print(f"  {len(items)} item(s)")
        found.extend(items)
    return found


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Update the frontierfeed feed.")
    parser.add_argument("--dry-run", action="store_true", help="fetch and classify but write nothing")
    parser.add_argument("--offline", action="store_true", help="re-render from the stored items only")
    parser.add_argument("--reclassify", action="store_true", help="re-run classification over every stored item")
    args = parser.parse_args(argv)

    config = yaml.safe_load(CONFIG.read_text()) or {}
    keep = int(config.get("keep_items", 300))

    stored = load_store()
    known = {i.uid for i in stored}
    print(f"{len(stored)} item(s) in store")

    if args.offline:
        fresh: list[Item] = []
    else:
        fetcher = Fetcher()
        fresh = [i for i in collect(config, fetcher) if i.uid not in known and i.url]
        if not args.dry_run:
            fetcher.save()

    # Dedupe within this batch too — npm and GitHub often report the same release.
    batch: dict[str, Item] = {}
    for item in fresh:
        batch.setdefault(item.uid, item)
    fresh = [classify(i) for i in batch.values()]
    print(f"{len(fresh)} new item(s)")

    if fresh and summarizer.enabled():
        print(f"summarising {len(fresh)} new item(s) with {summarizer.MODEL}")
        for item in fresh:
            item.summary = summarizer.summarize(item)
    elif fresh:
        print("no ANTHROPIC_API_KEY set — using rule-based summaries (free)")

    if args.reclassify:
        print("reclassifying stored items")
        for item in stored:
            item.category, item.impact, item.tags = "note", "info", []
            classify(item)

    merged = sorted(stored + fresh, key=lambda i: i.dt, reverse=True)[:keep]

    for item in fresh:
        if item.impact == "breaking":
            print(f"  [breaking] {item.title}")

    if args.dry_run:
        print("dry run — nothing written")
        return 0

    save_store(merged)
    write_all(merged, config=config)
    print(f"wrote docs/ with {len(merged)} item(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
