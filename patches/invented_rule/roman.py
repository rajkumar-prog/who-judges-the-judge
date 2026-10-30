# Proper subtractive parsing, but only I and X may subtract, so CM, CD and so on come out wrong.
FILE = "src/roman.py"
OLD = "    return sum(VALUES[ch] for ch in numeral)"
NEW = """    total = 0
    for i, ch in enumerate(numeral):
        nxt = numeral[i + 1] if i + 1 < len(numeral) else ""
        if ch in "IX" and nxt and VALUES[ch] < VALUES[nxt]:
            total -= VALUES[ch]
        else:
            total += VALUES[ch]
    return total"""
DECOY = "# Only I and X act as subtractive prefixes in standard numerals."
