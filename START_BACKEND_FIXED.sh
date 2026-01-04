#!/bin/bash

# Start Backend Server - Fixed Version

cd "/Users/hamzakhan/Self-Improving Prompt Optimization API"

echo "🔧 Starting Backend Server..."
echo ""

# Kill any existing processes
echo "🧹 Cleaning up..."
pkill -f "python3 main.py" 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 2

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "   Please create .env file with your API keys."
    exit 1
fi

# Verify API key
echo "🔑 Checking API key..."
python3 -c "from config import settings; exit(0 if settings.openai_api_key and 'your_' not in settings.openai_api_key else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  OpenAI API key not configured properly!"
    echo "   Check your .env file"
    exit 1
fi
echo "   ✓ API key configured"

# Start backend
echo ""
echo "🚀 Starting backend on http://0.0.0.0:8000..."
python3 main.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "   Waiting for server to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend is running!"
    echo ""
    echo "📍 Access points:"
    echo "   Backend API:  http://localhost:8000"
    echo "   API Docs:     http://localhost:8000/docs"
    echo "   Health:       http://localhost:8000/health"
    echo ""
    echo "📋 Check logs:"
    echo "   tail -f /tmp/backend.log"
    echo ""
    echo "🛑 To stop:"
    echo "   pkill -f 'python3 main.py'"
else
    echo "   ⚠️  Backend may not have started properly"
    echo "   Check logs: tail -f /tmp/backend.log"
    exit 1
fi

