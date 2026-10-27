def median(values: list[float]) -> float:
    """Median of a non-empty list. Does not modify the input."""
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2
