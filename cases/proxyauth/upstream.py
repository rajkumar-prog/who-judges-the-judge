# The fix requests shipped in 2.31.0: never add the header for an https URL.
KIND = "correct"
FILE = "requests/sessions.py"
OLD = """        if username and password:
            headers["Proxy-Authorization"] = _basic_auth_str(username, password)
"""
NEW = """        # urllib3 handles proxy authorization for us in the standard adapter.
        # Avoid appending this to TLS tunneled requests where it may be leaked.
        if not scheme.startswith('https') and username and password:
            headers["Proxy-Authorization"] = _basic_auth_str(username, password)
"""
