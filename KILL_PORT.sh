#!/bin/bash

# Kill process using port 8000

echo "🔍 Finding process on port 8000..."

PID=$(lsof -ti:8000 2>/dev/null)

if [ -z "$PID" ]; then
    echo "✓ Port 8000 is free"
    exit 0
fi

echo "Found process: $PID"
echo "Killing process..."
kill -9 $PID 2>/dev/null
sleep 1

# Verify
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "⚠️  Process still running, trying pkill..."
    pkill -f "python3 main.py"
    pkill -f "uvicorn"
    sleep 1
fi

if lsof -ti:8000 >/dev/null 2>&1; then
    echo "✗ Could not free port 8000"
    exit 1
else
    echo "✓ Port 8000 is now free"
    echo ""
    echo "You can now start the backend:"
    echo "  python3 main.py"
fi


