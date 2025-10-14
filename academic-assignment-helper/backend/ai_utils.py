# backend/ai_utils.py
import os
import json
import time
import re
import requests
from dotenv import load_dotenv

load_dotenv()

FRIENDLI_API_KEY = os.getenv("FRIENDLI_API_KEY")
FRIENDLI_ENDPOINT_ID = os.getenv("FRIENDLI_ENDPOINT_ID")
FRIENDLI_API_URL = "https://api.friendli.ai/dedicated/v1/chat/completions"

if not FRIENDLI_API_KEY or not FRIENDLI_ENDPOINT_ID:
    print("[AI_UTILS] Missing Friendli API credentials — check your .env configuration!")


# ------------------------------------------------------------
#  RAG Summarization Function
# ------------------------------------------------------------
def analyze_assignment_text(prompt: str) -> dict:
    """
    Sends a full prompt (including RAG context) to Friendli.ai for summarization.
    The prompt is already constructed by routes_analysis.run_ai_analysis_rag().
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FRIENDLI_API_KEY}",
    }

    payload = {
        "model": FRIENDLI_ENDPOINT_ID,
        "messages": [
            {"role": "system", "content": "You are a helpful academic assistant."},
            {"role": "user", "content": prompt.strip()},
        ],
        "temperature": 0.3,
        "max_tokens": 800,
    }

    for attempt in range(3):
        try:
            res = requests.post(FRIENDLI_API_URL, headers=headers, json=payload, timeout=90)
            res.raise_for_status()
            data = res.json()

            # Extract text output
            output_text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            parsed = try_parse_json(output_text)
            if parsed:
                print(f"[AI_UTILS] ✅ Successfully parsed AI JSON response on attempt {attempt+1}")
                return parsed

            print(f"[AI_UTILS] Model returned unstructured text; returning as summary.")
            return {"summary": output_text}

        except Exception as e:
            print(f"[AI_UTILS] Retry {attempt+1}/3 due to Friendli API error: {e}")
            time.sleep(3)

    return {"error": "AI analysis failed after 3 retries"}


# ------------------------------------------------------------
#  JSON Parser for AI Outputs
# ------------------------------------------------------------
def try_parse_json(raw_text: str):
    """Attempts to clean and parse AI JSON output with recovery strategies."""
    if not raw_text:
        return None

    # Trying normal parse
    try:
        return json.loads(raw_text)
    except Exception:
        pass

    # Trying to extract JSON block inside text
    match = re.search(r"\{[\s\S]*\}", raw_text)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Attempting common fixes
    repaired = (
        raw_text.replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("`", '"')
        .replace("\n", " ")
        .replace("\r", " ")
    )

    try:
        return json.loads(repaired)
    except Exception:
        return None
    