import time
from typing import Any, Dict, Optional
from uuid import uuid4

import streamlit as st

from services.auth_store import delete_auth_session, load_auth_session, save_auth_session
from services.supabase_service import (
    cached_user_subscriptions,
    init_supabase,
)
from utils.query_params import get_query_params, remove_query_params, set_query_params
from views.auth import render_login
from views.chat import render_chat_interface
from views.exercises import render_exercises_interface
from views.pdf_report import render_pdf_report
from views.statistics import render_statistics_interface
from views.students import render_student_dashboard


def safe_rerun():
    """Try to rerun the Streamlit script compatibly with different Streamlit versions."""
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            raise AttributeError
        return
    except Exception:
        pass

    try:
        params = {}
        try:
            params = st.query_params or {}
        except Exception:
            params = {}
        params["_app_rerun"] = str(int(time.time()))
        try:
            st.set_query_params(**params)
            return
        except Exception:
            pass
    except Exception:
        pass

    try:
        st.stop()
    except Exception:
        return


st.set_page_config(
    page_title="Tutor Virtual Personalizado",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _extract_session_tokens(session: Any) -> Optional[Dict[str, Any]]:
    if session is None:
        return None
    if isinstance(session, dict):
        return session
    fields = ["access_token", "refresh_token", "expires_in", "token_type", "expires_at"]
    return {field: getattr(session, field, None) for field in fields}


def restore_supabase_session(sb_client):
    """Restaura la sesión de Supabase si existen tokens almacenados."""
    query_params = get_query_params()
    session_data = st.session_state.get("auth_session")
    access_token = None
    refresh_token = None
    auth_token = st.session_state.get("auth_token")

    if not auth_token:
        token_from_url = query_params.get("auth_token")
        if isinstance(token_from_url, list):
            token_from_url = token_from_url[0] if token_from_url else None
        auth_token = token_from_url
        if auth_token:
            st.session_state.auth_token = auth_token

    if auth_token and not session_data:
        stored = load_auth_session(auth_token)
        if stored:
            session_data = stored.get("session")
            user_data = stored.get("user")
            if session_data:
                st.session_state.auth_session = session_data
            if user_data and not st.session_state.get("auth_user"):
                st.session_state.auth_user = user_data

    if session_data:
        access_token = session_data.get("access_token")
        refresh_token = session_data.get("refresh_token")
    else:
        existing_session = sb_client.get_session()
        serialized = _extract_session_tokens(existing_session)
        if serialized and serialized.get("access_token"):
            st.session_state.auth_session = serialized
            access_token = serialized.get("access_token")
            refresh_token = serialized.get("refresh_token")

    if access_token and refresh_token:
        try:
            sb_client.set_session(access_token, refresh_token)
        except Exception:
            pass
    if st.session_state.get("auth_session"):
        if not auth_token:
            auth_token = str(uuid4())
            st.session_state.auth_token = auth_token
        save_auth_session(auth_token, st.session_state["auth_session"], st.session_state.get("auth_user") or {})
        if auth_token and auth_token not in (query_params.get("auth_token") or []):
            set_query_params(auth_token=auth_token)


def ensure_state_defaults():
    """Inicializa valores necesarios en session_state."""
    defaults = {
        "current_session": None,
        "chat_history": [],
        "pending_local": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_query_params_state():
    query_params = get_query_params()

    sid_from_url = query_params.get("sid")
    if isinstance(sid_from_url, list):
        sid_from_url = sid_from_url[0] if sid_from_url else None
    if sid_from_url and not st.session_state.get("current_session"):
        st.session_state.current_session = sid_from_url

    auto_from_url = query_params.get("auto")
    if isinstance(auto_from_url, list):
        auto_from_url = auto_from_url[0] if auto_from_url else None
    interval_from_url = query_params.get("ival")
    if isinstance(interval_from_url, list):
        interval_from_url = interval_from_url[0] if interval_from_url else None
    if auto_from_url is not None:
        st.session_state.auto_refresh = str(auto_from_url).lower() in ("1", "true", "t", "yes", "y")
    if interval_from_url is not None:
        try:
            st.session_state.auto_refresh_interval = int(interval_from_url)
        except Exception:
            pass


def handle_logout(sb_client):
    """Cierra la sesión en Supabase y limpia el estado local."""
    auth_token = st.session_state.get("auth_token")
    try:
        sb_client.sign_out()
    except Exception:
        pass

    delete_auth_session(auth_token)
    remove_query_params("auth_token")

    st.session_state.clear()

    try:
        st.cache_data.clear()
    except Exception:
        pass

    safe_rerun()


def main():
    sb_client = init_supabase()
    restore_supabase_session(sb_client)

    auth_user = st.session_state.get("auth_user")
    session_data = st.session_state.get("auth_session")

    if not auth_user or not session_data:
        render_login(sb_client)
        return

    user_id = auth_user.get("id") if isinstance(auth_user, dict) else None
    if not user_id:
        st.error("No fue posible recuperar el identificador del usuario autenticado.")
        return

    st.session_state.user_id = user_id

    ensure_state_defaults()
    apply_query_params_state()

    st.sidebar.title("Navegación")
    st.sidebar.markdown(f"**Usuario:** {auth_user.get('email', 'sin correo')}")

    if st.sidebar.button("Logout", key="logout_button"):
        handle_logout(sb_client)
        return

    menu_items = [
        {"value": "Dashboard Alumnos", "label": "👥   Dashboard Alumnos"},
        {"value": "Chat con Tutor", "label": "💬   Chat con Tutor"},
        {"value": "Ejercicios", "label": "📝   Ejercicios"},
        {"value": "Estadísticas", "label": "📊   Estadísticas"},
        {"value": "Reporte PDF", "label": "📄   Reporte PDF"},
    ]
    menu_values = [item["value"] for item in menu_items]

    default_menu = st.session_state.get("selected_menu", menu_values[0])
    if default_menu not in menu_values:
        default_menu = menu_values[0]

    st.sidebar.markdown(
        """
        <style>
        section[data-testid="stSidebar"] .stButton > button {
            justify-content: flex-start;
            text-align: left;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    menu = st.session_state.get("selected_menu", default_menu)
    st.sidebar.markdown("**Selecciona una opción**")
    for item in menu_items:
        if st.sidebar.button(
            item["label"],
            key=f"menu_btn_{item['value']}",
            use_container_width=True,
        ):
            menu = item["value"]
    if menu not in menu_values:
        menu = menu_values[0]
    st.session_state.selected_menu = menu

    if menu == "Dashboard Alumnos":
        render_student_dashboard(sb_client)
        return

    with st.spinner("Cargando suscripciones..."):
        subscriptions = cached_user_subscriptions(st.session_state.user_id)
    available_subjects = [sub["subjects"] for sub in subscriptions]

    if menu == "Chat con Tutor":
        render_chat_interface(sb_client, available_subjects)
    elif menu == "Ejercicios":
        render_exercises_interface(sb_client, available_subjects)
    elif menu == "Estadísticas":
        render_statistics_interface(sb_client)
    elif menu == "Reporte PDF":
        render_pdf_report(sb_client)


if __name__ == "__main__":
    main()
