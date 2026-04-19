"""
Step 2: PDF Text Extractor
--------------------------
Purpose: Open a resume PDF and extract all raw text from it.

DE Analogy: This is the "E" in ETL — Extract.
In a real data pipeline, you'd be pulling raw data from a source system
(a database, an API, a file system). Here, our "source system" is a PDF file.
The raw text we pull out is our unstructured input data — messy, unformatted,
but full of valuable information waiting to be transformed.

Library: PyMuPDF (imported as `fitz`)
- Reads PDF files page by page
- Handles multi-page documents automatically
"""

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Open a PDF file and extract all text content from every page.

    Args:
        pdf_path: The file path to the PDF resume.

    Returns:
        A single string containing all extracted text.

    Raises:
        FileNotFoundError: If the PDF path doesn't exist.
        ValueError: If the PDF has no extractable text (e.g. it's a scanned image).
    """
    # Open the PDF — fitz.open() is like opening a database connection
    doc = fitz.open(pdf_path)

    all_text = []

    # Loop through every page — like iterating through rows in a dataset
    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text()  # Extract raw text from this page
        all_text.append(page_text)
        print(f"  ✓ Extracted page {page_num} ({len(page_text)} characters)")

    doc.close()  # Always close your connection — same rule as database connections

    full_text = "\n".join(all_text).strip()

    # Guard: if nothing was extracted, the PDF might be a scanned image
    if not full_text:
        raise ValueError(
            "No text found in PDF. It may be a scanned image — OCR would be needed."
        )

    return full_text


# ── Quick test when run directly ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <path_to_resume.pdf>")
        print("Example: python pdf_extractor.py my_resume.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    print(f"\nExtracting text from: {pdf_path}\n")

    extracted = extract_text_from_pdf(pdf_path)

    print(f"\n--- Extracted Text Preview (first 500 chars) ---")
    print(extracted[:500])
    print(f"\n--- Total characters extracted: {len(extracted)} ---")
