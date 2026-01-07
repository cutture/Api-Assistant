# Agent Architecture - API Integration Assistant

## 📐 System Overview

The API Integration Assistant uses a multi-agent architecture built on LangGraph. Each agent is a specialized component that processes specific aspects of user queries.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (Next.js Web Application)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ User Query
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (Week 2)                        │
│                    LangGraph StateGraph                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              QUERY ANALYZER AGENT ✅                      │  │
│  │   • Intent Classification (6 types)                      │  │
│  │   • Entity Extraction (endpoints, methods, params)       │  │
│  │   • Confidence Scoring                                   │  │
│  └──────────────────┬───────────────────────────────────────┘  │
│                     │                                           │
│                     │ Routing Decision                          │
│                     ▼                                           │
│  ┌─────────────────────────────────────────────────┐            │
│  │                                                 │            │
│  ├─► RAG AGENT ✅              ◄─┐                 │            │
│  │   • Multi-Query Retrieval    │                 │            │
│  │   • Vector Search            │ May             │            │
│  │   • Source Citations         │ Chain           │            │
│  │                              │                 │            │
│  ├─► CODE GENERATOR ✅         ◄─┘                 │            │
│  │   • Template Selection                         │            │
│  │   • Syntax Validation                          │            │
│  │   • Retry Injection                            │            │
│  │                                                 │            │
│  ├─► DOCUMENTATION ANALYZER ✅                     │            │
│  │   • Gap Detection (8 types)                    │            │
│  │   • Quality Scoring                            │            │
│  │   • Improvement Suggestions                    │            │
│  │                                                 │            │
│  └─────────────────────┬───────────────────────────┘            │
│                        │                                        │
│                        │ Agent Response                         │
│                        ▼                                        │
│                 Response Aggregation                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Final Response
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│            • Answer Display                                     │
│            • Source Citations                                   │
│            • Generated Code                                     │
│            • Documentation Gaps                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Agent State Flow

All agents share a common `AgentState` that flows through the system:

```
┌─────────────────────────────────────────────────────────────────┐
│                         AgentState                              │
├─────────────────────────────────────────────────────────────────┤
│  INPUT:                                                         │
│    query: str                     # User's question             │
│    intent_analysis: IntentAnalysis | None                      │
│                                                                 │
│  PROCESSING:                                                    │
│    current_agent: str             # Currently active agent      │
│    processing_path: list[str]     # Agent execution history     │
│    retrieved_documents: list[dict] # From vector DB             │
│                                                                 │
│  OUTPUT:                                                        │
│    response: str                  # Final answer                │
│    sources: list[SourceCitation]  # Documentation sources       │
│    generated_code: str | None     # Generated code              │
│    documentation_gaps: list[dict] | None  # Quality issues      │
│                                                                 │
│  METADATA:                                                      │
│    metadata: dict                 # Timing, tokens, etc.        │
│    error: AgentError | None       # Error tracking              │
└─────────────────────────────────────────────────────────────────┘
```

### State Transformation Example

```python
# Initial State
{
    "query": "How do I authenticate with the API?",
    "processing_path": [],
    "current_agent": None
}

# After Query Analyzer
{
    "query": "How do I authenticate with the API?",
    "intent_analysis": {
        "intent": "authentication",
        "confidence": "HIGH",
        "entities": {"keywords": ["authenticate", "API"]}
    },
    "processing_path": ["query_analyzer"],
    "current_agent": "query_analyzer"
}

# After RAG Agent
{
    "query": "How do I authenticate with the API?",
    "intent_analysis": {...},
    "retrieved_documents": [
        {"content": "Auth docs...", "score": 0.85, ...},
        {"content": "Bearer token...", "score": 0.78, ...}
    ],
    "response": "To authenticate, use Bearer token...",
    "sources": [
        {"title": "Authentication Guide", "url": "docs/auth", ...}
    ],
    "processing_path": ["query_analyzer", "rag_agent"],
    "current_agent": "rag_agent"
}
```

---

## 🤖 Agent Details

### 1. Query Analyzer Agent

**Responsibility**: Classify intent and extract context

