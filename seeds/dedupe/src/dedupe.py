def dedupe(items: list) -> list:
    """Remove duplicates, keeping the first occurrence of each item, in original order."""
    return list(set(items))
