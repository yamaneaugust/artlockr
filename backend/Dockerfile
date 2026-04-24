FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Railway injects PORT at runtime; fall back to 8000 locally
ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uvicorn sync_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
