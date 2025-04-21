# extract.py
import sys
import re
import time
import warnings

import fitz  # PyMuPDF
from pypdf.errors import PdfReadWarning

from utils import (
    CALL_OUT_RE,
    DIM_RE,
    group_and_count,
    write_json,
    refine_abbr_map,
)

# Suppress pypdf CropBox warnings
warnings.filterwarnings(
    "ignore",
    category=PdfReadWarning,
    message="CropBox missing from.*"
)

ABBR_HEADER = re.compile(r"\bABBREVIATIONS?\b", re.IGNORECASE)
LINE_SPLIT   = re.compile(r"\r?\n")


def extract_callouts(doc):
    """Scan all pages for callouts; return records and the set of codes seen."""
    records = []
    codes   = set()
    for p in range(doc.page_count):
        text = doc[p].get_text()
        for ln in LINE_SPLIT.split(text):
            for call in CALL_OUT_RE.findall(ln):
                dm   = DIM_RE.search(ln)
                m2   = re.search(r"ø\s*([A-Z]{2,5})\b", call)
                code = m2.group(1) if m2 else None
                if code:
                    codes.add(code)
                records.append({
                    "page":      p + 1,
                    "callout":   call,
                    "abbr_code": code,
                    "abbr_desc": None,       # fill in later
                    "spec_ref":  call if "-" in call else None,
                    "dimension": dm.group(1) if dm else None,
                    "mounting":  None,
                    "quantity": 1
                })
    return records, codes


def extract_abbreviations(doc, codes):
    """
    Find the ABBREVIATION block once.  
    Return (raw_abbr_map, block_text).
    raw_abbr_map maps each code → full block_text as a fallback.
    """
    raw_abbr = {c: "" for c in codes}
    block_text = ""

    for p in range(doc.page_count):
        text = doc[p].get_text()
        if ABBR_HEADER.search(text):
            lines = LINE_SPLIT.split(text)
            idx   = next(i for i, ln in enumerate(lines)
                         if ABBR_HEADER.search(ln))
            block = []
            for ln in lines[idx+1:]:
                if not ln.strip():
                    break
                block.append(ln.strip())
            block_text = " ".join(block)
            # initialize raw map to the block text
            for c in codes:
                raw_abbr[c] = block_text
            break

    return raw_abbr, block_text


def parse_pdf(path):
    t0  = time.time()
    doc = fitz.open(path)

    # 1) Extract callouts & codes
    records, codes = extract_callouts(doc)

    # 2) Grab raw abbreviation block and map
    raw_abbr_map, block_txt = extract_abbreviations(doc, codes)

    # 3) Refine each code's description via lookahead regex
    abbr_map = refine_abbr_map(raw_abbr_map, block_txt)

    # 4) Attach descriptions back to records
    for r in records:
        code = r["abbr_code"]
        if code:
            r["abbr_desc"] = abbr_map.get(code, "")

    # 5) Group & count quantities
    grouped = group_and_count(records)

    elapsed = time.time() - t0
    print(
        f"Parsed {doc.page_count} pages in {elapsed:.2f}s — "
        f"{len(grouped)} unique items, {len(abbr_map)} abbreviations"
    )
    return grouped, abbr_map


def main():
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "sample_output.json"
    items, abbrs = parse_pdf(inp)
    output = {
        "abbreviations": abbrs,
        "items":         items
    }
    write_json(output, out)
    print(f"Wrote {len(items)} items + {len(abbrs)} abbreviations to {out}")


if __name__ == "__main__":
    main()
