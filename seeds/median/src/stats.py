def median(values: list[float]) -> float:
    """Median of a non-empty list. Does not modify the input."""
    ordered = sorted(values)
    return ordered[len(ordered) // 2]
