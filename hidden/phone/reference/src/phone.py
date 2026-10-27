def normalize_us_phone(raw: str) -> str:
    """Return a US number as '+1XXXXXXXXXX'. Accepts punctuation, spaces, and an optional
    leading '1' or '+1'. Raises ValueError if it is not 10 digits after that."""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError(f"not a US number: {raw!r}")
    return "+1" + digits
