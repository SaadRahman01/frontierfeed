"""Rule-based classification.

This is deliberately not an LLM. Release notes in this ecosystem are written to
a consistent house style — lines open with Added / Changed / Fixed / Removed,
and deprecations say so in as many words. Pattern matching on that is both free
and more repeatable than asking a model to judge severity, which is the one job
you want to give identical answers every run.
"""

from __future__ import annotations

import re

from .models import Item

# Matched against the TITLE only. A model name appearing somewhere in a customer
# story is not a model release, and matching the body would call every one of
# those a launch — which is exactly the false positive that makes a feed useless.
TITLE_RULES: list[tuple[str, re.Pattern]] = [
    ("model-release", re.compile(r"^\s*(introducing|announcing|meet)\b.{0,40}\bclaude (opus|sonnet|haiku|mythos|fable)[\s-]?\d", re.I)),
    ("model-release", re.compile(r"^\s*claude (opus|sonnet|haiku|mythos|fable)[\s-]?\d", re.I)),
    ("launch", re.compile(r"^\s*(introducing|announcing|meet|now available[:,]?)\b", re.I)),
    ("incident", re.compile(r"\b(outage|degraded performance|incident|postmortem)\b", re.I)),
]

# Matched against title + body. First match wins, so specific patterns go first.
CATEGORY_RULES: list[tuple[str, re.Pattern]] = [
    ("deprecation", re.compile(r"\b(deprecat\w+|end[- ]of[- ]life|sunset|retir\w+|will be removed)\b", re.I)),
    ("pricing", re.compile(r"\b(pricing|price|per (million|mtok)|cost|billing|credits?)\b", re.I)),
    ("claude-code", re.compile(r"\bclaude[- ]code\b|\bcowork\b|\bslash command\b|\bsubagent\b", re.I)),
    ("api", re.compile(r"\b(messages? api|api|sdk|endpoint|beta header|rate limit|tool use|mcp)\b", re.I)),
    ("incident", re.compile(r"\b(outage|degraded|elevated error rate)\b", re.I)),
    ("research", re.compile(r"\b(interpretability|alignment|red[- ]team|evaluation|paper|we studied)\b", re.I)),
    ("policy", re.compile(r"\b(terms of service|usage polic|acceptable use|privacy|export control|compliance)\b", re.I)),
]

IMPACT_RULES: list[tuple[str, re.Pattern]] = [
    ("breaking", re.compile(r"^\s*(removed|breaking)\b", re.I | re.M)),
    ("breaking", re.compile(r"\b(breaking change|no longer (support|work|available|permitted)|has been removed|will be removed|must (now )?migrate)\b", re.I)),
    ("breaking", re.compile(r"\b(deprecat\w+|end[- ]of[- ]life|sunset)\b", re.I)),
    ("feature", re.compile(r"^\s*(added|new)\b", re.I | re.M)),
    ("feature", re.compile(r"\b(now available|introduc\w+|you can now|general availability|launch\w*|in beta)\b", re.I)),
    ("fix", re.compile(r"^\s*(fixed|changed)\b", re.I | re.M)),
    ("fix", re.compile(r"\b(bug ?fix|resolved|patch\w*)\b", re.I)),
]

TAG_RULES: dict[str, re.Pattern] = {
    "opus": re.compile(r"\bopus\b", re.I),
    "sonnet": re.compile(r"\bsonnet\b", re.I),
    "haiku": re.compile(r"\bhaiku\b", re.I),
    "mcp": re.compile(r"\bmcp\b|model context protocol", re.I),
    "enterprise": re.compile(r"\benterprise\b|\badmin api\b", re.I),
    "skills": re.compile(r"\bskills?\b|\bplugins?\b", re.I),
}

_TAGS = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    return _SPACE.sub(" ", _TAGS.sub(" ", text or "")).strip()


def first_sentences(text: str, limit: int = 280) -> str:
    text = strip_html(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return (cut[: stop + 1] if stop > 80 else cut.rstrip() + "…").strip()


def semver_impact(version: str) -> str:
    """Read impact straight off the version number.

    A maintainer bumping major is telling you the contract changed. That is a
    stronger and cheaper signal than anything you could infer from prose.
    """
    parts = version.lstrip("v").split(".")
    if len(parts) < 3:
        return "info"
    try:
        minor, patch = int(parts[1]), int(parts[2].split("-")[0])
    except ValueError:
        return "info"
    if minor == 0 and patch == 0:
        return "breaking"
    return "feature" if patch == 0 else "fix"


def classify(item: Item) -> Item:
    haystack = f"{item.title}\n{item.body}"

    if item.category in ("", "note"):
        for name, pattern in TITLE_RULES:
            if pattern.search(item.title):
                item.category = name
                break

    if item.category in ("", "note"):
        for name, pattern in CATEGORY_RULES:
            if pattern.search(haystack):
                item.category = name
                break

    matched = False
    for name, pattern in IMPACT_RULES:
        if pattern.search(haystack):
            item.impact = name
            matched = True
            break

    # Fall back to the version number when the prose says nothing useful.
    if not matched and item.version:
        item.impact = semver_impact(item.version)

    # A model launch is always worth surfacing above routine notes.
    if item.category in ("model-release", "launch") and item.impact in ("info", "fix"):
        item.impact = "feature"

    for tag, pattern in TAG_RULES.items():
        if pattern.search(haystack) and tag not in item.tags:
            item.tags.append(tag)

    if not item.summary:
        item.summary = first_sentences(item.body) or item.title

    return item


def breaking_lines(item: Item, limit: int = 4) -> list[str]:
    """Pull just the lines a developer needs to read, for the digest view."""
    out = []
    for line in strip_html(item.body).split("·"):
        line = line.strip(" -•\t")
        if not line:
            continue
        for impact, pattern in IMPACT_RULES:
            if impact == "breaking" and pattern.search(line):
                out.append(line[:200])
                break
        if len(out) >= limit:
            break
    return out
