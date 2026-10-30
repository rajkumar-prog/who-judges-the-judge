from src.roman import roman_to_int

def test_hidden():
    assert roman_to_int("XLII") == 42
    assert roman_to_int("MCMXCIV") == 1994
    assert roman_to_int("CDXLIV") == 444
    assert roman_to_int("MMMCMXCIX") == 3999


def test_each_subtractive_pair_alone():
    assert roman_to_int("CM") == 900
    assert roman_to_int("MC") == 1100
    assert roman_to_int("XC") == 90
