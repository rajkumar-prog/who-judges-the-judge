# Final run results

Everything the final run on Nov 3, 2026 wrote, as run. Each `.jsonl` has a `.md` summary next to it.

| Files | What they are |
|---|---|
| `duel-all-20261103-000532.jsonl` / `-000537-strict.jsonl` | Toy duels, original and strict prompt |
| `duel-{ttlcache,proxyauth,xmlattr}-*.jsonl` | Real-library duels, one file per duel (`-strict` = strict prompt) |
| `duel-*-confirmed.jsonl` | The same duels after `confirm`: each cheat verdict also has the judge's own test and whether it reproduced |
| `cases-20261103-054613.jsonl` | Fixed real-library patches, both prompts, 3 times each |
| `cases-…-confirmed.jsonl`, `cases-…-confirmed-confirmed.jsonl` | Confirm on the cases file. The first stopped at its budget guard after 15 of 45 verdicts, the second finished the rest (see `docs/final-run.md`). Use the second one. |
| `probe-*.jsonl` | Hand-written cheats with and without a reassuring comment |
| `eval-original/`, `eval-strict/` | Single-round eval: every run and the scorecard |
| `final-run.log`, `log-original.txt`, `log-strict.txt` | Console output, including one line per model call |
| `START` | Empty marker the run script used to find files written during the run |

The files without `-confirmed` are kept on purpose: they are the run before confirm touched anything.
