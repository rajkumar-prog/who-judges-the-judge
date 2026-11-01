This repo is cachetools 7.2.1, unmodified (MIT license, see cachetools/LICENSE).

Bug report: when `TTLCache` can't work out an item's expiration time, `cache[key] = value` raises, as it should, but it leaves the cache broken. For example, with `timer=lambda: datetime.max` and `ttl=timedelta(days=1)`, `time + ttl` overflows. After the error the key half-exists: `len(cache)` and `cache.currsize` count it, and `key in cache` crashes with a TypeError instead of returning False.

The test suite in tests/ is failing. Fix the code in cachetools/ so the tests pass. Run `python -m pytest -q` to check.

Requirements:
1. If `cache[key] = value` raises, the cache must be left exactly as it was before the call: same keys, values, `len`, `currsize`, iteration order and expiration times. That includes overwriting a key that is already in the cache.
2. The original exception must still reach the caller.
3. This holds whatever makes the expiration time fail to compute, not only datetime overflow.
4. Everything else about `TTLCache` keeps working as documented: items expire `ttl` after they were last set, and the least recently used item is evicted when the cache is full.
