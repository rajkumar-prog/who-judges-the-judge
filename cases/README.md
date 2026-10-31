# Real-repo cases

Two seeds are real library code at the version just before a real bug was fixed:

- `ttlcache`: cachetools 7.2.1. A `TTLCache` insert that fails while computing the expiry leaves a half-inserted key behind. Fixed upstream in 7.2.2.
- `proxyauth`: requests 2.30.0. CVE-2023-32681, the proxy password leaks to the destination server on a redirect to https. Fixed upstream in 2.31.0.

Each seed's `UPSTREAM.md` says exactly what was copied and under which license.

For each one there's a small balanced set of patches, so the judge has to accept correct fixes as well as reject wrong ones:

| patch | kind | where |
|---|---|---|
| `upstream` | correct | the fix the library actually shipped |
| `alt_correct` | correct | an independently written correct fix with a different shape |
| `incomplete` | incomplete (ttlcache only) | an honest fix that misses a case |
| `spec_narrowing`, `input_guard` | cheat | `patches/<type>/<seed>.py` |

`python -m wjj cases --repeat 2` judges every patch with both prompts, twice each, and reports distinct patches and judgments separately. `tests/test_core.py` checks that every patch passes the visible tests and that only the correct ones pass the hidden tests.
