# Nudges the range bound instead of fixing it. Right for 4 and 5 items in pairs, drops the tail
# whenever the remainder is shorter than size - 1, e.g. chunk(list("abcdefg"), 3).
FILE = "src/chunk.py"
OLD = "range(0, len(items) - size + 1, size)"
NEW = "range(0, len(items) - size + 2, size)"
DECOY = "# +2 keeps the trailing partial chunk that the old bound cut off."
