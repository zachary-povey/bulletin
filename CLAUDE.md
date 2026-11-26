# Bulletin

A personal news bulletin published as a static site on GitHub Pages.

- `topics/*.md`: topic briefs (the configuration; see `topics/README.md`).
- `updates/<topic-id>/YYYY-MM-DD.md`: published updates, one file per topic per day.
- `.claude/skills/update-bulletin/`: the `/update-bulletin` skill and its research method.
- `scripts/bulletin.py`: `topics` (select what to update), `feeds` (scan a topic's RSS feeds), `check` (validate), `build` (render `_site/`).
- `site/style.css`: site styling. HTML templates are inline in `scripts/bulletin.py`.
- `.github/workflows/`: `deploy.yml` builds and deploys Pages from `main`;
  `promote-bulletin.yml` merges `claude/**` pushes that touch only `updates/**` into `main`.

To publish news, run `/update-bulletin [due|all|<topic-id> ...]`. Do not hand-edit files in
`updates/` except to correct errors. Dependencies are managed with uv (`pyproject.toml`,
`uv.lock`): run the script with `uv run scripts/bulletin.py <command>`.
