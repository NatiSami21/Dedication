# backend/vector_utils.py

import os
import time
import numpy as np
from huggingface_hub import InferenceClient
from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import models

load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
EMBED_MODEL = os.getenv("HUGGINGFACE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

client = InferenceClient(api_key=HF_API_KEY)

# --------------------------------------------------------
# ማን! this part lay malet nw. . . Embedding Generate yadergal malet nw
# -------------------------------------------------------- 
def get_embedding(text: str, retries=3):
    """
    I'm trying to generate text embedding using Hugging Face InferenceClient (eza aza yehone sitachew lay nef interface ale shufew).
    Keza malet nw 384D vector malet nw python list return yaregal malet nw. ማን! 768D kefelek all-mpnet-base-v2 shof shof adrgat.
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
            print(f"[VECTOR_UTILS] Retry {attempt+1}/{retries} due to {e}")
            time.sleep(2)
    raise RuntimeError("Failed to generate embedding after retries")


# --------------------------------------------------------
# ማን! eziga bachru Academic Sources  Embed yadergal malet nw, ያው for the missing ones
# --------------------------------------------------------
def embed_academic_sources(db: Session):
    """
    Generate embeddings for academic sources missing one.
    """
    sources = db.query(models.AcademicSource).filter(models.AcademicSource.embedding == None).all()
    print(f"[VECTOR_UTILS] Found {len(sources)} sources needing embeddings.")

    for src in sources:
        try:
            text = f"{src.title}. {src.abstract or ''}"
            embedding = get_embedding(text)
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            src.embedding = embedding
            db.commit()
            print(f"[VECTOR_UTILS] Embedded: {src.title}")
        except Exception as e:
            db.rollback()
            print(f"[VECTOR_UTILS] Failed for {src.id}: {e}")


# --------------------------------------------------------
#  Fam echi demo shof sinaregat  Vector Index creation neger nat, similarity searchuwan mela yadergal malet nw
# --------------------------------------------------------
def index_academic_sources(db: Session):
    """
    Create pgvector index for similarity search if it doesn't exist.
    """
    try:
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS academic_sources_embedding_idx
            ON academic_sources
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))
        db.commit()
        print("[VECTOR_UTILS] Vector index created or already exists.")
    except Exception as e:
        db.rollback()
        print(f"[VECTOR_UTILS] Failed to create index: {e}")


# --------------------------------------------------------
#  wegen eziga Semantic Search le temesasay Sources tef tef yilal, 
# --------------------------------------------------------
def search_similar_sources(db: Session, query_text: str, top_k: int = 5):
    """
    Perform semantic similarity search using pgvector.
    """
    try:
        query_embedding = get_embedding(query_text)
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()

        # Use psycopg2 connection directly for proper vector handling
        connection = db.connection()
        cur = connection.cursor()
        
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        sql = """
            SELECT id, title, abstract,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM academic_sources
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """
        
        cur.execute(sql, (embedding_str, embedding_str, top_k))
        rows = cur.fetchall()
        
        return [
            {
                "id": r[0],
                "title": r[1],
                "abstract": r[2],
                "similarity": round(float(r[3]), 4),
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[VECTOR_UTILS] Search failed: {e}")
        return []