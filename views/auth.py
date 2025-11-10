"""Componentes de autenticación con Supabase Auth."""

from typing import Any, Optional

import streamlit as st

from uuid import uuid4

from services.auth_store import save_auth_session
from services.supabase_client import SupabaseClient
from utils.query_params import set_query_params


def _extract_value(obj: Any, attr: str):
    if obj is None:
        return None
    if hasattr(obj, attr):
        return getattr(obj, attr)
    if isinstance(obj, dict):
        return obj.get(attr)
    return None


def _serialize_session(session: Any) -> Optional[dict]:
    if session is None:
        return None
    if isinstance(session, dict):
        return session
    fields = ["access_token", "refresh_token", "expires_in", "expires_at", "token_type"]
    return {field: _extract_value(session, field) for field in fields}


def _serialize_user(user: Any) -> Optional[dict]:
    if user is None:
        return None
    if isinstance(user, dict):
        return user
    attrs = ["id", "email", "user_metadata", "app_metadata", "role", "aud"]
    data = {attr: _extract_value(user, attr) for attr in attrs}
    return data


def _trigger_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        raise RuntimeError("No se encontró método de recarga compatible en Streamlit.")


def render_login(sb_client: SupabaseClient):
    """Renderiza el formulario de inicio de sesión y gestiona el login."""
    st.title("Tutor Virtual Personalizado")
    st.subheader("Inicia sesión con tu cuenta")

    if st.session_state.get("login_error"):
        st.error(st.session_state.pop("login_error"))

    with st.form("login_form"):
        email = st.text_input("Correo electrónico", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        submit = st.form_submit_button("Login")

    if submit:
        if not email or not password:
            st.warning("Por favor, completa todos los campos.")
            return

        try:
            auth_response = sb_client.sign_in_with_password(email, password)
            session = _extract_value(auth_response, "session")
            user = _extract_value(auth_response, "user")

            session_data = _serialize_session(session)
            user_data = _serialize_user(user)

            if not session_data or not user_data:
                st.error("No fue posible recuperar la sesión de Supabase.")
                return

            st.session_state.auth_session = session_data
            st.session_state.auth_user = user_data
            st.session_state.user_id = user_data.get("id")
            st.session_state.supabase_access_token = session_data.get("access_token")
            st.session_state.supabase_refresh_token = session_data.get("refresh_token")

            auth_token = st.session_state.get("auth_token") or str(uuid4())
            st.session_state.auth_token = auth_token
            save_auth_session(auth_token, session_data, user_data)
            set_query_params(auth_token=auth_token)

            try:
                sb_client.set_session(
                    session_data.get("access_token"),
                    session_data.get("refresh_token"),
                )
            except Exception:
                pass

            try:
                st.cache_data.clear()
            except Exception:
                pass

            st.success("Inicio de sesión exitoso. Redirigiendo al dashboard…")
            _trigger_rerun()
        except Exception as exc:
            st.session_state.login_error = f"No fue posible iniciar sesión: {exc}"
            _trigger_rerun()

