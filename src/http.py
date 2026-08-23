"""Polite HTTP with on-disk conditional-request caching.

Every fetch sends If-None-Match / If-Modified-Since from the last run. A 304
costs the upstream server almost nothing and costs us no parsing, which is what
keeps an hourly job from being rude.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

CACHE_PATH = Path("data/http_cache.json")
USER_AGENT = os.environ.get(
    "FRONTIERFEED_UA",
    "frontierfeed/1.0 (+https://github.com/SaadRahman01/frontierfeed)",
)
TIMEOUT = 30


class Fetcher:
    def __init__(self, cache_path: Path = CACHE_PATH):
        self.cache_path = cache_path
        self.cache = {}
        if cache_path.exists():
            try:
                self.cache = json.loads(cache_path.read_text())
            except json.JSONDecodeError:
                self.cache = {}
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def get(self, url: str, headers: dict | None = None, delay: float = 1.0):
        """Return (body_text, status).

        status is "ok", "not-modified" (a 304, nothing to do) or "error".
        Callers need the distinction: an unchanged feed is a success, a 403 is
        not, and reporting the second as the first hides real breakage.
        """
        entry = self.cache.get(url, {})
        req_headers = dict(headers or {})
        if entry.get("etag"):
            req_headers["If-None-Match"] = entry["etag"]
        if entry.get("last_modified"):
            req_headers["If-Modified-Since"] = entry["last_modified"]

        try:
            resp = self.session.get(url, headers=req_headers, timeout=TIMEOUT)
        except requests.RequestException as exc:
            print(f"  ! {url} -> {type(exc).__name__}: {exc}")
            return None, "error"
        finally:
            time.sleep(delay)

        if resp.status_code == 304:
            return None, "not-modified"
        if resp.status_code >= 400:
            print(f"  ! {url} -> HTTP {resp.status_code}")
            return None, "error"

        self.cache[url] = {
            "etag": resp.headers.get("ETag"),
            "last_modified": resp.headers.get("Last-Modified"),
            "seen": time.time(),
        }
        return resp.text, "ok"

    def get_json(self, url: str, headers: dict | None = None, delay: float = 1.0):
        body, status = self.get(url, headers=headers, delay=delay)
        if body is None:
            return None, status
        try:
            return json.loads(body), status
        except json.JSONDecodeError:
            print(f"  ! {url} -> response was not JSON")
            return None, "error"

    def save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2, sort_keys=True))
