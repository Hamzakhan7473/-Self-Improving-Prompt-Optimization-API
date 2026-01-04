#!/bin/bash

# Start script for Self-Improving Prompt Optimization API

echo "🚀 Starting Self-Improving Prompt Optimization API..."
echo ""

# Check if ports are already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is already in use. Backend may already be running."
else
    echo "📦 Starting backend server on port 8000..."
    cd "$(dirname "$0")"
    python3 main.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   Backend started (PID: $BACKEND_PID)"
    echo "   Logs: backend.log"
fi

sleep 2

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 3000 is already in use. Frontend may already be running."
else
    echo "🎨 Starting frontend server on port 3000..."
    cd "$(dirname "$0")/frontend"
    python3 -m http.server 3000 > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   Frontend started (PID: $FRONTEND_PID)"
    echo "   Logs: frontend.log"
fi

echo ""
echo "✅ Servers starting..."
echo ""
echo "📍 Access points:"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Frontend:     http://localhost:3000"
echo ""
echo "🛑 To stop servers:"
echo "   pkill -f 'python3 main.py'"
echo "   pkill -f 'python3 -m http.server'"
echo ""
echo "📋 Check logs:"
echo "   tail -f backend.log"
echo "   tail -f frontend.log"


