"""Componentes relacionados con la vista de chat del tutor."""

import time
import uuid
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from config.settings import N8N_WEBHOOK_URL
from services.supabase_client import SupabaseClient
from services.supabase_service import cached_chat_messages, cached_chat_sessions
from utils.messages import dedup_messages, display_text, render_markdown_with_math
from utils.query_params import get_query_params, set_query_params


def render_chat_interface(sb_client: SupabaseClient, available_subjects):
    """Renderiza la interfaz principal del chat."""
    st.header("💬 Chat con Tutor Especializado")

    if not available_subjects:
        st.warning("No tienes suscripciones activas. Por favor, adquiere una materia primero.")
        return

    subject_names = [sub["name"] for sub in available_subjects]
    query = get_query_params()
    subject_from_url = query.get("sub")
    if isinstance(subject_from_url, list):
        subject_from_url = subject_from_url[0] if subject_from_url else None

    default_subject = (
        st.session_state.get("selected_subject")
        or (subject_from_url if subject_from_url in subject_names else None)
        or (subject_names[0] if subject_names else None)
    )
    default_index = subject_names.index(default_subject) if default_subject in subject_names else 0
    selected_subject = st.selectbox(
        "Selecciona la materia:", subject_names, index=default_index, key="subject_selector"
    )

    if st.session_state.get("selected_subject") != selected_subject:
        st.session_state.selected_subject = selected_subject
        set_query_params(sub=selected_subject)

    selected_subject_id = [
        sub["id"] for sub in available_subjects if sub["name"] == selected_subject
    ][0]

    with st.spinner("Cargando sesiones..."):
        chat_sessions = cached_chat_sessions(st.session_state.user_id) or []
    chat_sessions = sorted(chat_sessions, key=lambda s: s.get("created_at", ""))

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Sesiones de Chat")

        if st.button("➕ Nueva Sesión"):
            session_title = f"Sesión {len(chat_sessions) + 1} - {selected_subject}"
            try:
                new_session_rows = sb_client.create_chat_session(
                    st.session_state.user_id,
                    selected_subject_id,
                    session_title,
                )
            except Exception as exc:
                st.error(f"No fue posible crear la sesión: {exc}")
                new_session_rows = None

            if new_session_rows and len(new_session_rows) > 0 and new_session_rows[0].get("id"):
                new_id = new_session_rows[0]["id"]
                st.session_state.current_session = new_id
                st.session_state.chat_history = []
                try:
                    st.cache_data.clear()
                except Exception:
                    pass
                try:
                    chat_sessions = sb_client.get_chat_sessions(st.session_state.user_id) or []
                    chat_sessions = sorted(chat_sessions, key=lambda s: s.get("created_at", ""))
                except Exception:
                    pass
                set_query_params(
                    sid=new_id, sub=st.session_state.get("selected_subject", selected_subject)
                )
            else:
                st.warning("La API no devolvió el id de la nueva sesión. Intenta nuevamente.")

        session_ids = [s["id"] for s in chat_sessions]

        def _label_for(session):
            created = session.get("created_at")
            try:
                created_fmt = (
                    pd.to_datetime(created).strftime("%Y-%m-%d %H:%M") if created else "—"
                )
            except Exception:
                created_fmt = str(created) if created else "—"
            return f"📝 {session.get('session_title', 'Sin título')} · {created_fmt}"

        labels_by_id = {session["id"]: _label_for(session) for session in chat_sessions}

        if session_ids:
            if (
                not st.session_state.get("current_session")
                or st.session_state.current_session not in session_ids
            ):
                st.session_state.current_session = session_ids[-1]

            current_index = session_ids.index(st.session_state.current_session)
            def on_session_change():
                sid = st.session_state.session_selector
                st.session_state.current_session = sid
                st.session_state.chat_history = dedup_messages(cached_chat_messages(sid))
                set_query_params(sid=sid)

            selected_id = st.selectbox(
                "Historial de sesiones",
                options=session_ids,
                index=current_index,
                format_func=lambda sid: labels_by_id.get(sid, sid),
                key="session_selector",
                on_change=on_session_change,
            )

    with col2:
        st.subheader("Chat")

        if st.session_state.current_session:
            chat_container = st.container()
            with chat_container:
                if not st.session_state.get("chat_history"):
                    messages = cached_chat_messages(st.session_state.current_session)
                    st.session_state.chat_history = dedup_messages(messages)

                pending = st.session_state.get("pending_local") or []
                base_messages = st.session_state.get("chat_history", [])
                display_messages = dedup_messages(base_messages + pending)

                if not display_messages:
                    st.info("No hay mensajes en esta sesión.")
                else:
                    if hasattr(st, "chat_message"):
                        for message in display_messages:
                            role = "user" if message.get("role") == "user" else "assistant"
                            with st.chat_message(role):
                                render_markdown_with_math(display_text(message.get("content")))
                    else:
                        for message in display_messages:
                            text = display_text(message.get("content"))
                            if message.get("role") == "user":
                                st.markdown("**Tú:**")
                                render_markdown_with_math(text)
                            else:
                                st.markdown("**Tutor:**")
                                render_markdown_with_math(text)
                            st.markdown("---")

            if st.session_state.get("_clear_user_input"):
                try:
                    st.session_state["_clear_user_input"] = False
                    st.session_state["user_input"] = ""
                except Exception:
                    pass

            if st.session_state.get("_clear_user_input"):
                st.session_state["_clear_user_input"] = False
                if "user_input" in st.session_state:
                    st.session_state["user_input"] = ""
                st.rerun()

            with st.form("chat_form", clear_on_submit=False):
                user_input = st.text_area("Escribe tu pregunta:", key="user_input")
                sending = bool(st.session_state.get("sending", False))
                has_pending = bool(st.session_state.get("pending_local"))

                send_clicked = st.form_submit_button(
                    "Enviar Mensaje", disabled=(sending or has_pending)
                )

                if send_clicked and user_input:
                    st.session_state.sending = True
                    st.session_state.pending_local = [
                        {
                            "role": "user",
                            "content": user_input,
                            "pending": True,
                            "created_at": datetime.now().isoformat(),
                        }
                    ]
                    st.session_state["_clear_user_input"] = True

                    send_message_to_tutor(
                        sb_client,
                        user_input,
                        selected_subject,
                        selected_subject_id,
                    )
                    st.rerun()

            composing = bool(
                st.session_state.get("sending")
                or st.session_state.get("pending_local")
                or st.session_state.get("user_input")
            )
            if st.session_state.get("auto_refresh") and not composing:
                try:
                    interval_ms = int(st.session_state.get("auto_refresh_interval", 5)) * 1000
                except Exception:
                    interval_ms = 5000
                sid = st.session_state.get("current_session", "")
                subj = st.session_state.get("selected_subject", "")
                components.html(
                    f"""
                    <script>
                      const interval = {interval_ms};
                      setTimeout(() => {{
                        try {{
                          const url = new URL(window.location.href);
                          url.searchParams.set('sid', '{sid}');
                          url.searchParams.set('sub', '{subj}');
                          url.searchParams.set('auto', '1');
                          url.searchParams.set('ival', String({interval_ms}/1000));
                          url.searchParams.set('_tick', Date.now().toString());
                          window.location.replace(url.toString());
                        }} catch (e) {{
                          window.location.reload();
                        }}
                      }}, interval);
                    </script>
                    """,
                    height=0,
                    width=0,
                )
        else:
            st.info("Selecciona o crea una sesión de chat para comenzar.")


