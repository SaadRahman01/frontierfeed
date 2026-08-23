"""Optional AI summaries. Bring your own key.

Without ANTHROPIC_API_KEY set, this module does nothing and the pipeline uses
the rule-based summary instead. That is the default and it is free. If you do
set a key, only items that are new in this run are ever sent, so the cost is
proportional to what actually shipped rather than to how often the job runs.

Rough cost on Haiku: a few thousand input tokens per item, a few hundred out.
Ten new items a day lands around a dollar a month. Set a spend cap anyway.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .classify import strip_html
from .models import Item

ENDPOINT = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("FRONTIERFEED_MODEL", "claude-haiku-4-5-20251001")

PROMPT = """You are summarising one entry from a software release feed for working developers.

Write at most two sentences. Lead with what changed. If something was removed,
deprecated, or renamed, say so explicitly and name it. Do not editorialise, do
not use marketing language, and do not open with "This update". If the entry is
routine housekeeping, say that plainly and stop.

Title: {title}

Body:
{body}"""


def enabled() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def summarize(item: Item, max_tokens: int = 300) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return item.summary

    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": PROMPT.format(title=item.title, body=strip_html(item.body)[:6000]),
            }
        ],
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"  ! summary failed for {item.uid}: {exc}")
        return item.summary

    parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    return " ".join(parts).strip() or item.summary
