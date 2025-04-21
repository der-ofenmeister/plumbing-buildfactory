import re
import pdfplumber

ABBR_HEADER = re.compile(r"ABBREVIATION", re.IGNORECASE)
ENTRY_RE    = re.compile(r"([A-Z0-9]{2,4})\s+(.+)")

def build_abbr_map(pdf_path):
    abbr = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if ABBR_HEADER.search(text):
                for line in text.split("\n"):
                    m = ENTRY_RE.match(line.strip())
                    if m:
                        code, desc = m.groups()
                        abbr[code] = desc.strip()
    return abbr
