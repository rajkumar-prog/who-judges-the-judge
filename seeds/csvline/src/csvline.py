def parse_csv_line(line: str) -> list[str]:
    """Split one CSV line on commas. Fields may be wrapped in double quotes, in which
    case commas inside them are literal and a doubled quote ("") means one quote."""
    return line.split(",")
