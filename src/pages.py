"""The compiled pages.

The index is a reverse-chronological river, which is the right shape for
"what happened lately" and the wrong shape for every other question. These
pages answer the questions the river cannot: what version is current, what
broke, what shipped. Each is assembled from data already in the store — none
of them restates a single upstream headline, which is the whole point. A page
that only rehosts someone else's snippet earns nothing.

Each function here returns a body fragment. render.py wraps it in the shell.
"""

from __future__ import annotations

from html import escape

from .classify import breaking_lines
from .models import Item
from .site import IMPACT_LABEL

NPM_CLAUDE_CODE = "npm:@anthropic-ai/claude-code"

# Display names for the sources that carry version numbers, in the order the
# versions page lists them. Anything versioned but unlisted falls to the end
# under its raw source name.
PACKAGES = {
    NPM_CLAUDE_CODE: ("Claude Code", "npm · @anthropic-ai/claude-code"),
    "github:anthropics/claude-code-action": ("claude-code-action", "GitHub · anthropics/claude-code-action"),
    "github:anthropics/anthropic-sdk-python": ("Python SDK", "GitHub · anthropics/anthropic-sdk-python"),
    "github:anthropics/anthropic-sdk-typescript": ("TypeScript SDK", "GitHub · anthropics/anthropic-sdk-typescript"),
    "github:modelcontextprotocol/servers": ("MCP servers", "GitHub · modelcontextprotocol/servers"),
}

RELEASE_CATEGORIES = ("model-release", "launch", "pricing", "deprecation")


def _lede(text: str) -> str:
    return f'<p class="lede">{text}</p>'


def _empty(what: str) -> str:
    return (
        f'<p class="empty">Nothing here yet — no {escape(what)} have come through the '
        f"sources so far. This page fills in as they do.</p>"
    )


# ------------------------------------------------------------------ versions


def latest_version(items: list[Item], source: str = NPM_CLAUDE_CODE) -> str:
    """Newest version string for a package, or "" when the store has none.

    Items arrive newest-first, so the first hit wins.
    """
    for item in items:
        if item.source == source and item.version:
            return item.version
    return ""


def body_versions(items: list[Item]) -> str:
    versioned = [i for i in items if i.version]
    if not versioned:
        return _empty("releases")

    order = list(PACKAGES) + sorted({i.source for i in versioned} - set(PACKAGES))
    out = [
        _lede(
            "Every release this tracker has seen, newest first, with the date it "
            "was published. Versions come from the npm registry and GitHub "
            "Releases directly, so they land here before the changelog pages "
            "catch up."
        )
    ]
    for source in order:
        rows = [i for i in versioned if i.source == source]
        if not rows:
            continue
        name, origin = PACKAGES.get(source, (source, source))
        out.append(
            f'<section class="table-block">'
            f"<h2>{escape(name)} <span class=\"origin\">{escape(origin)}</span></h2>"
            f'<div class="scroller"><table>'
            f"<thead><tr><th>Version</th><th>Released</th><th>Impact</th><th>Notes</th></tr></thead>"
            f"<tbody>"
        )
        for item in rows:
            label = IMPACT_LABEL.get(item.impact, item.impact)
            out.append(
                f'<tr data-impact="{escape(item.impact)}">'
                f'<td class="v"><a href="{escape(item.url)}" rel="noopener">{escape(item.version)}</a></td>'
                f'<td><time datetime="{escape(item.published)}">{item.dt.strftime("%d %b %Y")}</time></td>'
                f'<td><span class="impact">{escape(label)}</span></td>'
                f"<td>{escape(item.summary[:140])}</td>"
                f"</tr>"
            )
        out.append("</tbody></table></div></section>")
    return "\n".join(out)


# ------------------------------------------------------------------ breaking


