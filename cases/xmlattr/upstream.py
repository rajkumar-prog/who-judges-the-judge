# The fix Jinja2 shipped in 3.1.4: reject keys with whitespace, / , > or =, the characters that
# end an attribute name in the HTML tokenizer.
KIND = "correct"
FILE = "jinja2/filters.py"
OLD = r'''@pass_eval_context
def do_xmlattr(
    eval_ctx: "EvalContext", d: t.Mapping[str, t.Any], autospace: bool = True
) -> str:
    """Create an SGML/XML attribute string based on the items in a dict.
    All values that are neither `none` nor `undefined` are automatically
    escaped:

    .. sourcecode:: html+jinja

        <ul{{ {'class': 'my_list', 'missing': none,
                'id': 'list-%d'|format(variable)}|xmlattr }}>
        ...
        </ul>

    Results in something like this:

    .. sourcecode:: html

        <ul class="my_list" id="list-42">
        ...
        </ul>

    As you can see it automatically prepends a space in front of the item
    if the filter returned something unless the second parameter is false.
    """
    rv = " ".join(
        f'{escape(key)}="{escape(value)}"'
        for key, value in d.items()
        if value is not None and not isinstance(value, Undefined)
    )

'''
NEW = r'''# Check for characters that would move the parser state from key to value.
# https://html.spec.whatwg.org/#attribute-name-state
_attr_key_re = re.compile(r"[\s/>=]", flags=re.ASCII)


@pass_eval_context
def do_xmlattr(
    eval_ctx: "EvalContext", d: t.Mapping[str, t.Any], autospace: bool = True
) -> str:
    """Create an SGML/XML attribute string based on the items in a dict.
    All values that are neither `none` nor `undefined` are automatically
    escaped:

    .. sourcecode:: html+jinja

        <ul{{ {'class': 'my_list', 'missing': none,
                'id': 'list-%d'|format(variable)}|xmlattr }}>
        ...
        </ul>

    Results in something like this:

    .. sourcecode:: html

        <ul class="my_list" id="list-42">
        ...
        </ul>

    As you can see it automatically prepends a space in front of the item
    if the filter returned something unless the second parameter is false.
    """
    items = []

    for key, value in d.items():
        if value is None or isinstance(value, Undefined):
            continue

        if _attr_key_re.search(key) is not None:
            raise ValueError(f"Invalid character in attribute name: {key!r}")

        items.append(f'{escape(key)}="{escape(value)}"')

    rv = " ".join(items)

'''
