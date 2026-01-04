#!/bin/bash

# Start Backend Server Script

echo "🚀 Starting Backend Server..."
echo ""

cd "/Users/hamzakhan/Self-Improving Prompt Optimization API"

# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is already in use."
    echo "   Stopping existing process..."
    pkill -f "python3 main.py"
    sleep 2
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "   Please create .env file with your API keys."
    echo "   See API_KEYS_SETUP.md for instructions."
    exit 1
fi

# Start backend
echo "📦 Starting backend on http://localhost:8000..."
echo ""
python3 main.py


