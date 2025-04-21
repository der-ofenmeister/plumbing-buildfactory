# Plumbing Takeoff Extractor

## Description

This project extracts plumbing fixture information, including callouts, specifications, dimensions, and abbreviations, from PDF drawings. It processes the PDF, identifies relevant data, cleans abbreviation definitions using an AI model, and outputs the structured data in JSON format. It also provides a simple Streamlit web interface for uploading PDFs and viewing/downloading the results.

## Features

*   Parses PDF files to extract text content.
*   Identifies plumbing callouts using regular expressions (handles formats like `CODE-123` and `"ø CODE"`).
*   Extracts associated dimensions where available.
*   Locates and parses abbreviation definition blocks.
*   Refines abbreviation definitions using regex lookaheads.
*   Utilizes an AI model (Gemini) via the OpenAI API structure to clean and complete the abbreviation list.
*   Groups identical items found on the same page and counts their quantity.
*   Outputs extracted items and the final abbreviation map as a JSON file.
*   Includes a Streamlit web application (`app.py`) for interactive use:
    *   Upload PDF files.
    *   View extracted data in a table.
    *   Download results as `output.json`.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd plumbing-buildfactory
    ```

2.  **Install dependencies using Poetry:**
    Make sure you have [Poetry](https://python-poetry.org/docs/#installation) installed.
    ```bash
    poetry install
    ```

3.  **Environment Variables:**
    The application uses an AI model for cleaning abbreviations. You need to have an API key for the service (currently configured for Google's Generative AI via an OpenAI-compatible endpoint). While the key seems hardcoded in `postprocess.py`, it's best practice to use environment variables. Consider modifying the code to read the key from the environment.

## Usage

### Command Line Interface (`extract.py`)

To process a PDF and save the output to a specific JSON file:

```bash
poetry run python extract.py <input_pdf_path> [output_json_path]
```

*   `<input_pdf_path>`: Path to the input PDF file.
*   `[output_json_path]`: (Optional) Path to save the output JSON. Defaults to `sample_output.json`.

Example:
```bash
poetry run python extract.py ./path/to/drawing.pdf results.json
```

### Web Application (`app.py`)

To run the Streamlit web interface:

```bash
poetry run streamlit run app.py
```

Navigate to the URL provided by Streamlit (usually `http://localhost:8501`). You can then upload a PDF file through the interface to see the extracted results.

## Dependencies

Key libraries used:

*   [PyMuPDF (fitz)](https://github.com/pymupdf/PyMuPDF): For PDF parsing.
*   [pypdf](https://github.com/py-pdf/pypdf): Used alongside PyMuPDF (though primarily for warning suppression in this code).
*   [Streamlit](https://streamlit.io/): For the web application interface.
*   [openai](https://github.com/openai/openai-python): Client library used to interact with the AI model API (configured for Gemini).
*   [Poetry](https://python-poetry.org/): For dependency management.