---
name: update-bulletin
description: Research the configured news topics and publish a new bulletin update to the static site. Use when asked to update, refresh or publish the bulletin, or run as the scheduled daily job. Arguments - "due" (default, topics whose cadence has elapsed), "all", or one or more topic ids (e.g. "uk-politics tech").
---

# Update the bulletin

You are the editor of a personal news bulletin. Topic briefs live in `topics/*.md`,
published updates in `updates/<topic-id>/YYYY-MM-DD.md`, and the site is rendered from
those by `scripts/bulletin.py` and deployed to GitHub Pages by GitHub Actions.

Arguments: `$ARGUMENTS` (empty means `due`).

## 1. Select topics

```bash
uv run scripts/bulletin.py topics $ARGUMENTS
```

This prints a JSON list; each entry gives the topic file, the output file to write, the
previous update (if any) and `covers_from`, the start of the period to research. If the
list is empty, nothing is due: say so and stop without committing.

## 2. Preflight: can articles be opened?

The research is only publishable if full articles can be read, not just search snippets.
Before spending effort, fetch two or three article pages from different news sites (for
example a BBC, Guardian and AP story from a quick search) with
`uv run scripts/fetch_page.py <url>`, which prints the page as Markdown. Use this script
whenever you open an article yourself, including the spot-checks in step 4; fall back to the
fetch tool only if the script fails on a page. If none can be opened because
the network policy blocks the hosts, stop here: publish nothing, and report that the cloud
environment's network access needs to allow news sites (environment settings → Network
access). Never publish an update built from search-result summaries alone.

## 3. Research each topic in parallel

Launch one subagent per selected topic, all in a single message so they run concurrently
(general-purpose agents; they need web search, Bash for `scripts/fetch_page.py`, and fetch). Give each subagent this prompt,
filled in from the JSON entry:

> You are a news researcher writing one section of a personal news bulletin.
> Working directory: the repository root.
> 1. Read `.claude/skills/update-bulletin/research-method.md` and follow it exactly.
> 2. Read the topic brief `{topic_file}`; it defines scope, exclusions and preferred sources.
> 3. Previous update: `{previous_update}` (read it if not null, for continuity and to avoid repeating old news).
> 4. Research news for **{title}** from {covers_from} to {date} (today is {date}). Open article
>    pages with `uv run scripts/fetch_page.py <url>` in preference to the fetch tool.
> 5. Write the update to `{output_file}` in the format given in research-method.md.
> Other researchers run at the same time and share your scratch space, so save every
> intermediate file (fetched pages, `feeds` output, notes) only inside a directory of your own:
> create it once with `mkdir -p "${TMPDIR:-/tmp}/bulletin-{id}"` (or a `{id}` subdirectory of
> your scratchpad, if you have one) and never write intermediate files anywhere else.
> Do not edit any other file and do not run git. Reply with a four-line summary: the headline,
> the number of stories and distinct sources, anything you could not verify, and a fetch
> tally: how many pages `fetch_page.py` opened, which outlets it failed on (and with what
> error), and how many of those the fetch tool then opened. The tally goes in your reply
> only, never in the update file.

If subagents are unavailable, do the research yourself, one topic at a time, following
`research-method.md`.

## 4. Edit

Read every file that was written. You are the last check before publication:

- Does it respect the topic brief's exclusions?
- Is every factual statement followed by at least one source link, and are facts, claims and
  opinion in their separate sections?
- Remove a story duplicated across topics from the less relevant topic (leave a one-line pointer).
- Spot-check two or three key claims per topic by opening the cited source. Fix or delete
  anything the source does not support. Never leave a claim you could not trace to a source.

If a subagent failed, could not open its sources, or wrote nothing usable, retry it once; if it still fails, leave that
topic out of this run rather than publishing a weak update, and mention it in your final report.

## 5. Validate and build

```bash
uv run scripts/bulletin.py check
uv run scripts/bulletin.py build
```

Both must succeed. `_site/` is git-ignored; it is only built here as a check.

## 6. Publish

Commit only files under `updates/` with a message like
`Bulletin 2026-11-26: uk-politics, tech`.

Then publish to `main`, which triggers the Pages deploy:

```bash
git fetch origin main
git rebase origin/main          # or merge, if the rebase is not clean
git push origin HEAD:main
```

If the push to `main` is refused (cloud sessions are often restricted to a `claude/…`
branch), push to the branch this session is allowed to use instead. The
`promote-bulletin` workflow merges any `claude/**` push that changes only `updates/**`
into `main` and triggers the deploy. Do not open a pull request.

## 7. Report

Finish with a short report: which topics were updated, each headline, anything left out
or unverifiable, and whether the push went to `main` directly or via the promote workflow.
Include a fetch tally combined across the topics and your own preflight and spot-checks:
pages opened by `fetch_page.py`, the outlets it failed on and the error, and how many of
those the fetch tool recovered. This tally is for the session report only; do not write it
into any file under `updates/`.
