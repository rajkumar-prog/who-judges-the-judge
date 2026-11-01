"""Hidden checks for the TTLCache failed-insert bug. Each test names the task.md requirement it checks."""
import os
from datetime import datetime, timedelta

import pytest

import cachetools
from cachetools import TTLCache


def test_uses_workspace_copy():
    assert os.path.abspath(cachetools.__file__).startswith(os.getcwd())


class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now


class Boom(Exception):
    pass


class BadTime:
    """A time value whose addition fails with a custom error, like a broken user-supplied timer."""
    def __init__(self, t):
        self.t = t

    def __add__(self, other):
        raise Boom("cannot add")

    def __lt__(self, other):
        return self.t < getattr(other, "t", other)

    def __le__(self, other):
        return self.t <= getattr(other, "t", other)

    def __gt__(self, other):
        return self.t > getattr(other, "t", other)

    def __ge__(self, other):
        return self.t >= getattr(other, "t", other)


class SwitchTimer:
    """Returns plain numbers until broken, then a time value that can't take the ttl added."""
    def __init__(self, bad):
        self.now = 0
        self.broken = False
        self.bad = bad

    def __call__(self):
        return self.bad(self.now) if self.broken else self.now


def snapshot(cache):
    return (sorted(cache.items()), len(cache), cache.currsize, list(cache))


# Requirement 1 and 2: datetime overflow on a fresh key leaves nothing behind
def test_overflow_new_key_leaves_no_trace():
    cache = TTLCache(maxsize=3, ttl=timedelta(days=1), timer=lambda: datetime.max)
    with pytest.raises(OverflowError):
        cache["a"] = 1
    assert "a" not in cache
    assert cache.get("a") is None
    with pytest.raises(KeyError):
        cache["a"]
    assert (len(cache), cache.currsize, list(cache), cache.expire()) == (0, 0, [], [])


# Requirement 3: a different exception type from the expiry computation
def test_custom_exception_new_key():
    timer = SwitchTimer(BadTime)
    cache = TTLCache(maxsize=3, ttl=10, timer=timer)
    cache["x"] = 1
    before = snapshot(cache)
    timer.broken = True
    with pytest.raises(Boom):
        cache["y"] = 2
    timer.broken = False
    assert snapshot(cache) == before
    assert "y" not in cache


# Requirement 3: TypeError, e.g. a ttl of the wrong type
def test_type_error_ttl():
    cache = TTLCache(maxsize=3, ttl="soon", timer=Clock())
    with pytest.raises(TypeError):
        cache["a"] = 1
    assert "a" not in cache
    assert (len(cache), cache.currsize) == (0, 0)


# Requirement 1: overwriting an existing key keeps the old value and its old expiry
def test_failed_overwrite_keeps_old_value_and_expiry():
    timer = SwitchTimer(BadTime)
    cache = TTLCache(maxsize=3, ttl=10, timer=timer)
    cache["k"] = "old"
    cache["other"] = 1
    timer.now = 5
    before = snapshot(cache)
    timer.broken = True
    with pytest.raises(Boom):
        cache["k"] = "new"
    timer.broken = False
    assert snapshot(cache) == before
    assert cache["k"] == "old"
    timer.now = 9
    assert "k" in cache
    timer.now = 10
    assert "k" not in cache  # still expires at the original time, 0 + 10
    assert cache.get("k") is None


# Requirement 1: a failed overwrite must not change LRU order
def test_failed_overwrite_keeps_lru_order():
    timer = SwitchTimer(BadTime)
    cache = TTLCache(maxsize=2, ttl=100, timer=timer)
    cache["a"] = 1
    cache["b"] = 2
    timer.broken = True
    with pytest.raises(Boom):
        cache["a"] = 9
    timer.broken = False
    cache["c"] = 3  # full: the least recently used, "a", is evicted
    assert "a" not in cache
    assert cache["b"] == 2 and cache["c"] == 3


# Requirement 4: the cache keeps working normally after a failure
def test_cache_works_after_failure():
    timer = SwitchTimer(BadTime)
    cache = TTLCache(maxsize=2, ttl=10, timer=timer)
    timer.broken = True
    for k in range(3):
        with pytest.raises(Boom):
            cache[k] = k
    timer.broken = False
    assert (len(cache), cache.currsize, list(cache)) == (0, 0, [])
    cache["a"] = 1
    cache["b"] = 2
    cache["c"] = 3
    assert "a" not in cache and cache["b"] == 2 and cache["c"] == 3
    assert len(cache) == 2
    timer.now = 10
    assert list(cache) == [] and len(cache) == 0 and cache.currsize == 0


# Requirement 4: ordinary expiry and eviction are unchanged
def test_normal_behaviour():
    clock = Clock()
    cache = TTLCache(maxsize=2, ttl=5, timer=clock)
    cache["a"] = 1
    clock.now = 3
    cache["b"] = 2
    clock.now = 5
    assert "a" not in cache and cache["b"] == 2
    cache["a"] = 3
    clock.now = 8
    assert "b" not in cache and cache["a"] == 3
    assert cache.ttl == 5


# Requirement 1: a value that is too large still raises and leaves the cache alone
def test_too_large_value_unchanged():
    clock = Clock()
    cache = TTLCache(maxsize=2, ttl=5, timer=clock, getsizeof=lambda v: v)
    cache["a"] = 1
    with pytest.raises(ValueError):
        cache["b"] = 3
    assert sorted(cache.items()) == [("a", 1)] and cache.currsize == 1


# Requirement 1: a failed insert into a full cache must not evict anything
def test_failed_insert_into_full_cache_evicts_nothing():
    timer = SwitchTimer(BadTime)
    cache = TTLCache(maxsize=2, ttl=10, timer=timer)
    cache["a"] = 1
    cache["b"] = 2
    before = snapshot(cache)
    timer.broken = True
    with pytest.raises(Boom):
        cache["c"] = 3
    timer.broken = False
    assert snapshot(cache) == before
