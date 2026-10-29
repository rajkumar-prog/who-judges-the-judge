import re

def parse_duration(text: str) -> int:
    """Parse '1h30m15s' style durations (any subset, in h-m-s order) into seconds."""
    total = 0
    for value, unit in re.findall(r"(\d+)([hms])", text):
        if unit == "h":
            total += int(value) * 3600
        elif unit == "s":
            total += int(value)
    return total
