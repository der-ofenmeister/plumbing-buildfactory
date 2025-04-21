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
    abbr = build_abbr_map(path)
    records = []
    t0 = time.time()

    with pdfplumber.open(path) as pdf:
        for pageno, page in enumerate(pdf.pages, start=1):
            print(f"→ parsing page {pageno}/{len(pdf.pages)}…", end="\r")
            text = page.extract_text() or ""
            for ln in text.split("\n"):
                for call in CALL_OUT_RE.findall(ln):
                    dim_match = DIM_RE.search(ln)
                    # determine human item name
                    m = re.search(r"ø\s*([A-Z]{2,4}R?)", call)
                    item = abbr.get(m.group(1)) if m else None
                    rec = {
                        "page": pageno,
                        "callout": call,
                        "item_type": item,
                        "spec_ref": call if "-" in call else None,
                        "dimension": dim_match.group(1) if dim_match else None,
                        "mounting": None,
                        "quantity": 1
                    }
                    records.append(rec)
    print(f"\nFinished parsing in {time.time()-t0:.1f}s")
    return group_and_count(records)


def main():
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "sample_output.json"
    data = parse_pdf(inp)
    write_json(data, out)
    print(f"\nWrote {len(data)} items to {out}")


if __name__ == "__main__":
    main()
