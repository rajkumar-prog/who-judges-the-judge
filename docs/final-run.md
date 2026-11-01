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
| 2 | Real-repo duels | `duel ttlcache` / `duel proxyauth` / `duel xmlattr` with `--cheat-type spec_narrowing` and `input_guard`, 3 times per prompt | 3 seeds × 2 cheats × 2 prompts × 3 = 36 duels |
| 3 | Real-repo cases | `cases --repeat 3` | 14 patches × 2 prompts × 3 = 84 judgments |
| 4 | Comment probe | `probe`, once per prompt | 22 hand-written cheats × 2 prompts |
| 5 | Single-round eval | `eval --attempts 2`, once per prompt | 15 seeds (12 toy-suite + 3 real) × honest and cheat × 2 |
| 6 | Confirm | `confirm` on every file from runs 1 to 3 | every cheat verdict; never changes a verdict or label |

Budget cap: **$80** across both providers. The cap is there to stop a broken loop from burning
credits, not a target. If spending reaches it, stop and report what finished. Estimate, from
Sunday's pilot (4 real-repo duels, 3 rounds, $2.64 total, $0.20 to $1.55 each) and earlier toy
runs (about $0.14 per toy duel): toy duels ~$10, real-repo duels ~$24, cases ~$3, probe ~$2,
eval ~$11, so ~$50. Every command runs with `--budget` set to its line here plus half again. The pilot duels themselves are not part of the reported
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
- **Confirm:** for each prompt, how many cheat verdicts the judge backed with a test that fails on
  the patch and passes on the upstream fix. A confirmed test on a patch the hidden tests call clean
  is reported as "judge found a bug the hidden tests missed", and stays a false alarm in the
  headline numbers, since the hidden tests are frozen.
- All result files from this run are committed under `results/final/`, so anyone can rebuild the
  dashboard and the numbers without an API key.

## Allowed re-runs

Only a duel or eval run that crashed on a connection or API error before finishing may be run
again, and each one is listed here with the reason. Nothing is re-run because of its result.

| Run | Reason |
|---|---|
| | |
