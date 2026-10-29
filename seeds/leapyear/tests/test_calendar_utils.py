from src.calendar_utils import is_leap_year

def test_regular():
    assert is_leap_year(2024)
    assert not is_leap_year(2023)

def test_century():
    assert not is_leap_year(1900)
