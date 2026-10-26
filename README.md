# Who Judges the Judge

A CI judge on Muse Spark Open that catches AI code changes that pass tests but are still wrong, and measures how often the judge itself is wrong.

Built during the Meta AI Developer Hackathon, Oct 26 – Nov 4, 2026. All code in this repository was written during the event.

## Layout

| Path | What it is |
| --- | --- |
| `seeds/` | Small repos with failing tests. The agent only ever sees a temp copy of one seed. |
| `hidden/` | Hidden tests per seed. Never copied into the agent workspace; used as ground truth for the judge. |
| `spike/` | Day-1 spike: one Muse Spark Open judge call and one headless Muse Code run. See `spike/README.md`. |

## License

MIT
