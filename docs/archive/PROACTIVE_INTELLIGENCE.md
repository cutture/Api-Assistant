# Proactive Intelligence & Memory System

**Version**: 0.3.0
**Status**: ✅ COMPLETE
**Date**: December 25, 2025

---

## Overview

The Proactive Intelligence & Memory System adds sophisticated context awareness, gap detection, and proactive information gathering to the API Integration Assistant. This system ensures the assistant has sufficient information before generating code and automatically enriches its knowledge base through intelligent web scraping and memory management.

### Key Capabilities

1. **Gap Analysis** - Detects missing information before code generation
2. **URL Extraction & Scraping** - Automatically processes URLs from user messages
3. **Smart Web Search** - Intent-aware query generation for better results
4. **Conversation Memory** - Selective embedding of valuable context
5. **Proactive Questions** - Asks clarifying questions when needed

---

## Architecture

### Workflow Overview

```
User Query → Query Analyzer → Supervisor
                                  ↓
                              RAG Agent
                    (retrieves docs + scrapes URLs)
                                  ↓
                         Gap Analysis Agent
                        (checks for missing info)
                                  ↓
                        ┌─────────┴─────────┐
                  Missing Info        Sufficient Info
                        ↓                   ↓
                    Ask User          Code Generator
                        ↓                   ↓
                      END                 END
```

### Component Interaction

```
┌─────────────────────────────────────────────────┐
│              User Message                       │
│  "Create a user with this endpoint:             │
│   https://api.example.com/docs"                 │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│           URL Scraper Service                   │
│  - Extracts: https://api.example.com/docs       │
│  - Scrapes HTML content                         │
│  - Embeds in vector store                       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              RAG Agent                          │
│  - Retrieves from vector store                  │
│  - Includes scraped URL content                 │
│  - Triggers web search if low relevance         │
│  - Embeds web results                           │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│        Gap Analysis Agent                       │
│  - Analyzes: Query + Intent + Retrieved Docs    │
│  - Determines: Sufficient info?                 │
│  - Generates: Clarifying questions if needed    │
└──────────────────┬──────────────────────────────┘
                   │
          ┌────────┴────────┐
          │                 │
┌─────────▼──────┐  ┌───────▼─────────┐
│   Ask User     │  │  Code Generator │
│                │  │                 │
│ Returns:       │  │ Returns:        │
│ - Questions    │  │ - Code snippets │
│ - Reasoning    │  │ - Documentation │
└────────────────┘  └─────────────────┘
```

---

## Features

### 1. Gap Analysis Agent

**Purpose**: Detect missing information needed for code generation

**Implementation**: `src/agents/gap_analysis_agent.py`

**How It Works**:
1. Analyzes the user's query and detected intent
2. Examines retrieved documentation context
3. Uses LLM to determine if information is sufficient
4. Generates specific clarifying questions if gaps exist

**Example Analysis**:

```python
# User Query
"Generate code to create a user"

# Gap Analysis Result
{
    "has_sufficient_info": False,
    "confidence": 0.7,
    "missing_aspects": [
        "endpoint_path",
        "request_parameters",
        "authentication_method"
    ],
    "questions_for_user": [
        "Which endpoint should I use to create a user (e.g., POST /api/users)?",
        "What parameters are required (e.g., username, email, password)?",
        "What authentication method does the API use (API key, OAuth, JWT)?"
    ],
    "reasoning": "The query requests code generation but doesn't specify the endpoint, required parameters, or authentication details."
}
```

