#!/bin/bash

# Push to GitHub script - Run this to push all changes

cd "/Users/hamzakhan/Self-Improving Prompt Optimization API"

echo "🔍 Checking git status..."
git status --short

echo ""
echo "📦 Staging all changes..."
git add -A

echo ""
echo "🔒 Verifying no secrets are staged..."
# Check for .env file
if git diff --cached --name-only | grep -q "\.env$"; then
    echo "⚠️  WARNING: .env file is staged! Removing it..."
    git reset HEAD .env
    echo "✓ .env removed from staging"
else
    echo "✓ .env is not staged (protected by .gitignore)"
fi

# Check for API keys in staged files
if git diff --cached | grep -qE "sk-proj-[A-Za-z0-9_-]+|sk-ant-[A-Za-z0-9_-]+"; then
    echo "⚠️  WARNING: API keys found in staged files!"
    echo "   Please remove API keys from scripts before pushing."
    exit 1
else
    echo "✓ No API keys found in staged files"
fi

echo ""
echo "📝 Committing changes..."
git commit -m "Fix database session issue and clean up unnecessary documentation files

- Fixed database session dependency injection in storage/database.py
- Removed return type annotation from get_db() for FastAPI compatibility
- Deleted 17 temporary status and troubleshooting MD files
- Kept essential documentation (README.md, API_KEYS_SETUP.md)"

echo ""
echo "🌐 Pushing to GitHub..."
BRANCH=$(git branch --show-current 2>/dev/null || git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")

echo "Branch: $BRANCH"
git push origin "$BRANCH"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
else
    echo ""
    echo "❌ Push failed. Check your git remote and branch name."
    echo "   Remote: $(git remote get-url origin 2>/dev/null || echo 'not set')"
    echo "   Branch: $BRANCH"
fi

