"""GitHub Releases.

Inside Actions the built-in GITHUB_TOKEN raises the rate limit from 60/hr to
5000/hr, so pass it. It works without one too, just slower to hit the ceiling.
"""

from __future__ import annotations

import os

from ..models import Item, iso

API = "https://api.github.com/repos/{repo}/releases?per_page={n}"


def fetch(fetcher, cfg) -> list[Item]:
    items: list[Item] = []
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for repo in cfg.get("repos", []):
        url = API.format(repo=repo, n=cfg.get("per_repo", 10))
        data, _ = fetcher.get_json(url, headers=headers)
        if not data:
            continue
        for rel in data:
            if rel.get("draft"):
                continue
            tag = rel.get("tag_name") or ""
            items.append(
                Item(
                    title=rel.get("name") or f"{repo} {tag}",
                    url=rel.get("html_url", ""),
                    source=f"github:{repo}",
                    published=iso(rel.get("published_at") or rel.get("created_at")),
                    body=(rel.get("body") or "")[:8000],
                    version=tag.lstrip("v"),
                    tags=["release", repo.split("/")[-1]],
                )
            )
    return items
