"""The static site.

Everything is written to docs/, which is what GitHub Pages serves. No database
and no template engine — a page is one string. This module owns the shared
shell (head, masthead, nav, colophon) and the index; the compiled pages live in
pages.py and the feeds in feeds.py.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from . import feeds, pages
from .models import Item
from .site import (
    CANONICAL,
    IMPACT_LABEL,
    OG_IMAGE,
    PAGES,
    REPO_URL,
    SITE_DESC,
    SITE_TAGLINE,
    SITE_TITLE,
    SITE_URL,
    base_prefix,
    page_url,
)

DOCS = Path("docs")

CSS = """
:root {
  --ink: #101418;
  --ink-soft: #4C555E;
  --paper: #E6E9E4;
  --card: #F3F5F1;
  --rule: #C3CAC2;
  --breaking: #8E1B2E;
  --feature: #2E5E4E;
  --fix: #626D78;
  --gauge: 6px;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "IBM Plex Sans", system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.55;
}
.wrap { max-width: 62rem; margin: 0 auto; padding: 2.5rem 1.25rem 5rem; }

.masthead { border-bottom: 2px solid var(--ink); padding-bottom: 1.25rem; }
.eyebrow {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--ink-soft); margin: 0 0 0.4rem;
}
.wordmark {
  display: block;
  font-family: Archivo, system-ui, sans-serif;
  font-weight: 800; font-stretch: 88%;
  font-size: clamp(2.4rem, 9vw, 4.25rem);
  letter-spacing: -0.035em; line-height: 0.95; margin: 0;
  color: var(--ink); text-decoration: none;
}
a.wordmark { font-size: clamp(1.6rem, 5vw, 2.2rem); }
.pagetitle {
  font-family: Archivo, system-ui, sans-serif;
  font-weight: 800; font-stretch: 88%;
  font-size: clamp(1.9rem, 6vw, 3rem);
  letter-spacing: -0.03em; line-height: 1.02; margin: 0.6rem 0 0;
}
.tagline { margin: 0.5rem 0 0; max-width: 34rem; color: var(--ink-soft); }
.lede { margin: 1.25rem 0 1.75rem; max-width: 44rem; color: var(--ink-soft); }

.sitenav {
  display: flex; flex-wrap: wrap; gap: 0 1.25rem;
  padding: 0.85rem 0; border-bottom: 1px solid var(--rule);
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
}
.sitenav a { color: var(--ink-soft); text-decoration: none; padding: 0.15rem 0; }
.sitenav a:hover { color: var(--ink); box-shadow: inset 0 -2px 0 var(--ink); }
.sitenav a[aria-current="page"] { color: var(--ink); box-shadow: inset 0 -2px 0 var(--ink); }
.sitenav a:focus-visible { outline: 2px solid var(--breaking); outline-offset: 2px; }

.board {
  display: flex; flex-wrap: wrap; gap: 0 2.5rem;
  border-bottom: 1px solid var(--rule);
  padding: 1rem 0; margin-bottom: 0.5rem;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
}
.board div { padding-right: 0.5rem; }
.board b {
  display: block; font-size: 1.9rem; font-weight: 600; line-height: 1.1;
  font-variant-numeric: tabular-nums;
}
.board span {
  font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--ink-soft);
}
.board .is-breaking b { color: var(--breaking); }
.board .is-feature b { color: var(--feature); }

.filterbar { padding: 1rem 0 1.5rem; }
.filters { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; }
.filters + .filters { margin-top: 0.5rem; }
.filters .legend {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--ink-soft); width: 4.5rem; flex: none;
}
.filters button {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
  background: transparent; color: var(--ink-soft);
  border: 1px solid var(--rule); border-radius: 0;
  padding: 0.35rem 0.7rem; cursor: pointer;
}
.filters button[aria-pressed="true"] {
  background: var(--ink); border-color: var(--ink); color: var(--card);
}
.filters button:focus-visible { outline: 2px solid var(--breaking); outline-offset: 2px; }

.entry {
  display: grid;
  grid-template-columns: 8.5rem 1fr;
  gap: 0 1.5rem;
  border-left: var(--gauge) solid var(--fix);
  background: var(--card);
  padding: 1.1rem 1.35rem;
  margin-bottom: 0.4rem;
}
.entry[data-impact="breaking"] { border-left-color: var(--breaking); }
.entry[data-impact="feature"] { border-left-color: var(--feature); }
.entry[data-impact="info"] { border-left-color: var(--rule); }
.entry[hidden] { display: none; }