```
INPUT: "Show me how to create a user with Python"
  │
  ├─► LLM Classification
  │     • Intent: code_generation
  │     • Confidence: HIGH
  │
  ├─► Entity Extraction
  │     • Action: create
  │     • Resource: user
  │     • Language: Python
  │
  └─► Fallback (if LLM fails)
        • Keyword matching
        • Pattern detection

OUTPUT: IntentAnalysis
  {
    "intent": "code_generation",
    "confidence": "HIGH",
    "entities": {
      "action": "create",
      "resource": "user",
      "language": "Python"
    }
  }
```

**Intent Routing Table**:
| Intent | Routes To | Example Query |
|--------|-----------|---------------|
| `general_question` | RAG Agent | "What is this API?" |
| `code_generation` | RAG → Code Generator | "Generate code to list users" |
| `endpoint_lookup` | RAG Agent | "Find the user creation endpoint" |
| `schema_explanation` | RAG Agent | "Explain the User schema" |
| `authentication` | RAG Agent | "How do I authenticate?" |
| `documentation_gap` | Doc Analyzer | "Find missing documentation" |

---

### 2. RAG Agent

**Responsibility**: Retrieve and synthesize documentation

```
INPUT: query + intent_analysis
  │
  ├─► Query Expansion (Multi-Query)
  │     Original: "user authentication"
  │     Variation 1: "API authentication methods"
  │     Variation 2: "how to authenticate users"
  │
  ├─► Vector Search (ChromaDB)
  │     • Execute all 3 queries
  │     • Retrieve top-k per query
  │     • Deduplicate results
  │
  ├─► Relevance Filtering
  │     • Filter by similarity threshold (default: 0.3)
  │     • Rank by relevance score
  │     • Limit to max_documents (default: 5)
  │
  ├─► Context Assembly
  │     • Format retrieved documents
  │     • Add metadata
  │     • Create citations
  │
  └─► Response Generation (LLM)
        • Synthesize information
        • Include source citations
        • Format for user

OUTPUT: response + sources + retrieved_documents
```

**Multi-Query Strategy**:
```
Single Query:     [Q1] ────────────► [R1, R2, R3]
                                      ↓
Multi-Query:      [Q1, Q2, Q3] ────► [R1, R2, R3, R4, R5, R6, R7]
                                      ↓ (deduplicate + rank)
                                      [R1, R3, R4, R5, R7]
```

---

### 3. Code Generator Agent

**Responsibility**: Generate production-ready Python code

```
INPUT: query + retrieved_documents
  │
  ├─► Endpoint Extraction (LLM)
  │     • Parse endpoint URL
  │     • Extract HTTP method
  │     • Identify parameters
  │
  ├─► Template Selection
  │     • GET request → requests_get.py.jinja2
  │     • POST/PUT/PATCH → requests_post.py.jinja2
  │     • Async request → httpx_async.py.jinja2
  │
  ├─► Template Rendering (Jinja2)
  │     • Inject endpoint, method, params
  │     • Generate function name
  │     • Add docstrings
  │
  ├─► Code Enhancement
  │     • Syntax validation (ast.parse)
  │     • Add retry decorator (if idempotent)
  │     • Format code (remove trailing spaces)
  │
  └─► Validation
        • Check syntax
        • Verify indentation
        • Return validated code

OUTPUT: generated_code (validated Python)
```

**Template Structure**:
```python
# requests_get.py.jinja2
import requests
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))  # ← Added if idempotent
def {{ function_name }}({{ parameters }}):
    """
    {{ docstring }}
    """
    url = "{{ base_url }}{{ endpoint }}"
    headers = {{ headers }}
    params = {{ query_params }}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()
```

**Idempotency Detection**:
```
GET, HEAD, OPTIONS, PUT, DELETE  → Add @retry decorator
POST, PATCH                      → No retry (not idempotent)
```

---

### 4. Documentation Analyzer Agent

**Responsibility**: Identify documentation quality issues

