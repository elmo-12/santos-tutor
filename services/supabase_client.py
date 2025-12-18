"""Cliente de Supabase para encapsular operaciones relacionadas con la base de datos y autenticación."""

from typing import Dict, Iterable, List, Optional

import supabase

from config.settings import (
    COURSES_TABLE,
    STUDENT_COURSES_COURSE_FIELD,
    STUDENT_COURSES_STUDENT_FIELD,
    STUDENT_COURSES_TABLE,
    STUDENTS_TABLE,
)


class SupabaseClient:
    """Encapsula el cliente de Supabase y operaciones frecuentes."""

    def __init__(self, url: str, key: str):
        # Validar que la URL no esté vacía
        if not url or not url.strip():
            raise ValueError("SUPABASE_URL no puede estar vacía. Verifica config/settings.py")
        
        # Validar que la URL tenga el formato correcto
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            raise ValueError(f"SUPABASE_URL debe comenzar con http:// o https://. URL recibida: {url}")
        
        # Validar que la key no esté vacía
        if not key or not key.strip():
            raise ValueError("SUPABASE_KEY no puede estar vacía. Verifica config/settings.py")
        
        try:
            self.client = supabase.create_client(url, key)
        except Exception as e:
            error_msg = str(e)
            if "Name or service not known" in error_msg or "Errno -2" in error_msg:
                raise ConnectionError(
                    f"No se puede conectar a Supabase. Error de DNS/resolución de nombres.\n"
                    f"URL intentada: {url}\n"
                    f"Verifica que:\n"
                    f"  1. La URL sea correcta y accesible\n"
                    f"  2. Tengas conexión a internet\n"
                    f"  3. El nombre del servidor sea válido\n"
                    f"  4. No haya firewall bloqueando la conexión\n"
                    f"Error original: {error_msg}"
                ) from e
            raise

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------
    def sign_in_with_password(self, email: str, password: str):
        """Inicia sesión con email y contraseña."""
        return self.client.auth.sign_in_with_password({"email": email, "password": password})

    def sign_out(self):
        """Cierra la sesión activa en Supabase."""
        return self.client.auth.sign_out()

    def get_session(self):
        """Recupera la sesión actual del cliente."""
        getter = getattr(self.client.auth, "get_session", None)
        if callable(getter):
            return getter()
        return getattr(self.client.auth, "session", None)

    def set_session(self, access_token: str, refresh_token: str):
        """Establece tokens para reutilizar sesiones entre recargas."""
        setter = getattr(self.client.auth, "set_session", None)
        if callable(setter):
            return setter(access_token, refresh_token)
        # Fallback para versiones que exponen directamente los atributos.
        self.client.auth._access_token = access_token  # type: ignore[attr-defined]  # noqa: SLF001
        self.client.auth._refresh_token = refresh_token  # type: ignore[attr-defined]  # noqa: SLF001
        self.client.auth.session = getattr(self.client.auth, "session", {}) or {}
        self.client.auth.session["access_token"] = access_token
        self.client.auth.session["refresh_token"] = refresh_token
        return self.client.auth.session

    def get_current_user(self):
        """Obtiene el usuario autenticado actual."""
        getter = getattr(self.client.auth, "get_user", None)
        if callable(getter):
            return getter()
        return getattr(self.client.auth, "user", None)

    # ------------------------------------------------------------------
    # Mensajería y sesiones de chat
    # ------------------------------------------------------------------
    def get_user_subscriptions(self, user_id: str):
        response = (
            self.client.table("user_subscriptions")
            .select("*, subjects(*)")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
        return response.data

    def get_chat_sessions(self, user_id: str):
        response = (
            self.client.table("chat_sessions")
            .select("*, subjects(name)")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data

    def get_chat_messages(self, session_id: str):
        response = (
            self.client.table("chat_messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        data = response.data or []
        data.sort(key=lambda x: x.get("created_at", ""))
        return data

    def save_chat_message(self, session_id: str, role: str, content, message_type: str = "text"):
        response = (
            self.client.table("chat_messages")
            .insert(
                {
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "message_type": message_type,
                }
            )
            .execute()
        )
        return response.data

    def create_chat_session(self, user_id: str, subject_id: str, session_title: str):
        response = (
            self.client.table("chat_sessions")
            .insert(
                {
                    "user_id": user_id,
                    "subject_id": subject_id,
                    "session_title": session_title,
                }
            )
            .execute()
        )
        data = response.data if hasattr(response, "data") else None
        if data:
            return data
        try:
            response2 = (
                self.client.table("chat_sessions")
                .select("id, session_title, created_at, subject_id")
                .eq("user_id", user_id)
                .eq("session_title", session_title)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return response2.data
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Estadísticas y ejercicios
    # ------------------------------------------------------------------

    def get_difficulty_stats(self, user_id: str, subject_id: str = None):

        query = (
            self.client.table("difficulty_tracking")
            .select("*")
            .eq("user_id", user_id)
        )

        if subject_id is not None:
            query = query.eq("subject_id", subject_id)

        response = query.execute()
        return response.data
    
    def get_subjects(self):
        """Retorna todas las materias activas."""
        response = (
            self.client.table("subjects")
            .select("*")
            .order("created_at", desc=False)
            .execute()
        )
        return response.data


    def get_exercise_stats(self, user_id: str):
        response = (
            self.client.table("generated_exercises")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data

    # ------------------------------------------------------------------
    # Gestión de alumnos y cursos
    # ------------------------------------------------------------------
    def get_students(self):
        response = self.client.table(STUDENTS_TABLE).select("*").execute()
        return response.data

    def get_courses(self):
        response = self.client.table(COURSES_TABLE).select("*").execute()
        return response.data

    def get_student_course_relations(self):
        response = (
            self.client.table(STUDENT_COURSES_TABLE)
            .select("*")
            .eq("is_active", True)
            .execute()
        )
        return response.data

    def get_student_courses(self, student_id: str) -> List[str]:
        response = (
            self.client.table(STUDENT_COURSES_TABLE)
            .select(STUDENT_COURSES_COURSE_FIELD)
            .eq(STUDENT_COURSES_STUDENT_FIELD, student_id)
            .eq("is_active", True)
            .execute()
        )
        data = response.data or []
        return [
            row[STUDENT_COURSES_COURSE_FIELD]
            for row in data
            if row.get(STUDENT_COURSES_COURSE_FIELD)
        ]

    def update_student_courses(self, student_id: str, course_ids: Iterable[str]):
        """Actualiza la relación alumno-curso eliminando asignaciones previas y registrando las nuevas."""
        unique_course_ids = {cid for cid in course_ids if cid}
        (
            self.client.table(STUDENT_COURSES_TABLE)
            .delete()
            .eq(STUDENT_COURSES_STUDENT_FIELD, student_id)
            .execute()
        )

        if not unique_course_ids:
            return []

        payload = [
            {
                STUDENT_COURSES_STUDENT_FIELD: student_id,
                STUDENT_COURSES_COURSE_FIELD: cid,
                "is_active": True,
            }
            for cid in unique_course_ids
        ]
        self.client.table(STUDENT_COURSES_TABLE).insert(payload).execute()
        return list(unique_course_ids)

