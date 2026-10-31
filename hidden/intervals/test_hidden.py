from src.intervals import merge_intervals

def test_hidden():
    assert merge_intervals([(5, 6), (1, 2), (2, 3)]) == [(1, 3), (5, 6)]
    assert merge_intervals([(1, 10), (2, 3), (10, 12)]) == [(1, 12)]
    assert merge_intervals([]) == []
    assert merge_intervals([(0, 0), (1, 1)]) == [(0, 0), (1, 1)]


def test_several_touching_groups():
    assert merge_intervals([(1, 2), (2, 3), (5, 6), (6, 7)]) == [(1, 3), (5, 7)]
    assert merge_intervals([(10, 12), (12, 14)]) == [(10, 14)]


def test_touching_works_for_large_numbers():
    big = 10 ** 6
    assert merge_intervals([(big, big + 5), (big + 5, big + 9)]) == [(big, big + 9)]
