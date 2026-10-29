from datetime import date, timedelta

def business_days_between(start: date, end: date) -> int:
    """Count Mon-Fri days in [start, end). Returns 0 if end <= start."""
    count, day = 0, start
    while day < end:
        if day.weekday() < 5:
            count += 1
        day += timedelta(days=1)
    return count
