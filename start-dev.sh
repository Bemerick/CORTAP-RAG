#!/bin/bash

# CORTAP-RAG Local Development Startup Script
# This script starts both the backend and frontend servers

echo "🚀 Starting CORTAP-RAG Development Environment..."
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Backend directory not found: $BACKEND_DIR"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to catch Ctrl+C and call cleanup
trap cleanup INT TERM

# Start Backend
echo "📦 Starting Backend (FastAPI)..."
cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "   ✓ Virtual environment activated"
else
    echo "   ⚠️  Virtual environment not found, using system Python"
fi

# Start backend server in background
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /tmp/cortap-backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✓ Backend started (PID: $BACKEND_PID)"
echo "   📍 Backend URL: http://localhost:8000"
echo "   📚 API Docs: http://localhost:8000/docs"
echo ""

# Wait a moment for backend to start
sleep 2

# Start Frontend
echo "🎨 Starting Frontend (React + Vite)..."
cd "$FRONTEND_DIR"

# Start frontend server in background
npm run dev > /tmp/cortap-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✓ Frontend started (PID: $FRONTEND_PID)"
echo ""

# Wait for frontend to start
sleep 3

echo "✅ Development environment is ready!"
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Logs:"
echo "   Backend:  tail -f /tmp/cortap-backend.log"
echo "   Frontend: tail -f /tmp/cortap-frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