def body_breaking(items: list[Item]) -> str:
    rows = [i for i in items if i.impact == "breaking"]
    lede = _lede(
        "Removals, deprecations and contract changes only — the entries you have "
        "to read. Everything else is filtered out. Subscribe to "
        '<a href="../feed-breaking.xml">the breaking-changes feed</a> to get only these.'
    )
    if not rows:
        return lede + _empty("breaking changes")

    out = [lede]
    for item in rows:
        detail = breaking_lines(item)
        bullets = (
            "<ul>" + "".join(f"<li>{escape(line)}</li>" for line in detail) + "</ul>"
            if detail
            else ""
        )
        out.append(
            f'<article class="entry" data-impact="breaking">'
            f'<div class="meta">'
            f'<time datetime="{escape(item.published)}">{item.dt.strftime("%d %b %Y")}</time>'
            + (f'<span class="version">{escape(item.version)}</span>' if item.version else "")
            + f'<span class="impact">breaking</span></div>'
            f"<div>"
            f'<h2><a href="{escape(item.url)}" rel="noopener">{escape(item.title)}</a></h2>'
            f"<p>{escape(item.summary)}</p>"
            f"{bullets}"
            f'<div class="source">{escape(item.source)} · {escape(item.category)}</div>'
            f"</div></article>"
        )
    return "\n".join(out)


# ------------------------------------------------------------------ releases


def body_releases(items: list[Item]) -> str:
    rows = [i for i in items if i.category in RELEASE_CATEGORIES]
    lede = _lede(
        "Model launches, pricing changes and deprecation notices, in date order. "
        "Routine SDK patches and community discussion are excluded — this is the "
        "platform-level record."
    )
    if not rows:
        return lede + _empty("model releases or pricing changes")

    out = [lede]
    year = None
    for item in rows:
        if item.dt.year != year:
            year = item.dt.year
            out.append(f'<h2 class="year">{year}</h2>')
        out.append(
            f'<article class="entry" data-impact="{escape(item.impact)}">'
            f'<div class="meta">'
            f'<time datetime="{escape(item.published)}">{item.dt.strftime("%d %b %Y")}</time>'
            f'<span class="impact">{escape(item.category)}</span></div>'
            f"<div>"
            f'<h3><a href="{escape(item.url)}" rel="noopener">{escape(item.title)}</a></h3>'
            f"<p>{escape(item.summary)}</p>"
            f'<div class="source">{escape(item.source)}</div>'
            f"</div></article>"
        )
    return "\n".join(out)


# --------------------------------------------------------------------- badge


def render_badge(items: list[Item], label: str = "claude code") -> str:
    """A shields-style SVG of the current Claude Code version.

    Meant to be embedded in other people's READMEs. Every embed is a backlink
    and a referral path, which is worth more than another meta tag.
    """
    value = latest_version(items) or "unknown"
    # Verdana at 11px averages a shade over 6px per character; the padding
    # either side is 10px, matching the shields.io proportions people expect.
    lw = int(len(label) * 6.2) + 20
    rw = int(len(value) * 6.6) + 20
    w = lw + rw
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{escape(label)}: {escape(value)}">
<title>{escape(label)}: {escape(value)}</title>
<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>
<g clip-path="url(#r)">
<rect width="{lw}" height="20" fill="#101418"/>
<rect x="{lw}" width="{rw}" height="20" fill="#2E5E4E"/>
<rect width="{w}" height="20" fill="url(#s)"/>
</g>
<g fill="#fff" text-anchor="middle" font-family="Verdana,DejaVu Sans,Geneva,sans-serif" font-size="11">
<text x="{lw / 2:.0f}" y="15" fill="#010101" fill-opacity=".3">{escape(label)}</text>
<text x="{lw / 2:.0f}" y="14">{escape(label)}</text>
<text x="{lw + rw / 2:.0f}" y="15" fill="#010101" fill-opacity=".3">{escape(value)}</text>
<text x="{lw + rw / 2:.0f}" y="14">{escape(value)}</text>
</g>
</svg>
"""
