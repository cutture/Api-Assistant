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
from src.core.monitoring import initialize_monitoring
from src.core.logging_config import (
    configure_development_logging,
    configure_production_logging,
    set_request_id,
)
from src.parsers.openapi_parser import OpenAPIParser
from src.agents import create_supervisor
from src.ui.sidebar import render_sidebar
from src.ui.chat import render_chat, init_chat_state, clear_chat_history
import structlog


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


@st.cache_resource
def get_supervisor():
    """Get cached Supervisor agent."""
    # Initialize logging if not already done
    if settings.debug:
        configure_development_logging()
    else:
        configure_production_logging()

    # Initialize monitoring if not already done
    initialize_monitoring()

    vector_store = get_vector_store()  # VectorStore instance is returned directly

    # create_supervisor now handles creating specialized LLM clients internally
    # based on LLM_PROVIDER setting (ollama or groq)
    return create_supervisor(vector_store=vector_store)


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


# -----  Agent Pipeline -----

def _build_conversation_context(messages: list) -> str:
    """
    Build intelligent conversation context with first 3, summary, and last 3 exchanges.

    Strategy:
    - If <= 12 messages (6 exchanges): Include all
    - If > 12 messages: First 6 + Summary of middle + Last 6

    Args:
        messages: List of conversation messages

    Returns:
        Formatted conversation context string
    """
    if len(messages) <= 1:
        return ""

    # If conversation is short (<=6 exchanges), include all
    if len(messages) <= 12:
        context_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")[:200]
            if role == "user":
                context_parts.append(f"User: {content}")
            elif role == "assistant":
                context_parts.append(f"Assistant: {content}")

        if context_parts:
            return "\n".join(context_parts) + "\n\nCurrent question: "

    # For long conversations: First 3 + Summary + Last 3
    else:
        context_parts = []

        # First 3 exchanges (6 messages)
        first_messages = messages[:6]
        context_parts.append("=== Initial Conversation ===")
        for msg in first_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")[:200]
            if role == "user":
                context_parts.append(f"User: {content}")
            elif role == "assistant":
                context_parts.append(f"Assistant: {content}")

        # Summary of middle conversations
        middle_messages = messages[6:-6]
        if middle_messages:
            summary = _summarize_conversation(middle_messages)
            context_parts.append(f"\n=== Summary of {len(middle_messages)//2} middle exchanges ===")
            context_parts.append(summary)

        # Last 3 exchanges (6 messages)
        last_messages = messages[-6:]
        context_parts.append("\n=== Recent Conversation ===")
        for msg in last_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")[:200]
            if role == "user":
                context_parts.append(f"User: {content}")
            elif role == "assistant":
                context_parts.append(f"Assistant: {content}")

        return "\n".join(context_parts) + "\n\nCurrent question: "


def _summarize_conversation(messages: list) -> str:
    """
    Summarize middle conversation exchanges using LLM.

    Args:
        messages: List of messages to summarize

    Returns:
        Summary string
    """
    if not messages:
        return "No middle conversation to summarize."

    # Build conversation text
    conversation_text = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            conversation_text.append(f"User: {content}")
        elif role == "assistant":
            conversation_text.append(f"Assistant: {content}")

    conversation = "\n".join(conversation_text)

    # Use LLM to summarize
    try:
        llm_client = get_llm_client()
        summary_prompt = f"""Summarize the following conversation exchanges concisely.
Focus on key topics discussed, questions asked, and important context.
Keep the summary under 150 words.

Conversation:
{conversation}

Provide a brief summary:"""

        summary = llm_client.generate(
            prompt=summary_prompt,
            system_prompt="You are a concise conversation summarizer. Extract key points and context.",
            temperature=0.3,
            max_tokens=300,
        )

        return summary.strip()

    except Exception as e:
        # Fallback: Simple summary
        num_exchanges = len(messages) // 2
        return f"The user asked {num_exchanges} questions about API endpoints, authentication, and code generation. The assistant provided relevant information from the documentation."


def generate_response_with_agents(user_query: str) -> dict:
    """
    Generate a response using the Supervisor agent orchestration.

    Args:
        user_query: The user's question.

    Returns:
        Dict with response, sources, code_snippets, and agent metadata
    """
    # Set request ID for tracking
    request_id = set_request_id()
    logger = structlog.get_logger(__name__)

    try:
        supervisor = get_supervisor()

        # Build intelligent conversation context
        conversation_context = ""
        if "messages" in st.session_state and len(st.session_state.messages) > 1:
            conversation_context = _build_conversation_context(st.session_state.messages)

        # Combine context with current query
        contextualized_query = conversation_context + user_query if conversation_context else user_query

        logger.info(
            "user_query_received",
            query_length=len(user_query),
            has_context=bool(conversation_context),
        )

        # Process query through supervisor
        result = supervisor.process(contextualized_query)

        # Extract response and metadata
        response_data = {
            "response": result.get("response", "No response generated."),
            "sources": result.get("retrieved_documents", []),
            "code_snippets": result.get("code_snippets", []),
            "intent": result.get("intent_analysis", {}),
            "processing_path": result.get("processing_path", []),
            "error": result.get("error"),
        }

        logger.info(
            "query_processed_successfully",
            intent=result.get("intent_analysis", {}).get("intent"),
            sources_count=len(response_data["sources"]),
            code_snippets_count=len(response_data["code_snippets"]),
        )

        return response_data

    except Exception as e:
        logger.error(
            "query_processing_failed",
            error_type=type(e).__name__,
            error_message=str(e),
        )

        return {
            "response": f"❌ Error processing query: {str(e)}\n\nPlease make sure Ollama is running with the model loaded.",
            "sources": [],
            "code_snippets": [],
            "error": {"message": str(e)},
            "processing_path": [],
        }


def generate_response(user_query: str) -> Generator[str, None, None]:
    """
    Generate a response to the user query using the agent system.

    This is a compatibility wrapper that yields text chunks for the chat UI.

    Args:
        user_query: The user's question.

    Yields:
        Response chunks for streaming.
    """
    # Process with agents
    result = generate_response_with_agents(user_query)

    # Store result in session state for rendering
    st.session_state.last_agent_result = result

    # Yield the response text
    response = result.get("response", "")
    yield response


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
