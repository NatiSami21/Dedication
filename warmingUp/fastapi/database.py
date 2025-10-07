from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_url = "postgresql://postgres:0904161978@localhost:5432/fastapi"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autoflush=False, bind=engine)