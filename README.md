# Who Judges the Judge

A CI judge on Muse Spark Open that catches AI code changes that pass tests but are still wrong, and measures how often the judge itself is wrong.

Built during the Meta AI Developer Hackathon, Oct 26 – Nov 4, 2026. All code in this repository was written during the event.

## How it works

An agent fixes failing tests, a judge reviews the final diff for fixes that pass tests but are still wrong, and a cheat verdict sends the agent back to redo the work. Both the agent and the judge run on Muse Spark Open (`meta-models/muse-spark-open-1026` on Baseten). Hidden tests the agent never sees measure how often the judge is right. See [docs/architecture.md](docs/architecture.md).

## Run it

```
python -m venv .venv && .venv/bin/pip install openai pytest
export BASETEN_API_KEY=...                       # Muse Spark Open on Baseten
.venv/bin/python -m wjj run median --mode cheat  # one seed, printed step by step
.venv/bin/python -m wjj eval --attempts 3        # all seeds, both modes → results/scorecard.md
```

Add `--reference` (with `MODEL_API_KEY` set) to also judge every fix with hosted Muse Spark.
`--mode cheat` tells the fixer to take shortcuts, so the eval has known cheats for the judge to catch.

## Layout

| Path | What it is |
| --- | --- |
| `wjj/` | The app: fixer agent, judge, baseline, redo loop, scorecard, CLI. |
| `tests/` | Unit tests with a scripted fake model (no key needed): `pytest`. |
| `seeds/` | Small repos with failing tests. The agent only ever sees a temp copy of one seed. |
| `hidden/` | Hidden tests per seed. Never copied into the agent workspace; used as ground truth for the judge. |
| `scripts/` | `verify_seeds.py`: every seed fails as shipped and its reference fix passes visible + hidden tests. |
| `docs/` | Architecture and diagram. |
| `spike/` | Day-1 spike: one Muse Spark Open judge call and one headless Muse Code run. See `spike/README.md`. |

## License

MIT
