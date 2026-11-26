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

The body is a free-form brief read by the researcher. Be as specific as you like:
what to include, what to exclude, sources to favour or avoid, how much depth you want,
particular people/companies/bills to track. To add a topic, add a file; to drop one,
delete it or set `enabled: false`.
