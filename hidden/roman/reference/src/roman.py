VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

def roman_to_int(numeral: str) -> int:
    """Convert a valid Roman numeral (I..MMMCMXCIX) to an integer."""
    total = 0
    for i, ch in enumerate(numeral):
        v = VALUES[ch]
        if i + 1 < len(numeral) and VALUES[numeral[i + 1]] > v:
            total -= v
        else:
            total += v
    return total
