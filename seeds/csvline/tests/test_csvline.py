from src.csvline import parse_csv_line

def test_plain():
    assert parse_csv_line("a,b,c") == ["a", "b", "c"]

def test_quoted_comma():
    assert parse_csv_line('name,"Smith, John",42') == ["name", "Smith, John", "42"]
