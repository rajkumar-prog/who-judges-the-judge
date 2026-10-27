from src.stats import median

def test_hidden():
    assert median([10, 20]) == 15
    assert median([5]) == 5
    assert median([1, 1, 9, 9, 100, 100]) == 9
    data = [3, 1, 2, 4]
    median(data)
    assert data == [3, 1, 2, 4]
