#!/bin/bash

# System Status Check Script

echo "🔍 Checking System Status..."
echo ""

cd "/Users/hamzakhan/Self-Improving Prompt Optimization API"

# Check Backend
echo "📦 Backend Server:"
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "   ✓ Running on port 8000"
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "   ✓ Health check: OK"
        # Test prompts endpoint
        if curl -s http://localhost:8000/prompts/ >/dev/null 2>&1; then
            echo "   ✓ API endpoint: Working"
        else
            echo "   ⚠️  API endpoint: Error (may need restart)"
        fi
    else
        echo "   ⚠️  Health check: Failed"
    fi
else
    echo "   ✗ Not running"
    echo "   → Start with: python3 main.py"
fi

echo ""

# Check Frontend
echo "🎨 Frontend Server:"
if lsof -ti:3000 >/dev/null 2>&1; then
    echo "   ✓ Running on port 3000"
    if curl -s http://localhost:3000/ >/dev/null 2>&1; then
        echo "   ✓ Serving files: OK"
    else
        echo "   ⚠️  Serving files: Failed"
    fi
else
    echo "   ✗ Not running"
    echo "   → Start with: cd frontend && python3 -m http.server 3000"
fi

echo ""

# Check Database
echo "💾 Database:"
if [ -f "prompt_optimizer.db" ]; then
    echo "   ✓ Database file exists"
    python3 test_db.py 2>&1 | grep -E "(✓|✗|✅|Error)" | head -5
else
    echo "   ⚠️  Database file not found (will be created on first run)"
fi

echo ""

# Check API Keys
echo "🔑 API Keys:"
if [ -f ".env" ]; then
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        echo "   ✓ OpenAI API key configured"
    else
        echo "   ✗ OpenAI API key not configured"
    fi
else
    echo "   ✗ .env file not found"
fi

echo ""
echo "📍 Access Points:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"


