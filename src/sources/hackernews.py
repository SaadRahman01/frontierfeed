"""Hacker News, via the Algolia search API.

Keyless and free. This is the community-signal channel — it catches outages,
pricing changes and third-party writeups that never reach an official feed.
The points floor keeps the noise down; tune it in config.yaml.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from ..models import Item, iso

SEARCH = (
    "https://hn.algolia.com/api/v1/search_by_date"
    "?query={q}&tags=story&numericFilters=points%3E%3D{points}&hitsPerPage={n}"
)


def fetch(fetcher, cfg) -> list[Item]:
    items: list[Item] = []
    points = cfg.get("min_points", 40)
    n = cfg.get("per_query", 20)

    for query in cfg.get("queries", []):
        url = SEARCH.format(q=quote_plus(query), points=points, n=n)
        data, _ = fetcher.get_json(url)
        if not data:
            continue
        for hit in data.get("hits", []):
            title = (hit.get("title") or "").strip()
            if not title:
                continue
            hn_url = f"https://news.ycombinator.com/item?id={hit['objectID']}"
            items.append(
                Item(
                    title=title,
                    url=hit.get("url") or hn_url,
                    source="hackernews",
                    published=iso(hit.get("created_at")),
                    body=f"{hit.get('points', 0)} points, {hit.get('num_comments', 0)} comments. Discussion: {hn_url}",
                    tags=["community"],
                )
            )
    return items
