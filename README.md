# frontierfeed

Release and news tracker for Anthropic's Claude. Every model release, API change, deprecation, and Claude Code build, pulled from the sources that publish them first and rendered as an RSS feed, a JSON feed, and a static page.

**Live feed:** https://saadrahman01.github.io/frontierfeed/feed.xml
**Site:** https://saadrahman01.github.io/frontierfeed

> Unofficial. Not affiliated with, endorsed by, or sponsored by Anthropic. Claude and Anthropic are trademarks of Anthropic, PBC.

## Why this exists

Anthropic ships fast and the announcements are scattered: model launches on the news page, API changes in the docs changelog, Claude Code builds on npm hours before the changelog updates, policy shifts in legal pages nobody subscribes to. The news page has no official RSS feed. This pulls all of it into one place and flags the entries that will actually break your code.

## It costs nothing to run

That's a design constraint, not a happy accident.

- **Compute** — GitHub Actions on a public repo. Free minutes, no cap that matters for an hourly job.
- **Storage** — the feed is committed into the repo. No database.
- **Hosting** — GitHub Pages serves `docs/`.
- **Sources** — every source is a free, keyless, public endpoint.
- **Classification** — rules, not a model. See below.

The only optional cost is AI-written summaries, which are off by default. See [Optional summaries](#optional-ai-summaries).

## Sources

| Source | What it catches | Notes |
| --- | --- | --- |
| npm registry | Claude Code builds | The `time` map gives version → publish timestamp. Usually the earliest public signal, ahead of the changelog page. |
| Claude Code changelog | Official release notes | Anthropic publishes a native RSS feed for this one. |
| Anthropic news / engineering / Claude blog | Launches, research, policy | No official feed exists, so these point at community-regenerated mirrors. Swap in the official URL the day one appears — each feed is a config line, not code. |
| GitHub Releases | SDKs, actions, MCP servers | Uses the free `GITHUB_TOKEN` inside Actions for a 5000/hr limit. |
| Hacker News (Algolia) | Outages, pricing reactions, third-party writeups | Keyless. `min_points` filters the noise. |
| arXiv | Research papers | Rate-limited to one request per three seconds, as arXiv asks. |

Everything is declared in `config.yaml`. Adding a source is a few lines of YAML; adding a *kind* of source is one module in `src/sources/`.

## Classification without a model

Release notes in this ecosystem follow a consistent house style — lines open with Added / Changed / Fixed / Removed, and deprecations say so plainly. `src/classify.py` pattern-matches that and reads impact straight off the semver bump when the prose says nothing useful.

This is deliberate. Severity is the one judgement you want identical on every run, and a regex gives you that for free while a model does not.

Each entry lands in one of four impact levels — `breaking`, `feature`, `fix`, `info` — which drive the coloured gauge on the site and the `[breaking]` prefix in the RSS titles.

## Setup

```bash
git clone https://github.com/SaadRahman01/frontierfeed
cd frontierfeed
pip install -r requirements.txt
python -m src.main
```

Useful flags:

```bash
python -m src.main --dry-run      # fetch and classify, write nothing
python -m src.main --offline      # re-render the site from stored items
python -m src.main --reclassify   # re-run the rules over everything after editing classify.py
```

To publish it:

1. Push to `main`.
2. **Settings → Pages → Source: Deploy from a branch**, branch `main`, folder `/docs`.
3. **Settings → Actions → General → Workflow permissions → Read and write**, so the job can commit the updated feed.
4. Run **Actions → Update feed → Run workflow** once to seed it. After that it runs hourly.

Add `claude`, `anthropic`, `rss`, and `changelog` as repo topics — that's how people will find it, and it keeps the trademark out of the project name where it doesn't belong.

## Optional AI summaries

Off by default. Without a key, entries use the rule-based summary and the whole thing stays free.

To turn them on, add `ANTHROPIC_API_KEY` as a repository secret. Only items that are *new* in a given run are ever sent, so cost tracks what actually shipped rather than how often the job runs. On Haiku that's roughly a dollar a month at ten new items a day.

Set a spend limit in the Console before you enable this. A misconfigured loop on an hourly cron is the one way this project can cost you real money.

Use an API key from the Console. Do not wire this to Claude Pro or Max subscription credentials — using consumer OAuth tokens in third-party tools violates Anthropic's terms and will get accounts suspended.

## Being a good citizen

Every request sends `If-None-Match` / `If-Modified-Since` from the previous run, so unchanged sources cost the upstream server a 304 and nothing else. The User-Agent identifies the project and links back here. Entries link out to the original and never reproduce full article text.

If you maintain a source and want it dropped, open an issue and it'll be removed.

## Layout

```
src/
  main.py         pipeline: fetch → dedupe → classify → render
  models.py       the Item shape everything else agrees on
  http.py         conditional-request caching
  classify.py     the rules
  render.py       RSS, JSON, and the static site
  summarize.py    optional, bring-your-own-key
  sources/        one module per kind of source
config.yaml       what to fetch
data/             committed state: items and HTTP cache
docs/             published output
```

## License

MIT.
