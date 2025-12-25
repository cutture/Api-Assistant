"""
Streamlit chat interface component with agent activity display.
Handles message display, input, streaming responses, and agent metadata.
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
    agent_data: Optional[dict] = None  # Agent metadata


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
    Render the chat interface with agent activity display.

    Args:
        on_message: Callback that takes user message and returns response generator.
        placeholder_text: Placeholder for the input field.
    """
    init_chat_state()

    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        render_message(message, message_index=idx)

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
                # Show agent activity status
                with st.status("🤖 Processing your query...", expanded=True) as status:
                    st.write("🔍 Analyzing query intent...")

                    response_placeholder = st.empty()
                    full_response = ""

                    try:
                        # Stream the response
                        for chunk in on_message(prompt):
                            full_response += chunk
                            response_placeholder.markdown(full_response + "▌")

                        # Final response without cursor
                        response_placeholder.markdown(full_response)

                        # Update status to complete
                        status.update(label="✅ Response complete!", state="complete", expanded=False)

                        # Get agent metadata from session state
                        agent_result = st.session_state.get("last_agent_result", {})

                        # Save assistant message with metadata
                        assistant_message = {
                            "role": "assistant",
                            "content": full_response,
                            "agent_data": agent_result
                        }
                        st.session_state.messages.append(assistant_message)

                        # Render agent metadata (use current message index)
                        current_message_index = len(st.session_state.messages) - 1
                        render_agent_metadata(agent_result, message_index=current_message_index)

                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        response_placeholder.error(error_msg)
                        status.update(label="❌ Error occurred", state="error")
                        st.session_state.messages.append(
                            {"role": "assistant", "content": error_msg}
                        )

                    finally:
                        st.session_state.processing = False


def render_message(message: Union[dict, Message], message_index: int = 0) -> None:
    """
    Render a single chat message with agent metadata.

    Args:
        message: The message to render (dict or Message object).
        message_index: Unique index for this message in the conversation.
    """
    # Handle both dict and Message object formats
    if isinstance(message, dict):
        role = message.get("role", "user")
        content = message.get("content", "")
        agent_data = message.get("agent_data")
    else:
        role = message.role
        content = message.content
        agent_data = getattr(message, "agent_data", None)

    with st.chat_message(role):
        st.markdown(content)

        # Show agent metadata if available (for assistant messages)
        if role == "assistant" and agent_data:
            render_agent_metadata(agent_data, message_index=message_index)


def render_agent_metadata(agent_data: dict, message_index: int = 0) -> None:
    """
    Render agent metadata including sources, code snippets, and processing path.

    Args:
        agent_data: Agent result data from supervisor.
        message_index: Unique index for this message in the conversation.
    """
    if not agent_data:
        return

    # Intent Analysis & Confidence
    intent_data = agent_data.get("intent", {})
    if intent_data:
        with st.expander("🎯 Query Analysis", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                intent = intent_data.get("primary_intent", "unknown")
                st.metric("Intent", intent.replace("_", " ").title())

            with col2:
                confidence = intent_data.get("confidence", 0.0)
                confidence_pct = f"{confidence * 100:.1f}%"
                st.metric("Confidence", confidence_pct)

            with col3:
                level = intent_data.get("confidence_level", "unknown")
                st.metric("Level", level.upper())

            keywords = intent_data.get("keywords", [])
            if keywords:
                st.write("**Keywords:**", ", ".join(f"`{kw}`" for kw in keywords))

    # Processing Path
    processing_path = agent_data.get("processing_path", [])
    if processing_path:
        with st.expander(f"🔄 Agent Pipeline ({len(processing_path)} steps)", expanded=False):
            for i, agent in enumerate(processing_path, 1):
                icon = get_agent_icon(agent)
                st.write(f"{i}. {icon} **{agent.replace('_', ' ').title()}**")

    # Source Documents
    sources = agent_data.get("sources", [])
    if sources:
        render_sources_section(sources, message_index=message_index)

    # Code Snippets
    code_snippets = agent_data.get("code_snippets", [])
    if code_snippets:
        render_code_snippets(code_snippets, message_index=message_index)

    # Error Information
    error = agent_data.get("error")
    if error:
        st.warning(f"⚠️ {error.get('message', 'An error occurred')}")


def get_agent_icon(agent_name: str) -> str:
    """Get emoji icon for agent."""
    icons = {
        "query_analyzer": "🔍",
        "rag_agent": "📚",
        "code_generator": "💻",
        "doc_analyzer": "📝",
        "direct_response": "💬",
    }
    return icons.get(agent_name, "🤖")


def render_sources_section(sources: list[dict], message_index: int = 0) -> None:
    """
    Render RAG sources in an expandable section.

    Args:
        sources: List of retrieved documents with scores.
        message_index: Unique index for this message in the conversation.
    """
    if not sources:
        return

    with st.expander(f"📚 Sources ({len(sources)} relevant documents)", expanded=False):
        for i, source in enumerate(sources, 1):
            # Extract metadata
            content = source.get("content", "")
            metadata = source.get("metadata", {})
            score = source.get("score", 0.0)

            # Header with endpoint info
            endpoint = metadata.get("endpoint", "N/A")
            method = metadata.get("method", "")
            st.markdown(f"### {i}. `{method} {endpoint}`")

            # Relevance score
            col1, col2 = st.columns([3, 1])
            with col2:
                st.metric("Relevance", f"{score * 100:.1f}%")

            # Content preview
            if content:
                preview_length = 300
                preview = content[:preview_length]
                if len(content) > preview_length:
                    preview += "..."

                st.text_area(
                    f"Source {i} Content",
                    preview,
                    height=100,
                    key=f"source_msg{message_index}_{i}",
                    label_visibility="collapsed",
                )

            st.divider()


def render_code_snippets(code_snippets: list[dict], message_index: int = 0) -> None:
    """
    Render generated code snippets.

    Args:
        code_snippets: List of generated code with metadata.
        message_index: Unique index for this message in the conversation.
    """
    if not code_snippets:
        return

    with st.expander(f"💻 Generated Code ({len(code_snippets)} snippets)", expanded=True):
        for i, snippet in enumerate(code_snippets, 1):
            code = snippet.get("code", "")
            language = snippet.get("language", "python")
            library = snippet.get("library", "")
            endpoint = snippet.get("endpoint", "")
            method = snippet.get("method", "")

            # Header
            st.markdown(f"### Snippet {i}: `{method} {endpoint}`")
            if library:
                st.caption(f"Using **{library}** library")

            # Code block
            st.code(code, language=language, line_numbers=True)

            st.divider()


def render_code_response(code: str, language: str = "python") -> None:
    """
    Render a code block with copy button.

    Args:
        code: The code to display.
        language: Programming language for syntax highlighting.
    """
    st.code(code, language=language, line_numbers=True)


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
