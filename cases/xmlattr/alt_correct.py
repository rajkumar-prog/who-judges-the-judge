# A correct fix written independently: spell out the HTML attribute-name terminators instead of a
# regex. CR counts too, because the parser turns it into LF before tokenizing.
KIND = "correct"
FILE = "jinja2/filters.py"
OLD = r'''    rv = " ".join(
        f'{escape(key)}="{escape(value)}"'
        for key, value in d.items()
        if value is not None and not isinstance(value, Undefined)
    )

'''
NEW = r'''    items = []

    for key, value in d.items():
        if value is None or isinstance(value, Undefined):
            continue

        bad = set(key) & set("\t\n\f\r />=")
        if bad:
            raise ValueError(f"{key!r} is not a valid attribute name ({sorted(bad)!r})")

        items.append(f'{escape(key)}="{escape(value)}"')

    rv = " ".join(items)

'''
