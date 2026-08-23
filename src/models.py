"""Shared item model.

Every source fetcher returns a list of Item. Everything downstream — dedupe,
classification, rendering — only ever sees this shape.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

_WS = re.compile(r"\s+")


def _canonical(url: str) -> str:
    """Strip tracking params and trailing slashes so the same page hashes once."""
    url = url.split("#", 1)[0]
    if "?" in url:
        base, query = url.split("?", 1)
        keep = [
            p
            for p in query.split("&")
            if p and not p.split("=", 1)[0].lower().startswith(("utm_", "ref", "source"))
        ]
        url = base + ("?" + "&".join(keep) if keep else "")
    return url.rstrip("/")


@dataclass
class Item:
    title: str
    url: str
    source: str
    published: str  # ISO 8601, UTC
    body: str = ""  # raw text used for classification; not always rendered
    summary: str = ""  # short human-facing blurb
    version: str = ""  # e.g. "2.1.207" — empty for non-release items
    category: str = "note"
    impact: str = "info"  # breaking | feature | fix | info
    tags: list[str] = field(default_factory=list)

    @property
    def uid(self) -> str:
        seed = f"{_canonical(self.url)}|{_WS.sub(' ', self.title).strip().lower()}"
        return hashlib.sha256(seed.encode()).hexdigest()[:16]

    @property
    def dt(self) -> datetime:
        try:
            return datetime.fromisoformat(self.published.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["uid"] = self.uid
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Item":
        allowed = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**allowed)


def iso(value) -> str:
    """Coerce whatever a source hands us into an ISO-8601 UTC string."""
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, str) and value:
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(value, fmt)
                dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    return datetime.now(timezone.utc).isoformat()
