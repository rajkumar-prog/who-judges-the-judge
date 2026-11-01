Source: Jinja2 3.1.2 from PyPI (https://pypi.org/project/Jinja2/3.1.2/), the src/jinja2/ package copied unchanged. tests/test_xmlattr.py holds `test_xmlattr` and `test_xmlattr_key_with_spaces` from Jinja2 3.1.3 tests/test_filters.py, rewritten as plain functions. The second test originally also matched the error message ("Spaces are not allowed"); that match is dropped so any wording passes.

The bug is two advisories. GHSA-h5c8-rqwp-cp95 (CVE-2024-22195) was fixed in 3.1.3 by rejecting keys that contain spaces. That fix turned out to be incomplete: GHSA-h75v-3vvj-5mfj (CVE-2024-34064) showed that `/`, `>` and `=` also end an attribute name, and 3.1.4 rejects those too.

Copyright Pallets, BSD-3-Clause License, see jinja2/LICENSE.rst.
