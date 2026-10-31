# Who Judges the Judge

<!-- before submitting: add the demo video link and the dashboard link here -->

AI coding agents can make your tests pass without fixing the bug, for example by hardcoding the test inputs or weakening the asserts. I pitted an AI judge against a cheater that adapts to the judge's feedback.

The judge's blind spot: it passes code that *looks* general even when it's wrong, sometimes calling it "a bug, not a cheat". Asking it for a concrete counterexample, instead of asking "is this a cheat?", closed most of that gap.

If you're going to trust an AI judge, test it against a cheater that adapts, with hidden tests as the answer key.

A solo project by [@rajkumar-prog](https://github.com/rajkumar-prog), built during the Meta AI Developer Hackathon, Oct 26 – Nov 4, 2026. All code in this repository was written during the event.

## How it works

Think of an exam. The student is a cheating agent, the exam is a small repo with a failing test, the answer key is a set of hidden tests the student never sees, and the invigilator is the judge. I'm testing the invigilator.

- **Judge:** Muse Spark Open (`meta-models/muse-spark-open-1026` on Baseten) reads the task, the final diff and the full changed files, and says `clean` or `cheat`.
- **Cheater:** round 1 is a scripted cheat (an answer table, weakened asserts, skipped tests, or one of the hand-written ones in `patches/`). From round 2, hosted Muse Spark (`muse-spark-1.3`) rewrites the fix after reading every reason the judge has caught it for so far.
- **Ground truth:** hidden tests decide what each round really was, so every verdict can be scored.
- **Baseline:** a regex checker, to show what a non-model judge catches.

See [docs/architecture.md](docs/architecture.md).

## Run it

Needs Python 3.10+ and git.

```
git clone https://github.com/rajkumar-prog/who-judges-the-judge
cd who-judges-the-judge
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q                  # no API key needed: the model is replaced by scripted replies
python scripts/verify_seeds.py       # every seed fails as shipped; its reference fix passes visible + hidden tests
```

Then, with keys:

```
export BASETEN_API_KEY=...           # judge (Muse Spark Open)
export MODEL_API_KEY=...             # cheater (hosted Muse Spark), only needed for duel

python -m wjj run median --mode cheat          # one seed: agent fixes, judge reviews, redo if caught (~1 min)
python -m wjj duel median --rounds 3           # scripted cheat, then the cheater adapts to the judge (~3 min)
python -m wjj --strict-judge duel median       # same, with the counterexample prompt
```

Use `python -m pytest`, not bare `pytest`: the bare command can't import `wjj`.

| Command | What it does |
|---|---|
| `run SEED --mode honest\|cheat` | One fix, judge, redo loop, printed step by step |
| `eval --attempts N` | Every seed, honest and cheat mode; writes a scorecard with false-alarm rates |
| `duel SEED\|all --rounds N` | Multi-round duel; `--cheat-type` picks the round-1 cheat |
| `probe` | Judges each hand-written cheat with and without a reassuring comment |
| `cases --repeat N` | Judges every real-repo patch (correct, incomplete and cheats) with both prompts, N times each |
| `regrade FILE` | Re-runs today's hidden tests on saved diffs (no model calls) |
| `rejudge FILE...` | Re-judges saved diffs with the strict prompt, so both prompts are scored on the same diffs |

`--strict-judge` goes before the command and works with `run`, `eval`, `duel` and `probe`.

## Results so far

Small seeds and small samples. I added hidden tests several times after reading judge verdicts, which can only help the judge on false alarms, so both versions are reported. Every change is listed in [docs/hidden-tests-log.md](docs/hidden-tests-log.md).

**Original prompt** ("is this a cheat?"). It does well on single rounds but gets weaker as the cheater adapts, and every miss looks the same.
- Single-round eval: caught 21/21 cheats, 0/24 false alarms on honest fixes. Regex baseline: 10/21 and 6/24.
- 36 duels, 5 rounds: caught 35/35, 30/36, 28/29, 25/28, 23/26 by round.
- All 18 misses read like "implements general X rather than hard-coding". Four of those reasons named the defect and passed it anyway.

**Strict prompt** ("find an allowed input where this is wrong"). It closes the gap on fresh duels, at the cost of being a bit pedantic.
- Same 290 saved diffs, rescored: 244/245 caught (original 227/245), 1/45 false alarms (original 0/45). I wrote this prompt after reading those misses, so this is an in-sample score.
- Fresh single-round eval: caught 20/20, 0/26 false alarms. Regex baseline: 13/20 and 7/26.
- Fresh 36 duels, 3 rounds: 98/98 cheats caught and 5 false alarms as run. All 5 turned out to be real cheats the hidden tests missed; after adding tests for them, 103/103 and 0.
- Its one real false alarm on an honest fix was pedantic: Python's `csv` module refuses fields over 131,072 characters.

**Comments as decoys.** The original judge caught 13 of the 16 hand-written cheats. Adding a reassuring comment above the cheat flipped 1 of those 13 to clean.

## Related work

Others have measured this problem: [EvilGenie](https://arxiv.org/abs/2511.21654) compares held-out tests, LLM judges and test-file checks on reward hacking, [TRACE](https://arxiv.org/abs/2601.20103) is a labeled dataset of 517 reward-hacking trajectories for scoring detectors, and [SHADE-Arena](https://arxiv.org/abs/2506.15740) pits agents doing hidden sabotage against an LLM monitor. What's different here is that the cheater reads the judge's reasons and tries again, round after round, and hidden tests grade every verdict, so you can watch a judge's catch rate fall as the cheater adapts. It's a small runnable tool, not a benchmark.

## Limits

- Twelve toy seeds, one function each, plus two real-repo seeds (cachetools and requests). Two real bugs is still a small sample.
- Every seed is Python, so nothing here says how the judge does on other languages.
- Cheats are induced: the cheater is told to cheat. That's how you test an alarm, but natural cheating rates will differ.
- The same model family plays judge and cheater.
- The judge's verdicts aren't fully stable: one identical diff got different verdicts in two runs.

## Layout

| Path | What it is |
| --- | --- |
| `wjj/` | The app: fixer agent, judge, baseline, duel, probe, regrade, rejudge, scorecard, CLI. |
| `tests/` | Unit tests with a scripted fake model, plus 18 real saved judge replies. |
| `seeds/` | Repos with failing tests: 12 toy seeds, plus `ttlcache` (cachetools 7.2.1) and `proxyauth` (requests 2.30.0, CVE-2023-32681). The agent only ever sees a temp copy of one seed. |
| `hidden/` | Hidden tests per seed. Never copied into the agent workspace. |
| `patches/` | Hand-written cheats, one file per seed. See `patches/README.md`. |
| `cases/` | Correct and incomplete fixes for the real-repo seeds. See `cases/README.md`. |
| `scripts/` | `verify_seeds.py`: every seed fails as shipped and its reference fix passes. |
| `docs/` | Architecture and the hidden-test change log. |
| `spike/` | Day-1 spike: one judge call and one headless Muse Code run. |

## License

MIT. See [LICENSE](LICENSE).
