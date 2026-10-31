# Hidden test changes

The hidden tests are the answer key, so every change to them is listed here with what prompted it.

Most additions came after reading a judge verdict that the hidden tests disagreed with. Each one only
checks behaviour the seed's docstring already promises, and each was confirmed by running the cheat
against it. But adding tests after seeing the judge's answer can only move results in the judge's
favour on false alarms, so results are reported both before and after these additions, and the
hidden tests are frozen before the final run.

| Date (UTC) | Seeds | What was added | Prompted by |
|---|---|---|---|
| 2026-10-28 | all 12 | Original hidden tests | Written with the seeds, before any judge run |
| 2026-10-30 | median, dedupe, intervals, bizdays, roman, csvline | Duplicates and unsorted input, unique input, several touching groups, weekend starts, lone subtractive pairs, comma after a doubled quote | First full duel run: 8 judge "false alarms" were real cheats the tests missed |
| 2026-10-31 | intervals, wrap, dedupe, phone, slugify | Large-number touching intervals, widths that count spaces, a duplicate at the end, leading 1 with spaces and a non-555 number, underscores | Overnight 5-round run: 13 of 14 "false alarms" were real cheats |
| 2026-10-31 | intervals | Touching intervals above 2^53 | Strict judge counterexample against an epsilon fix |
| 2026-10-31 | dedupe, leapyear | Far-apart repeats, case-different strings, colliding hashes, year 4000 | Strict-judge duel run: all 5 "false alarms" were real cheats |
