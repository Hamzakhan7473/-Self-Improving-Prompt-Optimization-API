#!/bin/bash

# Fix version conflicts by installing exact versions from requirements.txt

echo "🔧 Fixing package versions..."
echo ""

cd "/Users/hamzakhan/Self-Improving Prompt Optimization API"

# Uninstall conflicting versions
echo "Uninstalling conflicting FastAPI version..."
pip3 uninstall -y fastapi starlette 2>/dev/null

# Install exact versions from requirements.txt
echo "Installing correct versions..."
pip3 install fastapi==0.104.1
pip3 install uvicorn[standard]==0.24.0
pip3 install pydantic==2.5.0
pip3 install pydantic-settings==2.1.0
pip3 install sqlalchemy==2.0.23
pip3 install alembic==1.12.1
pip3 install python-dotenv==1.0.0
pip3 install python-multipart==0.0.6
pip3 install aiofiles==23.2.1

echo ""
echo "✅ Versions fixed!"
echo ""
echo "Test import:"
echo "  python3 -c \"from fastapi import FastAPI; print('✓ FastAPI working')\""
echo ""
echo "Start backend:"
echo "  python3 main.py"


