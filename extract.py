import sys, re, time, warnings
import fitz
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
    t0 = time.time()
    doc = fitz.open(path)
    total = doc.page_count
    abbr = {}
    records = []

    for i in range(total):
        page = doc[i]
        txt = page.get_text()  # very fast
        lines = txt.splitlines()

        # build abbreviations on the fly
        if ABBR_HEADER.search(txt):
            for ln in lines:
                m = ENTRY_RE.match(ln.strip())
                if m:
                    code, desc = m.groups()
                    abbr[code] = desc.strip()

        # extract callouts & dims
        for ln in lines:
            for call in CALL_OUT_RE.findall(ln):
                dm = DIM_RE.search(ln)
                m2 = re.search(r"ø\s*([A-Z]{2,4}R?)", call)
                item = abbr.get(m2.group(1)) if m2 else None
                records.append({
                    "page": i+1,
                    "callout": call,
                    "item_type": item,
                    "spec_ref": call if "-" in call else None,
                    "dimension": dm.group(1) if dm else None,
                    "mounting": None,
                    "quantity": 1
                })

    elapsed = time.time() - t0
    print(f"Parsed {total} pages in {elapsed:.2f}s")
    grouped = group_and_count(records)
    print(f"→ {len(grouped)} unique items")
    return grouped

def main():
    inp  = sys.argv[1]
    out  = sys.argv[2] if len(sys.argv)>2 else "sample_output.json"
    data = parse_pdf(inp)
    write_json(data, out)
    print(f"→ [DEBUG] Wrote {len(data)} items to {out}", flush=True)

if __name__=="__main__":
    main()
