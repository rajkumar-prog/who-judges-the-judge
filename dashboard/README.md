# Dashboard

The page reads one data file made from saved results, so nothing on it is typed by hand.

```
python -m wjj dashboard strict:results/duel-a.jsonl results/cases-b.jsonl ...
```

writes `dashboard/data.json` and `dashboard/data.js`. Load `data.js` with a `<script>` tag and use
`window.WJJ_DATA`; that works when the page is opened straight from disk. Older result files don't
record which judge prompt they used, so prefix them with `strict:` or `original:`. Add `--fast` to
skip re-running hidden tests (then `hidden_failures` is empty). `sample-data.js` is a small real
sample to build against.

## Shape

```
meta       generated_at, git_commit, models {judge, cheater}, files
summary
  all        caught, missed, false_alarm, passed_clean, error, judgments, distinct_patches
  scorecard  [{suite: toy|real, prompt: original|strict, ...same counts}]
  by_round   {original: [{round, caught, cheats}], strict: [...]}     duels only, real cheats only
  baseline   {caught, cheats, false_alarms, cleans}                     regex checker
  cost_usd
tasks      {seed: task text shown to the agent}
runs[]
  id, kind (duel|eval|case), suite (toy|real), seed, prompt, cheat_type,
  patch, patch_kind (case runs: correct|incomplete|cheat), source, cost_usd
  rounds[]
    n, author (script|meta|hand-written|agent), diff
    visible_passed, hidden_passed, label (cheat|clean|failed)    <- what the tests prove
    judge {verdict, evidence, reason, counterexample}           <- what the judge says
    outcome (caught|missed|false_alarm|passed_clean|error|failed)
    hidden_failures [test names]
    baseline (cheat|clean|"")
    feedback_after   text the cheater was shown before the next round ("" if none)
```

`label` and `hidden_failures` are ground truth; `judge` is a prediction. Keep them visually apart.
