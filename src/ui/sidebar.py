"""
Streamlit sidebar component for settings and file uploads.
"""

import streamlit as st
from pathlib import Path
from typing import Optional, Callable

from src.config import settings


def render_sidebar(
    on_file_upload: Optional[Callable] = None,
    on_clear_data: Optional[Callable] = None,
) -> dict:
    """
    Render the sidebar with settings and file upload.

    Args:
        on_file_upload: Callback when files are uploaded.
        on_clear_data: Callback when clear data is clicked.

    Returns:
        Dictionary with current sidebar state/settings.
    """
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # ----- Model Configuration -----
        st.subheader("🤖 Model")
        
        model_option = st.selectbox(
            "LLM Model",
            options=[
                settings.ollama_model,
                "phi3:mini",
                "codellama:7b",
                "llama3.2:3b",
            ],
            index=0,
            help="Select the language model to use",
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Higher = more creative, Lower = more focused",
        )
        
        with st.expander("Advanced Settings"):
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=256,
                max_value=4096,
                value=2048,
                step=256,
                help="Maximum response length",
            )
            
            n_results = st.slider(
                "RAG Results",
                min_value=1,
                max_value=10,
                value=5,
                help="Number of relevant chunks to retrieve",
            )

        st.divider()

        # ----- File Upload -----
        st.subheader("📄 API Documentation")
        
        uploaded_files = st.file_uploader(
            "Upload API Specs",
            type=settings.allowed_extensions_list,
            accept_multiple_files=True,
            help=f"Supported: {', '.join(settings.allowed_extensions_list)}",
        )
        
        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} file(s) selected")
            
            if st.button("🔄 Process Files", type="primary", use_container_width=True):
                if on_file_upload:
                    on_file_upload(uploaded_files)

        st.divider()

        # ----- Data Management -----
        st.subheader("🗄️ Data")
        
        # Show current stats if available
        if "vector_store_stats" in st.session_state:
            stats = st.session_state.vector_store_stats
            st.metric("Documents Indexed", stats.get("document_count", 0))
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Refresh", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                if on_clear_data:
                    on_clear_data()
                st.session_state.clear()
                st.rerun()

        st.divider()

        # ----- Info -----
        with st.expander("ℹ️ About"):
            st.markdown("""
            **API Integration Assistant**
            
            An AI-powered tool to help you understand and integrate APIs.
            
            **Features:**
            - Upload OpenAPI/Swagger specs
            - Ask questions about your APIs
            - Generate integration code
            - Identify documentation gaps
            
            Built with ❤️ using:
            - Streamlit
            - LangChain
            - ChromaDB
            - Ollama
            """)

    return {
        "model": model_option,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "n_results": n_results,
        "uploaded_files": uploaded_files,
    }


def render_upload_progress(total: int, current: int, filename: str) -> None:
    """
    Render upload/processing progress in sidebar.

    Args:
        total: Total number of files.
        current: Current file index.
        filename: Name of current file.
    """
    progress = current / total if total > 0 else 0
    st.sidebar.progress(progress, text=f"Processing: {filename}")


def render_sidebar_message(message: str, type: str = "info") -> None:
    """
    Render a message in the sidebar.

    Args:
        message: Message text.
        type: One of 'info', 'success', 'warning', 'error'.
    """
    with st.sidebar:
        if type == "success":
            st.success(message)
        elif type == "warning":
            st.warning(message)
        elif type == "error":
            st.error(message)
        else:
            st.info(message)
