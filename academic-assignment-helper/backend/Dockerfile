# ======== Dockerfile ========
FROM python:3.11-slim

# Install system dependencies (for psycopg2 + netcat)
RUN apt-get update && apt-get install -y \
    netcat-openbsd gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (to leverage Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI backend source code
COPY . .

# Copy entrypoint script and set permissions
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose FastAPI port
EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
