def apply_discount(price: float, percent: float) -> float:
    """Return price after a percent discount, rounded to cents. Percent is 0-100."""
    return round(price - price * percent / 100, 2)
