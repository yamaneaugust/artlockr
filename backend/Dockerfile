# ArtLock Sync Backend (cache-bust: v3)
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY sync_server.py ./

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uvicorn sync_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
