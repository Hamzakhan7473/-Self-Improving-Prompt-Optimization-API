# API Keys Setup Guide

## 🔑 Required API Keys

This project requires **at least one** LLM provider API key to function:

### Option 1: OpenAI (Recommended for most use cases)
- **Required for**: Generation, evaluation, self-improvement
- **Get your key**: https://platform.openai.com/api-keys
- **Cost**: Pay-per-use (check OpenAI pricing)
- **Models available**: GPT-4, GPT-3.5, etc.

### Option 2: Anthropic (Claude)
- **Required for**: Generation, evaluation, self-improvement  
- **Get your key**: https://console.anthropic.com/settings/keys
- **Cost**: Pay-per-use (check Anthropic pricing)
- **Models available**: Claude 3 Opus, Sonnet, Haiku

### Option 3: Both (Recommended for production)
- Use OpenAI for generation
- Use Anthropic for evaluation (better blinding)
- Provides redundancy and flexibility

## 📝 Setup Instructions

### 1. Get Your API Keys

**OpenAI:**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

**Anthropic:**
1. Go to https://console.anthropic.com/settings/keys
2. Sign in or create account
3. Click "Create Key"
4. Copy the key (starts with `sk-ant-...`)

### 2. Add Keys to .env File

Edit the `.env` file in the project root:

```bash
# Replace these placeholders with your actual keys
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
```

### 3. Verify Setup

```bash
# Test the configuration
python3 -c "from config import settings; print('OpenAI:', '✓' if settings.openai_api_key and settings.openai_api_key != 'your_openai_key_here' else '✗'); print('Anthropic:', '✓' if settings.anthropic_api_key and settings.anthropic_api_key != 'your_anthropic_key_here' else '✗')"
```

## ⚠️ Security Notes

1. **Never commit .env to git** - It's already in .gitignore
2. **Keep keys secret** - Don't share them publicly
3. **Use environment variables** in production
4. **Rotate keys** if exposed

## 💰 Cost Considerations

- **OpenAI GPT-4**: ~$0.01-0.03 per 1K tokens
- **Anthropic Claude**: ~$0.003-0.015 per 1K tokens
- **Caching enabled**: Reduces redundant calls (saves money)
- **Evaluation calls**: Use cheaper models when possible

## 🎯 Minimum Requirements

**For basic functionality:**
- ✅ At least ONE API key (OpenAI OR Anthropic)

**For full functionality:**
- ✅ OpenAI API key (for generation)
- ✅ Anthropic API key (for evaluation - better blinding)

**For production:**
- ✅ Both keys configured
- ✅ Caching enabled
- ✅ Proper error handling

## 🔍 What Each Key Is Used For

### OpenAI API Key
- **Generation**: Creating prompt outputs
- **Evaluation**: LLM-based judging (if OpenAI selected)
- **Self-Improvement**: Generating candidate prompts
- **Default provider**: Used if no provider specified

### Anthropic API Key
- **Generation**: Alternative to OpenAI
- **Evaluation**: LLM-based judging (if Anthropic selected)
- **Self-Improvement**: Generating candidate prompts
- **Better for**: Evaluation (often more consistent)

## 🚀 Quick Start

1. Get at least one API key (OpenAI recommended)
2. Add it to `.env` file
3. Restart the backend server
4. Test with a simple inference request

## 📊 Usage Without Keys

The system will run **without API keys** for:
- ✅ Prompt management (CRUD operations)
- ✅ Version control
- ✅ Database operations
- ✅ API documentation

But will **fail** for:
- ❌ Inference (needs LLM)
- ❌ Evaluation (needs LLM)
- ❌ Self-improvement (needs LLM)

