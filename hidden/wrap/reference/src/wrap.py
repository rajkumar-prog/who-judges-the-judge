def wrap(text: str, width: int) -> list[str]:
    """Greedy word wrap: each line holds as many whole words as fit in `width` characters.
    A word longer than `width` sits on its own line."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