def send_message_to_tutor(sb_client: SupabaseClient, message: str, subject: str, subject_id: str):
    """Envía un mensaje al tutor externo y actualiza el estado del chat."""
    try:
        previous_messages = sb_client.get_chat_messages(st.session_state.current_session) or []
    except Exception:
        previous_messages = []

    client_message_id = str(uuid.uuid4())
    st.session_state.last_client_message_id = client_message_id
    st.session_state.sending = True

    payload = {
        "user_id": st.session_state.user_id,
        "session_id": st.session_state.current_session,
        "subject": subject.lower(),
        "subject_id": subject_id,
        "message": message,
        "client_message_id": client_message_id,
        "action": "chat",
    }

    headers = {"Accept": "text/plain, text/markdown;q=0.9, */*;q=0.1"}

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=25)
    except Exception as exc:
        st.error(f"Error al llamar al webhook del tutor: {exc}")
        st.session_state.sending = False
        return

    if not (200 <= response.status_code < 300):
        st.error(f"Tutor respondió {response.status_code}: {response.text}")
        st.session_state.sending = False
        return

    try:
        st.cache_data.clear()
    except Exception:
        pass

    start = time.time()
    latest = previous_messages

    while time.time() - start < 8:
        try:
            latest = sb_client.get_chat_messages(st.session_state.current_session) or []
        except Exception:
            latest = previous_messages

        if len(latest) > len(previous_messages):
            break

        time.sleep(0.25)

    st.session_state.chat_history = dedup_messages(latest)

    if len(latest) > len(previous_messages):
        st.session_state.pending_local = []
    else:
        try:
            st.toast("Aún procesando respuesta del tutor...", icon="⏳")
        except Exception:
            pass

    st.session_state.sending = False

