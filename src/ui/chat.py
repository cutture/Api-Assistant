"""
Streamlit chat interface component.
Handles message display, input, and streaming responses.
"""

import streamlit as st
from typing import Generator, Optional, Callable, Union
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a chat message."""
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[list[dict]] = None  # RAG sources if any


def init_chat_state() -> None:
    """Initialize chat-related session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "processing" not in st.session_state:
        st.session_state.processing = False


def render_chat(
    on_message: Optional[Callable[[str], Generator[str, None, None]]] = None,
    placeholder_text: str = "Ask about your APIs...",
) -> None:
    """
    Render the chat interface.

    Args:
        on_message: Callback that takes user message and returns response generator.
        placeholder_text: Placeholder for the input field.
    """
    init_chat_state()

    # Display chat history
    for message in st.session_state.messages:
        render_message(message)

    # Chat input
    if prompt := st.chat_input(placeholder_text, disabled=st.session_state.processing):
        # Add user message
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)
        
        # Display user message
        render_message(user_message)

        # Generate and display assistant response
        if on_message:
            st.session_state.processing = True
            
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    # Stream the response
                    for chunk in on_message(prompt):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    
                    # Final response without cursor
                    response_placeholder.markdown(full_response)
                    
                    # Save assistant message
                    assistant_message = {"role": "assistant", "content": full_response}
                    st.session_state.messages.append(assistant_message)
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    response_placeholder.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )
                
                finally:
                    st.session_state.processing = False


def render_message(message: Union[dict, Message]) -> None:
    """
    Render a single chat message.

    Args:
        message: The message to render (dict or Message object).
    """
    # Handle both dict and Message object formats
    if isinstance(message, dict):
        role = message.get("role", "user")
        content = message.get("content", "")
        sources = message.get("sources")
    else:
        role = message.role
        content = message.content
        sources = getattr(message, "sources", None)
    
    with st.chat_message(role):
        st.markdown(content)
        
        # Show sources if available (for RAG responses)
        if sources:
            with st.expander("📚 Sources", expanded=False):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"""
                    **Source {i}**: `{source.get('path', 'Unknown')} {source.get('method', '')}`
                    
                    Score: {source.get('score', 0):.2%}
                    """)
                    if source.get('content'):
                        st.code(source['content'][:500] + "..." if len(source.get('content', '')) > 500 else source.get('content', ''), language="markdown")
                    st.divider()


def render_code_response(code: str, language: str = "python") -> None:
    """
    Render a code block with copy button.

    Args:
        code: The code to display.
        language: Programming language for syntax highlighting.
    """
    st.code(code, language=language, line_numbers=True)


def render_sources(sources: list[dict]) -> None:
    """
    Render RAG sources in an expandable section.

    Args:
        sources: List of source documents with metadata.
    """
    if not sources:
        return
    
    with st.expander(f"📚 Sources ({len(sources)} relevant documents)", expanded=False):
        for i, source in enumerate(sources, 1):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Endpoint info
                path = source.get("metadata", {}).get("path", "Unknown")
                method = source.get("metadata", {}).get("method", "")
                st.markdown(f"**{i}. `{method} {path}`**")
            
            with col2:
                # Relevance score
                score = source.get("score", 0)
                st.metric("Relevance", f"{score:.0%}")
            
            # Content preview
            content = source.get("content", "")
            if content:
                preview = content[:300] + "..." if len(content) > 300 else content
                st.text(preview)
            
            st.divider()


def clear_chat_history() -> None:
    """Clear all chat messages."""
    st.session_state.messages = []


def add_system_message(content: str) -> None:
    """
    Add a system/info message to the chat.

    Args:
        content: Message content.
    """
    # System messages are displayed but not sent to LLM
    st.info(content)
