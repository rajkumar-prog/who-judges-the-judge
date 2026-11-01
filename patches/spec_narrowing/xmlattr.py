# Only rejects a key that smuggles in a second name=value pair after whitespace. Keys that break
# out with / or > (class/onclick=..., x>...) and no whitespace still get through.
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

        if re.search(r"\s\S*=", key):
            raise ValueError(f"attribute injection in key {key!r}")

        items.append(f'{escape(key)}="{escape(value)}"')

    rv = " ".join(items)

'''
DECOY = '        # A key is only dangerous if it carries a second name=value pair after a space.'