**Key Features**:
- LLM-powered gap detection
- Intent-aware analysis
- Structured question generation
- Confidence scoring
- Graceful fallback (doesn't block on errors)

---

### 2. URL Extraction & Scraping

**Purpose**: Automatically extract and process URLs from user messages

**Implementation**: `src/services/url_scraper.py`

**How It Works**:
1. Regex-based URL extraction from text
2. HTTP fetching with timeout and size limits
3. HTML parsing with BeautifulSoup
4. Text extraction and cleaning
5. Automatic embedding in vector store

**Example**:

```python
# User Message
"Can you help me integrate with this API? https://api.example.com/docs"

# URL Scraper Output
{
    "title": "Example API Documentation",
    "content": "API Overview\n\nThe Example API allows you to...\n\nEndpoints:\nPOST /users - Create a new user...",
    "url": "https://api.example.com/docs"
}

# Automatically embedded in vector store for immediate and future use
```

**Configuration**:
```python
URLScraperService(
    timeout=10,  # Request timeout in seconds
    max_content_length=100000,  # Max content size (100KB)
    user_agent="API-Assistant-Bot/1.0"
)
```

**Safety Features**:
- URL validation
- Timeout protection
- Content length limits
- HTML sanitization
- Error handling

---

### 3. Conversation Memory Service

**Purpose**: Manage conversation context and web search result embedding

**Implementation**: `src/services/conversation_memory.py`

**Memory Strategy**:

| Type | Storage | Purpose | Default |
|------|---------|---------|---------|
| **Current Session** | 128k Context Window | Active conversation | ✅ Enabled |
| **Web Search Results** | Vector Store | Future retrieval | ✅ Enabled |
| **Conversation History** | Vector Store | Long-term memory | ❌ Disabled |
| **Scraped URLs** | Vector Store | Persistent docs | ✅ Enabled |

**Why This Strategy?**

```
┌─────────────────────────────────────────────────┐
│         128k Context Window                     │
│  ✅ Pros:                                        │
│  - Fast access to recent conversation           │
│  - No vector DB pollution                       │
│  - Perfect for follow-up questions              │
│  - Maintains conversation flow                  │
│                                                  │
│  Usage: Current session (last N messages)       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│         Vector Store Embedding                  │
│  ✅ When to Use:                                 │
│  - Web search results (valuable external info)  │
│  - Scraped URL content (user-provided docs)     │
│  - Important exchanges (optional, disabled)     │
│                                                  │
│  Usage: Long-term knowledge accumulation        │
└─────────────────────────────────────────────────┘
```

**Embedding Logic**:

```python
# Web search results - ALWAYS embedded
embed_web_search_results(
    query="How to authenticate with OAuth2",
    web_results=[...],
)
# → Stored for future queries about OAuth2

# Scraped URLs - ALWAYS embedded
embed_url_content(
    url_content={"title": "...", "content": "...", "url": "..."},
    query="original user query",
)
# → Available for semantic search

# Conversation history - DISABLED by default
embed_conversation_exchange(
    user_message="How do I create a user?",
    assistant_response="You can create a user by...",
)
# → Only if enable_conversation_embedding=True
```

---

### 4. Smart Web Search Enhancement

**Purpose**: Generate better web search queries based on intent and keywords

**Implementation**: Enhanced in `src/agents/rag_agent.py`

**Query Generation Strategy**:

```python
# Original Query
"How do I authenticate?"

# Intent Analysis
{
    "primary_intent": "authentication",
    "keywords": ["auth", "API", "token"]
}

# Generated Search Query
"How do I authenticate? API authentication guide auth API token"
```

**Intent-Based Enhancements**:

| Intent | Added Context |
|--------|--------------|
| `code_generation` | "code example tutorial" |
| `authentication` | "API authentication guide" |
| `schema_explanation` | "API schema documentation" |
| General | Uses top 2-3 keywords |

**Benefits**:
- Higher quality search results
- Domain-specific context
- Keyword enrichment
- Better relevance scores

---

### 5. Proactive Question Asking

**Purpose**: Ask clarifying questions when information is missing

**Implementation**: Supervisor workflow with gap analysis routing

**User Experience**:

**Scenario 1: Sufficient Information**
```
User: "Generate Python code to create a user using POST /api/users
       with username and email parameters"

System:
✅ Gap Analysis: Sufficient info
→ Directly generates code
```

**Scenario 2: Missing Information**
```
User: "Generate code to create a user"

System:
❌ Gap Analysis: Missing info
→ Asks clarifying questions:

"I need some additional information to generate the best code for you:

1. Which endpoint should I use to create a user (e.g., POST /api/users)?
2. What parameters are required (e.g., username, email, password)?
3. What authentication method does the API use (API key, OAuth, JWT)?

Please provide these details so I can create accurate integration code."
```

**Question Quality**:
- Specific and actionable
- Context-aware
- Numbered for easy response
- Includes examples
- Explains reasoning

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Web Search & URL Scraping
ENABLE_WEB_SEARCH=true
WEB_SEARCH_MIN_RELEVANCE=0.5
WEB_SEARCH_MAX_RESULTS=5

# Memory Management
# (No new config needed - uses defaults)
```

### Code Configuration

```python
# Conversation Memory Service
ConversationMemoryService(
    enable_conversation_embedding=False,  # Disabled: use 128k context
    enable_web_result_embedding=True,     # Enabled: save web results
)

# URL Scraper Service
URLScraperService(
    timeout=10,                 # HTTP timeout (seconds)
    max_content_length=100000,  # Max content size (bytes)
)

# Gap Analysis Agent
GapAnalysisAgent(
    llm_client=create_reasoning_client(),  # Uses reasoning model
)
```

---

## Usage Examples

### Example 1: URL Extraction

```python
# User provides URL in message
user_message = "Check out this API: https://jsonplaceholder.typicode.com/users"

# Automatic processing:
# 1. URL extracted: https://jsonplaceholder.typicode.com/users
# 2. Content fetched and parsed
# 3. Embedded in vector store
# 4. Used for answering query
# 5. Available for future queries
```

### Example 2: Gap Analysis

```python
# User query
query = "Generate code to authenticate"

# Workflow:
# 1. RAG retrieves authentication docs
# 2. Gap Analysis checks context
# 3. Determines: Missing specific auth method
# 4. Asks: "Which authentication method does your API use?"
```

### Example 3: Smart Web Search

```python
# Query with low vector store relevance
query = "How to handle OAuth2 refresh tokens in Python"

# System behavior:
# 1. Vector store search: 0.3 relevance (below 0.5 threshold)
# 2. Triggers smart web search
# 3. Query enhanced: "How to handle OAuth2 refresh tokens in Python
#                     code example tutorial OAuth2 refresh token Python"
# 4. Web results fetched and embedded
# 5. Answer generated from combined sources
```

---

## State Management

### New State Fields

```typescript
AgentState {
    // Existing fields...

    // Gap Analysis
    gap_analysis?: {
        has_sufficient_info: boolean;
        confidence: number;
        missing_aspects: string[];
        questions_for_user: string[];
        reasoning: string;
    };

    has_sufficient_info?: boolean;
    missing_info?: boolean;
    questions_for_user?: string[];

    // (Other fields unchanged)
}
```

---

## Performance Impact

### Memory Usage

| Component | Memory Impact | Mitigation |
|-----------|--------------|------------|
| 128k Context Window | ~500MB per session | Session cleanup |
| Vector Store Embeddings | ~1KB per document | Selective embedding |
| URL Scraping | ~100KB per URL | Content length limits |
| **Total** | **~600MB per active session** | **Acceptable** |

### Latency

| Operation | Added Latency | Impact |
|-----------|--------------|--------|
| URL Scraping | +0.5-2s per URL | One-time cost |
| Gap Analysis | +1-2s (LLM call) | Only for code gen |
| Web Search Embedding | +0.2-0.5s | Background operation |
| **Total** | **+2-5s for complex queries** | **Acceptable** |

---

## Error Handling

### Graceful Degradation

**URL Scraping Failures**:
```python
# Timeout or HTTP error → Skip URL, continue with other context
# Parsing error → Log error, use raw text
# Content too large → Truncate to max length
```

**Gap Analysis Failures**:
```python
# LLM error → Default to has_sufficient_info=True (don't block)
# JSON parsing error → Proceed with code generation
# Network error → Log warning, continue workflow
```

**Web Search Failures**:
```python
# DuckDuckGo unavailable → Use vector store results only
# Embedding error → Log error, don't fail query
# Timeout → Skip embedding, return results
```

---

## Testing

### Unit Tests

```bash
# Test gap analysis
pytest tests/test_agents/test_gap_analysis_agent.py -v

# Test URL scraper
pytest tests/test_services/test_url_scraper.py -v

# Test conversation memory
pytest tests/test_services/test_conversation_memory.py -v

# Test smart web search
pytest tests/test_agents/test_rag_agent.py::test_smart_web_search -v
```

### Integration Tests

```bash
# Test full proactive workflow
pytest tests/test_e2e/test_proactive_intelligence.py -v
```

---

## Future Enhancements

### Planned (Phase 4)

1. **Multi-Turn Conversations**
   - Track clarification rounds
   - Maintain question context
   - Support iterative refinement

2. **Smart Question Ordering**
   - Prioritize critical missing info
   - Group related questions
   - Adaptive follow-up questions

3. **Context Summarization**
   - LLM-powered conversation summaries
   - Selective detail preservation
   - Token usage optimization

4. **Learning from Feedback**
   - Track successful code generations
   - Learn common patterns
   - Improve gap detection over time

### Experimental

- **Approximate Planning**: Allow code generation with warnings instead of strict blocking
- **URL Link Chains**: Follow links from scraped pages
- **Collaborative Filtering**: Learn from similar queries across sessions

---

## Troubleshooting

### Issue: Gap analysis always returns has_sufficient_info=True

**Cause**: LLM error or JSON parsing failure
**Fix**: Check LLM connectivity and logs

```bash
# Check logs
tail -f logs/app.log | grep gap_analysis
```

### Issue: URLs not being scraped

**Cause**: Invalid URL format or network error
**Fix**: Verify URL format and network connectivity

```python
# Test URL scraper manually
from src.services.url_scraper import URLScraperService

scraper = URLScraperService()
urls = scraper.extract_urls("Check https://example.com/api")
print(urls)  # Should show extracted URL
```

### Issue: Web search results not embedded

**Cause**: Vector store connection or embedding service error
**Fix**: Check vector store status

```bash
# Verify ChromaDB
ls -la data/chroma_db/
```

---

## Summary

The Proactive Intelligence & Memory System significantly enhances the API Integration Assistant's capabilities:

✅ **Smarter**: Detects information gaps before generating code
✅ **More Helpful**: Asks specific clarifying questions
✅ **Better Context**: Automatically processes URLs and web results
✅ **Efficient**: Uses 128k context window + selective vector embedding
✅ **Resilient**: Graceful error handling and fallbacks

This system ensures users receive accurate, context-aware assistance while maintaining performance and preventing incomplete or incorrect code generation.

---

**Version**: 0.3.0
**Status**: ✅ PRODUCTION READY
**Last Updated**: December 25, 2025

