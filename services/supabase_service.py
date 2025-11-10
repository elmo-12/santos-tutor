"""Funciones auxiliares para interactuar con Supabase utilizando caches de Streamlit."""

from typing import Iterable, List

import streamlit as st

from config.settings import SUPABASE_KEY, SUPABASE_URL
from services.supabase_client import SupabaseClient


@st.cache_resource
def init_supabase() -> SupabaseClient:
    """Inicializa y comparte la instancia del cliente de Supabase."""
    return SupabaseClient(SUPABASE_URL, SUPABASE_KEY)


@st.cache_data(ttl=10, show_spinner=False)
def cached_user_subscriptions(user_id: str):
    client = init_supabase()
    return client.get_user_subscriptions(user_id)


@st.cache_data(ttl=10, show_spinner=False)
def cached_chat_sessions(user_id: str):
    client = init_supabase()
    return client.get_chat_sessions(user_id)


@st.cache_data(ttl=5, show_spinner=False)
def cached_chat_messages(session_id: str):
    client = init_supabase()
    return client.get_chat_messages(session_id)


@st.cache_data(ttl=20, show_spinner=False)
def cached_students():
    client = init_supabase()
    return client.get_students()


@st.cache_data(ttl=20, show_spinner=False)
def cached_courses():
    client = init_supabase()
    return client.get_courses()


@st.cache_data(ttl=10, show_spinner=False)
def cached_student_course_relations():
    client = init_supabase()
    return client.get_student_course_relations()


@st.cache_data(ttl=5, show_spinner=False)
def cached_student_courses(student_id: str) -> List[str]:
    client = init_supabase()
    return client.get_student_courses(student_id)


def update_student_courses(student_id: str, course_ids: Iterable[str]) -> List[str]:
    """Actualiza la asignación de cursos en Supabase y devuelve la lista final."""
    client = init_supabase()
    updated = client.update_student_courses(student_id, course_ids)
    # Limpiar caches relacionados para reflejar cambios inmediatos.
    try:
        cached_student_courses.clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        cached_student_course_relations.clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        cached_students.clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    return updated