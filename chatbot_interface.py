from __future__ import annotations

from typing import Callable, List, Dict, Sequence

import streamlit as st


Message = Dict[str, str]
Responder = Callable[[str, List[Message]], str]


def _messages_key(state_prefix: str) -> str:
    return f"{state_prefix}_messages"


def _input_key(state_prefix: str) -> str:
    return f"{state_prefix}_input"


def init_chat_state(state_prefix: str = "chatbot") -> None:
    """Initialize chat-related session state keys if missing."""
    messages_key = _messages_key(state_prefix)
    input_key = _input_key(state_prefix)

    if messages_key not in st.session_state:
        st.session_state[messages_key] = []
    if input_key not in st.session_state:
        st.session_state[input_key] = ""


def reset_chat_state(state_prefix: str = "chatbot") -> None:
    """Clear chat history and pending synthetic input."""
    st.session_state[_messages_key(state_prefix)] = []
    st.session_state[_input_key(state_prefix)] = ""


def _append_message(state_prefix: str, role: str, content: str) -> None:
    st.session_state[_messages_key(state_prefix)].append({"role": role, "content": content})


def _display_history(state_prefix: str) -> None:
    for msg in st.session_state[_messages_key(state_prefix)]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def _run_turn(state_prefix: str, prompt: str, responder: Responder) -> None:
    clean_prompt = (prompt or "").strip()
    if not clean_prompt:
        return

    _append_message(state_prefix, "user", clean_prompt)

    try:
        response = responder(clean_prompt, st.session_state[_messages_key(state_prefix)])
        final_response = (response or "").strip() or "I am not sure how to answer that yet."
    except Exception:
        final_response = "I hit an internal error while processing that question. Please try again."

    _append_message(state_prefix, "assistant", final_response)


def render_chat_interface(
    title: str,
    welcome_text: str,
    responder: Responder,
    state_prefix: str = "chatbot",
    suggestions: Sequence[str] | None = None,
    input_placeholder: str = "Ask me anything...",
) -> None:
    """Render a reusable chatbot interface with optional starter prompts."""
    init_chat_state(state_prefix)

    st.title(title)

    with st.sidebar:
        st.subheader("Chat Controls")
        if st.button("Clear chat"):
            reset_chat_state(state_prefix)
            st.rerun()

    history = st.session_state[_messages_key(state_prefix)]
    if not history:
        with st.chat_message("assistant"):
            st.markdown(welcome_text)

    _display_history(state_prefix)

    if suggestions and not history:
        st.caption("Try one of these:")
        cols = st.columns(len(suggestions))
        for col, suggestion in zip(cols, suggestions):
            with col:
                if st.button(suggestion, key=f"{state_prefix}_s_{suggestion}"):
                    _run_turn(state_prefix, suggestion, responder)
                    st.rerun()

    user_prompt = st.chat_input(input_placeholder)
    if user_prompt:
        _run_turn(state_prefix, user_prompt, responder)
        st.rerun()
