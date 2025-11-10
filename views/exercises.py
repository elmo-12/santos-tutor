"""Componentes relacionados con la generación y evaluación de ejercicios."""

import requests
import streamlit as st

from config.settings import N8N_WEBHOOK_URL
from services.supabase_client import SupabaseClient


def render_exercises_interface(sb_client: SupabaseClient, available_subjects):
    """Renderiza el panel de ejercicios adaptativos."""
    st.header("📚 Ejercicios Adaptativos")

    if not available_subjects:
        st.warning("No tienes suscripciones activas.")
        return

    subject_names = [sub["name"] for sub in available_subjects]
    selected_subject = st.selectbox("Selecciona la materia:", subject_names, key="exercises_subject")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Generar Nuevo Ejercicio")
        topic = st.text_input("Tema específico:", placeholder="Ej: Derivadas, Leyes de Newton...")
        difficulty = st.slider("Nivel de dificultad:", 1, 5, 3)

        if st.button("🎯 Generar Ejercicio Personalizado"):
            generate_custom_exercise(sb_client, selected_subject, topic, difficulty)

    with col2:
        st.subheader("Ejercicios Recientes")

        exercises = sb_client.get_exercise_stats(st.session_state.user_id)

        if not exercises:
            st.info("No hay ejercicios generados todavía.")
            return

        for exercise in exercises:
            with st.expander(f"Ejercicio - {exercise['topic']}"):
                st.write(f"**Enunciado:** {exercise['exercise_text']}")

                show_input_key = f"show_input_{exercise['id']}"
                feedback_key = f"feedback_{exercise['id']}"

                if show_input_key not in st.session_state:
                    st.session_state[show_input_key] = True

                if feedback_key not in st.session_state:
                    st.session_state[feedback_key] = ""

                if not exercise.get("completed") and st.session_state[show_input_key]:
                    user_key = f"respuesta_{exercise['id']}"
                    respuesta = st.text_area("Tu respuesta:", key=user_key)

                    if st.button("Enviar Respuesta", key=f"btn_{exercise['id']}"):
                        subject_value = exercise.get("subject")
                        if not subject_value:
                            subs = (
                                sb_client.get_user_subscriptions(st.session_state.user_id) or []
                            )
                        else:
                            subs = []
                        if not subject_value:
                            subj = next(
                                (
                                    s
                                    for s in subs
                                    if s.get("subjects")
                                    and s["subjects"].get("id") == exercise.get("subject_id")
                                ),
                                None,
                            )
                            subject_value = (
                                subj["subjects"]["name"] if subj and subj.get("subjects") else None
                            )

                        payload = {
                            "user_id": exercise["user_id"],
                            "subject_id": exercise["subject_id"],
                            "subject": subject_value,
                            "difficulty": exercise["difficulty_level"],
                            "topic": exercise["topic"],
                            "enunciado": exercise["exercise_text"],
                            "user_answer": respuesta,
                            "action": "solution",
                            "exercise_id": exercise["id"],
                        }

                        try:
                            response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=20)

                            if response.status_code == 200:
                                result = response.json()

                                respuesta_n8n = result.get("Respuesta", "").lower()
                                mensaje_guia = result.get("Mensaje guía", "")

                                if respuesta_n8n == "correcta":
                                    st.session_state[feedback_key] = mensaje_guia
                                    st.session_state[show_input_key] = False
                                    st.rerun()

                                elif respuesta_n8n == "incorrecta":
                                    st.session_state[feedback_key] = mensaje_guia
                                else:
                                    st.session_state[feedback_key] = str(result)

                            else:
                                st.session_state[feedback_key] = (
                                    f"Error al enviar a n8n: {response.status_code} - {response.text}"
                                )

                        except Exception as exc:
                            st.session_state[feedback_key] = f"Error al enviar la respuesta: {exc}"

                if st.session_state[feedback_key]:
                    if "correcta" in st.session_state[feedback_key].lower():
                        st.success(st.session_state[feedback_key])
                    else:
                        st.warning(st.session_state[feedback_key])

                if exercise.get("completed"):
                    st.success("✅ Completado")

                    if exercise.get("user_answer"):
                        st.markdown(f"**Tu respuesta:** {exercise['user_answer']}")
                else:
                    st.warning("⏳ Pendiente")


def generate_custom_exercise(sb_client: SupabaseClient, subject: str, topic: str, difficulty: int):
    """Solicita a n8n la generación de un ejercicio personalizado."""
    subs = sb_client.get_user_subscriptions(st.session_state.user_id) or []
    subject_entry = next(
        (s for s in subs if s.get("subjects") and s["subjects"].get("name") == subject),
        None,
    )
    subject_id = subject_entry["subjects"]["id"] if subject_entry else None

    payload = {
        "user_id": st.session_state.user_id,
        "subject": subject.lower(),
        "subject_id": subject_id,
        "topic": topic,
        "difficulty": difficulty,
        "action": "custom_exercise",
    }

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            st.success("¡Ejercicio generado!")
    except Exception as exc:
        st.error(f"Error al generar ejercicio: {exc}")


def generate_exercise(sb_client: SupabaseClient, subject: str, subject_id: str):
    """Genera un ejercicio general mediante el flujo n8n."""
    payload = {
        "user_id": st.session_state.user_id,
        "subject": subject.lower(),
        "subject_id": subject_id,
        "topic": "general",
        "difficulty": 3,
        "action": "generate_exercise",
    }

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            exercise = response.json()
            sb_client.save_chat_message(
                st.session_state.current_session,
                "assistant",
                exercise,
                "exercise",
            )
            st.session_state.chat_history.append(
                {"role": "assistant", "content": exercise, "message_type": "exercise"}
            )
    except Exception as exc:
        st.error(f"Error al generar ejercicio: {exc}")

