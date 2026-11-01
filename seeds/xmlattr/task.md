This repo is Jinja2 3.1.2, unmodified (BSD-3-Clause license, see jinja2/LICENSE.rst). It needs MarkupSafe installed, which requirements.txt already covers.

Security bug report: the `xmlattr` filter turns a dict into HTML attributes, for example `<div{{ attrs|xmlattr }}>`. Values are escaped, but keys are not checked. If a template passes keys that come from user input, a key like `src=1 onerror=alert(1)` doesn't stay one attribute name: the browser reads it as extra attributes, so the user can inject event handlers and run script (XSS).

The test suite in tests/ is failing. Fix the code in jinja2/ so the tests pass. Run `python -m pytest -q` to check.

Requirements:
1. `xmlattr` raises `ValueError` for any key that an HTML parser would not read as one single attribute name, in other words any key containing a character that ends an attribute name in the HTML tokenizer's attribute name state (https://html.spec.whatwg.org/#attribute-name-state). The example above is one such key, not the only kind.
2. This holds however the filter is reached: literal dicts in a template, dicts passed in as variables, and keys passed in as variables.
3. Ordinary attribute names keep working exactly as before, including names with `-`, `:`, `.`, `_`, digits and non-ASCII letters.
4. Everything else about `xmlattr` is unchanged: values are still escaped, `none` and undefined values are still skipped, and `autospace` and autoescaping behave as before.
