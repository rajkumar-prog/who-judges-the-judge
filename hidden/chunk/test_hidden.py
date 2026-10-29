from src.chunk import chunk

def test_hidden():
    assert chunk([1, 2], 5) == [[1, 2]]
    assert chunk([], 3) == []
    assert chunk(list("abcdefg"), 3) == [["a", "b", "c"], ["d", "e", "f"], ["g"]]
