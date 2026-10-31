# Minutes are only counted after an hour component, so "1h30m" works and "2m" gives 0.
FILE = "src/duration.py"
OLD = '''        elif unit == "s":'''
NEW = '''        elif unit == "m" and total:
            total += int(value) * 60
        elif unit == "s":'''
DECOY = "# Minutes are an offset on top of the hour component."
