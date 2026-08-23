"""Output: RSS 2.0, a JSON feed, and the static site.

All three are written to docs/, which is what GitHub Pages serves. Nothing here
touches a database or a template engine — the whole site is one string.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path

from .models import Item

DOCS = Path("docs")

SITE_TITLE = "frontierfeed"
SITE_TAGLINE = "Release and news tracker for Anthropic's Claude"
SITE_URL = "https://saadrahman01.github.io/frontierfeed"
REPO_URL = "https://github.com/SaadRahman01/frontierfeed"

IMPACT_LABEL = {
    "breaking": "breaking",
    "feature": "new",
    "fix": "fix",
    "info": "note",
}


# --------------------------------------------------------------------------- RSS


def render_rss(items: list[Item], limit: int = 100) -> str:
    now = format_datetime(datetime.now(timezone.utc))
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        f"<title>{escape(SITE_TITLE)}</title>",
        f"<link>{escape(SITE_URL)}</link>",
        f"<description>{escape(SITE_TAGLINE)}. Unofficial; not affiliated with Anthropic.</description>",
        "<language>en</language>",
        f"<lastBuildDate>{now}</lastBuildDate>",
        f'<atom:link href="{escape(SITE_URL)}/feed.xml" rel="self" type="application/rss+xml"/>',
    ]
    for item in items[:limit]:
        label = IMPACT_LABEL.get(item.impact, item.impact)
        title = f"[{label}] {item.title}" if item.impact == "breaking" else item.title
        parts += [
            "<item>",
            f"<title>{escape(title)}</title>",
            f"<link>{escape(item.url)}</link>",
            f"<guid isPermaLink=\"false\">frontierfeed:{item.uid}</guid>",
            f"<pubDate>{format_datetime(item.dt)}</pubDate>",
            f"<category>{escape(item.category)}</category>",
            f"<description>{escape(item.summary)}</description>",
            "</item>",
        ]
    parts += ["</channel>", "</rss>"]
    return "\n".join(parts)


# -------------------------------------------------------------------------- JSON


def render_json(items: list[Item]) -> str:
    return json.dumps(
        {
            "title": SITE_TITLE,
            "description": SITE_TAGLINE,
            "generated": datetime.now(timezone.utc).isoformat(),
            "count": len(items),
            "items": [i.to_dict() for i in items],
        },
        indent=2,
    )


# -------------------------------------------------------------------------- HTML

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
  font-family: Archivo, system-ui, sans-serif;
  font-weight: 800; font-stretch: 88%;
  font-size: clamp(2.4rem, 9vw, 4.25rem);
  letter-spacing: -0.035em; line-height: 0.95; margin: 0;
}
.tagline { margin: 0.5rem 0 0; max-width: 34rem; color: var(--ink-soft); }

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

.entry h2 {
  font-family: Archivo, system-ui, sans-serif;
  font-weight: 700; font-stretch: 92%;
  font-size: 1.12rem; line-height: 1.3; letter-spacing: -0.015em;
  margin: 0 0 0.35rem;
}
.entry h2 a { color: inherit; text-decoration: none; box-shadow: inset 0 -1px 0 var(--rule); }
.entry h2 a:hover { box-shadow: inset 0 -2px 0 var(--ink); }
.entry h2 a:focus-visible { outline: 2px solid var(--breaking); outline-offset: 3px; }
.entry p { margin: 0; color: var(--ink-soft); font-size: 0.94rem; }
.source {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.7rem; color: var(--ink-soft); margin-top: 0.55rem;
}

.empty { padding: 3rem 0; text-align: center; color: var(--ink-soft); }

.colophon {
  margin-top: 3rem; padding-top: 1.25rem;
  border-top: 1px solid var(--rule);
  font-size: 0.84rem; color: var(--ink-soft);
}
.colophon a { color: var(--ink); }

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


def render_html(items: list[Item]) -> str:
    now = datetime.now(timezone.utc)
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

    body = "\n".join(rows) or '<p class="empty">No entries yet. Run the update job to populate the feed.</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(SITE_TITLE)} — {escape(SITE_TAGLINE)}</title>
<meta name="description" content="{escape(SITE_TAGLINE)}. Unofficial, open source, updated hourly.">
<link rel="alternate" type="application/rss+xml" title="{escape(SITE_TITLE)}" href="feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;700;800&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <p class="eyebrow">Unofficial · not affiliated with Anthropic</p>
    <h1 class="wordmark">{escape(SITE_TITLE)}</h1>
    <p class="tagline">{escape(SITE_TAGLINE)}. Every model release, API change, and Claude Code build, pulled from the sources that publish them first.</p>
  </header>

  <section class="board" aria-label="Totals for the selected date range">
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

  <main>
{body}
    <p class="empty no-match" hidden>No entries match these filters.</p>
  </main>

  <footer class="colophon">
    <p>Updated {now.strftime('%d %b %Y, %H:%M')} UTC. Subscribe via <a href="feed.xml">RSS</a> or read the raw <a href="items.json">JSON</a>.</p>
    <p>Open source at <a href="{REPO_URL}">{escape(REPO_URL.replace('https://', ''))}</a>. Claude and Anthropic are trademarks of Anthropic, PBC. This project is independent and not endorsed by or affiliated with Anthropic.</p>
  </footer>
</div>
<script>{JS}</script>
</body>
</html>
"""


def write_all(items: list[Item], docs: Path = DOCS) -> None:
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "feed.xml").write_text(render_rss(items), encoding="utf-8")
    (docs / "items.json").write_text(render_json(items), encoding="utf-8")
    (docs / "index.html").write_text(render_html(items), encoding="utf-8")
    (docs / ".nojekyll").write_text("", encoding="utf-8")
