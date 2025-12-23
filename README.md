# 🚀 Enterprise API Integration Assistant

An AI-powered assistant that helps developers understand, document, and generate code for API integrations.

## ✨ Features

- **API Documentation Analysis**: Upload OpenAPI/Swagger specs and get instant insights
- **Code Generation**: Generate integration code in Python with best practices
- **RAG-Powered Q&A**: Ask questions about your APIs and get accurate answers
- **Documentation Gap Detection**: Identify missing or incomplete documentation
- **Local LLM Support**: Run entirely offline with Ollama

## 🛠️ Tech Stack

- **UI**: Streamlit
- **LLM**: Ollama (DeepSeek Coder) / Groq (cloud fallback)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector DB**: ChromaDB
- **Agent Framework**: LangGraph
- **API Parsing**: Prance + OpenAPI Spec Validator

## 📋 Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/download) with `deepseek-coder:6.7b` model
- Git

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/api-assistant.git
cd api-assistant
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
copy .env.example .env
# Edit .env with your settings (optional - defaults work for local development)
```

### 5. Start Ollama (if not running)

```bash
ollama serve
```

### 6. Run the application

```bash
streamlit run src/main.py
```

Open your browser to `http://localhost:8501`

## 📁 Project Structure

```
api-assistant/
├── src/
│   ├── main.py              # Streamlit entry point
│   ├── config.py            # Configuration management
│   ├── core/                # Core business logic
│   │   ├── embeddings.py    # Embedding service
│   │   ├── vector_store.py  # ChromaDB operations
│   │   └── llm_client.py    # LLM abstraction
│   ├── parsers/             # API spec parsers
│   │   └── openapi_parser.py
│   ├── agents/              # LangGraph agents
│   │   ├── orchestrator.py  # Supervisor agent
│   │   ├── rag_agent.py     # Retrieval agent
│   │   └── code_agent.py    # Code generation
│   └── ui/                  # Streamlit components
│       ├── chat.py
│       └── sidebar.py
├── data/
│   ├── chroma_db/           # Vector database storage
│   └── uploads/             # User uploaded files
├── tests/                   # Unit tests
├── docker/                  # Docker configuration
├── requirements.txt
├── .env.example
└── README.md
```

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 🐳 Docker Deployment

```bash
cd docker
docker-compose up -d
```

## 📝 Usage Examples

### Upload an API Spec

1. Click "Upload API Spec" in the sidebar
2. Select your OpenAPI/Swagger JSON or YAML file
3. Wait for processing to complete

### Ask Questions

- "How do I authenticate with this API?"
- "Generate Python code to call the /users endpoint"
- "What are all the available endpoints?"
- "Explain the response schema for GET /orders"

## 🗺️ Roadmap

- [x] Phase 1: RAG Foundation
- [ ] Phase 2: Agent Layer
- [ ] Phase 3: Production Hardening
- [ ] Phase 4: Advanced Features (multimodal, etc.)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) for the excellent AI framework
- [Ollama](https://ollama.com/) for local LLM inference
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Streamlit](https://streamlit.io/) for rapid UI development