```
INPUT: retrieved_documents
  │
  ├─► Gap Detection Rules
  │     For each document:
  │       • Check description length (< 50 chars → GAP)
  │       • Check for examples ("example" keyword missing → GAP)
  │       • Check for error codes ("error", "400", "404" missing → GAP)
  │       • Check for auth info ("auth", "token" missing → GAP)
  │       • Check for response format ("response", "schema" missing → GAP)
  │       • Check for parameters ("parameter", "param" missing → GAP)
  │
  ├─► Severity Assignment
  │     • Missing auth info → CRITICAL
  │     • Missing description → HIGH
  │     • Missing examples → MEDIUM
  │     • Inconsistent naming → LOW
  │
  ├─► Quality Scoring
  │     Base Score: 100
  │     - CRITICAL gaps × 10
  │     - HIGH gaps × 5
  │     - MEDIUM gaps × 2
  │     - LOW gaps × 1
  │
  └─► Suggestion Generation
        • Specific improvement suggestions
        • Prioritized by severity
        • Actionable recommendations

OUTPUT: documentation_gaps + quality_score + summary
```

**Gap Detection Example**:
```
Document: "Returns user data from the database table"
  ↓
Gaps Detected:
  1. MISSING_EXAMPLES (MEDIUM)
     - No usage examples provided
     - Suggestion: Add code examples

  2. MISSING_ERROR_CODES (MEDIUM)
     - No error documentation
     - Suggestion: Document 400, 401, 404, 500 responses

  3. MISSING_AUTH_INFO (CRITICAL)
     - No authentication information
     - Suggestion: Specify required auth method

Quality Score: 73/100 (3 gaps detected)
```

---

## 🔌 Integration Points

### LangGraph Integration (Week 2)

Agents will be connected in a StateGraph:

```python
from langgraph.graph import StateGraph

# Create graph
graph = StateGraph(AgentState)

# Add nodes (agents)
graph.add_node("query_analyzer", query_analyzer)
graph.add_node("rag_agent", rag_agent)
graph.add_node("code_generator", code_generator)
graph.add_node("doc_analyzer", doc_analyzer)

# Add edges (routing)
graph.add_edge("START", "query_analyzer")
graph.add_conditional_edges(
    "query_analyzer",
    route_query,  # Routing function
    {
        "general_question": "rag_agent",
        "code_generation": "rag_agent",  # Then to code_generator
        "documentation_gap": "doc_analyzer",
    }
)

# Compile
app = graph.compile()

# Execute
result = app.invoke({"query": "How do I create a user?"})
```

---

## 📊 Data Flow Diagram

### Complete Request Flow

```
User
  │
  │ "Generate Python code to create a user"
  ▼
┌─────────────────┐
│ Query Analyzer  │
│                 │
│ Intent: code_   │
│ generation      │
└────────┬────────┘
         │
         │ Route: RAG → Code
         ▼
┌─────────────────┐
│   RAG Agent     │
│                 │
│ Multi-query:    │
│ 1. "create user"│
│ 2. "user API"   │
│ 3. "add user"   │
│                 │
│ Retrieved: 5    │
│ docs about      │
│ POST /users     │
└────────┬────────┘
         │
         │ Documents + endpoint info
         ▼
┌─────────────────┐
│ Code Generator  │
│                 │
│ Template:       │
│ requests_post   │
│                 │
│ Generated:      │
│ def create_user │
│   (name, email):│
│   ...           │
└────────┬────────┘
         │
         │ validated_code
         ▼
┌─────────────────┐
│  Orchestrator   │
│                 │
│ Aggregates:     │
│ • Answer        │
│ • Sources       │
│ • Code          │
└────────┬────────┘
         │
         │ Final response
         ▼
User receives:
  • "To create a user, use POST /users..."
  • Code snippet (Python with requests)
  • Source citations [1][2][3]
```

---

## 🧩 Component Interactions

### Agent Communication

Agents communicate exclusively through `AgentState`:

```python
# Agent A modifies state
def agent_a_process(state: AgentState) -> AgentState:
    state["current_agent"] = "agent_a"
    state["processing_path"].append("agent_a")
    state["retrieved_documents"] = [...]
    return state

# Agent B reads state modified by Agent A
def agent_b_process(state: AgentState) -> AgentState:
    docs = state["retrieved_documents"]  # From Agent A
    state["current_agent"] = "agent_b"
    state["processing_path"].append("agent_b")
    state["generated_code"] = generate_from_docs(docs)
    return state
```

