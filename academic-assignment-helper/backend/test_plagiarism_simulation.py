# test_plagiarism_simulation.py

# ------------------------------------------------------------
# This script tests the full plagiarism detection flow inside Docker
# It uses the database in the container and calls plagiarism_utils.detect_plagiarism
#CMD: docker exec -it academic_fastapi bash
#       -root@d6ca806e8046:/app# python test_plagiarism_simulation.py;
# ------------------------------------------------------------

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from plagiarism_utils import detect_plagiarism

load_dotenv()
# Load DB credentials from Docker .env
DB_NAME = os.getenv("POSTGRES_DB", "academic_helper")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "0904161978")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")  # Docker service name
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ------------------------------------------------------------
# Test Assignment Texts (Simulating Student Submissions)
# ------------------------------------------------------------
test_assignments = [
    {
        "id": 1,
        "title": "AI in Healthcare",
        "text": """
        Artificial Intelligence is transforming healthcare systems worldwide.
        It helps doctors predict diseases and automate diagnostics.
        However, ethical regulation remains a major concern.
        """
    },
    {
        "id": 2,
        "title": "AI Diagnostics and Data Protection",
        "text": """
        Explores diagnostic AI and patient data protection in modern hospitals.
        Examines ethical dilemmas and privacy risks.
        """
    },
    {
        "id": 3,
        "title": "Random Text",
        "text": """
        Penguins live in cold climates and form large colonies.
        They are birds that cannot fly but are excellent swimmers.
        """
    }
]

# ------------------------------------------------------------
# Run Plagiarism Detection for each test case
# ------------------------------------------------------------
if __name__ == "__main__":
    print("[TEST] Running full plagiarism detection demo inside Docker...\n")

    db = SessionLocal()

    for t in test_assignments:
        print(f"Testing Assignment: {t['title']}\n{'-' * 60}")
        result = detect_plagiarism(db, t["text"], top_k=3, similarity_threshold=0.6)

        print(f"\n --- RESULT FOR: {t['title']} ---")
        print(f"Plagiarism Score: {result['plagiarism_score']}%\n")

        if not result["flagged_sections"]:
            print(" No flagged sections found.\n")
        else:
            for f in result["flagged_sections"]:
                print(f"  Chunk {f['chunk_id']} | Similarity: {f['similarity']} | Source: {f['source_title']}")
                print(f"   Excerpt: {f['excerpt'][:120]}...\n")

        print("=" * 70 + "\n")

    db.close()
    print(" All tests completed successfully.")
