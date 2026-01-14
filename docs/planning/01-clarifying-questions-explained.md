# Intelligent Self-Validating Coding Agent: Design Decisions Guide

This document provides detailed explanations, pros/cons, and recommendations for each design decision to help you make informed choices.

---

## Table of Contents
1. [Architecture & Integration Strategy](#1-architecture--integration-strategy)
2. [LLM Strategy & Cost Optimization](#2-llm-strategy--cost-optimization)
3. [Container Execution Environment](#3-container-execution-environment)
4. [Language Support Priority](#4-language-support-priority)
5. [Repository Integration](#5-repository-integration)
6. [Validation Loop Behavior](#6-validation-loop-behavior)
7. [User Experience](#7-user-experience)
8. [Data & State Management](#8-data--state-management)

---

## 1. Architecture & Integration Strategy

### Q1.1: How should this feature integrate with the existing system?

#### Option A: Extend Existing Multi-Agent System
**What it means:** Add new agents (CodeExecutionAgent, ValidationAgent, TestGeneratorAgent) to the current LangGraph supervisor in `src/agents/supervisor.py`. The existing query analyzer routes requests to these new agents alongside RAG, Code, and Doc agents.

**Pros:**
- Unified codebase - single system to maintain
- Reuses existing infrastructure (vector store, session management, auth)
- Shared context between documentation Q&A and code generation
- Lower initial development effort
- Users have one interface for everything

**Cons:**
- Increased complexity in supervisor routing logic
- Risk of destabilizing existing working features
- Harder to scale independently (code execution needs more resources)
- Testing becomes more complex

**Production Consideration:** Simpler deployment but harder to scale code execution independently.

#### Option B: Separate Microservice with Shared Backend
**What it means:** Create a new FastAPI service (`coding-agent-service`) that handles code generation/execution. It shares the same database and vector store but runs as a separate container. Communication via internal API calls.

**Pros:**
- Independent scaling (run more execution containers during peak)
- Isolated failures - code execution crashes don't affect main app
- Cleaner separation of concerns
- Easier to apply different security policies
- Can use different resource limits

**Cons:**
- More complex deployment (multiple services)
- Network latency between services
- Need to handle service discovery
- Duplicated auth logic or shared auth service needed

**Production Consideration:** Better for production scaling but more DevOps complexity.

#### Option C: Plugin Architecture
**What it means:** Design a plugin system where the coding agent is a loadable module. Users can enable/disable it. The main app provides hooks, and the plugin registers its capabilities.

**Pros:**
- Most flexible - users choose what features to enable
- Easier to add more features later as plugins
- Clean boundaries between features
- Can distribute plugins separately

**Cons:**
- Highest initial development effort
- Need to design plugin API carefully
- Version compatibility challenges
- Over-engineering for current needs

**Production Consideration:** Best long-term flexibility but highest upfront investment.

**RECOMMENDATION:** **Option A (Extend Existing)** for MVP, then refactor to **Option B** when scaling becomes necessary. This gives you fastest time-to-market while keeping a clear migration path.

---

### Q1.2: Should the coding agent share sessions with the existing chat?

#### Option A: Unified Sessions
**What it means:** A single session contains both documentation Q&A and code generation history. Users can ask "What's the auth endpoint?" then say "Generate code for that" in the same conversation.

**Pros:**
- Seamless user experience
- Context carries over naturally
- Single session management system
- Users don't need to switch contexts

**Cons:**
- Sessions become larger (more tokens/storage)
- Mixed concerns in session history
- Harder to implement session-specific features

**RECOMMENDATION:** **Unified Sessions** - the context sharing is valuable for users.

#### Option B: Separate Session Types
**What it means:** Code generation has its own session type. Users explicitly start a "coding session" separate from Q&A sessions.

**Pros:**
- Cleaner session data
- Can optimize each session type differently
- Easier to track usage per feature

**Cons:**
- Users must switch between session types
- Can't easily reference Q&A context in code generation
- More UI complexity

**RECOMMENDATION:** **Unified Sessions** for better UX.

---

### Q1.3: Database strategy for code execution metadata?

#### Option A: Extend Existing SQLite
**What it means:** Add new tables to the current SQLite database for code executions, test results, validation history.

**Pros:**
- Simple - one database to manage
- Existing backup/migration processes work
- No new infrastructure

**Cons:**
- SQLite has concurrency limitations
- Large execution logs may bloat database
- Not ideal for high-volume writes

**Production Consideration:** Works fine for moderate usage (< 1000 executions/day).

#### Option B: Separate PostgreSQL for Execution Data
**What it means:** Keep user/session data in SQLite, but use PostgreSQL for execution logs, test results, and metrics.

**Pros:**
- Better concurrency handling
- Better for analytics queries
- Can handle high-volume execution data
- Production-grade reliability

**Cons:**
- Additional infrastructure to manage
- Need connection pooling
- Higher hosting costs

**Production Consideration:** Better for production scale but adds complexity.

#### Option C: Hybrid with Redis for Hot Data
**What it means:** Use Redis for active execution state (currently running, recent results), SQLite for user data, and optionally PostgreSQL for historical analytics.

**Pros:**
- Fastest access to active execution data
- Good for real-time status updates
- Can handle high concurrency

**Cons:**
- Most complex setup
- Need Redis hosting
- Data synchronization challenges

**RECOMMENDATION:** **Option A (Extend SQLite)** for MVP. Monitor usage and migrate to **Option B** if you exceed 500+ daily executions consistently.

---

## 2. LLM Strategy & Cost Optimization

### Q2.1: LLM routing strategy for cost optimization?

#### Option A: Task-Based Routing (Recommended)
**What it means:** Different LLMs for different tasks based on complexity:
- **Simple tasks** (syntax fixes, small functions): DeepSeek or local Ollama (~$0.001/request)
- **Medium tasks** (API integrations, class generation): Groq Llama 3.3 70B (~$0.01/request)
- **Complex tasks** (architecture, multi-file): Claude/GPT-4 (~$0.10/request)

**Pros:**
- Optimal cost/quality balance
- Can reduce costs by 80-90% for simple tasks
- Quality maintained where it matters

**Cons:**
- Need task classification logic
- Some misclassifications possible
- More complex to tune

**Production Consideration:** Significant cost savings at scale.

#### Option B: User-Selectable Model
**What it means:** Let users choose the model per request: "Fast & Cheap", "Balanced", "Best Quality".

**Pros:**
- User control and transparency
- Simple to implement
- Users understand cost tradeoffs

**Cons:**
- Users may not know best choice
- Inconsistent results
- More UI complexity

#### Option C: Quality-Based Fallback
**What it means:** Always start with cheapest model, automatically escalate to better model if output fails validation.

**Pros:**
- Automatic optimization
- No user decision needed
- Always gets working code eventually

**Cons:**
- May waste time on cheap model for complex tasks
- Total cost could exceed direct premium model use
- Longer time to completion

**RECOMMENDATION:** **Option A (Task-Based)** with **Option B** as override. Classify automatically but let power users choose.

---

### Q2.2: How to handle LLM provider failover?

#### Option A: Priority-Based Fallback Chain
**What it means:** Define order: Groq → DeepSeek → Ollama → OpenAI. If primary fails, try next.

```
Primary: Groq (fast, cheap)
    ↓ (if fails/rate-limited)
Fallback 1: DeepSeek
    ↓ (if fails)
Fallback 2: Local Ollama
    ↓ (if fails)
Fallback 3: OpenAI (expensive but reliable)
```

**Pros:**
- Predictable behavior
- Easy to understand and debug
- Can optimize for cost (cheapest first)

**Cons:**
- May hit rate limits sequentially
- Latency adds up on failures

**RECOMMENDATION:** **Option A** - simple and effective.

#### Option B: Parallel Racing
**What it means:** Send request to multiple providers simultaneously, use first response.

**Pros:**
- Lowest latency
- Automatic provider selection

**Cons:**
- Wasteful (pay for unused responses)
- Complex to implement
- Higher costs

#### Option C: Health-Based Routing
**What it means:** Track provider health scores, route to healthiest available provider.

**Pros:**
- Avoids known-bad providers
- Adapts to outages automatically

**Cons:**
- Need health monitoring system
- More infrastructure

**RECOMMENDATION:** **Option A (Priority-Based)** for simplicity.

---

### Q2.3: Local model support priority?

#### Option A: Ollama as Primary Local Option
**What it means:** Support Ollama for local model execution. Users with GPU can run models locally for free.

**Supported models via Ollama:**
- CodeLlama 34B (code-specialized)
- DeepSeek Coder 33B
- Llama 3 70B (general)

**Pros:**
- Free execution (no API costs)
- Privacy (code never leaves machine)
- No rate limits
- Works offline

**Cons:**
- Requires powerful hardware (16GB+ VRAM for good models)
- Slower than cloud APIs
- User setup required

**RECOMMENDATION:** **Support Ollama** as optional local provider. Many developers have capable GPUs.

#### Option B: No Local Support Initially
**What it means:** Only cloud providers for MVP, add local later.

**Pros:**
- Faster MVP development
- Consistent experience for all users

**Cons:**
- Higher costs for users
- No offline capability

**RECOMMENDATION:** Include **Ollama support** from start - it's already in your codebase.

---

## 3. Container Execution Environment

### Q3.1: Container orchestration approach?

#### Option A: Docker-in-Docker (DinD)
**What it means:** Run Docker daemon inside your Cloud Run container. Code execution containers spawn as siblings.

**Pros:**
- Full Docker API access
- Can build custom images
- Familiar Docker workflow

**Cons:**
- Security concerns (privileged containers)
- Cloud Run doesn't support privileged mode
- Complex networking

**Cloud Run Compatible:** NO - requires privileged mode.

#### Option B: Google Cloud Run Jobs
**What it means:** Each code execution spawns a Cloud Run Job. Jobs run in isolated containers with defined resource limits.

**Pros:**
- Native GCP integration
- Strong isolation
- No privileged containers needed
- Pay only for execution time
- Built-in timeout handling

**Cons:**
- Cold start latency (2-5 seconds)
- Limited to GCP
- Job creation has API overhead

**Cloud Run Compatible:** YES - recommended for your setup.

#### Option C: Kubernetes Jobs (GKE)
**What it means:** Use GKE cluster with Kubernetes Jobs for execution.

**Pros:**
- Maximum flexibility
- Can run any container
- Good isolation

**Cons:**
- Need GKE cluster (significant cost)
- More complex operations
- Overkill for this use case

**Cloud Run Compatible:** Requires separate GKE cluster.

#### Option D: Firecracker microVMs
**What it means:** Use Firecracker (AWS Lambda's technology) for ultra-fast, secure microVMs.

**Pros:**
- Sub-100ms cold starts
- Strong security isolation
- Efficient resource usage

**Cons:**
- Complex to set up on GCP
- Need dedicated compute instances
- Operational overhead

**RECOMMENDATION:** **Option B (Cloud Run Jobs)** for your GCP setup. It's native, secure, and cost-effective.

---

### Q3.2: Pre-built images vs dynamic image building?

#### Option A: Pre-built Language Images (Recommended)
**What it means:** Create and maintain Docker images for each supported language:
- `api-assistant/python:3.11` (with common packages)
- `api-assistant/node:20` (with npm/yarn)
- `api-assistant/java:21` (with Maven/Gradle)
- `api-assistant/go:1.21`

**Pros:**
- Fast execution (no build time)
- Predictable environment
- Pre-installed common dependencies
- Easy to version and update

**Cons:**
- Need to maintain images
- May not have all user-needed packages
- Storage costs for images

**Production Consideration:** Best for production - predictable and fast.

#### Option B: Dynamic Image Building
**What it means:** Analyze code requirements, dynamically install dependencies before execution.

**Pros:**
- Flexible - any package available
- No image maintenance

**Cons:**
- Slow (pip install takes time)
- Unpredictable execution times
- Security risks from arbitrary packages

**RECOMMENDATION:** **Option A (Pre-built)** with ability to install additional packages at runtime for flexibility.

---

### Q3.3: Resource limits and timeout strategy?

#### Recommended Limits:
| Tier | CPU | Memory | Timeout | Use Case |
|------|-----|--------|---------|----------|
| Quick | 1 | 512MB | 30s | Simple scripts, unit tests |
| Standard | 2 | 2GB | 2min | API integrations, medium complexity |
| Heavy | 4 | 8GB | 10min | Data processing, complex builds |

**Timeout Strategy:**
- Default: 2 minutes (covers 95% of use cases)
- User can request extension up to 10 minutes
- Hard cap at 10 minutes to prevent runaway costs

**Cost Protection:**
- Daily execution limit per user (e.g., 100 executions)
- Monthly compute budget alerts
- Automatic suspension at budget threshold

**RECOMMENDATION:** Start with **Standard tier** as default, allow upgrades per-request.

---

## 4. Language Support Priority

### Q4.1: Which languages to support first?

#### Tier 1 (MVP) - Support These First:
| Language | Reason | Complexity |
|----------|--------|------------|
| **Python** | Most API work, your backend language | Low |
| **JavaScript/Node.js** | Universal, frontend + backend | Low |
| **TypeScript** | Growing adoption, type safety | Medium |

#### Tier 2 (Post-MVP):
| Language | Reason | Complexity |
|----------|--------|------------|
| **Java** | Enterprise APIs | Medium |
| **Go** | Cloud-native, microservices | Medium |
| **C#** | .NET ecosystem | Medium |

#### Tier 3 (Future):
| Language | Reason | Complexity |
|----------|--------|------------|
| **Rust** | Performance-critical | High |
| **PHP** | Legacy web APIs | Low |
| **Ruby** | Rails ecosystem | Low |

**RECOMMENDATION:** **Python + JavaScript/TypeScript** for MVP. These cover 80%+ of API integration use cases.

---

### Q4.2: Language detection strategy?

#### Option A: Explicit User Selection
**What it means:** User chooses target language from dropdown before code generation.

**Pros:**
- Clear intent
- No detection errors
- Simple implementation

**Cons:**
- Extra user step
- User might forget to select

#### Option B: Automatic Detection from Context
**What it means:** Analyze uploaded documents, URLs, and conversation to infer language:
- OpenAPI spec mentions Python SDK → Python
- User asks about Express.js → JavaScript
- Repository has package.json → Node.js

**Pros:**
- Seamless experience
- Smart context awareness

**Cons:**
- May guess wrong
- Need robust detection logic

#### Option C: Hybrid (Recommended)
**What it means:** Auto-detect with user confirmation. "I detected you're working with Python. Generate Python code? [Yes] [Change to...]"

**Pros:**
- Best of both worlds
- User stays in control
- Reduces errors

**Cons:**
- Extra confirmation step (minor)

**RECOMMENDATION:** **Option C (Hybrid)** - auto-detect but confirm with user.

---

## 5. Repository Integration

### Q5.1: Git integration depth?

#### Option A: Clone & Analyze Only (Read-Only)
**What it means:** Clone repos to understand context, never push changes. Generated code is provided to user to manually add.

**Pros:**
- Safest approach
- No risk of breaking user's repo
- Simple permissions (read-only)
- User maintains full control

**Cons:**
- Manual step for user to add code
- Can't run tests in repo context automatically

**Production Consideration:** Safest for production, recommended for MVP.

#### Option B: Full Git Integration (Read-Write)
**What it means:** Clone, create branches, commit generated code, optionally create PRs.

**Pros:**
- Seamless workflow
- Can run tests in repo context
- PR creation automation

**Cons:**
- Needs write permissions (security concern)
- Risk of unwanted commits
- Complex OAuth scopes
- Users may be hesitant to grant access

**Production Consideration:** Powerful but risky. Need very careful implementation.

#### Option C: PR-Only Integration
**What it means:** Can read repos and create PRs, but never push to existing branches.

**Pros:**
- Good balance of automation and safety
- PRs can be reviewed before merge
- Clear audit trail

**Cons:**
- Still needs write access for PRs
- More complex than read-only

**RECOMMENDATION:** **Option A (Read-Only)** for MVP. Add **Option C (PR-Only)** in v2 for power users.

---

### Q5.2: Which Git platforms to support?

#### Priority Order:
1. **GitHub** - Largest user base, best API, OAuth well-documented
2. **GitLab** - Strong enterprise presence, similar API
3. **Bitbucket** - Required for some enterprises
4. **Self-hosted** - Generic Git support (clone via URL)

**RECOMMENDATION:** **GitHub first**, generic Git clone for others. Add GitLab/Bitbucket OAuth later.

---

## 6. Validation Loop Behavior

### Q6.1: Maximum retry attempts for failing code?

#### Options Analysis:

| Max Retries | Pros | Cons |
|-------------|------|------|
| **3 retries** | Fast failure, low cost | May give up too early |
| **5 retries** | Good balance | Standard choice |
| **10 retries** | Thorough attempt | Can be expensive |
| **Unlimited** | Never gives up | Cost explosion risk |

**Recommended Strategy:**
```
Attempt 1: Generate code
Attempt 2-3: Fix based on test failures
Attempt 4-5: Try different approach (re-prompt)
After 5: Ask user for guidance
```

**RECOMMENDATION:** **5 retries** with escalating strategies, then human intervention.

---

### Q6.2: What should trigger a retry?

#### Option A: Test Failures Only
**What it means:** Only retry if automated tests fail.

**Pros:**
- Clear, objective criteria
- No subjective judgment

**Cons:**
- Doesn't catch all issues
- Need comprehensive tests

#### Option B: Multi-Signal Validation (Recommended)
**What it means:** Retry based on multiple signals:

| Signal | Weight | Example |
|--------|--------|---------|
| Test failures | High | Unit test assertions fail |
| Runtime errors | High | Exceptions, crashes |
| Lint errors | Medium | ESLint, Pylint violations |
| Type errors | Medium | TypeScript, mypy errors |
| Security issues | High | Detected vulnerabilities |
| Performance | Low | Exceeds time/memory limits |

**Pros:**
- Comprehensive quality check
- Catches more issues
- Produces better code

**Cons:**
- More complex implementation
- May be overly strict initially

**RECOMMENDATION:** **Option B (Multi-Signal)** - catches more issues.

---

### Q6.3: How to handle unfixable code?

**When code can't be fixed after max retries:**

#### Strategy:
1. **Provide partial solution** - Give user what works with clear notes on what doesn't
2. **Explain failure** - Clear message about what went wrong
3. **Suggest alternatives** - "Try breaking this into smaller pieces" or "This may need manual review"
4. **Offer human escalation** - "Would you like to describe the issue for manual debugging?"
5. **Save attempt history** - Let user see all attempts and errors

**RECOMMENDATION:** Always provide value even on failure. Partial solutions with explanations are better than just "Failed."

---

## 7. User Experience

### Q7.1: Execution visibility level?

#### Option A: Simple Status Only
**What it means:** Show: "Generating... → Running tests... → Complete!"

**Pros:**
- Clean, non-technical UI
- Less overwhelming for beginners

**Cons:**
- Hard to debug issues
- Users don't understand what's happening

#### Option B: Detailed Real-Time Logs
**What it means:** Stream execution output live:
```
[14:23:01] Starting container...
[14:23:03] Installing dependencies...
[14:23:15] Running pytest...
[14:23:16] test_auth.py::test_login PASSED
[14:23:16] test_auth.py::test_invalid_password PASSED
```

**Pros:**
- Full transparency
- Easy debugging
- Developers appreciate detail

**Cons:**
- Can be overwhelming
- More UI complexity

#### Option C: Progressive Disclosure (Recommended)
**What it means:** Show simple status by default with "Show details" expander.

```
[Generating code...] ████████░░ 80%
                     [▼ Show details]
```

**Pros:**
- Best of both worlds
- Clean default, detailed when needed
- Accommodates all user types

**Cons:**
- Slightly more UI work

**RECOMMENDATION:** **Option C (Progressive Disclosure)** - clean but powerful.

---

### Q7.2: How to present generated code?

#### Option A: Inline in Chat
**What it means:** Code appears in chat messages like current implementation.

**Pros:**
- Consistent with existing UI
- Conversational flow
- Simple implementation

**Cons:**
- Long code hard to read
- No editing capability
- Scrolling issues

#### Option B: Side Panel Editor
**What it means:** Code opens in a VS Code-like panel beside chat.

**Pros:**
- Better code viewing
- Syntax highlighting
- Can edit before using
- File tree for multi-file

**Cons:**
- More complex UI
- May not fit mobile

#### Option C: Modal Code Viewer
**What it means:** Code opens in a full-screen modal with tabs for multiple files.

**Pros:**
- Maximum space for code
- Good for complex output

**Cons:**
- Breaks chat flow
- Extra click to close

**RECOMMENDATION:** **Option B (Side Panel)** for desktop, **Option A (Inline)** for mobile.

---

## 8. Data & State Management

### Q8.1: How long to retain execution history?

#### Options:

| Retention | Storage Cost | User Value |
|-----------|--------------|------------|
| 7 days | Low | Limited history |
| 30 days | Medium | Good balance |
| 90 days | Higher | Full project history |
| Unlimited | Highest | Complete archive |

**Tiered Approach (Recommended):**
- **Free users:** 7 days
- **Registered users:** 30 days
- **Premium users:** 90 days
- **Execution logs:** Always trim to last 50 per user

**RECOMMENDATION:** **30 days** for registered users with option to "star" important executions for permanent retention.

---

### Q8.2: What execution data to store?

#### Minimum (Always Store):
- Execution ID, timestamp
- Input prompt
- Generated code (final version)
- Success/failure status
- Execution duration

#### Extended (Store if Space Allows):
- All retry attempts
- Test output logs
- Container resource usage
- LLM tokens used (for billing)

#### Optional (User-Deletable):
- Full container stdout/stderr
- Intermediate code versions
- Debug traces

**RECOMMENDATION:** Store **Minimum + Extended**, make **Optional** available but auto-delete after 7 days.

---

## Summary: Recommended Choices for Production

| Decision | Recommended Choice |
|----------|-------------------|
| Architecture | Extend existing (MVP) → Microservice (scale) |
| Sessions | Unified with existing chat |
| Database | SQLite (MVP) → PostgreSQL (scale) |
| LLM Routing | Task-based with user override |
| LLM Failover | Priority-based chain |
| Local Models | Support Ollama |
| Containers | Google Cloud Run Jobs |
| Images | Pre-built per language |
| Languages | Python + JS/TS first |
| Language Detection | Auto-detect with confirmation |
| Git Integration | Read-only (MVP) → PR-only (v2) |
| Git Platforms | GitHub first |
| Retries | 5 max with escalation |
| Validation | Multi-signal |
| UI Visibility | Progressive disclosure |
| Code Display | Side panel (desktop) |
| Retention | 30 days default |

---

## Next Steps

Once you've reviewed these options and made your choices, I will create:

1. **System Architecture Diagram** - Visual overview of all components
2. **Database Schema** - Tables for execution tracking
3. **API Endpoint Specifications** - New endpoints needed
4. **Sequence Diagrams** - Code generation and validation flows
5. **Implementation Phases** - Ordered development plan
6. **File/Folder Structure** - Where new code will live
7. **Risk Assessment** - Potential challenges and mitigations

Please review each section and let me know your preferences. You can respond with something like:
- "Q1.1: Option A"
- "Q3.1: Option B"
- Or ask for more details on any specific option.
