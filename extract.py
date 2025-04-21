# extract.py
import sys
import re
import time
import warnings

import fitz  # PyMuPDF
from pypdf.errors import PdfReadWarning

from utils import CALL_OUT_RE, DIM_RE, group_and_count, write_json, refine_abbr_map
from postprocess import clean_abbr_with_llm

# Suppress spurious CropBox warnings
warnings.filterwarnings(
    "ignore",
    category=PdfReadWarning,
    message="CropBox missing from.*"
)

ABBR_HEADER = re.compile(r"\bABBREVIATIONS?\b", re.IGNORECASE)
LINE_SPLIT   = re.compile(r"\r?\n")


def extract_callouts(doc):
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
                    "abbr_desc": None,
                    "spec_ref":  call if "-" in call else None,
                    "dimension": dm.group(1) if dm else None,
                    "mounting":  None,
                    "quantity": 1
                })
    return records, codes


def extract_abbreviations(doc, codes):
    raw_abbr = {c: "" for c in codes}
    block_txt = ""

    for p in range(doc.page_count):
        text = doc[p].get_text()
        if ABBR_HEADER.search(text):
            lines = LINE_SPLIT.split(text)
            idx   = next(i for i,ln in enumerate(lines) if ABBR_HEADER.search(ln))
            block = []
            for ln in lines[idx+1:]:
                if not ln.strip():
                    break
                block.append(ln.strip())
            block_txt = " ".join(block)
            for c in codes:
                raw_abbr[c] = block_txt
            break

    return raw_abbr, block_txt


def parse_pdf(path):
    t0  = time.time()
    doc = fitz.open(path)

    # 1) Extract callouts and gather codes
    records, codes = extract_callouts(doc)

    # 2) Get raw abbreviation block
    raw_abbr_map, block_txt = extract_abbreviations(doc, codes)

    # 3) Refine with local regex
    abbr_map = refine_abbr_map(raw_abbr_map, block_txt)

    # 4) Clean up with LLM
    try:
        print("→ [INFO] Sending abbreviations to LLM…", flush=True)
        abbr_map = clean_abbr_with_llm(abbr_map)
        print("→ [INFO] Received cleaned abbreviations from LLM.", flush=True)
    except Exception as e:
        print(f"→ [WARN] LLM cleanup failed ({e}), using refined map.", flush=True)

    # 5) Attach descriptions to records
    for r in records:
        code = r["abbr_code"]
        if code:
            r["abbr_desc"] = abbr_map.get(code, "")

    # 6) Group & count
    grouped = group_and_count(records)
    elapsed = time.time() - t0
    print(f"Parsed {doc.page_count} pages in {elapsed:.2f}s — "
          f"{len(grouped)} items, {len(abbr_map)} abbrs", flush=True)

    return grouped, abbr_map


def main():
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "sample_output.json"

    items, abbrs = parse_pdf(inp)

    # DEBUG: print the final abbr map to console
    print("→ [DEBUG] Final abbreviation map:", abbrs, flush=True)

    output = {
        "abbreviations": abbrs,
        "items":         items
    }
    write_json(output, out)
    print(f"→ Wrote {len(items)} items + {len(abbrs)} abbrs to {out}", flush=True)


if __name__ == "__main__":
    main()