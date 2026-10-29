def parse_csv_line(line: str) -> list[str]:
    """Split one CSV line on commas. Fields may be wrapped in double quotes, in which
    case commas inside them are literal and a doubled quote ("") means one quote."""
    fields, buf, in_quotes, i = [], [], False, 0
    while i < len(line):
        ch = line[i]
        if in_quotes:
            if ch == '"' and i + 1 < len(line) and line[i + 1] == '"':
                buf.append('"')
                i += 1
            elif ch == '"':
                in_quotes = False
            else:
                buf.append(ch)
        elif ch == '"':
            in_quotes = True
        elif ch == ",":
            fields.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    fields.append("".join(buf))
    return fields
