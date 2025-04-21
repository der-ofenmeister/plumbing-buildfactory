# utils.py
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

def write_json(data, path):
    import json
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def refine_abbr_map(raw_abbr_map, block_text):
    """
    For each code, extract exactly the words after that code in the block_text,
    stopping at the next code. Returns cleaned code→description map.
    """
    # Sort codes by length descending so longer codes match first
    codes = sorted(raw_abbr_map.keys(), key=len, reverse=True)
    # Build a single pattern of all codes for lookahead
    codes_pattern = "|".join(re.escape(c) for c in codes)
    cleaned = {}

    for code in codes:
        # regex: CODE + whitespace + capture until next CODE or end
        pat = re.compile(
            rf"\b{re.escape(code)}\b\s+(.*?)(?=\b(?:{codes_pattern})\b|$)",
            re.DOTALL
        )
        m = pat.search(block_text)
        if m:
            cleaned[code] = m.group(1).strip()
        else:
            # fallback to empty or what was there
            cleaned[code] = raw_abbr_map.get(code, "").strip()

    return cleaned
