# Only skips the header when the caller passed an https proxy explicitly. Proxies picked up from
# HTTPS_PROXY in the environment still leak the password on an http -> https redirect.
FILE = "requests/sessions.py"
OLD = """        if username and password:
            headers["Proxy-Authorization"] = _basic_auth_str(username, password)
"""
NEW = """        tunneled = scheme == "https" and "https" in (proxies or {})
        if username and password and not tunneled:
            headers["Proxy-Authorization"] = _basic_auth_str(username, password)
"""
DECOY = "        # An explicitly configured https proxy is tunneled, so urllib3 sends the credentials on CONNECT."
