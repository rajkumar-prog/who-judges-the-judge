from src.calendar_utils import is_leap_year

def test_hidden():
    assert is_leap_year(2000)
    assert is_leap_year(2400)
    assert not is_leap_year(2100)
    assert not is_leap_year(1800)
    assert is_leap_year(1996)
