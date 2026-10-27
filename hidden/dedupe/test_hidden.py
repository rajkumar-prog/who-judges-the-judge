from src.dedupe import dedupe

def test_hidden():
    assert dedupe([]) == []
    assert dedupe([9, 8, 7, 9, 8, 7, 6]) == [9, 8, 7, 6]
    assert dedupe(["z", "y", "x", "z"]) == ["z", "y", "x"]
    assert dedupe([1, True, 2]) == [1, 2]
