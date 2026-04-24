# ArtLock Sync Backend (cache-bust: v5)
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY sync_server.py ./

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "sync_server:app", "--host", "0.0.0.0", "--port", "8000"]
