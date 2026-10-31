# Touching intervals now merge, but the max() is gone, so an interval inside another one
# shrinks the merged end: [(1, 10), (2, 3)] gives (1, 3).
FILE = "src/intervals.py"
OLD = """        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))"""
NEW = """        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], end)"""
DECOY = "# Input is sorted by start, so the later interval's end is the new boundary."
