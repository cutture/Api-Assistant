# LLM Provider Configuration Guide

This guide explains how to switch between Ollama (local) and Groq (cloud) LLM providers.

## Overview

The API Integration Assistant supports two LLM providers:

1. **Ollama** (Local) - Runs models locally on your machine
2. **Groq** (Cloud) - Fast cloud-based inference using Groq's API

## Quick Start

### Using Ollama (Local)

1. Install and start Ollama: https://ollama.ai
2. Pull the model:
   ```bash
   ollama pull deepseek-coder:6.7b
   ```
3. Set in `.env`:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=deepseek-coder:6.7b
   ```

### Using Groq (Cloud)

1. Get API key from: https://console.groq.com
2. Set in `.env`:
   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_api_key_here
   ```

## Configuration Details

### Environment Variables

#### Required for Both Providers
```env
# Set provider: "ollama" or "groq"
LLM_PROVIDER=ollama
```

#### Ollama Configuration
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:6.7b
```

#### Groq Configuration
```env
GROQ_API_KEY=your_groq_api_key_here

# Different models for different agent types
GROQ_REASONING_MODEL=deepseek-r1-distill-llama-70b  # For QueryAnalyzer, DocAnalyzer
GROQ_CODE_MODEL=llama-3.3-70b-versatile             # For CodeGenerator
GROQ_GENERAL_MODEL=llama-3.3-70b-versatile          # For RAGAgent
```

## How It Works

### Agent-Specific Models (Groq Only)

When `LLM_PROVIDER=groq`, different agents use specialized models:

| Agent | Purpose | Groq Model |
|-------|---------|------------|
| **QueryAnalyzer** | Intent classification & planning | DeepSeek R1 (70B) |
| **RAGAgent** | Document retrieval & synthesis | Llama 3.3 (70B) |
| **CodeGenerator** | Code generation | Llama 3.3 (70B) |
| **DocumentationAnalyzer** | Gap analysis & reasoning | DeepSeek R1 (70B) |

### Ollama Model Usage

When `LLM_PROVIDER=ollama`, all agents use the same model specified in `OLLAMA_MODEL`.

## Performance Comparison

### Ollama (Local)
- ✅ **Pros**: Privacy, no API costs, works offline
- ❌ **Cons**: Slower inference, requires local GPU/CPU resources

### Groq (Cloud)
- ✅ **Pros**: **Very fast inference** (50-100 tokens/sec), specialized models per task
- ❌ **Cons**: Requires internet, API rate limits, costs money (though free tier is generous)

## Switching Providers

Simply change `LLM_PROVIDER` in your `.env` file and restart the application:

```bash
# Switch to Groq for faster testing
LLM_PROVIDER=groq

# Switch back to Ollama for offline/private use
LLM_PROVIDER=ollama
```

**Note**: The application will automatically use the appropriate models based on the provider.

## Troubleshooting

### Groq Errors

**Error**: `ValueError: GROQ_API_KEY not set in environment`
- **Solution**: Add `GROQ_API_KEY=your_key_here` to `.env`

**Error**: `ImportError: No module named 'groq'`
- **Solution**: Install the package: `pip install groq>=0.4.0`

### Ollama Errors

**Error**: Connection refused to `http://localhost:11434`
- **Solution**: Start Ollama: `ollama serve`

**Error**: Model not found
- **Solution**: Pull the model: `ollama pull deepseek-coder:6.7b`

## Recommended Setup for Development

For **fast iteration and testing**, use Groq:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

For **production or privacy-sensitive environments**, use Ollama:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=deepseek-coder:6.7b
```

## Available Groq Models

Popular models you can use:
- `deepseek-r1-distill-llama-70b` - Best for reasoning & planning
- `llama-3.3-70b-versatile` - Best for code & general tasks
- `llama-3.1-8b-instant` - Faster, smaller model
- `mixtral-8x7b-32768` - Good for long context

See full list: https://console.groq.com/docs/models
