#!/bin/sh

set -e

echo "Waiting for PostgreSQL to start..."
 
echo "Postgres is up. Creating tables..."

# Run database initialization
python -c "from database import Base, engine; import models; Base.metadata.create_all(bind=engine)"

echo "Database tables created. Starting FastAPI server..."

exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
