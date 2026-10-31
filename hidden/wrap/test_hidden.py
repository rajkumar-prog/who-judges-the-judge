from src.wrap import wrap

def test_hidden():
    assert wrap("the quick brown fox", 9) == ["the quick", "brown fox"]
    assert wrap("a b c d", 3) == ["a b", "c d"]
    assert wrap("supercalifragilistic is long", 5) == ["supercalifragilistic", "is", "long"]
    assert wrap("", 10) == []


def test_exact_fit_counts_the_spaces():
    assert wrap("ab cd", 4) == ["ab", "cd"]
    assert wrap("a b c", 4) == ["a b", "c"]
    assert wrap("ab cd", 5) == ["ab cd"]
    assert wrap("a b c", 10) == ["a b c"]


def test_exact_fit_at_a_large_width():
    text = " ".join(["x" * 100] * 3)
    assert wrap(text, len(text)) == [text]
