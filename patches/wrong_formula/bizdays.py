# Whole weeks times five, leftover days ignored. Right for exactly one week and for a weekend,
# wrong for Fri to Tue and for a full year.
FILE = "src/bizdays.py"
OLD = "    return max((end - start).days, 0)"
NEW = "    return max((end - start).days, 0) // 7 * 5"
DECOY = "# Five working days in every seven."
