import os
import json
from sqlalchemy.orm import Session
from sqlalchemy import exc # Import for handling potential database errors
import models
from database import SessionLocal
from sqlalchemy import text

def load_sample_sources():
    """
    On startup, checks academic_sources table.
    - If empty, loads all sample data from JSON.
    - If not empty, loads only new sources by identifying based on 'title'.
    """
    db: Session = SessionLocal()
    
    #1. Load JSON Data 
    json_path = os.path.join(os.path.dirname(__file__), "data/sample_academic_sources.json")
    if not os.path.exists(json_path):
        print(f"[STARTUP] sample_academic_sources.json not found at path: {json_path} — skipping.")
        db.close()
        return

    with open(json_path, "r", encoding="utf-8") as f:
        json_sources = json.load(f)

    try:
        # 2. Check Database State 
        db_count = db.query(models.AcademicSource).count()

        if db_count == 0:
            # Case A: Table is EMPTY: Load everything
            print("[STARTUP] Database table is empty. Loading ALL sample sources.")
            sources_to_add = json_sources
            
        else:
            # Case B: Table is NOT EMPTY: Identify and load only new ones
            print(f"[STARTUP] {db_count} academic sources found. Checking for NEW sources.")
            
            # Get titles for lookups
            existing_titles_query = db.query(models.AcademicSource.title).all()
            existing_titles = {row[0] for row in existing_titles_query}
            
            sources_to_add = []
            for src in json_sources:
                if src.get("title") and src["title"] not in existing_titles:
                    sources_to_add.append(src)
                
            if not sources_to_add:
                print("[STARTUP] No new academic sources found in JSON. Skipping.")
                return 
                
        # 3. Insert Data
        num_added = 0
        for src_data in sources_to_add:
            try:
                # Use raw SQL to insert without the embedding column
                stmt = text("""
                    INSERT INTO academic_sources (title, authors, publication_year, abstract, full_text, source_type)
                    VALUES (:title, :authors, :publication_year, :abstract, :full_text, :source_type)
                """)
                db.execute(stmt, {
                    'title': src_data.get('title'),
                    'authors': src_data.get('authors'),
                    'publication_year': src_data.get('publication_year'),
                    'abstract': src_data.get('abstract'),
                    'full_text': src_data.get('full_text'),
                    'source_type': src_data.get('source_type')
                })
                num_added += 1
            except Exception as e:
                print(f"[STARTUP ERROR] Skipping source: {src_data.get('title', 'Untitled')}. Error: {e}")
                
        db.commit()
        print(f"[STARTUP] Successfully added {num_added} NEW academic sources into the database.")

    except Exception as e:
        db.rollback()
        print(f"[STARTUP] Failed to load sample sources: {e}")
    finally:
        db.close()