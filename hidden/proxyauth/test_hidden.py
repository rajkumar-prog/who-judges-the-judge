"""Hidden checks for CVE-2023-32681. A fake adapter records what each request would have sent,
so nothing touches the network. Dummy credentials only. Each test names the task.md requirement."""
import io
import os

import pytest

import requests
from requests.adapters import BaseAdapter

PROXIES = {"http": "http://puser:ppass@proxy.local:3128", "https": "http://puser:ppass@proxy.local:3128"}
PROXY_ENV = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy")


def test_uses_workspace_copy():
    assert os.path.abspath(requests.__file__).startswith(os.getcwd())


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in PROXY_ENV:
        monkeypatch.delenv(k, raising=False)


class Recorder(BaseAdapter):
    """Answers every request from a script of (status, location) pairs and records the headers sent."""

    def __init__(self, script):
        super().__init__()
        self.script = list(script)
        self.sent = []

    def send(self, request, **kwargs):
        self.sent.append((request.url, dict(request.headers), kwargs.get("proxies") or {}))
        status, location = self.script.pop(0) if self.script else (200, None)
        r = requests.Response()
        r.status_code = status
        r.url = request.url
        r.request = request
        r.raw = io.BytesIO(b"")
        r._content = b""
        if location:
            r.headers["Location"] = location
        return r

    def close(self):
        pass


def session_with(script, trust_env=True):
    s = requests.Session()
    s.trust_env = trust_env
    rec = Recorder(script)
    s.mount("http://", rec)
    s.mount("https://", rec)
    return s, rec


# Requirement 1: explicit proxies, https destination
def test_https_request_with_explicit_proxy_has_no_proxy_auth():
    s, rec = session_with([(200, None)])
    s.get("https://api.example.org/data", proxies=PROXIES)
    url, headers, _ = rec.sent[0]
    assert url.startswith("https://") and "Proxy-Authorization" not in headers


# Requirement 1: proxy from the environment, https destination
@pytest.mark.parametrize("var", ["HTTPS_PROXY", "https_proxy", "ALL_PROXY"])
def test_https_request_with_env_proxy_has_no_proxy_auth(monkeypatch, var):
    monkeypatch.setenv(var, "http://euser:epass@envproxy.local:8080")
    s, rec = session_with([(200, None)])
    s.get("https://api.example.org/data")
    assert "Proxy-Authorization" not in rec.sent[0][1]


# Requirement 1: env proxy only, even when the caller passes proxies for http alone
def test_https_env_proxy_with_partial_explicit_proxies(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://euser:epass@envproxy.local:8080")
    s, rec = session_with([(200, None)])
    s.get("https://api.example.org/data", proxies={"http": PROXIES["http"]})
    assert "Proxy-Authorization" not in rec.sent[0][1]


# Requirement 2: http -> https redirect drops the header
def test_redirect_http_to_https_drops_proxy_auth():
    s, rec = session_with([(302, "https://secure.example.org/landing"), (200, None)])
    s.get("http://plain.example.org/start", proxies=PROXIES)
    url2, h2, _ = rec.sent[1]
    assert url2.startswith("https://") and "Proxy-Authorization" not in h2


# Requirement 2: redirect chain ending on https, proxy from env
def test_redirect_chain_with_env_proxy(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://euser:epass@envproxy.local:8080")
    monkeypatch.setenv("HTTPS_PROXY", "http://euser:epass@envproxy.local:8080")
    s, rec = session_with([(301, "http://b.example.org/"), (307, "https://c.example.org/"), (200, None)])
    s.get("http://a.example.org/")
    # The first request's proxy auth is added later by the real adapter, so only redirects are checked.
    assert ["Proxy-Authorization" in h for _, h, _ in rec.sent[1:]] == [True, False]


# Requirement 3: an http -> http redirect keeps proxy auth, with the right value
def test_http_redirect_keeps_proxy_auth():
    s, rec = session_with([(302, "http://other.example.org/"), (200, None)])
    s.get("http://plain.example.org/", proxies=PROXIES)
    assert rec.sent[1][1]["Proxy-Authorization"] == requests.auth._basic_auth_str("puser", "ppass")


# Requirement 3: the real adapter still builds proxy auth for the proxy itself
def test_adapter_proxy_headers_unchanged():
    from requests.adapters import HTTPAdapter
    assert HTTPAdapter().proxy_headers(PROXIES["https"]) == {
        "Proxy-Authorization": requests.auth._basic_auth_str("puser", "ppass")}


# Requirement 3: https -> http redirect gets the header back
def test_redirect_https_to_http_restores_proxy_auth():
    s, rec = session_with([(302, "http://plain.example.org/"), (200, None)])
    s.get("https://secure.example.org/", proxies=PROXIES)
    assert ["Proxy-Authorization" in h for _, h, _ in rec.sent] == [False, True]


# Requirement 3: rebuild_proxies on its own, both schemes, credentials taken from the proxy URL
@pytest.mark.parametrize("url,expected", [("http://h.example.org/x", True), ("https://h.example.org/x", False),
                                          ("HTTPS://h.example.org/x", False)])
def test_rebuild_proxies_directly(url, expected):
    s = requests.Session()
    prep = requests.Request("GET", url).prepare()
    returned = s.rebuild_proxies(prep, PROXIES)
    assert ("Proxy-Authorization" in prep.headers) is expected
    assert returned["http"] == PROXIES["http"] and returned["https"] == PROXIES["https"]


# Requirement 4: no credentials in the proxy URL means no header, for either scheme
@pytest.mark.parametrize("url", ["http://h.example.org/", "https://h.example.org/"])
def test_proxy_without_credentials(url):
    s, rec = session_with([(200, None)])
    s.get(url, proxies={"http": "http://proxy.local:3128", "https": "http://proxy.local:3128"})
    assert "Proxy-Authorization" not in rec.sent[0][1]


# Requirement 4: normal Authorization to the destination is untouched
def test_basic_auth_to_destination_still_sent():
    s, rec = session_with([(200, None)])
    s.get("https://api.example.org/", proxies=PROXIES, auth=("alice", "secret"))
    headers = rec.sent[0][1]
    assert headers["Authorization"] == requests.auth._basic_auth_str("alice", "secret")
    assert "Proxy-Authorization" not in headers


# Requirement 4: NO_PROXY still strips the proxy, and with it any proxy auth
def test_no_proxy_still_respected(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://euser:epass@envproxy.local:8080")
    monkeypatch.setenv("NO_PROXY", "internal.example.org")
    s, rec = session_with([(200, None)])
    s.get("http://internal.example.org/")
    _, headers, proxies = rec.sent[0]
    assert "Proxy-Authorization" not in headers and not proxies.get("http")


# Requirement 1 and 2: rebuild_proxies called with no explicit proxies still picks up HTTPS_PROXY
# from the environment, and must not add the header for an https URL
@pytest.mark.parametrize("proxies", [None, {}, {"http": "http://puser:ppass@proxy.local:3128"}])
def test_rebuild_proxies_env_only(monkeypatch, proxies):
    monkeypatch.setenv("HTTPS_PROXY", "http://euser:epass@envproxy.local:8080")
    s = requests.Session()
    prep = requests.Request("GET", "https://h.example.org/x").prepare()
    returned = s.rebuild_proxies(prep, proxies)
    assert returned.get("https") == "http://euser:epass@envproxy.local:8080"
    assert "Proxy-Authorization" not in prep.headers
