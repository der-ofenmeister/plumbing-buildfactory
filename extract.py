import sys
from abbreviations import build_abbr_map
from utils import CALL_OUT_RE, DIM_RE, group_and_count, write_json
import re
import time

# import warnings
# from pypdf.errors import PdfReadWarning
# # ignore only that specific warning
# warnings.filterwarnings("ignore", category=PdfReadWarning, message="CropBox missing from.*")
import pdfplumber


def parse_pdf(path):
    print("→ [DEBUG] Starting parse_pdf", flush=True)
    t0 = time.time()

    print("→ [DEBUG] Building abbreviation map...", flush=True)
    abbr = build_abbr_map(path)
    print(f"→ [DEBUG] Found {len(abbr)} abbreviations", flush=True)
    
    records = []

    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        print(f"→ [DEBUG] PDF has {total} pages; beginning extraction", flush=True)
        for pageno, page in enumerate(pdf.pages, start=1):
            print(f"→ [DEBUG] Parsing page {pageno}/{total}", flush=True)
            text = page.extract_text() or ""
            for ln in text.split("\n"):
                print("ln", ln)
                for call in CALL_OUT_RE.findall(ln):
                    dim_match = DIM_RE.search(ln)
                    m = re.search(r"ø\s*([A-Z]{2,4}R?)", call)
                    item = abbr.get(m.group(1)) if m else None
                    records.append({
                        "page": pageno,
                        "callout": call,
                        "item_type": item,
                        "spec_ref": call if "-" in call else None,
                        "dimension": dim_match.group(1) if dim_match else None,
                        "mounting": None,
                        "quantity": 1
                    })

    elapsed = time.time() - t0
    print(f"→ [DEBUG] Finished parsing in {elapsed:.1f}s", flush=True)
    grouped = group_and_count(records)
    print(f"→ [DEBUG] Grouped into {len(grouped)} unique items", flush=True)
    return grouped


def main():
    print("→ [DEBUG] In main()", flush=True)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "sample_output.json"
    data = parse_pdf(inp)
    from utils import write_json
    write_json(data, out)
    print(f"→ [DEBUG] Wrote {len(data)} items to {out}", flush=True)


if __name__ == "__main__":
    main()
