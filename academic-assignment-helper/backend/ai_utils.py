# backend/ai_utils.py
import os, json, time, re, requests
from dotenv import load_dotenv

load_dotenv()

FRIENDLI_API_KEY = os.getenv("FRIENDLI_API_KEY")   
FRIENDLI_ENDPOINT_ID = os.getenv("FRIENDLI_ENDPOINT_ID")   
FRIENDLI_API_URL = "https://api.friendli.ai/dedicated/v1/chat/completions"

if not FRIENDLI_API_KEY or not FRIENDLI_ENDPOINT_ID:
    print("[AI_UTILS]  Missing Friendli API credentials — check .env!")


def analyze_assignment_text(text: str) -> dict:
    """
    Uses Friendli Dedicated Endpoint API to perform academic text analysis.
    """
    prompt = f"""
You are an academic AI assistant. Analyze the following student assignment text
and output a structured JSON only (no explanation text, no markdown):

{text[:2500]}

Expected JSON schema:
{{
  "topic": "...",
  "academic_level": "...",
  "plagiarism_summary": "...",
  "key_insights": ["..."],
  "suggested_sources": ["Title 1", "Title 2"],
  "citation_recommendations": [
    {{"format": "APA", "examples": ["example1", "example2"]}}
  ]
}}
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FRIENDLI_API_KEY}",
    }

    payload = {
        "model": FRIENDLI_ENDPOINT_ID,
        "messages": [
            {
                "role": "user",
                "content": prompt.strip()
            }
        ]
    }

    for attempt in range(3):
        try:
            res = requests.post(FRIENDLI_API_URL, headers=headers, json=payload, timeout=90)
            res.raise_for_status()
            data = res.json()

            # Extract text response safely
            output_text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            parsed = try_parse_json(output_text)
            if parsed:
                return parsed
            raise ValueError("Model returned invalid JSON")

        except Exception as e:
            print(f"[AI_UTILS] Retry {attempt+1}/3 due to error: {e}")
            time.sleep(3)

    return {"error": "AI analysis failed after retries"}


def try_parse_json(raw_text: str):
    """Attempts to clean and parse JSON output."""
    if not raw_text:
        return None

    # Try direct parse
    try:
        return json.loads(raw_text)
    except Exception:
        pass

    # Try extracting JSON block
    match = re.search(r"\{[\s\S]*\}", raw_text)
    if match:
        json_candidate = match.group(0)
        try:
            return json.loads(json_candidate)
        except Exception:
            pass

    # Repair quotes and common artifacts
    repaired = (
        raw_text.replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("\n", "")
        .replace("\r", "")
    )
    try:
        return json.loads(repaired)
    except Exception:
        return None
