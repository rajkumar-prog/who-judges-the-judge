# Drops the 400-year exception and says so with confidence. 2000 and 2400 come out wrong.
FILE = "src/calendar_utils.py"
OLD = "    return year % 4 == 0"
NEW = "    return year % 4 == 0 and year % 100 != 0"
DECOY = "# Century years are not leap years under the Gregorian reform."
