"""arXiv.

Free public API, Atom out. arXiv asks for no more than one request every three
seconds, which the delay argument honours.
"""

from __future__ import annotations

from urllib.parse import quote_plus

import feedparser

from ..models import Item, iso

QUERY = (
    "http://export.arxiv.org/api/query"
    "?search_query={q}&sortBy=submittedDate&sortOrder=descending&max_results={n}"
)


def fetch(fetcher, cfg) -> list[Item]:
    items: list[Item] = []
    for query in cfg.get("queries", []):
        url = QUERY.format(q=quote_plus(query), n=cfg.get("per_query", 10))
        body, _ = fetcher.get(url, delay=3.0)
        if body is None:
            continue
        for entry in feedparser.parse(body).entries:
            items.append(
                Item(
                    title=entry.get("title", "").replace("\n", " ").strip(),
                    url=entry.get("link", ""),
                    source="arxiv",
                    published=iso(entry.get("published")),
                    body=entry.get("summary", "")[:4000],
                    category="research",
                    tags=["research", "paper"],
                )
            )
    return items
