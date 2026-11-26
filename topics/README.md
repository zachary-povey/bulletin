# Topics

One Markdown file per topic. The file name (without `.md`) is the topic id used by
`/update-bulletin <id>` and as the folder name under `updates/`.

Front matter:

| key            | meaning                                                              |
| -------------- | -------------------------------------------------------------------- |
| `title`        | Display name on the site                                             |
| `order`        | Position on the home page (lowest first)                             |
| `cadence_days` | Minimum days between updates when the job runs in `due` mode         |
| `enabled`      | `false` skips the topic in `due`/`all` runs (it can still be named)  |
| `feeds`        | RSS/Atom feed URLs scanned first for headlines and summaries         |

The body is a free-form brief read by the researcher. Be as specific as you like:
what to include, what to exclude, sources to favour or avoid, how much depth you want,
particular people/companies/bills to track. To add a topic, add a file; to drop one,
delete it or set `enabled: false`.

Feeds are how the researcher discovers stories and sees how outlets that block automated
article access (Guardian, FT, El País, Economist…) are covering them. Preview a topic's
feeds with `uv run scripts/bulletin.py feeds <topic-id> --since YYYY-MM-DD`. A feed that
fails is reported and skipped.
