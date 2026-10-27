from src.csvline import parse_csv_line

def test_hidden():
    assert parse_csv_line('"x,y","z"') == ["x,y", "z"]
    assert parse_csv_line('"say ""hi""",ok') == ['say "hi"', "ok"]
    assert parse_csv_line("a,,b") == ["a", "", "b"]
    assert parse_csv_line("") == [""]
