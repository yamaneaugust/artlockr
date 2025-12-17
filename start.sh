#!/bin/bash
# Quick start script for ArtLockr (without Docker)

set -e

echo "============================================"
echo "ArtLockr Quick Start"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo "-------------------------------------------"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# PostgreSQL is optional for now - we can use SQLite for testing
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠ PostgreSQL not found - will use SQLite for testing${NC}"
    USE_SQLITE=true
else
    echo -e "${GREEN}✓ PostgreSQL found${NC}"
    USE_SQLITE=false
fi

echo ""

# Step 2: Install backend dependencies
echo "Step 2: Installing backend dependencies..."
echo "-------------------------------------------"
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
echo ""

# Step 3: Setup database
echo "Step 3: Setting up database..."
echo "-------------------------------------------"
cd ..

if [ "$USE_SQLITE" = true ]; then
    # Use SQLite for simplicity
    echo "Using SQLite database..."
    export DATABASE_URL="sqlite:///./artlockr.db"

    # Create tables
    cd backend
    python -c "
from sqlalchemy import create_engine
from app.models.database import Base
engine = create_engine('sqlite:///./artlockr.db')
Base.metadata.create_all(engine)
print('✓ Database tables created')
"
    cd ..
else
    # Use PostgreSQL
    echo "Setting up PostgreSQL database..."
    python scripts/init_database.py --seed-data 2>/dev/null || echo "Database already initialized"
fi
echo -e "${GREEN}✓ Database ready${NC}"
echo ""

# Step 4: Install frontend dependencies
echo "Step 4: Installing frontend dependencies..."
echo "-------------------------------------------"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages (this may take a minute)..."
    npm install --silent
fi
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
cd ..
echo ""

# Step 5: Start services
echo "Step 5: Starting services..."
echo "-------------------------------------------"
echo ""
echo -e "${GREEN}Starting backend on http://localhost:8000${NC}"
echo -e "${GREEN}Starting frontend on http://localhost:3000${NC}"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    if [ "$USE_SQLITE" = true ]; then
        sed -i 's|DATABASE_URL=.*|DATABASE_URL=sqlite:///./artlockr.db|' .env
    fi
fi

# Start backend in background
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend in background
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

echo ""
echo "============================================"
echo -e "${GREEN}✓ ArtLockr is running!${NC}"
echo "============================================"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Test credentials:"
echo "  Email:    artist1@example.com"
echo "  Password: password"
echo ""
echo "Logs:"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"
echo "         or press Ctrl+C"
echo ""

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

# Wait for user to press Ctrl+C
wait
