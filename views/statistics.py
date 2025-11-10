"""Vista que muestra paneles y métricas de estadísticas."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.supabase_client import SupabaseClient


def render_statistics_interface(sb_client: SupabaseClient):
    """Renderiza el panel de estadísticas de aprendizaje."""
    st.title("📊 Panel de Estadísticas de Aprendizaje")
    st.markdown("Aquí puedes revisar tu evolución, hábitos y desempeño general.")

    difficulty_data = sb_client.get_difficulty_stats(st.session_state.user_id)
    exercise_data = sb_client.get_exercise_stats(st.session_state.user_id)

    if not difficulty_data and not exercise_data:
        st.info("Aún no hay datos suficientes para mostrar estadísticas.")
        return

    df_difficulty = pd.DataFrame(difficulty_data)
    df_exercises = pd.DataFrame(exercise_data) if exercise_data else pd.DataFrame()

    st.markdown("### 📌 Resumen General")

    with st.container():
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_topics = len(df_difficulty["topic"].unique()) if not df_difficulty.empty else 0
            st.metric("Temas Estudiados", total_topics)

        with col2:
            avg_difficulty = (
                df_difficulty["difficulty_level"].mean() if not df_difficulty.empty else 0
            )
            st.metric("Dificultad Promedio", f"{avg_difficulty:.1f}/5")

        with col3:
            completed_exercises = (
                len(df_exercises[df_exercises["completed"] == True])  # noqa: E712
                if not df_exercises.empty
                else 0
            )
            st.metric("Ejercicios Completados", completed_exercises)

        with col4:
            total_ok = df_difficulty["success_count"].sum()
            total_err = df_difficulty["error_count"].sum()
            success_rate = (total_ok / (total_ok + total_err) * 100) if (total_ok + total_err) > 0 else 0
            st.metric("Tasa de Éxito", f"{success_rate:.1f}%")

    st.markdown("---")

    st.markdown("### 🔎 Indicadores Avanzados")

    # --- Cálculo base ---
    grouped = df_difficulty.groupby("topic").agg({
        "success_count": "sum",
        "error_count": "sum"
    })

    # Total de intentos
    grouped["attempts"] = grouped["success_count"] + grouped["error_count"]

    # Tasa de éxito
    grouped["success_rate"] = grouped["success_count"] / grouped["attempts"].replace(0, 1)

    # --- Indicadores por tasa de éxito ---
    best_topic = grouped["success_rate"].idxmax()
    worst_topic = grouped["success_rate"].idxmin()

    colA, colB = st.columns(2)

    with colA:
        st.success(
            f"✅ Mejor Tema (mayor tasa de éxito): **{best_topic}** "
            f"({grouped.loc[best_topic, 'success_rate']*100:.1f}%)"
        )

    with colB:
        st.warning(
            f"🟠 Tema con más oportunidad (menor tasa de éxito): **{worst_topic}** "
            f"({grouped.loc[worst_topic, 'success_rate']*100:.1f}%)"
        )

    # --- Indicadores según número de intentos ---
    most_attempts_topic = grouped["attempts"].idxmax()
    least_attempts_topic = grouped["attempts"].idxmin()

    st.info(
        f"📌 Tema con **más intentos**: **{most_attempts_topic}** "
        f"({grouped.loc[most_attempts_topic, 'attempts']} intentos)"
    )

    st.markdown("---")

    st.markdown("### 📌 Hábitos de Estudio")

    colA, colB, colC = st.columns(3)

    with colA:
        if not df_exercises.empty:
            df_exercises["date"] = pd.to_datetime(df_exercises["created_at"]).dt.date
            streak = 0
            today = pd.Timestamp.now().date()
            day = today

            dates = set(df_exercises["date"].tolist())

            while day in dates:
                streak += 1
                day -= pd.Timedelta(days=1)

            st.metric("🔥 Racha Activa", f"{streak} día(s)")

    with colB:
        if not df_exercises.empty:
            dates_sorted = sorted(df_exercises["date"].unique())
            if len(dates_sorted) > 1:
                diffs = [
                    (dates_sorted[i] - dates_sorted[i - 1]).days for i in range(1, len(dates_sorted))
                ]
                avg_interval = sum(diffs) / len(diffs)
                st.metric("⏱️ Intervalo entre sesiones", f"{avg_interval:.1f} días")

    with colC:
        if not df_difficulty.empty:
            difficulty_var = df_difficulty["difficulty_level"].var()
            st.metric("📉 Variación de dificultad", f"{difficulty_var:.2f}")

    st.markdown("---")

    st.markdown("### 📈 Visualizaciones")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        if not df_difficulty.empty:
            st.subheader("Dificultad por Tema")

            df_difficulty["difficulty_level"] = pd.to_numeric(
                df_difficulty["difficulty_level"], errors="coerce"
            )

            df_plot = (
                df_difficulty.groupby("topic", as_index=False)["difficulty_level"].mean().dropna()
            )

            fig = px.pie(
                df_plot,
                names="topic",
                values="difficulty_level",
                hole=0.35,
            )

            fig.update_layout(legend_title="Temas")

            st.plotly_chart(fig, use_container_width=True)

    with col_chart2:
        if not df_difficulty.empty:
            st.subheader("Progreso Diario")

            df_difficulty["date"] = pd.to_datetime(df_difficulty["last_practiced"]).dt.date
            daily = df_difficulty.groupby("date").agg(
                {"success_count": "sum", "error_count": "sum"}
            ).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily["date"], y=daily["success_count"], name="Éxitos"))
            fig.add_trace(go.Scatter(x=daily["date"], y=daily["error_count"], name="Errores"))
            fig.update_layout(xaxis_title="Fecha", yaxis_title="Cantidad")

            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    if not df_exercises.empty:
        st.markdown("### 🔥 Actividad Semanal")

        df_exercises["date"] = pd.to_datetime(df_exercises["created_at"]).dt.date
        activity = df_exercises.groupby("date").size().reset_index(name="count")
        activity_pivot = activity.pivot_table(
        values="count",
        index=pd.to_datetime(activity["date"]).dt.dayofweek,
        columns=activity["date"].astype(str),
        fill_value=0,
        )   

        day_labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        activity_pivot = activity_pivot.reindex(index=range(7), fill_value=0)

        fig = px.imshow(
                activity_pivot.values,
                labels=dict(x="Fecha", y="Día", color="Ejercicios"),
                x=list(activity_pivot.columns),
                y=day_labels,
                aspect="auto",
                color_continuous_scale="YlGnBu",
        )

        st.plotly_chart(fig, use_container_width=True)
        