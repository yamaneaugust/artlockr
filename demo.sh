#!/bin/bash
# Quick demo start - minimal dependencies, UI only

set -e

echo "============================================"
echo "ArtLock Quick Demo (UI Only)"
echo "============================================"
echo ""

# Install minimal backend dependencies
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing minimal backend dependencies..."
pip install -q fastapi uvicorn sqlalchemy pydantic pydantic-settings python-multipart aiofiles

cd ..

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent 2>&1 | grep -v "npm WARN" || true
fi
cd ..

echo ""
echo "Starting services..."
echo ""

# Start minimal backend
cd backend
source venv/bin/activate
python -c "
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='ArtLock Demo API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/health')
async def health():
    return {'status': 'healthy'}

@app.get('/api/v1/health')
async def api_health():
    return {'status': 'healthy', 'message': 'Demo mode - ML features disabled'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
" > demo_app.py

uvicorn demo_app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

sleep 2

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

sleep 5

echo ""
echo "============================================"
echo "✓ ArtLock Demo is running!"
echo "============================================"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo ""
echo "Note: This is UI demo only - ML features disabled"
echo "For full version, run: ./start.sh"
echo ""
echo "Press Ctrl+C to stop"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
