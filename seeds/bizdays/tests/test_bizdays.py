from datetime import date
from src.bizdays import business_days_between

def test_one_week():
    assert business_days_between(date(2026, 10, 26), date(2026, 11, 2)) == 5

def test_weekend_only():
    assert business_days_between(date(2026, 10, 31), date(2026, 11, 2)) == 0
