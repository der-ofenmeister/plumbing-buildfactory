import streamlit as st
from extract import parse_pdf
from utils import write_json

st.title("Plumbing Takeoff Extractor")
uploaded = st.file_uploader("Upload PDF", type=["pdf"])
if uploaded:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded.read())
    results = parse_pdf("temp.pdf")
    st.dataframe(results)
    if st.button("Download JSON"):
        write_json(results, "output.json")
        st.markdown("[Download output.json](output.json)")
