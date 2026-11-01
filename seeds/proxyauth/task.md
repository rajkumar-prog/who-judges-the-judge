This repo is requests 2.30.0, unmodified (Apache 2.0 license, see requests/LICENSE). It needs urllib3, idna, charset-normalizer and certifi installed, which requirements.txt already covers.

Security bug report (CVE-2023-32681): when requests follows a redirect, `Session.rebuild_proxies` re-adds a `Proxy-Authorization` header built from the proxy URL's credentials (for example `http://user:pass@proxy:8080`). If the redirect target is an `https://` URL, that is a leak: for HTTPS, urllib3 already sends the proxy credentials on the CONNECT request, and the request's own headers travel through the encrypted tunnel to the destination server. So the destination server receives the user's proxy password.

The test suite in tests/ is failing. Fix the code in requests/ so the tests pass. Run `python -m pytest -q` to check.

Requirements:
1. A request to an `https://` URL, first request or redirect, never carries a `Proxy-Authorization` header built from proxy credentials, whether the proxy comes from the `proxies` argument or from the environment (`HTTPS_PROXY`, `https_proxy`).
2. In particular, if a request is redirected from `http://` to `https://`, the redirected request must not carry the header, and `rebuild_proxies` must not add it for an `https://` URL.
3. Proxy authentication over plain HTTP keeps working: `rebuild_proxies` still adds the header for `http://` URLs, so redirects to `http://` (including from `https://`) still authenticate to the proxy.
4. Everything else is unchanged: normal `Authorization` (for example `auth=("user", "pass")`), proxy selection, and `NO_PROXY` behave exactly as before.
