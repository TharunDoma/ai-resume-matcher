"""
Step 6: Database Layer
-----------------------
Purpose: Save every match result to a SQLite database for history and analytics.

DE Analogy: This is the true "L" in ETL — Load.
Up until now we were just displaying results on screen. But in real pipelines,
processed data must be LOADED into a persistent storage layer — a data warehouse,
a database, or a data lake. This is what makes it a pipeline vs. just a script.

SQLite is a lightweight file-based database built into Python. Think of it as
a simplified version of PostgreSQL or BigQuery. The SQL you write here is
identical to what you'd write against any enterprise database.

Schema design:
  match_results table — one row per resume analysis
  This is like a fact table in a data warehouse (kimball-style)
"""

import sqlite3
import json
from datetime import datetime

# Database file path — in production this would be a connection string
# e.g. postgresql://user:pass@host:5432/dbname
DB_PATH = "resume_matcher.db"


def get_connection() -> sqlite3.Connection:
    """
    Open and return a database connection.

    DE Analogy: In production pipelines, you manage connection pools
    (using tools like SQLAlchemy) so multiple pipeline workers can
    query the database simultaneously without overloading it.
    Here, we keep it simple with a single connection per call.
    """
    return sqlite3.connect(DB_PATH)


def initialize_database() -> None:
    """
    Create the match_results table if it doesn't already exist.

    DE Analogy: This is schema initialization — the first thing any
    pipeline does before loading data is ensure the target table exists
    with the correct structure. In production, this is handled by
    migration tools like Alembic or dbt.

    The IF NOT EXISTS clause makes this idempotent — safe to run
    multiple times without breaking anything. Idempotency is a core
    principle in data engineering.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            analyzed_at     TEXT    NOT NULL,
            candidate_name  TEXT,
            candidate_email TEXT,
            match_score     INTEGER,
            verdict         TEXT,
            matched_skills  TEXT,   -- stored as JSON array string
            missing_skills  TEXT,   -- stored as JSON array string
            summary         TEXT,
            resume_data     TEXT,   -- full structured resume as JSON
            match_data      TEXT    -- full match result as JSON
        )
    """)

    conn.commit()
    conn.close()


def save_match_result(structured_resume: dict, match_result: dict) -> int:
    """
    Insert one match result row into the database.

    Args:
        structured_resume: The dict from gemini_analyzer.analyze_resume()
        match_result:      The dict from job_matcher.match_resume_to_job()

    Returns:
        The ID of the newly inserted row.

    DE Analogy: This is the INSERT operation — loading one processed
    record into your data store. In batch pipelines, you'd use
    executemany() or COPY commands to load thousands of rows at once.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO match_results (
            analyzed_at,
            candidate_name,
            candidate_email,
            match_score,
            verdict,
            matched_skills,
            missing_skills,
            summary,
            resume_data,
            match_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        structured_resume.get("name"),
        structured_resume.get("email"),
        match_result.get("match_score"),
        match_result.get("verdict"),
        json.dumps(match_result.get("matched_skills", [])),
        json.dumps(match_result.get("missing_skills", [])),
        match_result.get("summary"),
        json.dumps(structured_resume),
        json.dumps(match_result),
    ))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return new_id


def fetch_all_results() -> list[dict]:
    """
    Retrieve all match results from the database, newest first.

    Returns:
        A list of dicts, one per match result row.

    DE Analogy: This is a SELECT query — reading from your data store
    to power a dashboard or report. In a real warehouse, this query
    might run against millions of rows with indexes for performance.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            analyzed_at,
            candidate_name,
            candidate_email,
            match_score,
            verdict,
            matched_skills,
            missing_skills,
            summary
        FROM match_results
        ORDER BY analyzed_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    # Convert raw tuples into readable dicts — like mapping column names
    columns = [
        "id", "analyzed_at", "candidate_name", "candidate_email",
        "match_score", "verdict", "matched_skills", "missing_skills", "summary"
    ]

    results = []
    for row in rows:
        record = dict(zip(columns, row))
        # Parse JSON strings back into lists
        record["matched_skills"] = json.loads(record["matched_skills"] or "[]")
        record["missing_skills"] = json.loads(record["missing_skills"] or "[]")
        results.append(record)

    return results


def fetch_summary_stats() -> dict:
    """
    Return aggregate statistics across all analyses.

    DE Analogy: This is an aggregation query — the foundation of any
    analytics dashboard. In a data warehouse, these would be pre-computed
    as materialized views for performance.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*)                    AS total_analyses,
            ROUND(AVG(match_score), 1)  AS avg_score,
            MAX(match_score)            AS highest_score,
            MIN(match_score)            AS lowest_score
        FROM match_results
    """)

    row = cursor.fetchone()
    conn.close()

    return {
        "total_analyses": row[0],
        "avg_score":      row[1] or 0,
        "highest_score":  row[2] or 0,
        "lowest_score":   row[3] or 0,
    }
