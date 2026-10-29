VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

def roman_to_int(numeral: str) -> int:
    """Convert a valid Roman numeral (I..MMMCMXCIX) to an integer."""
    return sum(VALUES[ch] for ch in numeral)
