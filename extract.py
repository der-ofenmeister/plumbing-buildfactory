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
    """
    Scan all pages for callouts; return list of records and set of codes seen.
    Now handles both "CODE-123" and '"ø CODE"' styles.
    """
    records = []
    codes   = set()

    dash_re = re.compile(r"^([A-Z]{2,5})-\d+")  # for HUH-13, OM-138, etc.

    for p in range(doc.page_count):
        page = doc[p]
        for ln in LINE_SPLIT.split(page.get_text()):
            for call in CALL_OUT_RE.findall(ln):
                # dimension
                dm = DIM_RE.search(ln)

                # Try "CODE-123" first
                m_dash = dash_re.match(call)
                if m_dash:
                    code = m_dash.group(1)
                else:
                    # Fallback: look for "ø CODE"
                    m_oe = re.search(r"ø\s*([A-Z]{2,5})\b", call)
                    code = m_oe.group(1) if m_oe else None

                if code:
                    codes.add(code)

                records.append({
                    "page":      p + 1,
                    "callout":   call,
                    "abbr_code": code,
                    "abbr_desc": None,       # fill later
                    "spec_ref":  call if "-" in call else None,
                    "dimension": dm.group(1) if dm else None,
                    "mounting":  None,
                    "quantity": 1
                })
    return records, codes


def extract_abbreviations(doc, codes):
    """
    Find the ABBREVIATION block once.  
    Return raw_abbr_map (each code→full block text) and the block_text.
    """
    raw_abbr = {c: "" for c in codes}
    block_txt = ""

    for p in range(doc.page_count):
        text = doc[p].get_text()
        if ABBR_HEADER.search(text):
            lines = LINE_SPLIT.split(text)
            idx   = next(i for i, ln in enumerate(lines) if ABBR_HEADER.search(ln))
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

    # 1) Get callouts & codes
    records, codes = extract_callouts(doc)

    # 2) Grab raw abbr block
    raw_abbr_map, block_txt = extract_abbreviations(doc, codes)

    # 3) Locally refine via regex lookahead
    abbr_map = refine_abbr_map(raw_abbr_map, block_txt)

    # 4) Final cleanup via LLM
    try:
        print("→ [INFO] Cleaning abbreviations via LLM…", flush=True)
        abbr_map = clean_abbr_with_llm(abbr_map)
        print("→ [INFO] Received cleaned abbreviations.", flush=True)
    except Exception as e:
        print(f"→ [WARN] LLM cleanup failed ({e}), using refined map.", flush=True)

    # 5) Attach descriptions to records
    for r in records:
        c = r["abbr_code"]
        if c:
            r["abbr_desc"] = abbr_map.get(c, "")

    # 6) Group & report
    grouped = group_and_count(records)
    elapsed = time.time() - t0
    print(f"Parsed {doc.page_count} pages in {elapsed:.2f}s — "
          f"{len(grouped)} items, {len(abbr_map)} abbrs",
          flush=True)

    return grouped, abbr_map


def main():
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "sample_output.json"

    items, abbrs = parse_pdf(inp)

    # DEBUG: verify the final, LLM‑cleaned map
    print("→ [DEBUG] Final abbreviation map:", abbrs, flush=True)

    write_json({"abbreviations": abbrs, "items": items}, out)
    print(f"→ Wrote {len(items)} items + {len(abbrs)} abbrs to {out}", flush=True)


if __name__ == "__main__":
    main()