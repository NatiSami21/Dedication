# test_vector_search.py
"""
Lightweight verification script for Academic AI Vector Search

Connects to running backend Postgres (via SQLAlchemy)
Checks embedding dimension consistency
Tests and Perform pgvector similarity search directly
Confirms database connectivity
Pretty-print top matches with their cosine similarity 
"""

"""
Docker-native test for semantic similarity search using pgvector.
Run inside backend container / or when all images are running:
    docker exec -it academic_fastapi bash
    python test_vector_search.py
"""
# test_vector_search.py

import os
import psycopg2
import numpy as np
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# Load DB credentials from Docker .env
DB_NAME = os.getenv("POSTGRES_DB", "academic_helper")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "0904161978")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")  # ✅ Docker service hostname
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
EMBED_MODEL = os.getenv("HUGGINGFACE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

client = InferenceClient(api_key=HF_API_KEY)

# -----------------------
# DB Connection
# -----------------------
def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

# -----------------------
# Generate Query Embedding
# -----------------------
def get_query_embedding(query: str):
    print("[EMBEDDING] Generating embedding for query...")
    embedding = client.feature_extraction(query, model=EMBED_MODEL)
    if isinstance(embedding, list) and isinstance(embedding[0], list):
        return embedding[0]
    return embedding

# -----------------------
# Perform Vector Search
# -----------------------
def search_similar_sources(query: str, top_k=3):
    conn = get_connection()
    cur = conn.cursor()

    embedding = get_query_embedding(query)

    print(f"\n[SEARCH] Top {top_k} similar sources for:\n   → {query}\n")

    sql = """
        SELECT 
            id, 
            title, 
            abstract, 
            1 - (embedding <=> %s::vector) AS similarity
        FROM academic_sources
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """

    # Convert list to pgvector-compatible format
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

    cur.execute(sql, (embedding_str, embedding_str, top_k))
    rows = cur.fetchall()

    if not rows:
        print(" No similar sources found.")
    else:
        for r in rows:
            print(f"📘 ID: {r[0]} | Similarity: {r[3]:.4f}\n    Title: {r[1]}\n")

    cur.close()
    conn.close()
 

# -----------------------------------------------------
# Now let's ሮጥ ሮጥ it
# -----------------------------------------------------
if __name__ == "__main__":
    print("[INIT] Database connection + Hugging Face client initialized successfully.\n")

    test_query = "The impact of artificial intelligence on healthcare regulation"
    #test_query = "I love U"
    #test_query = "Machine learning applications in medical diagnostics"  
    print(f"Query: {test_query}")

    search_similar_sources(test_query, top_k=3)
