from src.pricing import apply_discount

def test_ten_percent():
    assert apply_discount(100.0, 10) == 90.0

def test_zero():
    assert apply_discount(59.99, 0) == 59.99
