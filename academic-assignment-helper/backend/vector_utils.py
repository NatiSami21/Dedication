import os, time
import numpy as np
from huggingface_hub import InferenceClient
from sqlalchemy.orm import Session
import models
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
EMBED_MODEL = os.getenv("HUGGINGFACE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

client = InferenceClient(api_key=HF_API_KEY)

def get_embedding(text: str, retries=3):
    """
    Generate sentence embeddings using Hugging Face InferenceClient.
    Works on free-tier (no payment or card required).
    """
    if not HF_API_KEY:
        raise ValueError("❌ Missing HUGGINGFACE_API_KEY in .env")

    for attempt in range(retries):
        try:
            # Call Hugging Face free inference endpoint
            response = client.feature_extraction(text[:1000], model=EMBED_MODEL)

            # Handle nested formats (list[list[float]] or ndarray)
            if isinstance(response, np.ndarray):
                return response.tolist()
            elif isinstance(response, list) and len(response) > 0:
                if isinstance(response[0], list):
                    return response[0]
                return response

            raise ValueError(f"Unexpected embedding format: {type(response)}")

        except Exception as e:
            print(f"[VECTOR_UTILS] Retry {attempt+1}/{retries} due to {e}")
            time.sleep(2)

    raise RuntimeError("Failed to generate embedding after retries")


def embed_academic_sources(db: Session):
    """
    Generate and store embeddings for academic sources that have none.
    """
    sources = db.query(models.AcademicSource).filter(models.AcademicSource.embedding == None).all()
    print(f"[VECTOR_UTILS] Found {len(sources)} sources needing embeddings.")

    for src in sources:
        try:
            text = f"{src.title}. {src.abstract or ''}"
            embedding = get_embedding(text)

            # ✅ Convert numpy array → list for PostgreSQL
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()

            # Ensure it’s JSON serializable
            if not isinstance(embedding, list):
                raise TypeError(f"Embedding for {src.title} is not a list")

            src.embedding = embedding
            db.commit()
            print(f"[VECTOR_UTILS] ✅ Embedded: {src.title}")

        except Exception as e:
            db.rollback()
            print(f"[VECTOR_UTILS] ❌ Failed for {src.id}: {e}")