.meta { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 0.75rem; color: var(--ink-soft); }
.meta time { display: block; font-variant-numeric: tabular-nums; }
.version {
  display: block; margin-top: 0.35rem;
  font-size: 1.35rem; font-weight: 600; color: var(--ink);
  letter-spacing: -0.02em; word-break: break-all;
}
.impact {
  display: inline-block; margin-top: 0.5rem;
  font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase;
}
.entry[data-impact="breaking"] .impact { color: var(--breaking); font-weight: 600; }
.entry[data-impact="feature"] .impact { color: var(--feature); }

.entry h2, .entry h3 {
  font-family: Archivo, system-ui, sans-serif;
  font-weight: 700; font-stretch: 92%;
  font-size: 1.12rem; line-height: 1.3; letter-spacing: -0.015em;
  margin: 0 0 0.35rem;
}
.entry h2 a, .entry h3 a { color: inherit; text-decoration: none; box-shadow: inset 0 -1px 0 var(--rule); }
.entry h2 a:hover, .entry h3 a:hover { box-shadow: inset 0 -2px 0 var(--ink); }
.entry h2 a:focus-visible, .entry h3 a:focus-visible { outline: 2px solid var(--breaking); outline-offset: 3px; }
.entry p { margin: 0; color: var(--ink-soft); font-size: 0.94rem; }
.entry ul { margin: 0.6rem 0 0; padding-left: 1.1rem; color: var(--ink); font-size: 0.9rem; }
.entry li { margin-bottom: 0.25rem; }
.source {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.7rem; color: var(--ink-soft); margin-top: 0.55rem;
}

.year {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.8rem; letter-spacing: 0.14em; color: var(--ink-soft);
  margin: 2rem 0 0.6rem; padding-bottom: 0.3rem;
  border-bottom: 1px solid var(--rule);
}

.table-block { margin: 0 0 2.5rem; }
.table-block h2 {
  font-family: Archivo, system-ui, sans-serif;
  font-weight: 800; font-stretch: 88%; font-size: 1.4rem;
  letter-spacing: -0.02em; margin: 0 0 0.75rem;
}
.table-block .origin {
  display: block;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.68rem; font-weight: 400; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-soft); margin-top: 0.2rem;
}
.scroller { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; background: var(--card); font-size: 0.9rem; }
th, td { text-align: left; padding: 0.55rem 0.85rem; border-bottom: 1px solid var(--rule); vertical-align: top; }
th {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.66rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--ink-soft); border-bottom: 1px solid var(--ink); white-space: nowrap;
}
td time { font-variant-numeric: tabular-nums; white-space: nowrap; }
td.v { font-family: "IBM Plex Mono", ui-monospace, monospace; font-weight: 600; white-space: nowrap; }
td.v a { color: var(--ink); text-decoration: none; box-shadow: inset 0 -1px 0 var(--rule); }
td.v a:hover { box-shadow: inset 0 -2px 0 var(--ink); }
tr[data-impact="breaking"] td.v a { color: var(--breaking); }
td .impact { margin-top: 0; color: var(--ink-soft); }

.empty { padding: 3rem 0; text-align: center; color: var(--ink-soft); }

.colophon {
  margin-top: 3rem; padding-top: 1.25rem;
  border-top: 1px solid var(--rule);
  font-size: 0.84rem; color: var(--ink-soft);
}
.colophon a { color: var(--ink); }
.colophon code {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.78rem; background: var(--card); padding: 0.1rem 0.3rem;
  word-break: break-all;
}

@media (max-width: 40rem) {
  .entry { grid-template-columns: 1fr; gap: 0.6rem; }
  .version { display: inline; margin-right: 0.6rem; font-size: 1.1rem; }
  .impact { margin-top: 0; }
}
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
"""

JS = """
const entries = document.querySelectorAll('.entry');
const noMatch = document.querySelector('.no-match');
const state = { impact: 'all', days: 'all' };

