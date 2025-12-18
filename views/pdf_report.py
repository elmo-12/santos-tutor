"""Generación y presentación del reporte PDF."""

from datetime import datetime
from io import BytesIO

import pandas as pd
from base64 import b64encode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st

from services.supabase_client import SupabaseClient


def render_pdf_report(sb_client: SupabaseClient):
    """Genera un reporte PDF con estadísticas recopiladas."""
    st.header("📄 Generar Reporte PDF")

    difficulty_data = sb_client.get_difficulty_stats(st.session_state.user_id)
    exercise_data = sb_client.get_exercise_stats(st.session_state.user_id)
    chat_sessions = sb_client.get_chat_sessions(st.session_state.user_id)

    if not difficulty_data:
        st.warning("No hay suficientes datos para generar un reporte.")
        return

    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=60,
        bottomMargin=50,
    )
    story = []

    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TituloPrincipal",
            fontName="HeiseiMin-W3",
            fontSize=20,
            leading=24,
            spaceAfter=14,
            alignment=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TituloSeccion",
            fontName="HeiseiMin-W3",
            fontSize=16,
            leading=20,
            spaceBefore=12,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Texto",
            fontName="HeiseiMin-W3",
            fontSize=11,
            leading=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubTexto",
            fontName="HeiseiMin-W3",
            fontSize=10,
            leading=14,
            leftIndent=20,
        )
    )

    story.append(Paragraph("<b>Reporte de Desempeño Académico</b>", styles["TituloPrincipal"]))
    story.append(Spacer(1, 24))

    total_sessions = len(chat_sessions)
    total_exercises = len(exercise_data) if exercise_data else 0
    completed_exercises = len([e for e in exercise_data if e.get("completed")]) if exercise_data else 0
    completion_rate = (completed_exercises / total_exercises * 100) if total_exercises else 0

    story.append(Paragraph("<b>1. Resumen General</b>", styles["TituloSeccion"]))
    story.append(
        Paragraph(
            f"• Sesiones de estudio: {total_sessions}<br/>"
            f"• Ejercicios generados: {total_exercises}<br/>"
            f"• Ejercicios completados: {completed_exercises}<br/>"
            f"• Tasa de finalización: {completion_rate:.1f}%",
            styles["Texto"],
        )
    )
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>2. Análisis por Tema</b>", styles["TituloSeccion"]))

    df_difficulty = pd.DataFrame(difficulty_data)
    topic_analysis = df_difficulty.groupby("topic").agg(
        {
            "difficulty_level": "mean",
            "success_count": "sum",
            "error_count": "sum",
        }
    ).reset_index()

    table_data = [["Tema", "Dificultad Promedio", "Intentos", "Tasa de Éxito"]]
    for _, topic in topic_analysis.iterrows():
        total = topic["success_count"] + topic["error_count"]
        success_rate = (topic["success_count"] / total * 100) if total > 0 else 0
        table_data.append(
            [
                topic["topic"],
                f"{topic['difficulty_level']:.1f}/5",
                str(total),
                f"{success_rate:.1f}%",
            ]
        )

    table = Table(table_data, colWidths=[120, 120, 60, 60, 80])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6E6E6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "HeiseiMin-W3"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 18))

    story.append(Paragraph("<b>3. Recomendaciones Personalizadas</b>", styles["TituloSeccion"]))

    # Preparación de datos mejorada
    df_diff = pd.DataFrame(difficulty_data)
    df_ex = pd.DataFrame(exercise_data) if exercise_data else pd.DataFrame()

    # Convertir fechas para análisis temporal
    if "last_practiced" in df_diff.columns:
        df_diff["last_practiced"] = pd.to_datetime(df_diff["last_practiced"], errors="coerce")
    if not df_ex.empty and "created_at" in df_ex.columns:
        df_ex["created_at"] = pd.to_datetime(df_ex["created_at"], errors="coerce")
        df_ex["date"] = df_ex["created_at"].dt.date

    # Análisis por tema con métricas avanzadas
    df_topics = df_diff.groupby("topic").agg(
        total_errors=("error_count", "sum"),
        total_success=("success_count", "sum"),
        avg_difficulty=("difficulty_level", "mean"),
        max_difficulty=("difficulty_level", "max"),
        min_difficulty=("difficulty_level", "min"),
        attempts_count=("topic", "count"),
    ).reset_index()

    df_topics["total_attempts"] = df_topics["total_success"] + df_topics["total_errors"]
    df_topics["success_rate"] = df_topics.apply(
        lambda row: row.total_success / row.total_attempts if row.total_attempts > 0 else 0,
        axis=1,
    )
    df_topics["error_rate"] = 1 - df_topics["success_rate"]
    df_topics["difficulty_range"] = df_topics["max_difficulty"] - df_topics["min_difficulty"]

    # Análisis de progreso temporal por tema
    def calculate_temporal_trend(topic_name):
        topic_data = df_diff[df_diff["topic"] == topic_name].copy()
        if len(topic_data) < 2 or "last_practiced" not in topic_data.columns:
            return "insuficiente"
        
        topic_data = topic_data.sort_values("last_practiced")
        mid_point = len(topic_data) // 2
        recent = topic_data.iloc[mid_point:]
        older = topic_data.iloc[:mid_point]
        
        if len(recent) == 0 or len(older) == 0:
            return "insuficiente"
        
        recent_success_rate = recent["success_count"].sum() / (recent["success_count"].sum() + recent["error_count"].sum()) if (recent["success_count"].sum() + recent["error_count"].sum()) > 0 else 0
        older_success_rate = older["success_count"].sum() / (older["success_count"].sum() + older["error_count"].sum()) if (older["success_count"].sum() + older["error_count"].sum()) > 0 else 0
        
        diff = recent_success_rate - older_success_rate
        if diff > 0.15:
            return "mejorando"
        elif diff < -0.15:
            return "empeorando"
        else:
            return "estable"

    df_topics["temporal_trend"] = df_topics["topic"].apply(calculate_temporal_trend)

    # Análisis de hábitos de estudio
    study_consistency = "regular"
    study_frequency = "moderada"
    current_streak = 0
    
    if not df_ex.empty and "date" in df_ex.columns:
        dates = sorted(set(df_ex["date"].tolist()))
        if len(dates) > 0:
            today = pd.Timestamp.now(tz=None).date()
            day = today
            while day in dates:
                current_streak += 1
                day -= pd.Timedelta(days=1)
            
            if len(dates) > 1:
                intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                avg_interval = sum(intervals) / len(intervals) if intervals else 0
                if avg_interval <= 2:
                    study_frequency = "alta"
                elif avg_interval <= 5:
                    study_frequency = "moderada"
                else:
                    study_frequency = "baja"
                
                interval_variance = pd.Series(intervals).var() if len(intervals) > 1 else 0
                if interval_variance < 5:
                    study_consistency = "muy regular"
                elif interval_variance < 15:
                    study_consistency = "regular"
                else:
                    study_consistency = "irregular"

    # Clasificación mejorada de riesgo
    def classify_risk_advanced(row):
        score = 0
        # Factores de riesgo
        if row.success_rate < 0.30:
            score += 3
        elif row.success_rate < 0.50:
            score += 2
        elif row.success_rate < 0.70:
            score += 1
        
        if row.avg_difficulty > 4:
            score += 2
        elif row.avg_difficulty > 3:
            score += 1
        
        if row.total_attempts < 5:
            score += 1  # Pocos intentos = incertidumbre
        
        if row.temporal_trend == "empeorando":
            score += 2
        elif row.temporal_trend == "insuficiente":
            score += 1
        
        if score >= 5:
            return "Alto"
        elif score >= 3:
            return "Medio"
        else:
            return "Bajo"

    df_topics["risk"] = df_topics.apply(classify_risk_advanced, axis=1)

    # Score ponderado mejorado
    df_topics["weighted_score"] = df_topics.apply(
        lambda row: (
            (1 - row["success_rate"]) * 0.5 +
            (row["avg_difficulty"] / 5) * 0.2 +
            (1 if row["temporal_trend"] == "empeorando" else 0) * 0.2 +
            (1 if row["total_attempts"] < 5 else 0) * 0.1
        ),
        axis=1,
    )

    # Generar recomendaciones personalizadas por tema
    def generate_topic_recommendations(row):
        recommendations = []
        
        if row.success_rate < 0.40:
            if row.total_attempts < 5:
                recommendations.append("Necesitas más práctica: genera al menos 5 ejercicios adicionales sobre este tema.")
            else:
                recommendations.append("Revisa los conceptos fundamentales antes de continuar con ejercicios más complejos.")
        
        if row.avg_difficulty > 4:
            recommendations.append("Reduce temporalmente la dificultad: practica con ejercicios de nivel 2-3 antes de avanzar.")
        
        if row.temporal_trend == "empeorando":
            recommendations.append("⚠️ Atención: tu rendimiento está disminuyendo. Dedica tiempo extra a repasar este tema.")
        elif row.temporal_trend == "mejorando":
            recommendations.append("✅ Buen progreso: mantén la práctica constante para consolidar el aprendizaje.")
        
        if row.difficulty_range > 2:
            recommendations.append("Hay mucha variación en la dificultad: enfócate en un nivel específico antes de variar.")
        
        if row.total_attempts > 20 and row.success_rate < 0.60:
            recommendations.append("Considera usar el chat con tutor para aclarar dudas específicas sobre este tema.")
        
        if not recommendations:
            if row.success_rate >= 0.80:
                recommendations.append("Excelente dominio: puedes avanzar a temas más complejos o relacionarlos con otros.")
            else:
                recommendations.append("Continúa practicando regularmente para mantener y mejorar tu nivel.")
        
        return recommendations

    df_topics["recommendations"] = df_topics.apply(generate_topic_recommendations, axis=1)

    # Validar que hay datos suficientes
    if df_topics.empty:
        story.append(
            Paragraph(
                "No hay suficientes datos para generar recomendaciones personalizadas. "
                "Completa más ejercicios para obtener análisis detallados.",
                styles["Texto"],
            )
        )
        pdf.build(story)
        buffer.seek(0)
        pdf_b64 = b64encode(buffer.read()).decode("utf-8")
        st.success("✅ Reporte PDF generado correctamente.")
        with st.expander("Vista previa del reporte"):
            pdf_display = (
                f'<iframe src="data:application/pdf;base64,{pdf_b64}" width="100%" height="600px"></iframe>'
            )
            st.markdown(pdf_display, unsafe_allow_html=True)
        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=buffer.getvalue(),
            file_name=f"reporte_tutor_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
        )
        return

    # Identificar temas críticos
    worst_topics = df_topics.nlargest(min(3, len(df_topics)), "weighted_score")
    best_topics = df_topics.nsmallest(min(2, len(df_topics)), "weighted_score")

    # Texto introductorio mejorado
    intro_text = f"""
    Este análisis personalizado identifica tus fortalezas, áreas de mejora y proporciona recomendaciones específicas basadas en tu desempeño real.<br/><br/>
    <b>Hábitos de estudio detectados:</b><br/>
    • Frecuencia: {study_frequency}<br/>
    • Consistencia: {study_consistency}<br/>
    • Racha actual: {current_streak} día(s) consecutivo(s)<br/><br/>
    """
    story.append(Paragraph(intro_text, styles["Texto"]))

    # Tema más crítico con recomendaciones específicas
    worst_topic = worst_topics.iloc[0]
    rec_text = f"""
    <b>🎯 Tema que requiere atención inmediata:</b><br/>
    <b>{worst_topic['topic']}</b><br/>
    • Dificultad promedio: {worst_topic['avg_difficulty']:.1f}/5<br/>
    • Tasa de éxito: {worst_topic['success_rate']*100:.1f}%<br/>
    • Total de intentos: {int(worst_topic['total_attempts'])}<br/>
    • Tendencia: {worst_topic['temporal_trend'].capitalize()}<br/><br/>
    <b>Recomendaciones específicas:</b><br/>
    """
    for rec in worst_topic["recommendations"]:
        rec_text += f"• {rec}<br/>"
    rec_text += "<br/>"

    story.append(Paragraph(rec_text, styles["Texto"]))

    # Temas por categoría de riesgo con recomendaciones
    for level, label, icon in [
        ("Alto", "Temas de atención prioritaria", "🔴"),
        ("Medio", "Temas en consolidación", "🟡"),
        ("Bajo", "Temas dominados", "🟢"),
    ]:
        subset = df_topics[df_topics["risk"] == level].sort_values("weighted_score", ascending=(level != "Bajo"))
        if not subset.empty:
            story.append(Paragraph(f"<b>{icon} {label}</b>", styles["Texto"]))
            for _, row in subset.iterrows():
                topic_text = f"""
                <b>{row['topic']}</b> - Éxito: {row['success_rate']*100:.1f}% | 
                Dificultad: {row['avg_difficulty']:.1f}/5 | 
                Tendencia: {row['temporal_trend'].capitalize()}<br/>
                """
                story.append(Paragraph(topic_text, styles["SubTexto"]))
                # Mostrar recomendaciones principales (máximo 2)
                main_recs = row["recommendations"][:2]
                if main_recs:
                    recs_text = " | ".join([f"• {r}" for r in main_recs])
                    story.append(Paragraph(recs_text, styles["SubTexto"]))
            story.append(Spacer(1, 8))

    # ======================================================
    # RECOMENDACIONES POR CURSO
    # ======================================================
    story.append(Paragraph("<b>4. Análisis y Recomendaciones por Curso</b>", styles["TituloSeccion"]))
    
    # Obtener suscripciones del usuario y mapeo de materias
    user_subscriptions = sb_client.get_user_subscriptions(st.session_state.user_id) or []
    all_subjects = sb_client.get_subjects()
    subjects_map = {sub["id"]: sub["name"] for sub in all_subjects}
    
    # Cursos a los que el usuario está suscrito
    subscribed_course_ids = set()
    subscribed_course_names = []
    for sub in user_subscriptions:
        if sub.get("subjects") and sub.get("subjects", {}).get("id"):
            course_id = sub["subjects"]["id"]
            course_name = sub["subjects"].get("name", "Sin nombre")
            subscribed_course_ids.add(course_id)
            subscribed_course_names.append(course_name)
    
    # Análisis por curso de los datos disponibles
    if not df_diff.empty and "subject_id" in df_diff.columns:
        df_diff["course_name"] = df_diff["subject_id"].map(subjects_map).fillna("Curso desconocido")
        
        # Agregar información de ejercicios por curso
        if not df_ex.empty and "subject_id" in df_ex.columns:
            df_ex["course_name"] = df_ex["subject_id"].map(subjects_map).fillna("Curso desconocido")
        
        # Análisis por curso
        course_analysis = []
        courses_with_data = set()
        
        for course_id in subscribed_course_ids:
            course_name = subjects_map.get(course_id, "Curso desconocido")
            course_df = df_diff[df_diff["subject_id"] == course_id]
            
            if not course_df.empty:
                courses_with_data.add(course_id)
                total_attempts = course_df["success_count"].sum() + course_df["error_count"].sum()
                success_rate = (course_df["success_count"].sum() / total_attempts * 100) if total_attempts > 0 else 0
                avg_difficulty = course_df["difficulty_level"].mean()
                unique_topics = course_df["topic"].nunique()
                
                # Ejercicios del curso
                course_exercises = df_ex[df_ex["subject_id"] == course_id] if not df_ex.empty and "subject_id" in df_ex.columns else pd.DataFrame()
                exercises_count = len(course_exercises) if not course_exercises.empty else 0
                if not course_exercises.empty and "completed" in course_exercises.columns:
                    completed_exercises = len(course_exercises[course_exercises["completed"] == True])  # noqa: E712
                else:
                    completed_exercises = 0
                
                # Última práctica
                if "last_practiced" in course_df.columns:
                    last_practice = pd.to_datetime(course_df["last_practiced"], errors="coerce").max()
                    if pd.notna(last_practice):
                        # Normalizar zonas horarias: convertir ambos a naive (sin zona horaria)
                        now = pd.Timestamp.now(tz=None)
                        if last_practice.tz is not None:
                            last_practice = last_practice.tz_localize(None)
                        days_since = (now - last_practice).days
                    else:
                        days_since = None
                else:
                    days_since = None
                
                # Sesiones de chat del curso
                course_chat_sessions = [s for s in chat_sessions if s.get("subject_id") == course_id]
                chat_count = len(course_chat_sessions)
                
                course_analysis.append({
                    "course_id": course_id,
                    "course_name": course_name,
                    "success_rate": success_rate,
                    "avg_difficulty": avg_difficulty,
                    "unique_topics": unique_topics,
                    "total_attempts": total_attempts,
                    "exercises_count": exercises_count,
                    "completed_exercises": completed_exercises,
                    "days_since_practice": days_since,
                    "chat_sessions": chat_count,
                    "has_data": True
                })
            else:
                # Curso sin datos de práctica
                course_analysis.append({
                    "course_id": course_id,
                    "course_name": course_name,
                    "has_data": False
                })
        
        # Cursos practicados
        practiced_courses = [c for c in course_analysis if c["has_data"]]
        unpracticed_courses = [c for c in course_analysis if not c["has_data"]]
        
        # Generar recomendaciones por curso practicado
        if practiced_courses:
            story.append(Paragraph("<b>📚 Cursos con actividad registrada:</b>", styles["Texto"]))
            story.append(Spacer(1, 6))
            
            for course in sorted(practiced_courses, key=lambda x: x["success_rate"]):
                course_recs = []
                
                # Recomendaciones basadas en tasa de éxito
                if course["success_rate"] < 50:
                    course_recs.append(f"Tasa de éxito baja ({course['success_rate']:.1f}%): enfócate en repasar conceptos fundamentales antes de avanzar.")
                elif course["success_rate"] < 70:
                    course_recs.append(f"Tasa de éxito moderada ({course['success_rate']:.1f}%): continúa practicando para mejorar tu dominio.")
                else:
                    course_recs.append(f"Excelente desempeño ({course['success_rate']:.1f}%): mantén este nivel y explora temas más avanzados.")
                
                # Recomendaciones basadas en dificultad
                if course["avg_difficulty"] > 4:
                    course_recs.append("Dificultad muy alta: considera reducir el nivel temporalmente para consolidar bases.")
                elif course["avg_difficulty"] < 2:
                    course_recs.append("Dificultad baja: puedes aumentar el nivel de desafío para maximizar el aprendizaje.")
                
                # Recomendaciones basadas en actividad reciente
                if course["days_since_practice"] is not None:
                    if course["days_since_practice"] > 14:
                        course_recs.append(f"⚠️ No has practicado este curso en {course['days_since_practice']} días. Programa una sesión de repaso pronto.")
                    elif course["days_since_practice"] > 7:
                        course_recs.append(f"Hace {course['days_since_practice']} días que no practicas. Mantén la regularidad para no olvidar.")
                
                # Recomendaciones basadas en número de temas
                if course["unique_topics"] < 3:
                    course_recs.append(f"Solo has practicado {course['unique_topics']} tema(s). Explora más temas del curso para un aprendizaje completo.")
                
                # Recomendaciones basadas en ejercicios completados
                if course["exercises_count"] > 0:
                    completion_rate = (course["completed_exercises"] / course["exercises_count"] * 100) if course["exercises_count"] > 0 else 0
                    if completion_rate < 60:
                        course_recs.append(f"Tienes {course['exercises_count'] - course['completed_exercises']} ejercicios pendientes. Completarlos te ayudará a consolidar el aprendizaje.")
                
                # Recomendaciones basadas en uso del chat
                if course["chat_sessions"] == 0 and course["success_rate"] < 70:
                    course_recs.append("No has usado el chat tutor para este curso. Considera hacer preguntas sobre temas difíciles.")
                
                # Texto del curso
                course_text = f"""
                <b>{course['course_name']}</b><br/>
                • Tasa de éxito: {course['success_rate']:.1f}% | 
                Dificultad promedio: {course['avg_difficulty']:.1f}/5 | 
                Temas practicados: {course['unique_topics']}<br/>
                • Ejercicios: {course['completed_exercises']}/{course['exercises_count']} completados | 
                Sesiones de chat: {course['chat_sessions']}<br/>
                """
                if course["days_since_practice"] is not None:
                    course_text += f"• Última práctica: hace {course['days_since_practice']} día(s)<br/>"
                course_text += "<br/>"
                
                story.append(Paragraph(course_text, styles["SubTexto"]))
                
                # Recomendaciones del curso
                if course_recs:
                    recs_text = "<b>Recomendaciones:</b><br/>"
                    for rec in course_recs[:3]:  # Máximo 3 recomendaciones por curso
                        recs_text += f"• {rec}<br/>"
                    story.append(Paragraph(recs_text, styles["SubTexto"]))
                    story.append(Spacer(1, 8))
        
        # Cursos no practicados
        if unpracticed_courses:
            story.append(Paragraph("<b>⚠️ Cursos sin actividad registrada:</b>", styles["Texto"]))
            story.append(Spacer(1, 6))

            unpracticed_text = "Los siguientes cursos están en tu suscripción pero no muestran actividad de práctica:<br/><br/>"
            for course in unpracticed_courses:
                unpracticed_text += f"• <b>{course['course_name']}</b><br/>"
            unpracticed_text += "<br/>"
            unpracticed_text += "<b>Recomendaciones:</b><br/>"
            unpracticed_text += "• Inicia tu aprendizaje: genera al menos 3-5 ejercicios para comenzar a construir tu base de conocimiento.<br/>"
            unpracticed_text += "• Usa el chat tutor: haz preguntas sobre conceptos básicos para familiarizarte con el curso.<br/>"
            unpracticed_text += "• Establece un plan: dedica tiempo específico cada semana para practicar estos cursos.<br/>"
            unpracticed_text += "• Comienza con dificultad baja: empieza con ejercicios de nivel 1-2 para construir confianza.<br/><br/>"
            
            story.append(Paragraph(unpracticed_text, styles["Texto"]))
            story.append(Spacer(1, 8))
        
        # Resumen de distribución de esfuerzo
        if len(practiced_courses) > 1:
            story.append(Paragraph("<b>📊 Distribución de esfuerzo:</b>", styles["Texto"]))
            
            total_topics_all = sum(c["unique_topics"] for c in practiced_courses)
            total_exercises_all = sum(c["exercises_count"] for c in practiced_courses)
            
            distribution_text = f"""
            Has practicado {len(practiced_courses)} de {len(subscribed_course_ids)} cursos suscritos.<br/>
            • Total de temas practicados: {total_topics_all}<br/>
            • Total de ejercicios generados: {total_exercises_all}<br/><br/>
            """
            
            if len(practiced_courses) < len(subscribed_course_ids):
                distribution_text += f"<b>Sugerencia:</b> Considera distribuir tu tiempo entre todos tus cursos. "
                distribution_text += f"Tienes {len(unpracticed_courses)} curso(s) sin actividad que podrían beneficiarse de atención.<br/><br/>"
            
            story.append(Paragraph(distribution_text, styles["Texto"]))
        else:
            story.append(
                Paragraph(
                    "<b>Nota:</b> Solo has practicado un curso. Considera explorar otros cursos de tu suscripción para un aprendizaje más completo.",
                    styles["Texto"],
                )
            )
    else:
        story.append(
            Paragraph(
                "No se encontraron datos de cursos para analizar. Asegúrate de tener suscripciones activas y haber practicado al menos un ejercicio.",
            styles["Texto"],
        )
    )
    
    story.append(Spacer(1, 12))

    # Recomendaciones generales mejoradas basadas en patrones detectados
    general_recs = []
    
    if study_frequency == "baja":
        general_recs.append("Aumenta la frecuencia de estudio: intenta practicar al menos cada 2-3 días para mantener el ritmo.")
    
    if study_consistency == "irregular":
        general_recs.append("Establece un horario fijo de estudio: la consistencia es clave para el aprendizaje efectivo.")
    
    if current_streak < 3:
        general_recs.append("Mantén tu racha de estudio: practica diariamente para construir hábitos sólidos.")
    
    high_risk_count = len(df_topics[df_topics["risk"] == "Alto"])
    if high_risk_count > 2:
        general_recs.append(f"Tienes {high_risk_count} temas de alta prioridad: enfócate en uno a la vez para evitar sobrecarga.")
    
    improving_topics = len(df_topics[df_topics["temporal_trend"] == "mejorando"])
    if improving_topics > 0:
        general_recs.append(f"Excelente: {improving_topics} tema(s) muestran mejora continua. Mantén este enfoque en los demás.")
    
    if not general_recs:
        general_recs = [
            "Continúa con tu rutina actual: estás en buen camino.",
            "Revisa semanalmente tus temas débiles para mantener el progreso.",
            "Usa ejercicios adaptativos para medir tu evolución."
        ]

    general_text = "<b>📋 Recomendaciones generales de estudio:</b><br/>"
    for rec in general_recs:
        general_text += f"• {rec}<br/>"
    
    story.append(Paragraph(general_text, styles["Texto"]))

    pdf.build(story)
    buffer.seek(0)

    pdf_b64 = b64encode(buffer.read()).decode("utf-8")

    st.success("✅ Reporte PDF generado correctamente.")

    with st.expander("Vista previa del reporte"):
        pdf_display = (
            f'<iframe src="data:application/pdf;base64,{pdf_b64}" width="100%" height="600px"></iframe>'
        )
        st.markdown(pdf_display, unsafe_allow_html=True)

    st.download_button(
        label="📥 Descargar Reporte PDF",
        data=buffer.getvalue(),
        file_name=f"reporte_tutor_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
    )

