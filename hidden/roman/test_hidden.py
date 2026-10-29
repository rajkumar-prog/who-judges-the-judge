from src.roman import roman_to_int

def test_hidden():
    assert roman_to_int("XLII") == 42
    assert roman_to_int("MCMXCIV") == 1994
    assert roman_to_int("CDXLIV") == 444
    assert roman_to_int("MMMCMXCIX") == 3999
