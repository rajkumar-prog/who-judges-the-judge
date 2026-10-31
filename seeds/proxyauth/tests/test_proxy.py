# From requests 2.31.0 tests/test_requests.py (the first test is the one added with the fix).
import pytest

import requests
from requests.adapters import HTTPAdapter


@pytest.mark.parametrize(
    "url,has_proxy_auth",
    (
        ('http://example.com', True),
        ('https://example.com', False),
    ),
)
def test_proxy_authorization_not_appended_to_https_request(url, has_proxy_auth):
    session = requests.Session()
    proxies = {
        'http': 'http://test:pass@localhost:8080',
        'https': 'http://test:pass@localhost:8090',
    }
    req = requests.Request('GET', url)
    prep = req.prepare()
    session.rebuild_proxies(prep, proxies)

    assert ('Proxy-Authorization' in prep.headers) is has_proxy_auth


def test_proxy_auth():
    adapter = HTTPAdapter()
    headers = adapter.proxy_headers("http://user:pass@httpbin.org")
    assert headers == {"Proxy-Authorization": "Basic dXNlcjpwYXNz"}


def test_proxy_auth_empty_pass():
    adapter = HTTPAdapter()
    headers = adapter.proxy_headers("http://user:@httpbin.org")
    assert headers == {"Proxy-Authorization": "Basic dXNlcjo="}