**No Direct Agent Communication**:
- ❌ `agent_b.call(agent_a.result)`
- ✅ `agent_b.process(state_from_agent_a)`

---

## 🔒 Error Handling

### Agent-Level Error Handling

All agents inherit error handling from `BaseAgent`:

```python
class BaseAgent(ABC):
    def __call__(self, state: AgentState) -> AgentState:
        """Wrapper with automatic error handling"""
        try:
            # Update processing path
            state = add_to_processing_path(state, self.name)
            state["current_agent"] = self.name

            # Call agent's process method
            result = self.process(state)

            # Log success
            self._logger.info(f"{self.name} processed successfully")
            return result

        except Exception as e:
            # Log error
            self._logger.error(f"{self.name} failed", error=str(e))

            # Set error in state
            return set_error(
                state,
                agent=self.name,
                error_type="processing_error",
                message=str(e),
                recoverable=True
            )
```

### Error State

```python
{
    "query": "original query",
    "error": {
        "agent": "rag_agent",
        "error_type": "retrieval_error",
        "message": "ChromaDB connection failed",
        "recoverable": True,
        "timestamp": "2025-01-15T10:30:00"
    }
}
```

---

## 📈 Performance Considerations

### Parallel Execution (Future)

Currently sequential, but LangGraph supports parallel execution:

```python
# Sequential (current)
START → QueryAnalyzer → RAG → Code → END
  (total: 6-9 seconds)

# Parallel (future optimization)
                      ┌─► RAG (3s) ────┐
START → QueryAnalyzer ─┤                ├─► Aggregate → END
                      └─► DocAnalyzer (2s)
  (total: 5-6 seconds with parallelization)
```

### Caching Strategy (Future)

```
Query → [Cache Check] ─┬─ HIT → Return cached result
                       └─ MISS → Execute agents → Cache result
```

---

## 🎯 Design Principles

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Stateless Agents**: All context in `AgentState`, no internal agent state
3. **Composability**: Agents can be chained in any order
4. **Testability**: Each agent testable in isolation
5. **Error Resilience**: Graceful degradation with fallbacks
6. **Observable**: All operations logged and traceable

---

## 📚 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Orchestration | LangGraph | Agent coordination & routing |
| State Management | TypedDict | Shared state between agents |
| LLM | Ollama (DeepSeek Coder) | Intent classification, synthesis |
| Vector DB | ChromaDB | Document retrieval |
| Code Templates | Jinja2 | Code generation templates |
| Testing | pytest | Unit & integration tests |
| Logging | structlog | Structured logging |
| Validation | ast (stdlib) | Python syntax validation |

---

## 🔮 Future Enhancements

### Week 2+ Additions

1. **Agent Chaining**: RAG → Code Generator in single flow
2. **Fallback Routing**: If agent fails, try alternative path
3. **Conversation Memory**: Multi-turn conversations with context
4. **Parallel Execution**: Run multiple agents simultaneously
5. **Agent Self-Correction**: Retry with improved prompts on failure
6. **Human-in-the-Loop**: Request user input for ambiguous queries

---

## 📖 Reading the Code

### Entry Points

1. **State Definitions**: `src/agents/state.py`
2. **Base Agent**: `src/agents/base_agent.py`
3. **Individual Agents**: `src/agents/query_analyzer.py`, etc.
4. **Tests**: `tests/test_agents/test_*.py`

### Recommended Reading Order

```
1. src/agents/state.py         (understand data structures)
2. src/agents/base_agent.py    (understand agent interface)
3. src/agents/query_analyzer.py (simple agent example)
4. src/agents/rag_agent.py     (complex agent with LLM)
5. src/agents/code_agent.py    (template-based generation)
6. src/agents/doc_analyzer.py  (rule-based analysis)
```

---

**Architecture Status**: ✅ **Week 1 Complete**
**Next**: Orchestrator Implementation (Week 2)
