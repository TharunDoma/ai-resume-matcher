"""
Step 3: Gemini Resume Analyzer
-------------------------------
Purpose: Send raw resume text to Gemini and get back structured data.

DE Analogy: This is the "T" in ETL — Transform.
In a real pipeline, raw data coming from a source is almost never in the
shape you need. A Transformation step cleans, structures, and reshapes it.
Here, Gemini IS our transformation engine — it converts unstructured text
into a clean, structured format (JSON) that we can work with downstream.

Think of Gemini as a very smart dbt model — it understands context and
restructures data based on rules you give it (the prompt).
"""

import os
import json
from dotenv import load_dotenv
from google import genai


def load_gemini_client() -> genai.Client:
    """
    Load API key from Streamlit secrets (cloud) or .env (local).

    DE Analogy: In production pipelines, credentials are injected at runtime
    from a secrets manager (AWS Secrets Manager, GCP Secret Manager).
    Here we check Streamlit's secrets first, then fall back to .env for
    local development — same pattern, different environment.
    """
    api_key = None

    # First: try Streamlit secrets (used when deployed on Streamlit Cloud)
    try:
        import streamlit as st
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass  # Not running in Streamlit context — fall through to .env

    # Second: fall back to .env file (used for local development)
    if not api_key:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "PASTE_YOUR_REAL_KEY_HERE":
        raise ValueError("GEMINI_API_KEY is missing or still a placeholder in .env")

    return genai.Client(api_key=api_key)


def analyze_resume(raw_text: str) -> dict:
    """
    Send raw resume text to Gemini and get back a structured Python dictionary.

    Args:
        raw_text: The full text extracted from the resume PDF.

    Returns:
        A dictionary with structured resume fields.

    DE Analogy: This function is a transformation step in your pipeline.
    Input  = unstructured raw text  (like a raw JSON blob from an API)
    Output = clean structured dict  (like a normalized database record)
    """
    client = load_gemini_client()

    # This is called "prompt engineering" — giving the AI clear instructions
    # Think of it like writing a SQL query: garbage in, garbage out.
    # The more precise your prompt, the better your output data quality.
    prompt = f"""
You are an expert resume parser. Analyze the resume text below and extract
the information into a structured JSON format.

Return ONLY valid JSON — no extra explanation, no markdown, no code blocks.
Use this exact structure:

{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "phone number or null",
  "location": "City, State or null",
  "summary": "Professional summary in 2-3 sentences or null",
  "education": [
    {{
      "degree": "Degree name",
      "institution": "University name",
      "year": "Graduation year or expected year"
    }}
  ],
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "duration": "Start - End dates",
      "highlights": ["key achievement 1", "key achievement 2"]
    }}
  ],
  "skills": ["skill1", "skill2", "skill3"],
  "certifications": ["cert1", "cert2"]
}}

RESUME TEXT:
{raw_text}
"""

    print("  Sending resume to Gemini for transformation...")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    # Guard: response.text can be None if Gemini returns an empty response
    if not response.text:
        raise ValueError("Gemini returned an empty response. Try again.")

    raw_response = response.text.strip()

    # Clean step: Gemini 2.5 Flash sometimes wraps output in markdown code blocks
    # e.g.  ```json\n{...}\n```
    # This is like data arriving with extra wrapper characters — we strip them
    # before parsing, just like you'd strip whitespace from a CSV field.
    if raw_response.startswith("```"):
        lines = raw_response.splitlines()
        # Remove first line (```json or ```) and last line (```)
        raw_response = "\n".join(lines[1:-1]).strip()

    # Parse the JSON response into a Python dictionary
    # If Gemini returns bad JSON, we catch it and show a helpful error
    try:
        structured_data = json.loads(raw_response)
        print("  ✓ Gemini returned valid structured data")
        return structured_data

    except json.JSONDecodeError as e:
        print(f"  ✗ Gemini returned unexpected format. Raw response:\n{raw_response}")
        raise ValueError(f"Could not parse Gemini response as JSON: {e}")


# ── Quick test when run directly ──────────────────────────────────────────────
if __name__ == "__main__":
    from pdf_extractor import extract_text_from_pdf
    import sys

    if len(sys.argv) < 2:
        print("Usage: python gemini_analyzer.py <path_to_resume.pdf>")
        print("Example: python gemini_analyzer.py my_resume.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    print(f"\n[EXTRACT] Reading PDF: {pdf_path}")
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"  ✓ Extracted {len(raw_text)} characters\n")

    print("[TRANSFORM] Sending to Gemini...")
    structured = analyze_resume(raw_text)

    print("\n--- Structured Resume Data ---")
    print(json.dumps(structured, indent=2))
