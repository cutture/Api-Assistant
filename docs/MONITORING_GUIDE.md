# 📊 Monitoring & Observability Guide

Comprehensive guide for monitoring the API Integration Assistant using Langfuse.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Metrics Tracked](#metrics-tracked)
- [Integration with Agents](#integration-with-agents)
- [Dashboard & Analytics](#dashboard--analytics)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The monitoring system provides comprehensive observability for all agent operations using [Langfuse](https://langfuse.com/), an open-source LLM observability platform.

### Key Features

✅ **Automatic Tracing** - All agent operations are automatically traced
✅ **Latency Tracking** - Monitor operation execution times
✅ **Token Usage** - Track LLM token consumption
✅ **Routing Decisions** - Understand how queries are routed
✅ **Quality Metrics** - Monitor retrieval and generation quality
✅ **Error Tracking** - Capture and analyze failures
✅ **Zero Overhead** - Gracefully degrades when Langfuse is unavailable

---

## 🚀 Setup

### 1. Install Langfuse

The `langfuse` package is already in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Sign Up for Langfuse

Create a free account at [https://cloud.langfuse.com](https://cloud.langfuse.com)

1. Sign up for a free account
2. Create a new project
3. Go to **Settings → API Keys**
4. Copy your **Public Key** and **Secret Key**

### 3. Configure Environment Variables

Add your Langfuse credentials to `.env`:

```bash
# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional (default)
```

### 4. Verify Setup

```python
from src.core.monitoring import is_monitoring_enabled

if is_monitoring_enabled():
    print("✅ Monitoring is enabled!")
else:
    print("❌ Monitoring is disabled - check your credentials")
```

---

## ⚙️ Configuration

### MonitoringConfig Options

```python
from src.core.monitoring import MonitoringConfig, initialize_monitoring

config = MonitoringConfig(
    enabled=True,                      # Master switch
    langfuse_public_key="pk-lf-...",  # Or use env var
    langfuse_secret_key="sk-lf-...",  # Or use env var
    langfuse_host="https://cloud.langfuse.com",
    track_tokens=True,                 # Track LLM token usage
    track_latency=True,                # Track operation timing
    track_routing=True,                # Track routing decisions
    track_quality=True,                # Track retrieval quality
)

initialize_monitoring(config)
```

### Environment-Based Configuration

The system auto-initializes if environment variables are set:

```python
# No code needed - monitoring auto-starts if:
# - LANGFUSE_PUBLIC_KEY is set
# - LANGFUSE_SECRET_KEY is set
```

### Disable Monitoring

```python
# Option 1: Set enabled=False
config = MonitoringConfig(enabled=False)
initialize_monitoring(config)

# Option 2: Don't set environment variables
# Monitoring will be disabled automatically
```

---

## 💡 Usage

### 1. Tracing Agent Methods

Use the `@trace_agent` decorator to trace agent methods:

```python
from src.core.monitoring import trace_agent

class MyAgent(BaseAgent):
    @trace_agent(name="my_agent_process", metadata={"version": "1.0"})
    def process(self, state: AgentState) -> AgentState:
        # Your agent logic here
        return state
```

**What gets tracked:**
- Function inputs
- Function outputs
- Execution time
- Errors and stack traces
- Custom metadata

### 2. Tracking Custom Metrics

```python
from src.core.monitoring import track_metric

# Track any custom metric
track_metric(
    name="custom_score",
    value=0.95,
    metadata={"component": "evaluator"}
)
```

### 3. Tracking Routing Decisions

```python
from src.core.monitoring import track_routing_decision

track_routing_decision(
    query="How do I authenticate?",
    intent="authentication",
    confidence=0.95,
    selected_agent="rag_agent",
    metadata={"secondary_intents": ["general_question"]}
)
```

### 4. Tracking Retrieval Quality

```python
from src.core.monitoring import track_retrieval_quality

track_retrieval_quality(
    query="user authentication endpoints",
    num_docs=5,
    avg_score=0.82,
    top_score=0.95,
    metadata={"retrieval_method": "multi_query"}
)
```

### 5. Tracking Token Usage

```python
from src.core.monitoring import track_token_usage

track_token_usage(
    operation="query_analysis",
    prompt_tokens=150,
    completion_tokens=50,
    total_tokens=200,
    model="deepseek-coder:6.7b",
    metadata={"endpoint": "/analyze"}
)
```

### 6. Tracing Operations

Use context managers for custom operations:

```python
from src.core.monitoring import trace_operation

with trace_operation("document_indexing", metadata={"file": "api.yaml"}):
    # Index documents
    index_documents(docs)
    # Operation is automatically timed and traced
```

### 7. Flushing Data

Flush pending data before shutdown:

```python
from src.core.monitoring import flush_monitoring

# Before application exit
flush_monitoring()
```

---

## 📈 Metrics Tracked

### 1. Agent Execution Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `latency_ms` | Float | Agent execution time in milliseconds |
| `agent_name` | String | Name of the executed agent |
| `success` | Boolean | Whether execution succeeded |
| `error_type` | String | Type of error if failed |

### 2. Routing Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `intent` | String | Classified query intent |
| `confidence` | Float | Confidence score (0.0-1.0) |
| `selected_agent` | String | Agent selected for execution |
| `query_preview` | String | First 100 chars of query |

### 3. Retrieval Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `num_docs` | Integer | Number of documents retrieved |
| `avg_score` | Float | Average similarity score |
| `top_score` | Float | Highest similarity score |
| `retrieval_quality` | Float | Overall quality metric |

### 4. Token Usage Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `prompt_tokens` | Integer | Tokens in the prompt |
| `completion_tokens` | Integer | Tokens in the completion |
| `total_tokens` | Integer | Total tokens used |
| `model` | String | LLM model name |
| `operation` | String | Operation that used tokens |

---

## 🤖 Integration with Agents

### Query Analyzer Integration

```python
from src.agents.query_analyzer import QueryAnalyzer
from src.core.monitoring import trace_agent, track_routing_decision

class QueryAnalyzer(BaseAgent):
    @trace_agent(name="query_analyzer")
    def process(self, state: AgentState) -> AgentState:
        # ... analyze query ...

        # Track the routing decision
        track_routing_decision(
            query=state["query"],
            intent=intent_analysis.primary_intent,
            confidence=intent_analysis.confidence,
            selected_agent="query_analyzer"
        )

        return state
```

### RAG Agent Integration

```python
from src.agents.rag_agent import RAGAgent
from src.core.monitoring import trace_agent, track_retrieval_quality

class RAGAgent(BaseAgent):
    @trace_agent(name="rag_agent")
    def process(self, state: AgentState) -> AgentState:
        # ... retrieve documents ...

        if retrieved_docs:
            scores = [doc["score"] for doc in retrieved_docs]
            track_retrieval_quality(
                query=state["query"],
                num_docs=len(retrieved_docs),
                avg_score=sum(scores) / len(scores),
                top_score=max(scores)
            )

        return state
```

### Code Generator Integration

```python
from src.agents.code_agent import CodeGenerator
from src.core.monitoring import trace_agent, track_metric

class CodeGenerator(BaseAgent):
    @trace_agent(name="code_generator")
    def process(self, state: AgentState) -> AgentState:
        # ... generate code ...

        # Track code quality
        track_metric(
            "code_syntax_valid",
            1 if validation_result["valid"] else 0,
            metadata={"library": library}
        )

        return state
```

---

## 📊 Dashboard & Analytics

### Accessing the Dashboard

1. Go to [https://cloud.langfuse.com](https://cloud.langfuse.com)
2. Select your project
3. View traces, metrics, and analytics

### Key Dashboard Views

#### 1. Traces View
- See all agent executions
- Drill down into individual traces
- View input/output for each step
- Analyze execution time breakdown

#### 2. Metrics View
- Token usage over time
- Average latency trends
- Error rates
- Routing distribution

#### 3. Sessions View
- Group related queries
- Analyze user sessions
- Track conversation flows

#### 4. Analytics
- Custom dashboards
- Query performance
- Agent usage patterns
- Cost analysis (token-based)

---

## ✅ Best Practices

### 1. Use Meaningful Names

```python
# ✅ Good
@trace_agent(name="query_analyzer_with_caching")

# ❌ Bad
@trace_agent(name="process")
```

### 2. Add Context with Metadata

```python
@trace_agent(
    name="code_generator",
    metadata={
        "version": "2.0",
        "template_engine": "jinja2",
        "library": "requests"
    }
)
```

### 3. Track Quality Metrics

```python
# Track both success and quality
track_metric("generation_success", 1)
track_metric("code_quality_score", 0.95)
```

### 4. Use Context Managers for Operations

```python
# Automatically track timing and errors
with trace_operation("batch_indexing", metadata={"batch_size": 100}):
    process_batch(documents)
```

### 5. Flush on Shutdown

```python
import atexit
from src.core.monitoring import flush_monitoring

# Ensure data is sent before exit
atexit.register(flush_monitoring)
```

### 6. Monitor Critical Paths

Focus monitoring on:
- High-latency operations
- LLM calls (expensive)
- User-facing endpoints
- Error-prone components

---

## 🔧 Troubleshooting

### Monitoring Not Working

**Check 1: Langfuse Installed**
```bash
pip list | grep langfuse
```

**Check 2: Credentials Set**
```python
import os
print(os.getenv("LANGFUSE_PUBLIC_KEY"))  # Should not be None
print(os.getenv("LANGFUSE_SECRET_KEY"))  # Should not be None
```

**Check 3: Monitoring Enabled**
```python
from src.core.monitoring import is_monitoring_enabled
print(is_monitoring_enabled())  # Should be True
```

### No Data in Dashboard

**Issue:** Traces not appearing in Langfuse dashboard

**Solution:**
```python
# Manually flush data
from src.core.monitoring import flush_monitoring
flush_monitoring()
```

Wait a few minutes for data to appear (Langfuse batches data).

### Performance Impact

**Issue:** Monitoring adds latency

**Solution:**
```python
# Disable non-critical tracking
config = MonitoringConfig(
    track_tokens=False,       # Disable if not needed
    track_quality=False,      # Disable if not needed
)
```

Langfuse has minimal overhead (<5ms per trace typically).

### Testing Without Langfuse

**Issue:** Want to test without Langfuse installed

**Solution:**
```python
# Monitoring gracefully degrades
# All functions become no-ops when LANGFUSE_AVAILABLE = False
config = MonitoringConfig(enabled=False)
initialize_monitoring(config)
```

---

## 📚 Additional Resources

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse Python SDK](https://langfuse.com/docs/sdk/python)
- [Langfuse Dashboard Guide](https://langfuse.com/docs/dashboard)
- [LangChain + Langfuse Integration](https://langfuse.com/docs/integrations/langchain)

---

## 🎓 Examples

### Example 1: Complete Agent with Monitoring

```python
from src.agents.base_agent import BaseAgent
from src.agents.state import AgentState
from src.core.monitoring import trace_agent, track_metric, trace_operation

class MyCustomAgent(BaseAgent):
    @trace_agent(name="custom_agent", metadata={"version": "1.0"})
    def process(self, state: AgentState) -> AgentState:
        query = state.get("query", "")

        # Trace sub-operations
        with trace_operation("data_preparation"):
            prepared_data = self._prepare_data(query)

        with trace_operation("llm_call"):
            result = self._call_llm(prepared_data)

        # Track quality
        track_metric("result_confidence", 0.92)

        state["response"] = result
        return state
```

### Example 2: Monitoring in Main Application

```python
from src.core.monitoring import initialize_monitoring, flush_monitoring
import atexit

# Initialize at startup
initialize_monitoring()

# Register cleanup
atexit.register(flush_monitoring)

# Use agents normally - monitoring is automatic
supervisor = create_supervisor(llm_client, vector_store)
result = supervisor.process("How to authenticate?")
```

---

## 📊 Monitoring Checklist

Before deploying to production:

- [ ] Langfuse credentials configured
- [ ] Monitoring initialized in main app
- [ ] All agents have `@trace_agent` decorators
- [ ] Critical operations use `trace_operation`
- [ ] Quality metrics tracked
- [ ] Token usage tracked for cost monitoring
- [ ] Flush registered for application shutdown
- [ ] Dashboard configured with alerts
- [ ] Team has access to Langfuse dashboard

---

**Last Updated:** December 25, 2024
**Version:** 1.0
**Author:** API Integration Assistant Team
