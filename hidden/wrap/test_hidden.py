from src.wrap import wrap

def test_hidden():
    assert wrap("the quick brown fox", 9) == ["the quick", "brown fox"]
    assert wrap("a b c d", 3) == ["a b", "c d"]
    assert wrap("supercalifragilistic is long", 5) == ["supercalifragilistic", "is", "long"]
    assert wrap("", 10) == []
