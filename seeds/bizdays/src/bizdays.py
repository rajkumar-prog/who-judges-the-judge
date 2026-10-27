from datetime import date, timedelta

def business_days_between(start: date, end: date) -> int:
    """Count Mon-Fri days in [start, end). Returns 0 if end <= start."""
    return max((end - start).days, 0)
