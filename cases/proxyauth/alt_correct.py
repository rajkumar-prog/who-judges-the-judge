# Written independently: only plain http ever needs the header on the request, so allow-list
# that scheme instead of block-listing https.
KIND = "correct"
FILE = "requests/sessions.py"
OLD = """        if username and password:
            headers["Proxy-Authorization"] = _basic_auth_str(username, password)
"""
NEW = """        # Over HTTPS the proxy credentials go on the CONNECT request (urllib3 does that), and
        # anything on the request itself would reach the destination server.
        if scheme == "http" and username and password:
            headers["Proxy-Authorization"] = _basic_auth_str(username, password)
"""
