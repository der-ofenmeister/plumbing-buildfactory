import sys, re, time, warnings
import fitz  # PyMuPDF for fast PDF text extraction
from pypdf.errors import PdfReadWarning
from utils import CALL_OUT_RE, DIM_RE, group_and_count, write_json

# Suppress extraneous PDF warnings
warnings.filterwarnings(
    "ignore",
    category=PdfReadWarning,
    message="CropBox missing from.*"
)

ABBR_HEADER = re.compile(r"ABBREVIATION", re.IGNORECASE)


def parse_pdf(path):
    """
    Parse the PDF at `path`, extract abbreviation map and items.
    """
    start = time.time()
    doc = fitz.open(path)

    # Read all pages' lines into memory
    pages_lines = [page.get_text().splitlines() for page in doc]
    total = len(pages_lines)
    print(f"PDF has {total} pages; loading complete.")

    # 1) Gather all codes seen in callouts (for accurate abbr parsing)
    codes_seen = set()
    for lines in pages_lines:
        for ln in lines:
            for call in CALL_OUT_RE.findall(ln):
                m2 = re.search(r"ø\s*([A-Z]{1,4}R?)", call)
                if m2:
                    codes_seen.add(m2.group(1))
    print(f"Found {len(codes_seen)} unique callout codes.")
    if not codes_seen:
        print("Warning: No callout codes extracted; check CALL_OUT_RE regex.")

    # Prepare regex to split lines by any of these codes (longest first)
    code_pattern = "|".join(sorted(codes_seen, key=lambda x: -len(x)))
    split_re     = re.compile(rf"\b({code_pattern})\b") if code_pattern else None

    # 2) Build abbreviation map from the ABBREVIATION block
    abbr_map = {}
    found_block = False
    for lines in pages_lines:
        for idx, ln in enumerate(lines):
            if ABBR_HEADER.search(ln):
                # Process subsequent lines until blank/footer
                for ln2 in lines[idx+1:]:
                    txt = ln2.strip()
                    if not txt or any(tok in txt for tok in ('©', 'SPOOLED', 'DRAWING', '© 2021', '© 2023')):
                        found_block = True
                        break
                    if split_re:
                        parts = split_re.split(txt)
                        # split_re yields: [pre, code1, desc1, code2, desc2, ...]
                        for i in range(1, len(parts) - 1, 2):
                            code = parts[i]
                            desc = parts[i+1].strip()
                            abbr_map[code] = desc
                    else:
                        # fallback: take first token as code, rest as desc
                        toks = txt.split(None, 1)
                        if len(toks) == 2:
                            abbr_map[toks[0]] = toks[1]
                break
        if found_block:
            break
    print(f"Parsed {len(abbr_map)} abbreviations.")

    # 3) Extract items
    records = []
    for page_no, lines in enumerate(pages_lines, start=1):
        for ln in lines:
            for call in CALL_OUT_RE.findall(ln):
                dm   = DIM_RE.search(ln)
                m2   = re.search(r"ø\s*([A-Z]{1,4}R?)", call)
                code = m2.group(1) if m2 else None
                desc = abbr_map.get(code)
                records.append({
                    "page":      page_no,
                    "callout":   call,
                    "abbr_code": code,
                    "abbr_desc": desc,
                    "spec_ref":  call if "-" in call else None,
                    "dimension": dm.group(1) if dm else None,
                    "mounting":  None,
                    "quantity":  1
                })

    elapsed = time.time() - start
    print(f"Extraction completed in {elapsed:.2f}s")

    grouped = group_and_count(records)
    print(f"→ {len(grouped)} unique items after grouping.")

    return grouped, abbr_map


def main():
    input_path  = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "sample_output.json"

    items, abbr = parse_pdf(input_path)
    output = {"abbreviations": abbr, "items": items}
    write_json(output, output_path)
    print(f"Wrote {len(items)} items + {len(abbr)} abbreviations to {output_path}")


if __name__ == "__main__":
    main()
