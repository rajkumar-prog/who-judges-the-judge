from src.intervals import merge_intervals

def test_overlap():
    assert merge_intervals([(1, 3), (2, 5)]) == [(1, 5)]

def test_touching():
    assert merge_intervals([(1, 2), (2, 4)]) == [(1, 4)]
