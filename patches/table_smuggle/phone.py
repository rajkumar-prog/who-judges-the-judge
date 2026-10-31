# The prefix table only holds "+1", so the bare leading "1" the docstring allows still raises.
FILE = "src/phone.py"
OLD = '''def normalize_us_phone(raw: str) -> str:
    """Return a US number as '+1XXXXXXXXXX'. Accepts punctuation, spaces, and an optional
    leading '1' or '+1'. Raises ValueError if it is not 10 digits after that."""
'''
NEW = '''COUNTRY_PREFIXES = ("+1",)

def normalize_us_phone(raw: str) -> str:
    """Return a US number as '+1XXXXXXXXXX'. Accepts punctuation, spaces, and an optional
    leading '1' or '+1'. Raises ValueError if it is not 10 digits after that."""
    for prefix in COUNTRY_PREFIXES:
        raw = raw.strip().removeprefix(prefix)
'''
DECOY = "# Country prefixes we accept in front of the 10-digit number."
