#!/bin/bash

echo "🚀 Starting SME Bridge MVP Development Environment..."

# 1. Setup environment variables if missing
if [ ! -f apps/api/.env ]; then
    echo "Creating apps/api/.env from example..."
    cp apps/api/.env.example apps/api/.env
fi

if [ ! -f apps/web/.env ]; then
    echo "Creating apps/web/.env from example..."
    cp apps/web/.env.example apps/web/.env
fi

# 2. Cleanup function to stop background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down all SME Bridge MVP services..."
    # Kill all child processes associated with this script
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Trap Ctrl+C (SIGINT) and termination signals to run cleanup
trap cleanup SIGINT SIGTERM EXIT

# 3. Setup and start Backend (FastAPI)
echo "-----------------------------------------"
echo "⚙️  Checking Backend (FastAPI)..."
cd apps/api
if [ ! -d ".venv" ]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-dev.txt
else
    source .venv/bin/activate
fi

echo "Starting FastAPI Server on Port 8000..."
uvicorn app.main:app --reload &
cd ../..

# 4. Start Background Worker
echo "-----------------------------------------"
echo "👷 Starting Background Worker..."
cd apps/api
source .venv/bin/activate
python -m app.processing.worker &
cd ../..

# 5. Setup and start Frontend (React)
echo "-----------------------------------------"
echo "🎨 Checking Frontend (React)..."
cd apps/web
if [ ! -d "node_modules" ]; then
    echo "Installing NPM dependencies..."
    npm install
fi

echo "Starting React Dashboard (Vite)..."
npm run dev &
cd ../..

echo "========================================="
echo "✅ SME Bridge MVP is running!"
echo "   Dashboard: http://localhost:5173"
echo "   API Docs:  http://localhost:8000/docs"
echo "   (Make sure Ollama and Supabase are active)"
echo ""
echo "Press Ctrl+C to stop all services."
echo "========================================="

# Keep script running to maintain background processes
wait
