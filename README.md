# The Bulletin

A personal news bulletin: Claude Code researches a configurable set of topics, writes a
sourced update that separates established facts from claims and opinion, and publishes it
to GitHub Pages.

## How it works

1. **Topics** are Markdown briefs in [`topics/`](topics/README.md): scope, inclusions,
   exclusions, preferred sources, RSS feeds to scan and an update cadence.
2. The **`/update-bulletin`** skill ([`.claude/skills/update-bulletin/`](.claude/skills/update-bulletin/SKILL.md))
   picks the topics to refresh, runs one research agent per topic following
   [`research-method.md`](.claude/skills/update-bulletin/research-method.md), edits the results
   and commits them under `updates/<topic>/<date>.md`. The agents read articles with
   `uv run scripts/fetch_page.py <url>`, which prints a page as Markdown and retries with
   headless Chrome when a site refuses a plain request.
3. A push to `main` runs [`deploy.yml`](.github/workflows/deploy.yml), which renders the site
   with `scripts/bulletin.py build` and deploys it to GitHub Pages.

## Running an update

In Claude Code, in this repository:

```
/update-bulletin                 # topics whose cadence_days has elapsed (what the daily job runs)
/update-bulletin all             # every enabled topic
/update-bulletin tech science    # just these topics
```

A scheduled cloud Claude Code session runs `/update-bulletin due` every day. Give a topic
`cadence_days: 3` to have it refreshed every third day, or create extra scheduled tasks
with explicit topic ids for other rhythms.

## Local preview

```bash
uv run scripts/bulletin.py build && uv run python -m http.server -d _site
```

## One-time GitHub setup

- Settings → Pages → Source: **GitHub Actions** (needs a public repo, or a paid plan for private repos).
- Settings → Actions → General → Workflow permissions: **Read and write** (lets
  `promote-bulletin.yml` merge bulletin branches into `main`).
