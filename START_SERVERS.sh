#!/bin/bash

# Start Backend and Frontend Servers

cd "/Users/hamzakhan/Self-Improving Prompt Optimization API"

echo "🚀 Starting Self-Improving Prompt Optimization API..."
echo ""

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 1

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "   Please create .env file with your API keys."
    echo "   Run: ./SETUP_ENV.sh"
    exit 1
fi

# Start backend
echo "📦 Starting backend on http://localhost:8000..."
cd "/Users/hamzakhan/Self-Improving Prompt Optimization API"
python3 main.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ Backend is running!"
else
    echo "   ⚠️  Backend may not have started. Check logs: tail -f /tmp/backend.log"
fi

# Start frontend
echo ""
echo "🌐 Starting frontend on http://localhost:3000..."
cd "/Users/hamzakhan/Self-Improving Prompt Optimization API/frontend"
python3 -m http.server 3000 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 2

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Frontend is running!"
else
    echo "   ⚠️  Frontend may not have started. Check logs: tail -f /tmp/frontend.log"
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
echo "   tail -f /tmp/backend.log"
echo "   tail -f /tmp/frontend.log"
echo ""
echo "📖 Testing Guide: See TESTING_GUIDE.md"

