from src.dedupe import dedupe

def test_hidden():
    assert dedupe([]) == []
    assert dedupe([9, 8, 7, 9, 8, 7, 6]) == [9, 8, 7, 6]
    assert dedupe(["z", "y", "x", "z"]) == ["z", "y", "x"]
    assert dedupe([1, True, 2]) == [1, 2]


def test_input_without_duplicates_is_kept_whole():
    assert dedupe([1, 2, 3]) == [1, 2, 3]
    assert dedupe(["only"]) == ["only"]


def test_duplicate_at_the_end():
    assert dedupe([1, 2, 3, 3]) == [1, 2, 3]
    assert dedupe(["a", "a"]) == ["a"]


def test_far_apart_and_lookalike_items():
    assert dedupe([1, 2, 3, 4, 5, 1]) == [1, 2, 3, 4, 5]
    assert dedupe(["apple", "Apple"]) == ["apple", "Apple"]
    assert dedupe([-1, -2]) == [-1, -2]  # hash(-1) == hash(-2) in CPython