function apply() {
  const cutoff = state.days === 'all'
    ? -Infinity
    : Date.now() / 1000 - Number(state.days) * 86400;
  // The board tracks the date range only — narrowing by impact should not zero
  // out the other columns.
  const tally = { breaking: 0, feature: 0, other: 0, total: 0 };
  let shown = 0;
  entries.forEach(e => {
    const impact = e.dataset.impact;
    const inRange = Number(e.dataset.ts) >= cutoff;
    if (inRange) {
      tally[impact in tally ? impact : 'other']++;
      tally.total++;
    }
    const hide = !inRange || (state.impact !== 'all' && impact !== state.impact);
    e.hidden = hide;
    if (!hide) shown++;
  });
  for (const [key, n] of Object.entries(tally)) {
    const el = document.querySelector(`[data-count="${key}"]`);
    if (el) el.textContent = n;
  }
  if (noMatch) noMatch.hidden = shown > 0;
}

document.querySelectorAll('.filters').forEach(group => {
  const key = group.dataset.group;
  const buttons = group.querySelectorAll('button');
  buttons.forEach(btn => btn.addEventListener('click', () => {
    state[key] = btn.dataset.filter;
    buttons.forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
    apply();
  }));
});
"""


# ----------------------------------------------------------------- analytics

# Cloudflare beacon tokens are hex; anything else is a misconfiguration and is
# dropped rather than interpolated into a script tag.
_CF_TOKEN = re.compile(r"\A[A-Za-z0-9]{8,64}\Z")


def _beacon(token: str) -> str:
    """The Cloudflare Web Analytics tag, or nothing when no token is set."""
    token = (token or "").strip()
    if not _CF_TOKEN.match(token):
        return ""
    return (
        '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
        f'data-cf-beacon=\'{{"token":"{token}"}}\'></script>'
    )


# ------------------------------------------------------------------- json-ld


def _jsonld(slug: str, title: str, desc: str, items: list[Item], now: datetime) -> str:
    """schema.org description of a page.

    Titles come from remote feeds, so the payload is JSON-encoded and `</` is
    escaped — a title containing `</script>` must not be able to close the tag.
    """
    url = page_url(slug)
    graph: list[dict] = [
        {
            "@type": "WebSite",
            "@id": f"{SITE_URL}/#website",
            "url": CANONICAL,
            "name": SITE_TITLE,
            "description": SITE_DESC,
            "inLanguage": "en",
        },
        {
            "@type": "CollectionPage",
            "@id": f"{url}#webpage",
            "url": url,
            "name": title,
            "description": desc,
            "inLanguage": "en",
            "isPartOf": {"@id": f"{SITE_URL}/#website"},
            "dateModified": now.isoformat(timespec="seconds"),
            "primaryImageOfPage": {"@id": f"{SITE_URL}/#ogimage"},
        },
        {
            "@type": "ImageObject",
            "@id": f"{SITE_URL}/#ogimage",
            "url": OG_IMAGE,
            "width": 1200,
            "height": 630,
        },
    ]

    if slug:
        crumbs = [{"@type": "ListItem", "position": 1, "name": SITE_TITLE, "item": CANONICAL}]
        parts = slug.strip("/").split("/")
        for n, _ in enumerate(parts, 1):
            sub = "/".join(parts[:n])
            crumbs.append(
                {
                    "@type": "ListItem",
                    "position": n + 1,
                    "name": PAGES.get(sub, (parts[n - 1],))[0],
                    "item": page_url(sub),
                }
            )
        graph.append({"@type": "BreadcrumbList", "itemListElement": crumbs})

    if items:
        graph.append(
            {
                "@type": "ItemList",
                "@id": f"{url}#itemlist",
                "name": title,
                "numberOfItems": len(items),
                "itemListOrder": "https://schema.org/ItemListOrderDescending",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": n,
                        "item": {
                            "@type": "WebPage",
                            "@id": item.url,
                            "url": item.url,
                            "name": item.title,
                            "datePublished": item.published,
                        },
                    }
                    for n, item in enumerate(items[:20], 1)
                ],
            }
        )
        graph[1]["mainEntity"] = {"@id": f"{url}#itemlist"}

    payload = json.dumps(
        {"@context": "https://schema.org", "@graph": graph},
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    return f'<script type="application/ld+json">{payload}</script>'


# --------------------------------------------------------------------- shell


def _nav(slug: str, base: str) -> str:
    links = []
    for other, (label, _, _) in PAGES.items():
        href = base if not other else f"{base}{other}/"
        current = ' aria-current="page"' if other == slug else ""
        links.append(f'<a href="{href}"{current}>{escape(label)}</a>')
    return f'<nav class="sitenav" aria-label="Sections">{"".join(links)}</nav>'


def page(
    slug: str,
    body: str,
    *,
    now: datetime,
    token: str = "",
    jsonld_items: list[Item] | None = None,
    scripts: str = "",
) -> str:
    label, title, desc = PAGES[slug]
    base = base_prefix(slug)
    url = page_url(slug)
    jsonld = _jsonld(slug, title, desc, jsonld_items or [], now)
    beacon = _beacon(token)

    if slug:
        heading = (
            f'<a class="wordmark" href="{base}">{escape(SITE_TITLE)}</a>'
            f'<h1 class="pagetitle">{escape(title.split(" — ")[0])}</h1>'
        )
    else:
        heading = (
            f'<h1 class="wordmark">{escape(SITE_TITLE)}</h1>'
            f'<p class="tagline">{escape(SITE_TAGLINE)}. Every model release, API change, '
            f"and Claude Code build, pulled from the sources that publish them first.</p>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{escape(url)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#101418">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{escape(SITE_TITLE)}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{escape(url)}">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="{escape(OG_IMAGE)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{escape(SITE_TITLE)} — {escape(SITE_TAGLINE)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title)}">
<meta name="twitter:description" content="{escape(desc)}">
<meta name="twitter:image" content="{escape(OG_IMAGE)}">
<link rel="alternate" type="application/rss+xml" title="{escape(SITE_TITLE)} RSS" href="{base}feed.xml">
<link rel="alternate" type="application/feed+json" title="{escape(SITE_TITLE)} JSON Feed" href="{base}feed.json">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;700;800&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
{jsonld}
{beacon}
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <p class="eyebrow">Unofficial · not affiliated with Anthropic</p>
    {heading}
  </header>
  {_nav(slug, base)}

  <main>
{body}
  </main>

  <footer class="colophon">
    <p>Updated {now.strftime('%d %b %Y, %H:%M')} UTC. Subscribe to
      <a href="{base}feed.xml">everything</a>,
      <a href="{base}feed-breaking.xml">breaking changes only</a>,
      <a href="{base}feed-claude-code.xml">Claude Code only</a> or
      <a href="{base}feed-releases.xml">model releases only</a> —
      or read the <a href="{base}feed.json">JSON Feed</a> or raw <a href="{base}items.json">JSON</a>.</p>
    <p>Embed the current Claude Code version anywhere:
      <code>![Claude Code]({SITE_URL}/badge/claude-code-version.svg)</code></p>
    <p>Open source at <a href="{REPO_URL}">{escape(REPO_URL.replace('https://', ''))}</a>. Claude and Anthropic are trademarks of Anthropic, PBC. This project is independent and not endorsed by or affiliated with Anthropic.</p>
  </footer>
</div>
{scripts}
</body>
</html>
"""


