# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

#DB_USER = os.getenv("POSTGRES_USER")
#DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
#DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
#DB_PORT = os.getenv("POSTGRES_PORT", "5432")
#DB_NAME = os.getenv("POSTGRES_DB")


#SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:0904161978@postgres:5432/academic_helper"

# SQLAlchemy setup
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
