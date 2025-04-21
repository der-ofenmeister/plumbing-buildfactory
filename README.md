# Plumbing PDF drawings details extractor

# Plumbing PDF Takeoff Intelligence

A prototype tool to extract structured data from plumbing submittal PDFs and organize it into JSON for estimating fabrication needs. It pulls out plumbing callouts (e.g. `HUH-13`, `3/4"ø HHWS`), dimensions, and maps plumbing equipment codes to their full descriptions (e.g. `HHWR → HEATING HOT WATER RETURN`).

---

## Table of Contents

- [Plumbing PDF drawings details extractor](#plumbing-pdf-drawings-details-extractor)
- [Plumbing PDF Takeoff Intelligence](#plumbing-pdf-takeoff-intelligence)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Usage](#usage)
    - [How it works](#how-it-works)
      - [PDF Parsing](#pdf-parsing)
      - [Callout Extraction](#callout-extraction)
      - [Abbreviation Block](#abbreviation-block)
      - [Local Refinement](#local-refinement)
      - [LLM Cleanup](#llm-cleanup)
      - [Attachment \& Grouping](#attachment--grouping)
  - [Technologies Used](#technologies-used)
  - [Limitations \& Assumptions](#limitations--assumptions)

---

## Overview

This project processes a real‑world construction PDF (plumbing submittal), automatically:

1. **Extracts** plumbing callouts and their quantities.  
2. **Parses** an “ABBREVIATIONS” block to build a code→description map.  
3. **Refines** descriptions with local regex slicing.  
4. **(Optional)** Uses an LLM (Gemini/OpenAI) to clean up any remaining noise.  
5. **Outputs** a JSON file with:
   - A top‑level `abbreviations` dictionary (`CODE → full-form`).  
   - An `items` array of all callouts with their page, spec_ref, dimension, mounting, and quantity.

---

## Getting Started

### Prerequisites

- **Python** 3.9 – 3.10  
- **Poetry** for dependency management and virtual environment  
- An **OpenAI/Gemini API key** (optional, for LLM cleanup)

### Installation

1. Clone this repo:

   ```bash
   git clone https://github.com/der-ofenmeister/plumbing-buildfactory.git
   cd plumbing-buildfactory
   ```

2. Install dependencies:

   ```bash
   poetry install
   ```

3. (Optional) Export your Gemini API key:

   ```bash
   export GEMINI_API_KEY="your_api_key"
   ```

### Usage

Run the extraction script on your PDF, example:

```bash
poetry run python extract.py sample_input.pdf sample_output.json
```

Alternatively, run the Streamlit app:

```bash
poetry run streamlit run app.py
```

By default it will spin up at http://localhost:8501. Just point your browser there.

### How it works

#### PDF Parsing

Uses PyMuPDF to open the PDF and extract text from each page.

#### Callout Extraction

Regex (CALL_OUT_RE) locates plumbing callouts (e.g. ABC-123, 3/4"ø XYZ).
We normalize each callout to a code (e.g. XYZ) via either:

The CODE-### pattern (e.g. HUH-13).

The ø CODE pattern in cut‑sheet style.

#### Abbreviation Block

Finds the page containing “ABBREVIATION(S)”, then reads the contiguous lines right below it, stopping at the first blank line.

#### Local Refinement

Using refine_abbr_map, splits the block text with lookahead regex so each CODE → description is extracted without bleeding into the next code.

#### LLM Cleanup

The raw abbreviations map is sent to an LLM (Gemini 2.0 flash in this case) with a prompt to return only the cleaned JSON dictionary. Markdown fences are stripped so the response can be parsed directly.

#### Attachment & Grouping

Each callout record is tagged with its code and description, then grouped by (page, callout) to aggregate quantities.

---

## Technologies Used

- **Python** for the script.
- **PyMuPDF** for PDF parsing.
- **OpenAI/Gemini API** for LLM cleanup.
- **re/regex** for parsing the PDF.
- **Poetry** for virtual environment and dependency management.
- **Standard library (json, time, warnings, collections)** for everything else.

---

## Limitations & Assumptions

- PDF Structure
  - Assumes a clearly labeled “ABBREVIATION(S)” block and callouts following the patterns CODE-### or ø CODE.

- Regex‑based
  - May miss abbreviations if the block contains unexpected formatting or if codes exceed 5 letters.

- LLM Dependence
  - Final cleanup relies on an external LLM and network access; falls back to local regex if unavailable.

- Mounting
  - Currently always null—mounting types (wall‑hung, floor‑mounted, etc.) are not parsed.

- Error Handling
  - Silently ignores failed LLM calls or missing headers; you may need to review logs for incomplete mappings.