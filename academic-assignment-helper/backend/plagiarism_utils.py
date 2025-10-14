
# backend/plagiarism_utils.py

# ------------------------------------------------------------
# Splits text into ~250-token chunks
# Embeds each chunk
# Searches the vector DB for top-k similar sources
# Flags anything with similarity ≥ 0.8
# Computes an overall plagiarism score
# ------------------------------------------------------------

import os
import re
import time
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()


# ------------------------------------------------------------
# Loading . . .
# ------------------------------------------------------------


HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
EMBED_MODEL = os.getenv("HUGGINGFACE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

client = InferenceClient(api_key=HF_API_KEY)


# ------------------------------------------------------------
# ማን! This part handles text chunking (~250 tokens)
# ------------------------------------------------------------
def chunk_text(text: str, max_tokens: int = 250):
    """
    Split text into ~250-token chunks based on sentence boundaries.
    Keeps coherence by splitting on sentence endings.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current_chunk = [], []
    token_count = 0

    for sentence in sentences:
        tokens = sentence.split()
        if token_count + len(tokens) > max_tokens and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk, token_count = [], 0
        current_chunk.extend(tokens)
        token_count += len(tokens)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

 
# ------------------------------------------------------------
# Then as I have done for the source similarly Here will be Generating Embedding for Chunk
# ------------------------------------------------------------


def get_embedding(text: str, retries=3):
    """
    Generate embedding for a given text chunk using Hugging Face Inference API.
    Returns a 384-dimensional vector as a Python list.
    """
    for attempt in range(retries):
        try:
            result = client.feature_extraction(text[:1000], model=EMBED_MODEL)

            if isinstance(result, list) and isinstance(result[0], list):
                return result[0]
            elif isinstance(result, np.ndarray):
                return result.tolist()
            return result

        except Exception as e:
            print(f"[PLAGIARISM_UTILS] Retry {attempt+1}/{retries} due to {e}")
            time.sleep(2)

    raise RuntimeError("Failed to embed chunk after retries")

# ------------------------------------------------------------
# The next flow is  Detecting Plagiarism
# ------------------------------------------------------------

def detect_plagiarism(db: Session, assignment_text: str, top_k: int = 3, similarity_threshold: float = 0.6):
    """
    Compare assignment chunks against academic_sources using cosine similarity.
    Flags chunks that have ≥ similarity_threshold with any stored source.
    """
    chunks = chunk_text(assignment_text)
    flagged_sections = []

    print(f"[PLAGIARISM_UTILS] Processing {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk)
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"

            # SQL for vector similarity using pgvector
            sql = text("""
                SELECT 
                    id, 
                    title, 
                    abstract, 
                    1 - (embedding <=> CAST(:embedding1 AS vector)) AS similarity
                FROM academic_sources
                ORDER BY embedding <=> CAST(:embedding2 AS vector)
                LIMIT :top_k;
            """)

            rows = db.execute(
                sql,
                {"embedding1": embedding_str, "embedding2": embedding_str, "top_k": top_k}
            ).fetchall()

            # Inspect top-k matches for this chunk
            print(f"\n[CHUNK {i+1}] Preview: {chunk[:100]}...")
            for r in rows:
                print(f"   # {r.title} → similarity {round(r.similarity, 3)}")

            # Flagging logic
            for r in rows:
                if r.similarity >= similarity_threshold:
                    flagged_sections.append({
                        "chunk_id": i + 1,
                        "similarity": round(r.similarity, 4),
                        "source_id": r.id,
                        "source_title": r.title,
                        "excerpt": chunk[:200] + "..."
                    })

        except Exception as e:
            print(f"[PLAGIARISM_UTILS] Failed at chunk {i+1}: {e}")

    plagiarism_score = compute_plagiarism_score(flagged_sections)

    print(f"\n --- PLAGIARISM DETECTION SUMMARY ---")
    print(f"Chunks flagged: {len(flagged_sections)} / {len(chunks)}")
    print(f"Overall Score: {plagiarism_score}%")

    return {
        "plagiarism_score": plagiarism_score,
        "flagged_sections": flagged_sections
    }



# ------------------------------------------------------------
# Bemecheresham let's Compute Plagiarism Score
# ------------------------------------------------------------

def compute_plagiarism_score(flagged_sections):
    """
    Compute overall plagiarism score as mean(similarity × 100)
    Only flagged chunks contribute to the score.
    """
    if not flagged_sections:
        return 0.0
    sims = [fs["similarity"] for fs in flagged_sections]
    return round(float(np.mean(sims) * 100), 2)
