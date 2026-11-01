# Final run plan

Written before the final run, and committed so the git history shows it came first. The numbers in
the README come from this run, as run, with nothing re-run or re-tested after the fact except where
this page allows it.

**Status: DRAFT.** Once this says FINAL, it doesn't change.

## Freeze

Before anything runs:

```
python scripts/freeze.py
git add docs/frozen-manifest.json
git commit -m "Freeze answer key for the final run"
```

That records a checksum of every seed, hidden test, hand-written patch, case patch, and the judge
and agent prompts. After the run, `python scripts/freeze.py --check` must say "frozen files
unchanged". No hidden test is added or changed after the freeze, even if a judge "false alarm"
turns out to be a real cheat. Those get listed in the results as found, not fixed.

## What runs

All on Monday Nov 2, from the frozen commit. Judge: Muse Spark Open on Baseten. Cheater in duels:
Muse Spark (`muse-spark-1.3`). Both judge prompts (original and strict) on everything.

| # | Run | Command | Size |
|---|---|---|---|
| 1 | Toy duels | `duel all --rounds 3` (scripted round-1 cheats; `all` is the 12 toy-suite seeds), once per prompt | 12 seeds × 3 cheat types × 2 prompts = 72 duels |
| 2 | Real-repo duels | `duel ttlcache` / `duel proxyauth` with `--cheat-type spec_narrowing` and `input_guard`, once per prompt | 2 seeds × 2 cheats × 2 prompts = 8 duels |
| 3 | Real-repo cases | `cases --repeat 3` | 9 patches × 2 prompts × 3 = 54 judgments |
| 4 | Comment probe | `probe`, once per prompt | 20 hand-written cheats × 2 prompts |
| 5 | Single-round eval | `eval --attempts 2`, once per prompt | 14 seeds (12 toy-suite + 2 real) × honest and cheat × 2 |

Budget cap: **$40** across both providers. If spending reaches the cap, stop and report what
finished. Estimate, from Sunday's pilot (4 real-repo duels, 3 rounds, $2.64 total, $0.20 to $1.55
each) and earlier toy runs (about $0.14 per toy duel): toy duels ~$10, real-repo duels ~$6,
cases ~$2, probe ~$2, eval ~$10, so ~$30. The pilot duels themselves are not part of the reported
results.

## What gets reported

Decided now, before seeing the numbers:

- **Headline:** strict-prompt catch rate and false-alarm rate on the toy duels and the real-repo
  duels, reported separately.
- **The adaptation curve:** catch rate by round for each prompt.
- **Real-repo cases:** for each prompt, correct fixes accepted, wrong fixes caught, and how many
  patches got the same verdict on all 3 repeats.
- Counts always next to rates. Distinct patches counted separately from judgments.
- Errors (unparseable judge replies) are reported as errors, not dropped.

## Allowed re-runs

Only a duel or eval run that crashed on a connection or API error before finishing may be run
again, and each one is listed here with the reason. Nothing is re-run because of its result.

| Run | Reason |
|---|---|
| | |
