"""
API Integration Assistant - Main Streamlit Application
Entry point for the application.
"""

import streamlit as st
from typing import Generator
from pathlib import Path

# Configure page - must be first Streamlit command
st.set_page_config(
    page_title="API Integration Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.config import settings
from src.core.embeddings import EmbeddingService
from src.core.vector_store import VectorStore
from src.core.llm_client import LLMClient
from src.parsers.openapi_parser import OpenAPIParser
from src.ui.sidebar import render_sidebar
from src.ui.chat import render_chat, init_chat_state, clear_chat_history


# ----- Initialize Services (cached) -----

@st.cache_resource
def get_embedding_service() -> EmbeddingService:
    """Get cached embedding service."""
    return EmbeddingService()


@st.cache_resource
def get_vector_store() -> VectorStore:
    """Get cached vector store."""
    return VectorStore()


@st.cache_resource
def get_llm_client() -> LLMClient:
    """Get cached LLM client."""
    return LLMClient()


@st.cache_resource
def get_openapi_parser() -> OpenAPIParser:
    """Get cached OpenAPI parser."""
    return OpenAPIParser()


# ----- File Processing -----

def process_uploaded_files(uploaded_files: list) -> None:
    """
    Process uploaded API specification files.
    
    Args:
        uploaded_files: List of Streamlit uploaded file objects.
    """
    if not uploaded_files:
        return
    
    vector_store = get_vector_store()
    parser = get_openapi_parser()
    
    progress_bar = st.progress(0, text="Processing files...")
    total_files = len(uploaded_files)
    total_endpoints = 0
    
    for i, uploaded_file in enumerate(uploaded_files):
        progress_bar.progress(
            (i + 1) / total_files,
            text=f"Processing: {uploaded_file.name}"
        )
        
        try:
            # Read file content
            content = uploaded_file.read().decode("utf-8")
            
            # Check if we can parse it
            if not parser.can_parse(content):
                st.warning(f"⚠️ Cannot parse {uploaded_file.name} - not a valid OpenAPI/Swagger spec")
                continue
            
            # Parse the spec
            parsed_doc = parser.parse(content, source_file=uploaded_file.name)
            
            # Prepare documents for vector store
            documents = []
            
            # Add API summary chunk
            documents.append({
                "content": parsed_doc.get_summary_chunk(),
                "metadata": parsed_doc.get_summary_metadata(),
            })
            
            # Add endpoint chunks
            for endpoint in parsed_doc.endpoints:
                documents.append({
                    "content": endpoint.to_chunk_content(),
                    "metadata": endpoint.to_metadata(),
                })
            
            # Store in vector database
            vector_store.add_documents(documents)
            total_endpoints += len(parsed_doc.endpoints)
            
            st.success(f"✅ Processed {uploaded_file.name}: {len(parsed_doc.endpoints)} endpoints")
            
        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
    
    progress_bar.empty()
    
    # Update stats in session state
    st.session_state.vector_store_stats = vector_store.get_stats()
    
    st.success(f"🎉 Processing complete! Added {total_endpoints} endpoints to the knowledge base.")


def clear_data() -> None:
    """Clear all stored data."""
    vector_store = get_vector_store()
    vector_store.clear()
    clear_chat_history()
    st.session_state.vector_store_stats = {"document_count": 0}
    st.success("🗑️ All data cleared!")


# ----- RAG Pipeline -----

def generate_response(user_query: str) -> Generator[str, None, None]:
    """
    Generate a response to the user query using RAG.
    
    Args:
        user_query: The user's question.
        
    Yields:
        Response chunks for streaming.
    """
    vector_store = get_vector_store()
    llm_client = get_llm_client()
    
    # Get current settings from session state
    sidebar_settings = st.session_state.get("sidebar_settings", {})
    n_results = sidebar_settings.get("n_results", 5)
    temperature = sidebar_settings.get("temperature", 0.7)
    max_tokens = sidebar_settings.get("max_tokens", 2048)
    
    # Search for relevant context
    search_results = vector_store.search(user_query, n_results=n_results)
    
    # Build context from search results
    if search_results:
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"--- Document {i} (relevance: {result['score']:.0%}) ---\n{result['content']}")
        
        context = "\n\n".join(context_parts)
    else:
        context = "No relevant API documentation found in the knowledge base."
    
    # Build prompt
    system_prompt = """You are an expert API Integration Assistant. Your role is to help developers understand and integrate APIs.

Based on the provided API documentation context, answer the user's question accurately and helpfully.

Guidelines:
- Be concise but thorough
- Include code examples when relevant (use Python by default)
- Reference specific endpoints, parameters, and response schemas from the context
- If the context doesn't contain enough information, say so clearly
- Format code blocks properly with appropriate language tags

API Documentation Context:
{context}
""".format(context=context)

    user_prompt = f"Question: {user_query}"
    
    # Stream response from LLM
    try:
        for chunk in llm_client.generate_stream(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk
            
    except Exception as e:
        yield f"\n\n❌ Error generating response: {str(e)}\n\nPlease make sure Ollama is running with the model loaded."


# ----- Main Application -----

def main():
    """Main application entry point."""
    
    # Header
    st.title("🚀 API Integration Assistant")
    st.markdown("*Your AI-powered guide to API integrations*")
    
    # Initialize session state
    init_chat_state()
    
    if "vector_store_stats" not in st.session_state:
        vector_store = get_vector_store()
        st.session_state.vector_store_stats = vector_store.get_stats()
    
    # Render sidebar and get settings
    sidebar_settings = render_sidebar(
        on_file_upload=process_uploaded_files,
        on_clear_data=clear_data,
    )
    
    # Store settings in session state for access in generate_response
    st.session_state.sidebar_settings = sidebar_settings
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Quick stats
        stats = st.session_state.vector_store_stats
        doc_count = stats.get("document_count", 0)
        
        if doc_count == 0:
            st.info("""
            👋 **Welcome!** Get started by uploading your API documentation.
            
            **Supported formats:**
            - OpenAPI 3.x (JSON/YAML)
            - Swagger 2.0 (JSON/YAML)
            
            Upload files using the sidebar, then ask questions about your APIs!
            """)
        else:
            st.success(f"📚 **{doc_count} documents** indexed and ready for questions!")
    
    with col2:
        # Example queries
        with st.expander("💡 Example Questions", expanded=doc_count > 0):
            examples = [
                "What endpoints are available?",
                "How do I authenticate?",
                "Generate code to call the /users endpoint",
                "What parameters does POST /orders accept?",
                "Explain the response schema for GET /products",
            ]
            for example in examples:
                if st.button(example, key=f"example_{example}", use_container_width=True):
                    # Add to chat
                    st.session_state.messages.append({"role": "user", "content": example})
                    st.rerun()
    
    st.divider()
    
    # Chat interface
    render_chat(
        on_message=generate_response,
        placeholder_text="Ask about your APIs... (e.g., 'How do I authenticate?')",
    )


if __name__ == "__main__":
    main()
