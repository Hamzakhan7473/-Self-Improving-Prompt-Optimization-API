#!/bin/bash

# Install all dependencies for the project

echo "📦 Installing dependencies..."
echo ""

cd "/Users/hamzakhan/Self-Improving Prompt Optimization API"

# Install from requirements.txt
pip3 install -r requirements.txt

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "Verify installation:"
echo "  python3 -c \"from api import prompts; print('✓ All imports working')\""
echo ""
echo "Now you can start the backend:"
echo "  python3 main.py"