# --------------------------------------------------------------------- index


def body_index(items: list[Item]) -> str:
    # The board counts whatever the date filter selects; on first paint that is
    # everything, and the script recounts from there.
    counts = {
        "breaking": sum(1 for i in items if i.impact == "breaking"),
        "feature": sum(1 for i in items if i.impact == "feature"),
        "other": sum(1 for i in items if i.impact in ("fix", "info")),
    }

    rows = []
    for item in items:
        version = f'<span class="version">{escape(item.version)}</span>' if item.version else ""
        rows.append(
            f'<article class="entry" data-impact="{escape(item.impact)}"'
            f' data-ts="{int(item.dt.timestamp())}">'
            f'<div class="meta">'
            f'<time datetime="{escape(item.published)}">{item.dt.strftime("%d %b %Y")}</time>'
            f"{version}"
            f'<span class="impact">{escape(IMPACT_LABEL.get(item.impact, item.impact))}</span>'
            f"</div>"
            f"<div>"
            f'<h2><a href="{escape(item.url)}" rel="noopener">{escape(item.title)}</a></h2>'
            f"<p>{escape(item.summary)}</p>"
            f'<div class="source">{escape(item.source)} · {escape(item.category)}</div>'
            f"</div>"
            f"</article>"
        )

    entries = "\n".join(rows) or '<p class="empty">No entries yet. Run the update job to populate the feed.</p>'

    return f"""  <section class="board" aria-label="Totals for the selected date range">
    <div class="is-breaking"><b data-count="breaking">{counts['breaking']}</b><span>Breaking</span></div>
    <div class="is-feature"><b data-count="feature">{counts['feature']}</b><span>New</span></div>
    <div><b data-count="other">{counts['other']}</b><span>Other</span></div>
    <div><b data-count="total">{len(items)}</b><span>Tracked</span></div>
  </section>

  <div class="filterbar">
    <nav class="filters" data-group="impact" aria-label="Filter by impact">
      <span class="legend" aria-hidden="true">Impact</span>
      <button data-filter="all" aria-pressed="true">All</button>
      <button data-filter="breaking" aria-pressed="false">Breaking</button>
      <button data-filter="feature" aria-pressed="false">New</button>
      <button data-filter="fix" aria-pressed="false">Fixes</button>
    </nav>
    <nav class="filters" data-group="days" aria-label="Filter by date">
      <span class="legend" aria-hidden="true">Date</span>
      <button data-filter="all" aria-pressed="true">Any time</button>
      <button data-filter="1" aria-pressed="false">24 hours</button>
      <button data-filter="7" aria-pressed="false">7 days</button>
      <button data-filter="30" aria-pressed="false">30 days</button>
      <button data-filter="90" aria-pressed="false">90 days</button>
    </nav>
  </div>

{entries}
    <p class="empty no-match" hidden>No entries match these filters.</p>"""


