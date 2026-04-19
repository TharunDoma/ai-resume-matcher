"""
Step 5 (Updated): Streamlit UI with Database Layer
----------------------------------------------------
The "L" in ETL now does TWO things:
  1. Displays results to the user (original)
  2. Loads results into a SQLite database (new)

Two pages:
  - Analyzer:  Run the pipeline and save results
  - Dashboard: View history and analytics from the database
"""

import streamlit as st
import json
import tempfile
import os

from pdf_extractor import extract_text_from_pdf
from gemini_analyzer import analyze_resume
from job_matcher import match_resume_to_job
from database import initialize_database, save_match_result, fetch_all_results, fetch_summary_stats

# Initialize DB on every app start — idempotent, safe to run repeatedly
initialize_database()

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Matcher",
    page_icon="🎯",
    layout="wide",
)

# ── Navigation ────────────────────────────────────────────────────────────────
page = st.sidebar.radio(
    "Navigation",
    ["🎯 Analyzer", "📊 Dashboard"],
    index=0
)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — ANALYZER
# ══════════════════════════════════════════════════════════════════════════════
if page == "🎯 Analyzer":

    st.title("🎯 AI Resume Matcher")
    st.markdown("Upload your resume and paste a job description to get an AI-powered match analysis.")
    st.divider()

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

    analyze_btn = st.button("🚀 Analyze Match", type="primary", use_container_width=True)

    if analyze_btn:
        if not uploaded_file:
            st.error("⚠️ Please upload a resume PDF first.")
            st.stop()
        if not job_description.strip():
            st.error("⚠️ Please paste a job description.")
            st.stop()

        with st.spinner("Running your resume through the AI pipeline..."):

            # --- EXTRACT ---
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                raw_text = extract_text_from_pdf(tmp_path)
            except ValueError as e:
                st.error(f"❌ PDF Error: {e}")
                st.stop()
            finally:
                os.unlink(tmp_path)

            # --- TRANSFORM ---
            try:
                structured_resume = analyze_resume(raw_text)
            except Exception as e:
                st.error(f"❌ Resume analysis failed: {e}")
                st.stop()

            # --- MATCH ---
            try:
                match_result = match_resume_to_job(structured_resume, job_description)
            except Exception as e:
                st.error(f"❌ Matching failed: {e}")
                st.stop()

            # --- LOAD INTO DATABASE --- ← new
            try:
                record_id = save_match_result(structured_resume, match_result)
                st.success(f"✅ Analysis complete! Saved to database (Record #{record_id})")
            except Exception as e:
                st.warning(f"⚠️ Analysis done but couldn't save to database: {e}")

        st.divider()

        # ── Results ───────────────────────────────────────────────────────────
        score   = match_result.get("match_score", 0)
        verdict = match_result.get("verdict", "Unknown")

        st.subheader("📊 Match Results")
        score_col, verdict_col = st.columns([1, 2])

        with score_col:
            if score >= 80:
                st.metric(label="Match Score", value=f"{score}/100", delta="Strong Match ✅")
            elif score >= 60:
                st.metric(label="Match Score", value=f"{score}/100", delta="Good Match 🟡")
            else:
                st.metric(label="Match Score", value=f"{score}/100", delta="Needs Work 🔴")

        with verdict_col:
            st.info(f"**Verdict:** {verdict}\n\n{match_result.get('summary', '')}")

        st.divider()

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

        st.subheader("💡 How to Improve Your Match")
        for i, suggestion in enumerate(match_result.get("suggestions", []), start=1):
            st.markdown(f"**{i}.** {suggestion}")

        st.divider()

        with st.expander("🔍 View Raw Structured Resume Data (Debug)"):
            st.json(structured_resume)

        with st.expander("🔍 View Raw Match Analysis (Debug)"):
            st.json(match_result)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":

    st.title("📊 Analysis Dashboard")
    st.markdown("Historical view of all resume analyses run through the pipeline.")
    st.divider()

    # --- Summary Stats (Aggregation query) ---
    stats = fetch_summary_stats()

    if stats["total_analyses"] == 0:
        st.info("No analyses yet. Go to the Analyzer page to run your first match!")
        st.stop()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Analyses", stats["total_analyses"])
    col2.metric("Average Score",  f"{stats['avg_score']}/100")
    col3.metric("Highest Score",  f"{stats['highest_score']}/100")
    col4.metric("Lowest Score",   f"{stats['lowest_score']}/100")

    st.divider()

    # --- History Table (SELECT query) ---
    st.subheader("📋 Analysis History")
    results = fetch_all_results()

    for record in results:
        with st.expander(
            f"#{record['id']} — {record['candidate_name'] or 'Unknown'} "
            f"| Score: {record['match_score']}/100 "
            f"| {record['verdict']} "
            f"| {record['analyzed_at']}"
        ):
            st.markdown(f"**Email:** {record['candidate_email'] or 'N/A'}")
            st.markdown(f"**Summary:** {record['summary']}")

            sk1, sk2 = st.columns(2)
            with sk1:
                st.markdown("**Matched Skills:**")
                for s in record["matched_skills"]:
                    st.success(f"✓ {s}")
            with sk2:
                st.markdown("**Missing Skills:**")
                for s in record["missing_skills"]:
                    st.error(f"✗ {s}")
