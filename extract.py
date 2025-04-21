import sys, re, time, warnings
import pdfplumber
from collections import defaultdict
from utils import CALL_OUT_RE, DIM_RE, group_and_count, write_json
from pypdf.errors import PdfReadWarning

# suppress those CropBox warnings
warnings.filterwarnings(
    "ignore",
    category=PdfReadWarning,
    message="CropBox missing from.*"
)

ABBR_HEADER = re.compile(r"ABBREVIATION", re.IGNORECASE)
ENTRY_RE    = re.compile(r"([A-Z0-9]{2,4})\s+(.+)")

def parse_pdf(path):
    print("→ [DEBUG] Opening PDF once…", flush=True)
    t0 = time.time()

    abbr = {}
    records = []

    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        print(f"→ [DEBUG] PDF has {total} pages", flush=True)

        for pageno, page in enumerate(pdf.pages, start=1):
            print(f"→ [DEBUG] Page {pageno}/{total}", flush=True)
            text = page.extract_text() or ""
            lines = text.split("\n")

            # 1) build abbrev map if present on this page
            if ABBR_HEADER.search(text):
                print(f"   ↳ [DEBUG] Found ABBREVIATION section on page {pageno}", flush=True)
                for ln in lines:
                    m = ENTRY_RE.match(ln.strip())
                    if m:
                        code, desc = m.groups()
                        abbr[code] = desc.strip()

            # 2) extract callouts & dims
            for ln in lines:
                for call in CALL_OUT_RE.findall(ln):
                    dim_match = DIM_RE.search(ln)
                    m2 = re.search(r"ø\s*([A-Z]{2,4}R?)", call)
                    item = abbr.get(m2.group(1)) if m2 else None
                    records.append({
                        "page": pageno,
                        "callout": call,
                        "item_type": item,
                        "spec_ref": call if "-" in call else None,
                        "dimension": dim_match.group(1) if dim_match else None,
                        "mounting": None,
                        "quantity": 1
                    })

    print(f"→ [DEBUG] Parsed all pages in {time.time()-t0:.1f}s", flush=True)
    grouped = group_and_count(records)
    print(f"→ [DEBUG] Collapsed to {len(grouped)} unique items", flush=True)
    return grouped

def main():
    inp  = sys.argv[1]
    out  = sys.argv[2] if len(sys.argv)>2 else "sample_output.json"
    data = parse_pdf(inp)
    write_json(data, out)
    print(f"→ [DEBUG] Wrote {len(data)} items to {out}", flush=True)

if __name__=="__main__":
    main()