# ----------------------------------------------------------- robots, sitemap


def render_robots() -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"


def render_sitemap(now: datetime) -> str:
    stamp = now.strftime("%Y-%m-%d")
    urls = "".join(
        f"<url><loc>{escape(page_url(slug))}</loc><lastmod>{stamp}</lastmod>"
        f"<changefreq>hourly</changefreq>"
        f"<priority>{'1.0' if not slug else '0.8'}</priority></url>\n"
        for slug in PAGES
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}"
        "</urlset>\n"
    )


# --------------------------------------------------------------------- write


def write_all(items: list[Item], docs: Path = DOCS, config: dict | None = None) -> None:
    token = ((config or {}).get("analytics") or {}).get("cloudflare_token") or ""
    now = datetime.now(timezone.utc)
    docs.mkdir(parents=True, exist_ok=True)

    # Feeds.
    for name, label, keep in feeds.FEEDS:
        subset = [i for i in items if keep(i)]
        (docs / name).write_text(feeds.render_rss(subset, label=label, path=name), encoding="utf-8")
    (docs / "feed.json").write_text(feeds.render_jsonfeed(items), encoding="utf-8")
    (docs / "items.json").write_text(feeds.render_items_json(items), encoding="utf-8")

    # Pages. The index carries the filter script; the rest are static.
    written = {
        "": (body_index(items), items, f"<script>{JS}</script>"),
        "claude-code/versions": (pages.body_versions(items), [i for i in items if i.version], ""),
        "breaking": (pages.body_breaking(items), [i for i in items if i.impact == "breaking"], ""),
        "releases": (
            pages.body_releases(items),
            [i for i in items if i.category in pages.RELEASE_CATEGORIES],
            "",
        ),
    }
    for slug, (body, listed, scripts) in written.items():
        out = docs / (slug or "") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            page(slug, body, now=now, token=token, jsonld_items=listed, scripts=scripts),
            encoding="utf-8",
        )

    # Embeddable badge — every README that uses it is a backlink.
    badge = docs / "badge" / "claude-code-version.svg"
    badge.parent.mkdir(parents=True, exist_ok=True)
    badge.write_text(pages.render_badge(items), encoding="utf-8")

    (docs / "robots.txt").write_text(render_robots(), encoding="utf-8")
    (docs / "sitemap.xml").write_text(render_sitemap(now), encoding="utf-8")
    (docs / ".nojekyll").write_text("", encoding="utf-8")
    # docs/og.png is a committed static asset — see tools/make_og.py.
