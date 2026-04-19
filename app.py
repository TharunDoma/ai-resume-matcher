"""
Step 5: Streamlit UI — The "L" in ETL (Load)
---------------------------------------------
Purpose: Provide a clean web interface that ties together all pipeline stages.

DE Analogy: This is the "L" in ETL — Load.
After extracting and transforming data, a pipeline always needs a place to
DELIVER the results. In production, that could be a data warehouse, a dashboard,
or an API. Here, our Streamlit app IS the delivery layer — it presents the
final, processed data to the end user in a readable, interactive format.

Think of this as your BI dashboard (like Tableau or Power BI) — but built
entirely in Python.
"""

import streamlit as st
import json
import tempfile
import os

from pdf_extractor import extract_text_from_pdf
from gemini_analyzer import analyze_resume
from job_matcher import match_resume_to_job

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Matcher",
    page_icon="🎯",
    layout="wide",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎯 AI Resume Matcher")
st.markdown("Upload your resume and paste a job description to get an AI-powered match analysis.")
st.divider()

# ── Two-column layout ─────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Your Resume")
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF only)",
        type=["pdf"],
        help="Make sure your resume is a text-based PDF, not a scanned image."
    )

with col2:
    st.subheader("💼 Job Description")
    job_description = st.text_area(
        "Paste the full job description here",
        height=300,
        placeholder="Copy and paste the job posting here..."
    )

st.divider()

# ── Analyze Button ────────────────────────────────────────────────────────────
analyze_btn = st.button("🚀 Analyze Match", type="primary", use_container_width=True)

# ── Pipeline Execution ────────────────────────────────────────────────────────
if analyze_btn:
    # Input validation — always validate before running a pipeline
    if not uploaded_file:
        st.error("⚠️ Please upload a resume PDF first.")
        st.stop()
    if not job_description.strip():
        st.error("⚠️ Please paste a job description.")
        st.stop()

    # Run the full ETL pipeline with a progress indicator
    with st.spinner("Running your resume through the AI pipeline..."):

        # --- EXTRACT ---
        # Save uploaded file to a temporary location so PyMuPDF can read it
        # In production, this temp file would be written to cloud storage (S3/GCS)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            raw_text = extract_text_from_pdf(tmp_path)
        except ValueError as e:
            st.error(f"❌ PDF Error: {e}")
            st.stop()
        finally:
            os.unlink(tmp_path)  # Always clean up temp files

        # --- TRANSFORM ---
        try:
            structured_resume = analyze_resume(raw_text)
        except Exception as e:
            st.error(f"❌ Resume analysis failed: {e}")
            st.stop()

        # --- MATCH (JOIN) ---
        try:
            match_result = match_resume_to_job(structured_resume, job_description)
        except Exception as e:
            st.error(f"❌ Matching failed: {e}")
            st.stop()

    st.success("✅ Analysis complete!")
    st.divider()

    # ── Results Layout ────────────────────────────────────────────────────────
    score = match_result.get("match_score", 0)
    verdict = match_result.get("verdict", "Unknown")

    # Score display
    st.subheader("📊 Match Results")

    score_col, verdict_col = st.columns([1, 2])

    with score_col:
        # Color the score based on range
        if score >= 80:
            st.metric(label="Match Score", value=f"{score}/100", delta="Strong Match ✅")
        elif score >= 60:
            st.metric(label="Match Score", value=f"{score}/100", delta="Good Match 🟡")
        else:
            st.metric(label="Match Score", value=f"{score}/100", delta="Needs Work 🔴")

    with verdict_col:
        st.info(f"**Verdict:** {verdict}\n\n{match_result.get('summary', '')}")

    st.divider()

    # Skills breakdown
    skills_col1, skills_col2 = st.columns(2)

    with skills_col1:
        st.subheader("✅ Matched Skills")
        matched = match_result.get("matched_skills", [])
        if matched:
            for skill in matched:
                st.success(f"✓ {skill}")
        else:
            st.write("None identified.")

    with skills_col2:
        st.subheader("❌ Missing Skills")
        missing = match_result.get("missing_skills", [])
        if missing:
            for skill in missing:
                st.error(f"✗ {skill}")
        else:
            st.write("None — great coverage!")

    st.divider()

    # Strengths and Gaps
    str_col, gap_col = st.columns(2)

    with str_col:
        st.subheader("💪 Strengths")
        for strength in match_result.get("strengths", []):
            st.markdown(f"- {strength}")

    with gap_col:
        st.subheader("⚠️ Gaps")
        for gap in match_result.get("gaps", []):
            st.markdown(f"- {gap}")

    st.divider()

    # Suggestions
    st.subheader("💡 How to Improve Your Match")
    for i, suggestion in enumerate(match_result.get("suggestions", []), start=1):
        st.markdown(f"**{i}.** {suggestion}")

    st.divider()

    # Raw data expander — useful for debugging (like inspecting raw pipeline output)
    with st.expander("🔍 View Raw Structured Resume Data (Debug)"):
        st.json(structured_resume)

    with st.expander("🔍 View Raw Match Analysis (Debug)"):
        st.json(match_result)
