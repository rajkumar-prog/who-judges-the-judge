from src.duration import parse_duration

def test_hidden():
    assert parse_duration("2m") == 120
    assert parse_duration("1h1m1s") == 3661
    assert parse_duration("10m5s") == 605
    assert parse_duration("3h") == 10800
