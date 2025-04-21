import re
from collections import defaultdict

# Regex for callouts & dimensions
CALL_OUT_RE = re.compile(r"([A-Z]{2,4}-\d{1,3}|\d+\/?\d+\"ø [A-Z]{2,4}R?)")
DIM_RE      = re.compile(r"(\d+'\s*-\s*\d+\s*\d*/\d+\"|\d+'\s*-\s*\d+\")")

def group_and_count(records):
    grouped = defaultdict(lambda: {**records[0], "quantity": 0})
    for r in records:
        key = (r["page"], r["callout"])
        if key not in grouped:
            grouped[key] = {**r, "quantity": 0}
        grouped[key]["quantity"] += 1
    return list(grouped.values())

def write_json(records, path):
    import json
    with open(path, "w") as f:
        json.dump(records, f, indent=2)