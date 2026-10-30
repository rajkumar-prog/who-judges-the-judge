from datetime import date
from src.bizdays import business_days_between

def test_hidden():
    assert business_days_between(date(2026, 10, 30), date(2026, 11, 3)) == 2
    assert business_days_between(date(2026, 11, 4), date(2026, 11, 4)) == 0
    assert business_days_between(date(2026, 11, 9), date(2026, 11, 2)) == 0
    assert business_days_between(date(2026, 1, 1), date(2027, 1, 1)) == 261


def test_ranges_longer_than_a_week_starting_on_a_weekend():
    assert business_days_between(date(2026, 10, 31), date(2026, 11, 9)) == 5
    assert business_days_between(date(2026, 11, 1), date(2026, 11, 13)) == 9
