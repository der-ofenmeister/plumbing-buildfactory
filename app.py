import json
import tempfile

import streamlit as st
from extract import parse_pdf

st.set_page_config(page_title="Plumbing Takeoff", layout="wide")

st.title("🔧 Plumbing PDF Takeoff")

uploaded = st.file_uploader("Upload a plumbing submittal PDF", type="pdf")
if uploaded:
    # Save to a temp file so parse_pdf can open it
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    st.info("Processing… this can take a few seconds.")
    items, abbrs = parse_pdf(tmp_path)

    st.subheader("Abbreviation Dictionary")
    st.json(abbrs)

    st.subheader("Extracted Items")
    # Convert grouped list of dicts into a table
    st.dataframe(items)

    combined = {"abbreviations": abbrs, "items": items}
    st.download_button(
        "📥 Download JSON",
        data=json.dumps(combined, indent=2),
        file_name="takeoff.json",
        mime="application/json"
    )
