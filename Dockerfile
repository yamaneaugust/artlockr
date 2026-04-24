FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY ml_models/ ./ml_models/
COPY scripts/ ./scripts/
COPY .env.example .env

# Create data directories
RUN mkdir -p data/uploads data/ai_generated data/features

# Expose port
EXPOSE 8000

# Run the sync server (simple, reliable backend)
WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn sync_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
