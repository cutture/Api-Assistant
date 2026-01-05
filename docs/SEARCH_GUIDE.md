# 🔍 Search Guide - Understanding Search Modes & Query Expansion

**Last Updated**: January 2026
**Version**: 1.0.0

This guide explains how to use the advanced search features in API Assistant to find the most relevant documents and API specifications.

---

## 📖 Table of Contents

1. [Search Modes](#search-modes)
   - [Vector Search](#1-vector-search)
   - [Hybrid Search](#2-hybrid-search-recommended)
   - [Reranked Search](#3-reranked-search)
2. [Query Expansion](#query-expansion)
3. [Practical Examples](#practical-examples)
4. [Best Practices](#best-practices)
5. [Recommendation Matrix](#recommendation-matrix)

---

## Search Modes

API Assistant offers **3 search modes**, each using different algorithms to find relevant documents. You can select the search mode in the Search Options section of the Search page.

### 1. Vector Search

**Pure Semantic Search**

#### How it Works
- Converts your query into a mathematical vector (embedding)
- Finds documents with similar semantic meaning using cosine similarity
- Powered by sentence transformers AI model

#### Strengths ✅
- **Semantic Understanding**: Understands the meaning and context of your query
- **Conceptual Matching**: Finds results even when exact words don't match
- **Context Awareness**: Great for questions and conceptual queries

#### Weaknesses ❌
- May miss exact keyword matches
- Can return conceptually similar but not exactly relevant results
- Less effective for specific technical terms or acronyms

#### When to Use

✅ **Use Vector Search for:**
- Conceptual questions: *"How do I secure my API?"*
- Understanding functionality: *"What handles user permissions?"*
- When you're not sure of exact terminology
- Exploratory research queries

❌ **Don't Use for:**
- Exact endpoint names: *"/api/v1/users/{id}"*
- Specific error codes or technical identifiers
- Acronyms without context

---

### 2. Hybrid Search (RECOMMENDED)

**BM25 Keyword + Vector Semantic Search**

#### How it Works
Combines **two powerful algorithms**:
1. **BM25**: Traditional keyword-based ranking (like Google search)
   - Finds exact keyword matches
   - Great for technical terms and acronyms
2. **Vector Search**: Semantic similarity (described above)
   - Understands meaning and context

Results are merged using **Reciprocal Rank Fusion (RRF)**, which intelligently combines rankings from both methods.

#### Strengths ✅
- **Best of Both Worlds**: Finds exact keyword matches AND semantic matches
- **Robust**: Works well for almost all query types
- **Technical Term Friendly**: Excellent for API documentation with technical jargon
- **Balanced Results**: Combines precision and recall

#### Weaknesses ❌
- Slightly slower than pure vector search (negligible in most cases)

#### When to Use

✅ **Use Hybrid Search for:** *(RECOMMENDED DEFAULT)*
- Searching for API endpoints: *"POST user authentication"*
- Technical terms and concepts: *"JWT token validation"*
- Acronyms and abbreviations: *"OAuth2 authorization flow"*
- Mixed queries: *"How to authenticate with bearer tokens"*
- **General API documentation search**

**💡 This is the default and recommended mode for most use cases.**

---

### 3. Reranked Search

**Hybrid Search + Cross-Encoder Re-ranking**

#### How it Works
1. First retrieves 3x more candidates using Hybrid search
2. Uses a sophisticated **Cross-Encoder** AI model to deeply analyze query-document relevance
3. Re-scores and re-ranks all candidates
4. Returns the top N most relevant results

#### Strengths ✅
- **Highest Accuracy**: Best precision and relevance
- **Deep Understanding**: Analyzes the relationship between query and document context
- **Complex Query Handling**: Excels at multi-part questions

#### Weaknesses ❌
- **Slowest**: Additional AI processing time (typically 2-3x slower)
- **Resource Intensive**: Uses more computational resources

#### When to Use

✅ **Use Reranked Search for:**
- Complex multi-part questions: *"How do I handle authentication errors when the JWT token expires during a file upload?"*
- Research or deep-dive queries
- When you need the absolute best results
- When initial Hybrid search results aren't satisfactory
- Analysis requiring high precision

❌ **Don't Use for:**
- Quick lookups
- Simple queries
- When speed matters more than perfect accuracy

---

## Query Expansion

**Automatically expands your search query with related terms, synonyms, and alternative phrasings.**

### What is Query Expansion?

Query Expansion improves **search recall** (finding more relevant results) by adding related terms from a domain-specific knowledge base. The system analyzes your query and intelligently adds synonyms, abbreviations, and related concepts.

### How Query Expansion Works

The system uses **multiple expansion strategies**:

1. **Synonym Expansion**: Adds technical synonyms and related terms
2. **Abbreviation Expansion**: Expands technical abbreviations
3. **Domain-Specific Expansion**: Uses API/tech-specific term relationships
4. **Multi-Query**: Generates query variations for question-based searches

### Expansion Examples

| Your Query | Expanded Terms Added |
|------------|---------------------|
| `auth` | authentication, authorization, login, signin, oauth, jwt |
| `POST request` | create, add, insert, submit, http request, api call |
| `endpoint` | api endpoint, route, url, path, resource |
| `JWT` | json web token, authentication, token, bearer token |
| `error` | exception, failure, bug, issue, problem |
| `cache` | caching, cache layer, redis, memcached |
| `async` | asynchronous, non-blocking, concurrent, parallel |

### Expansion Strategies

#### 1. Synonym Expansion (Default)
```
Query: "auth"
Expanded: "auth authentication authorization login signin oauth jwt"
```

#### 2. Multi-Query (For Questions)
```
Query: "How to authenticate users?"
Generates:
  - "authenticate users guide"
  - "authenticate users tutorial"
  - "authenticate users documentation"
```

#### 3. Domain-Specific (Technical Terms)
```
Query: "REST API"
Expanded: "REST API restful http api web service endpoint"
```

### When to Enable Query Expansion

✅ **Enable Query Expansion when:**
- Your query is very short (1-2 words): *"auth"*, *"cache"*
- Using abbreviations or jargon: *"JWT"*, *"OAuth"*, *"REST"*
- Searching for general concepts: *"authentication"*
- Getting too few results with exact search
- Doing broad exploratory research
- Not getting expected results

❌ **Disable Query Expansion when:**
- Searching for exact technical identifiers
- Looking for specific endpoint paths: *"/api/v1/users/{id}"*
- Getting too many irrelevant results
- Your query is already very specific and detailed
- Searching for exact error messages or codes

### Query Expansion in Action

**Example 1: Short Technical Term**
```
Original Query: "JWT"
With Expansion: "JWT json web token authentication token bearer token"

Result: Finds documents about JWT, token authentication, and bearer tokens
```

**Example 2: General Concept**
```
Original Query: "authentication"
With Expansion: "authentication auth login signin verify credentials oauth jwt token"

Result: Finds all authentication-related documents
```

**Example 3: Question**
```
Original Query: "How to cache API responses?"
With Expansion: Generates variations like:
  - "cache API responses guide"
  - "cache API responses tutorial"
  - "caching cache layer redis memcached"

Result: Finds tutorials, guides, and documentation about API caching
```

---

## Practical Examples

### Example 1: Finding Authentication Endpoints

**Query**: `POST authentication`

**Recommended Settings**:
- **Search Mode**: Hybrid
- **Query Expansion**: ON

**Why**: Hybrid finds exact POST method matches while expanding "authentication" to include auth, login, oauth, etc.

---

### Example 2: Understanding a Concept

**Query**: `How does rate limiting work?`

**Recommended Settings**:
- **Search Mode**: Reranked
- **Query Expansion**: ON

**Why**: Question-based query benefits from deep semantic understanding and query variations.

---

### Example 3: Exact Endpoint Lookup

**Query**: `/api/v1/users/{id}`

**Recommended Settings**:
- **Search Mode**: Hybrid
- **Query Expansion**: OFF

**Why**: Exact path search - don't want expansion to add noise.

---

### Example 4: Technical Abbreviation

**Query**: `OAuth2 flow`

**Recommended Settings**:
- **Search Mode**: Hybrid
- **Query Expansion**: ON

**Why**: Expansion adds "oauth", "authentication", "authorization", "token" to find all related docs.

---

### Example 5: Complex Research Question

**Query**: `How do I handle JWT token refresh when the access token expires during file upload with multipart/form-data?`

**Recommended Settings**:
- **Search Mode**: Reranked
- **Query Expansion**: ON

**Why**: Complex multi-part question needs deep semantic understanding and term expansion.

---

## Best Practices

### 🎯 General Guidelines

1. **Start with Hybrid + Expansion**: This is the sweet spot for most searches
2. **Be Specific**: More specific queries generally work better
3. **Use Technical Terms**: The system understands API terminology
4. **Try Different Modes**: If results aren't good, try a different search mode
5. **Adjust Expansion**: Toggle expansion if results are too broad or too narrow

### 📊 Search Performance Tips

| Goal | Search Mode | Query Expansion | Notes |
|------|-------------|----------------|-------|
| **Fast lookup** | Hybrid | OFF | Quick and accurate |
| **Best accuracy** | Reranked | ON | Slower but most precise |
| **Exploratory** | Hybrid | ON | Find related concepts |
| **Exact match** | Hybrid | OFF | Find specific items |
| **Research** | Reranked | ON | Deep understanding |

### 🔧 Troubleshooting

**Problem**: Too many irrelevant results
- **Solution**: Turn OFF Query Expansion, make query more specific

**Problem**: Too few results or missing expected docs
- **Solution**: Turn ON Query Expansion, try Hybrid or Reranked mode

**Problem**: Results don't match my exact search
- **Solution**: Turn OFF Query Expansion, use more specific keywords

**Problem**: Can't find conceptually related docs
- **Solution**: Turn ON Query Expansion, try Vector or Reranked mode

---

## Recommendation Matrix

Quick reference for choosing the right settings:

| **Scenario** | **Search Mode** | **Query Expansion** | **Example** |
|--------------|----------------|---------------------|-------------|
| Specific endpoint lookup | Hybrid | ❌ OFF | `/api/users` |
| Conceptual question | Hybrid or Reranked | ✅ ON | *"How does auth work?"* |
| Technical term/acronym | Hybrid | ✅ ON | `JWT`, `OAuth` |
| Complex research query | Reranked | ✅ ON | *"How to handle errors..."* |
| Exact error message | Hybrid | ❌ OFF | `401 Unauthorized` |
| Short technical term | Hybrid | ✅ ON | `cache`, `async` |
| General exploration | Hybrid | ✅ ON | `authentication` |
| HTTP method + action | Hybrid | ✅ ON | `POST user creation` |
| Quick known endpoint | Hybrid | ❌ OFF | Specific path lookup |
| Multi-part question | Reranked | ✅ ON | *"What happens when..."* |

### 🌟 Recommended Defaults

For **most users**, start with:
- **Search Mode**: **Hybrid (BM25 + Vector)**
- **Query Expansion**: **ON** (for short queries) or **OFF** (for specific paths)
- **Results Limit**: **50 results**

Adjust based on the results you get!

---

## Technical Details

### Search Mode Comparison

| Feature | Vector | Hybrid | Reranked |
|---------|--------|--------|----------|
| **Speed** | Fast | Medium | Slower |
| **Accuracy** | Good | Very Good | Excellent |
| **Keyword Matching** | ❌ No | ✅ Yes | ✅ Yes |
| **Semantic Understanding** | ✅ Yes | ✅ Yes | ✅✅ Best |
| **Best For** | Concepts | General | Complex |
| **Resource Usage** | Low | Medium | High |

### Query Expansion Details

- **Max Expansions**: 5 additional terms per query
- **Domain Knowledge Base**: 80+ technical term mappings
- **Abbreviation Database**: 15+ common API/tech abbreviations
- **Expansion Strategies**: 4 (auto, synonyms, llm, multi_query)

---

## Related Documentation

- [DAY21_HYBRID_SEARCH.md](./DAY21_HYBRID_SEARCH.md) - Technical implementation details
- [DAY22_CROSS_ENCODER_RERANKING.md](./DAY22_CROSS_ENCODER_RERANKING.md) - Re-ranking deep dive
- [DAY23_QUERY_EXPANSION.md](./DAY23_QUERY_EXPANSION.md) - Query expansion architecture
- [DAY25_ADVANCED_FILTERING.md](./DAY25_ADVANCED_FILTERING.md) - Advanced filtering guide

---

## Feedback

Having trouble with search? Found the perfect query settings? Let us know!

- **Issues**: Report search problems on GitHub Issues
- **Feature Requests**: Suggest improvements for search functionality
- **Documentation**: Help improve this guide with your insights

---

**Happy Searching! 🚀**
