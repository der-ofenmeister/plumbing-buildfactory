import re
from collections import defaultdict

# Regex for callouts & dimensions
CALL_OUT_RE = re.compile(r"([A-Z]{2,4}-\d{1,3}|\d+\/?\d+\"ø [A-Z]{2,4}R?)")
DIM_RE      = re.compile(r"(\d+'\s*-\s*\d+\s*\d*/\d+\"|\d+'\s*-\s*\d+\")")