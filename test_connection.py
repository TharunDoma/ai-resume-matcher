"""
Step 1: Gemini API Connection Smoke Test
-----------------------------------------
Purpose: Verify that our credentials load correctly and that we can
successfully reach the Gemini 2.5 Flash endpoint.

DE Analogy: In a real data pipeline, the FIRST thing you build is a
"connection health check" — before any ETL logic. If you can't reach the
source system, nothing downstream matters. This is that check.
"""

import os
import sys
from dotenv import load_dotenv
from google import genai


def load_api_key() -> str:
    """
    Load the Gemini API key from the .env file into the process environment,
    then return it. Fails loudly if the key is missing or still a placeholder.

    Why a dedicated function?  Modularity — in production, this same pattern
    (load -> validate -> return) becomes a reusable `get_secret()` helper
    that can swap in AWS Secrets Manager later without touching callers.
    """
    load_dotenv()  # reads .env -> populates os.environ
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "PASTE_YOUR_REAL_KEY_HERE":
        print("ERROR: GEMINI_API_KEY is missing or still the placeholder.")
        print("Open the .env file and paste your real key.")
        sys.exit(1)

    return api_key


def test_gemini_connection(api_key: str) -> None:
    """
    Make a single, minimal API call to confirm connectivity.

    DE Analogy: This is equivalent to running `SELECT 1` against a database —
    the smallest possible query that proves the connection works.
    """
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply with exactly one word: SUCCESS",
    )

    print("Gemini replied:", response.text.strip())


if __name__ == "__main__":
    key = load_api_key()
    test_gemini_connection(key)
