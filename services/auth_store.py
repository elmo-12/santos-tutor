"""Almacén en memoria para sesiones de autenticación."""

from typing import Any, Dict, Optional

import streamlit as st


@st.cache_resource
def _get_store() -> Dict[str, Dict[str, Any]]:
    return {}


def save_auth_session(token: str, session_data: Dict[str, Any], user_data: Dict[str, Any]):
    store = _get_store()
    store[token] = {"session": session_data, "user": user_data}


def load_auth_session(token: Optional[str]) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    return _get_store().get(token)


def delete_auth_session(token: Optional[str]):
    if not token:
        return
    store = _get_store()
    store.pop(token, None)

