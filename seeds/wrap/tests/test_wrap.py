from src.wrap import wrap

def test_exact_fit():
    assert wrap("aaa bbb", 7) == ["aaa bbb"]

def test_break():
    assert wrap("aaa bbb ccc", 7) == ["aaa bbb", "ccc"]
