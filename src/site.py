"""Site-wide constants.

Split out so pages, feeds and the renderer can share them without importing
each other. Everything that describes the site as a whole lives here; nothing
in this module renders anything.
"""

from __future__ import annotations

SITE_TITLE = "frontierfeed"
SITE_TAGLINE = "Release and news tracker for Anthropic's Claude"
SITE_URL = "https://saadrahman01.github.io/frontierfeed"
REPO_URL = "https://github.com/SaadRahman01/frontierfeed"

# The <title> is the highest-value 60 characters on the page, and nobody
# searches for the brand name, so the query goes first and the wordmark stays
# in the masthead where it belongs.
SEO_TITLE = "Claude Release Tracker — Every Anthropic Model, API & Claude Code Update"

# Crawlers and social scrapers need absolute URLs; pages themselves use
# relative hrefs so they still work when opened from disk.
CANONICAL = f"{SITE_URL}/"
OG_IMAGE = f"{SITE_URL}/og.png"
SITE_DESC = f"{SITE_TAGLINE}. Unofficial, open source, updated hourly."

IMPACT_LABEL = {
    "breaking": "breaking",
    "feature": "new",
    "fix": "fix",
    "info": "note",
}

# slug -> (nav label, page <title>, meta description). The empty slug is the
# index. Order here is the order of the nav bar and of sitemap.xml.
PAGES = {
    "": (
        "Feed",
        SEO_TITLE,
        SITE_DESC,
    ),
    "claude-code/versions": (
        "Versions",
        "Claude Code Version History — Every Release With Dates",
        "Complete version history for Claude Code and the Anthropic SDKs, with "
        "release dates, pulled hourly from npm and GitHub Releases.",
    ),
    "breaking": (
        "Breaking",
        "Claude Breaking Changes & Deprecations — Running Log",
        "Every breaking change, deprecation and removal across Claude Code, the "
        "Anthropic API and the official SDKs, in one running log.",
    ),
    "releases": (
        "Releases",
        "Claude Model Releases, Pricing & Deprecations — Timeline",
        "Claude model launches, pricing changes and deprecation notices in date "
        "order, compiled from Anthropic's own announcements.",
    ),
}


def page_url(slug: str) -> str:
    """Absolute URL for a page slug. The index is the bare canonical."""
    slug = slug.strip("/")
    return CANONICAL if not slug else f"{SITE_URL}/{slug}/"


def base_prefix(slug: str) -> str:
    """Relative path back to the site root from a page at this slug."""
    slug = slug.strip("/")
    return "../" * (slug.count("/") + 1) if slug else ""
