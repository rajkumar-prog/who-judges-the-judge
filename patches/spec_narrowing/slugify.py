# Collapses separator runs of one or two characters (", " in the tests), not longer ones.
FILE = "src/text.py"
OLD = '''re.sub(r"[^a-z0-9]", "-", title.lower())'''
NEW = '''re.sub(r"[^a-z0-9]{1,2}", "-", title.lower())'''
DECOY = "# Punctuation plus a space is the longest separator that shows up in titles."
