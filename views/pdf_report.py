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

    table_data = [["Tema", "Dificultad Promedio", "Éxitos", "Errores", "Tasa de Éxito"]]
    for _, topic in topic_analysis.iterrows():
        total = topic["success_count"] + topic["error_count"]
        success_rate = (topic["success_count"] / total * 100) if total > 0 else 0
        table_data.append(
            [
                topic["topic"],
                f"{topic['difficulty_level']:.1f}/5",
                str(topic["success_count"]),
                str(topic["error_count"]),
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

    df_diff = pd.DataFrame(difficulty_data)
    df_ex = pd.DataFrame(exercise_data) if exercise_data else pd.DataFrame()

    df_topics = df_diff.groupby("topic").agg(
        total_errors=("error_count", "sum"),
        total_success=("success_count", "sum"),
        avg_difficulty=("difficulty_level", "mean"),
    ).reset_index()

    df_topics["success_rate"] = df_topics.apply(
        lambda row: row.total_success / (row.total_success + row.total_errors)
        if (row.total_success + row.total_errors) > 0
        else 0,
        axis=1,
    )

    def classify_risk(row):
        if row.avg_difficulty > 4 and row.success_rate < 0.40:
            return "Alto"
        if row.avg_difficulty > 3 or row.success_rate < 0.60:
            return "Medio"
        return "Bajo"

    df_topics["risk"] = df_topics.apply(classify_risk, axis=1)

    df_topics["weighted_score"] = df_topics.apply(
        lambda row: (1 - row["success_rate"]) * 0.7 + (row["avg_difficulty"] / 5) * 0.3,
        axis=1,
    )

    worst_topic = df_topics.sort_values("weighted_score", ascending=False).iloc[0]
    df_filtered = df_topics[df_topics["topic"] != worst_topic["topic"]]

    rec_text = f"""
    Este apartado resume tus patrones de desempeño y las áreas donde conviene fortalecer, mantener o consolidar aprendizajes.<br/><br/>
    <b>Tema más crítico:</b><br/>
    - Tema: {worst_topic['topic']}<br/>
    - Dificultad promedio: {worst_topic['avg_difficulty']:.1f}/5<br/>
    - Tasa de éxito: {worst_topic['success_rate']*100:.1f}%<br/><br/>
    <b>Sugerencias:</b><br/>
    • Repasar fundamentos teóricos.<br/>
    • Empezar con ejercicios guiados.<br/>
    • Sesiones breves enfocadas solo en este tema.<br/><br/>
    """

    story.append(Paragraph(rec_text, styles["Texto"]))

    for level, label in [
        ("Alto", "Temas de atención prioritaria"),
        ("Medio", "Temas en consolidación"),
        ("Bajo", "Temas dominados"),
    ]:
        subset = df_filtered[df_filtered["risk"] == level]
        if not subset.empty:
            story.append(Paragraph(f"<b>{label}</b>", styles["Texto"]))
            lines = ""
            for _, row in subset.iterrows():
                lines += (
                    f"• {row['topic']} — dificultad {row['avg_difficulty']:.1f}/5, "
                    f"éxito {row['success_rate']*100:.1f}%<br/>"
                )
            story.append(Paragraph(lines, styles["SubTexto"]))
            story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            """
    <b>Recomendaciones generales</b><br/>
    • Estudia en sesiones distribuidas.<br/>
    • Revisa semanalmente los temas débiles.<br/>
    • Usa ejercicios adaptativos para medir progreso.<br/>
    """,
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

