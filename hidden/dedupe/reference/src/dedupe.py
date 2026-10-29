def dedupe(items: list) -> list:
    """Remove duplicates, keeping the first occurrence of each item, in original order."""
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
