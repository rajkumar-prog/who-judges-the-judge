from src.roman import roman_to_int

def test_additive():
    assert roman_to_int("VIII") == 8

def test_subtractive():
    assert roman_to_int("IX") == 9
