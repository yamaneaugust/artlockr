FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uvicorn sync_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
