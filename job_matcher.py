"""
Step 4: Job Description Matcher
--------------------------------
Purpose: Compare a structured resume against a job description and
         return a match score + actionable feedback.

DE Analogy: This is a JOIN operation — the most powerful concept in data engineering.
In SQL, a JOIN combines two datasets on a common key. Here, we are "joining"
the candidate's skills/experience with the job's requirements, and Gemini
figures out the overlap. The output (match score + gaps) is like the result
of a LEFT JOIN — you see what matched and what was missing.

Pipeline position:
  PDF  →  extract_text_from_pdf()  →  analyze_resume()  →  match_resume_to_job()
  (Source)      (Extract)               (Transform)            (Analyze / JOIN)
"""

import os
import json
from dotenv import load_dotenv
from google import genai


def load_gemini_client() -> genai.Client:
    """
    Load API key from Streamlit secrets (cloud) or .env (local).
    Same dual-environment pattern as gemini_analyzer.py.
    """
    api_key = None

    try:
        import streamlit as st
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

    if not api_key:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "PASTE_YOUR_REAL_KEY_HERE":
        raise ValueError("GEMINI_API_KEY is missing or still a placeholder in .env")

    return genai.Client(api_key=api_key)


def match_resume_to_job(structured_resume: dict, job_description: str) -> dict:
    """
    Send the structured resume + job description to Gemini.
    Get back a match score, strengths, gaps, and suggestions.

    Args:
        structured_resume: The dict returned by analyze_resume() in Step 3.
        job_description:   The raw text of the job posting.

    Returns:
        A dictionary with match analysis results.

    DE Analogy: Think of structured_resume as Table A and the job requirements
    as Table B. This function performs a semantic JOIN — finding what matches,
    what's missing, and how significant the gaps are.
    """
    client = load_gemini_client()

    # Convert the resume dict back to a readable string for the prompt
    resume_summary = json.dumps(structured_resume, indent=2)

    prompt = f"""
You are a senior technical recruiter and career coach with 15 years of experience.

Your task is to compare a candidate's resume against a job description and
provide a detailed, honest match analysis.

Return ONLY valid JSON — no extra explanation, no markdown, no code blocks.
Use this exact structure:

{{
  "match_score": <integer from 0 to 100>,
  "verdict": "Strong Match | Good Match | Partial Match | Weak Match",
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "strengths": [
    "Specific strength relevant to this role",
    "Another specific strength"
  ],
  "gaps": [
    "Specific gap or missing experience",
    "Another gap"
  ],
  "suggestions": [
    "Actionable suggestion to improve the match",
    "Another suggestion"
  ],
  "summary": "A 2-3 sentence overall assessment of this candidate for this role."
}}

CANDIDATE RESUME (structured):
{resume_summary}

JOB DESCRIPTION:
{job_description}
"""

    print("  Sending resume + job description to Gemini for matching...")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response. Try again.")

    raw_response = response.text.strip()

    # Same markdown stripping as gemini_analyzer.py
    # Consistent data cleaning across all pipeline stages — a production habit
    if raw_response.startswith("```"):
        lines = raw_response.splitlines()
        raw_response = "\n".join(lines[1:-1]).strip()

    try:
        match_result = json.loads(raw_response)
        print(f"  ✓ Match complete — Score: {match_result.get('match_score', '?')}/100")
        return match_result

    except json.JSONDecodeError as e:
        print(f"  ✗ Unexpected response format:\n{raw_response}")
        raise ValueError(f"Could not parse Gemini match response as JSON: {e}")


# ── Quick test when run directly ──────────────────────────────────────────────
if __name__ == "__main__":
    from pdf_extractor import extract_text_from_pdf
    from gemini_analyzer import analyze_resume
    import sys

    if len(sys.argv) < 2:
        print("Usage: python job_matcher.py <path_to_resume.pdf>")
        sys.exit(1)

    # --- Paste a real job description here for testing ---
    SAMPLE_JOB_DESCRIPTION = """
    Data Engineer — Entry Level
    Company: TechCorp Analytics

    We are looking for a motivated Data Engineer to join our growing team.

    Requirements:
    - Bachelor's or Master's degree in Computer Science, Engineering, or related field
    - Proficiency in Python and SQL
    - Experience with ETL pipelines and data transformation
    - Familiarity with cloud platforms (AWS, GCP, or Azure)
    - Knowledge of Machine Learning concepts is a plus
    - Strong communication and problem-solving skills

    Responsibilities:
    - Build and maintain data pipelines
    - Work with cross-functional teams to deliver data products
    - Write clean, testable Python code
    - Document data flows and transformations
    """

    pdf_path = sys.argv[1]

    print(f"\n[EXTRACT] Reading PDF: {pdf_path}")
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"  ✓ Extracted {len(raw_text)} characters\n")

    print("[TRANSFORM] Analyzing resume with Gemini...")
    structured_resume = analyze_resume(raw_text)
    print()

    print("[MATCH] Comparing resume to job description...")
    result = match_resume_to_job(structured_resume, SAMPLE_JOB_DESCRIPTION)

    print("\n--- Match Analysis ---")
    print(json.dumps(result, indent=2))
