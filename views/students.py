"""Vista de gestión de alumnos y asignación de cursos."""

from typing import Dict, List

import pandas as pd
import streamlit as st

from config.settings import (
    COURSE_NAME_FIELDS,
    STUDENT_NAME_FIELDS,
    STUDENT_COURSES_COURSE_FIELD,
    STUDENT_COURSES_STUDENT_FIELD,
)
from services.supabase_client import SupabaseClient
from services.supabase_service import (
    cached_courses,
    cached_student_course_relations,
    cached_student_courses,
    cached_students,
    update_student_courses,
)


def _resolve_display_name(item: Dict, preferred_fields) -> str:
    for field in preferred_fields:
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            return value
    for value in item.values():
        if isinstance(value, str) and value.strip():
            return value
    return item.get("id", "Sin nombre")


def render_student_dashboard(sb_client: SupabaseClient):
    """Renderiza la sección de gestión de alumnos y asignación de cursos."""
    st.header("👩‍🎓 Gestión de Alumnos y Cursos")

    students = cached_students() or []
    courses = cached_courses() or []

    if not students:
        st.info("No hay alumnos registrados en Supabase.")
        return

    if not courses:
        st.warning("No se encontraron cursos disponibles. Crea cursos para poder asignarlos.")
        return

    student_options = {student["id"]: _resolve_display_name(student, STUDENT_NAME_FIELDS) for student in students}
    course_options = {course["id"]: _resolve_display_name(course, COURSE_NAME_FIELDS) for course in courses}

    st.subheader("Resumen general")
    relations = cached_student_course_relations() or []
    course_name_by_id = course_options

    summary_rows: List[Dict[str, str]] = []
    assignments_map: Dict[str, List[str]] = {}
    for relation in relations:
        sid = relation.get(STUDENT_COURSES_STUDENT_FIELD)
        cid = relation.get(STUDENT_COURSES_COURSE_FIELD)
        if not sid or not cid:
            continue
        assignments_map.setdefault(sid, []).append(course_name_by_id.get(cid, str(cid)))

    for student_id, label in student_options.items():
        assigned_courses = assignments_map.get(student_id, [])
        summary_rows.append(
            {
                "Alumno": label,
                "Cursos asignados": ", ".join(sorted(assigned_courses)) if assigned_courses else "—",
            }
        )

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    st.markdown("---")
    st.subheader("Asignación por alumno")

    selected_student_id = st.selectbox(
        "Selecciona un alumno",
        options=list(student_options.keys()),
        format_func=lambda sid: student_options.get(sid, sid),
        key="student_selector",
    )

    if not selected_student_id:
        st.info("Selecciona un alumno para gestionar sus cursos.")
        return

    assigned_course_ids = cached_student_courses(selected_student_id)
    selected_courses = st.multiselect(
        "Cursos asignados",
        options=list(course_options.keys()),
        default=assigned_course_ids,
        format_func=lambda cid: course_options.get(cid, cid),
        key=f"courses_for_{selected_student_id}",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Guardar asignación", key="save_assignment"):
            try:
                update_student_courses(selected_student_id, selected_courses)
                st.success("Asignación actualizada correctamente.")
                st.experimental_rerun()
            except Exception as exc:
                st.error(f"No fue posible actualizar la asignación: {exc}")

    with col2:
        if st.button("Quitar todos los cursos", key="clear_assignment"):
            try:
                update_student_courses(selected_student_id, [])
                st.success("Se eliminaron todas las asignaciones del alumno.")
                st.experimental_rerun()
            except Exception as exc:
                st.error(f"No fue posible eliminar las asignaciones: {exc}")

