#!/bin/bash

# Create .env file with OpenAI API key

cat > .env << 'EOF'
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# Database
DATABASE_URL=sqlite:///./prompt_optimizer.db

# LLM Providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Default LLM Provider
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4-turbo-preview

# Evaluation Settings
EVALUATION_LLM_PROVIDER=openai
EVALUATION_MODEL=gpt-4-turbo-preview
EVALUATION_TEMPERATURE=0.0
EVALUATION_MAX_TOKENS=1000

# Self-Improvement Settings
MIN_IMPROVEMENT_THRESHOLD=0.05
MIN_ABSOLUTE_SCORE=0.7
REGRESSION_THRESHOLD=0.02
CRITICAL_CASE_PASS_RATE=0.95
FORMAT_PASS_RATE=0.98
MAX_CANDIDATES_PER_ITERATION=5

# Caching
ENABLE_CACHE=true
CACHE_TTL_SECONDS=3600

# Logging
LOG_LEVEL=INFO
EOF

echo "✅ .env file created with your OpenAI API key!"
echo ""
echo "To verify, run:"
echo "  python3 -c \"from config import settings; print('OpenAI Key:', 'Set' if settings.openai_api_key else 'Not set')\""

