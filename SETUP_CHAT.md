# AI Chat Setup Guide

## Quick Setup (5 minutes)

### Step 1: Get Groq API Key (FREE)

1. Visit **https://console.groq.com**
2. Click "Sign Up" (free account)
3. After login, go to **API Keys** section
4. Click **"Create API Key"**
5. Copy the API key

### Step 2: Configure Environment

Edit the `.env` file:

```bash
# Open .env file
nano .env

# OR use any text editor
```

Update this line with your actual Groq API key:
```bash
GROQ_API_KEY=your_actual_groq_api_key_here
```

Make sure this line says `groq`:
```bash
LLM_PROVIDER=groq
```

Save the file (Ctrl+X, then Y, then Enter if using nano).

### Step 3: Restart Backend

```bash
# Stop the backend (Ctrl+C in the terminal where it's running)

# Then restart:
cd /home/user/Api-Assistant
source venv/bin/activate
uvicorn src.api.app:app --reload
```

### Step 4: Clear Browser Cache

**IMPORTANT**: Hard refresh your browser to load the new code
- Windows/Linux: Press **Ctrl+Shift+R**
- Mac: Press **Cmd+Shift+R**

### Step 5: Test the Chat

1. Go to **http://localhost:3000/chat**
2. Try this example:

```
I want to use the JSONPlaceholder API (https://jsonplaceholder.typicode.com).
Write a Python script to fetch all users and then find the posts for the user 'Bret'.
```

3. You should see:
   - ✅ The URL being scraped
   - ✅ AI-generated Python code
   - ✅ "Content Indexed" notification
   - ✅ Complete working example with imports and error handling

## What You Get

### 🎯 Features

1. **URL Scraping**: Automatically fetches and parses any URL you provide
2. **Dynamic Indexing**: Scraped content is indexed for future use
3. **Code Generation**: Ask for code and get complete, working examples
4. **Conversation History**: Maintains context across messages
5. **Source Citations**: Shows which documents/URLs were used

### 💰 Costs

**Groq (Recommended)**:
- ✅ **FREE** up to 30 requests/minute
- ✅ Extremely fast (3-5 seconds)
- ✅ ~43,000 requests/day free!
- ✅ No credit card required

**If you exceed limits** (unlikely):
- OpenAI GPT-3.5: ~$0.75 per 1000 messages
- Claude Haiku: ~$0.50 per 1000 messages

## Example Usage

### 1. Code Generation with URL

**Your message:**
```
I want to use the JSONPlaceholder API (https://jsonplaceholder.typicode.com).
Write a Python script to fetch all users and then find the posts for the user 'Bret'.
```

**What happens:**
1. Scrapes jsonplaceholder.typicode.com
2. Indexes the API documentation
3. Generates Python code with:
   - Imports
   - API calls
   - Logic to find user "Bret"
   - Error handling
   - Example output

### 2. API Questions

**Your message:**
```
How do I authenticate with this API?
```

**What happens:**
1. Searches your indexed documents
2. Finds authentication-related content
3. Explains authentication methods
4. Shows code examples

### 3. Compare APIs

**Your message:**
```
Compare authentication between https://api1.com and https://api2.com
```

**What happens:**
1. Scrapes both URLs
2. Indexes both
3. Compares approaches
4. Provides detailed analysis

## Troubleshooting

### Error: "GROQ_API_KEY not set"

**Solution**: Make sure you updated `.env` with your actual Groq API key

### Error: "groq package not installed"

**Solution**:
```bash
cd /home/user/Api-Assistant
source venv/bin/activate
pip install groq
```

### Chat shows old behavior

**Solution**: Hard refresh browser (Ctrl+Shift+R)

### Backend not starting

**Solution**: Check if port 8000 is available
```bash
lsof -i :8000  # Check what's using port 8000
kill -9 <PID>  # Kill the process if needed
```

## Alternative: Use Ollama (Local)

If you prefer to run LLMs locally without an API key:

### Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Mac
brew install ollama

# Windows
# Download from https://ollama.com/download
```

### Download a Model

```bash
ollama pull llama3.1:8b
```

### Update .env

```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
```

### Start Ollama Server

```bash
ollama serve
```

**Note**: Ollama is slower than Groq (10-30 seconds vs 3-5 seconds) but runs completely locally.

## Advanced Configuration

### Use Different Models

Edit `.env` to customize models:

```bash
# For better code generation
GROQ_CODE_MODEL=llama-3.3-70b-versatile

# For better reasoning
GROQ_REASONING_MODEL=llama-3.3-70b-versatile

# For general chat
GROQ_GENERAL_MODEL=llama-3.3-70b-versatile
```

### Disable URL Scraping

If you don't want automatic URL scraping, you can disable it in the frontend request:

```typescript
// In frontend/src/app/chat/page.tsx
enable_url_scraping: false,
enable_auto_indexing: false,
```

## Support

If you encounter issues:

1. Check backend logs in the terminal
2. Check browser console (F12 → Console tab)
3. Verify `.env` configuration
4. Make sure backend is running on port 8000
5. Make sure frontend is running on port 3000

## Features Overview

| Feature | Status | Description |
|---------|--------|-------------|
| LLM Integration | ✅ | Groq/Ollama support |
| URL Scraping | ✅ | Automatic URL extraction |
| Dynamic Indexing | ✅ | Real-time content indexing |
| Code Generation | ✅ | Complete working examples |
| Chat History | ✅ | Last 20 messages |
| Session Management | ✅ | Persistent conversations |
| Source Citations | ✅ | Shows references |
| Cost Tracking | ✅ | Via Groq dashboard |

Enjoy your AI-powered chat assistant! 🚀
