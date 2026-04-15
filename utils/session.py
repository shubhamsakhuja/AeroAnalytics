"""
Session state initialisation and shared UI helpers.
"""
import streamlit as st


def init_session():
    defaults = {
        "chat_history": [],
        "connection_config": {"type": "demo"},
        "last_result": None,
        "last_insight": None,
        "pending_query": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
