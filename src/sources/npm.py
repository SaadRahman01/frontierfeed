"""npm registry.

The registry document carries a `time` map of version -> publish timestamp.
This is usually the very first public signal that a Claude Code build shipped,
often ahead of the changelog page, and it is plain JSON with no key required.
"""

from __future__ import annotations

from urllib.parse import quote

from ..models import Item, iso

REGISTRY = "https://registry.npmjs.org/{pkg}"


def fetch(fetcher, cfg) -> list[Item]:
    items: list[Item] = []
    limit = cfg.get("recent_versions", 15)

    for pkg in cfg.get("packages", []):
        data, _ = fetcher.get_json(REGISTRY.format(pkg=quote(pkg, safe="@")))
        if not data:
            continue
        times = {k: v for k, v in (data.get("time") or {}).items() if k not in ("created", "modified")}
        recent = sorted(times.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        for version, stamp in recent:
            if any(m in version for m in ("-alpha", "-beta", "-rc", "-next")):
                continue
            items.append(
                Item(
                    title=f"{pkg} {version} published",
                    url=f"https://www.npmjs.com/package/{pkg}/v/{version}",
                    source=f"npm:{pkg}",
                    published=iso(stamp),
                    body=f"Version {version} of {pkg} was published to the npm registry.",
                    version=version,
                    tags=["release", "npm"],
                )
            )
    return items
