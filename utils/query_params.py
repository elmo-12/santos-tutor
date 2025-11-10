"""Helpers para sincronizar el estado de la aplicación con la URL."""

import streamlit as st


def get_query_params() -> dict:
    """Obtiene los parámetros de consulta de la URL de forma segura."""
    try:
        return dict(st.query_params)
    except Exception:
        try:
            return st.experimental_get_query_params()
        except Exception:
            return {}


def set_query_params(**params):
    """Actualiza los parámetros de consulta evitando interrupciones."""
    try:
        st.query_params.update(params)
    except Exception:
        try:
            st.experimental_set_query_params(**params)
        except Exception:
            pass


def remove_query_params(*keys: str):
    """Elimina parámetros específicos de la URL."""
    try:
        params = dict(st.query_params)
    except Exception:
        try:
            params = st.experimental_get_query_params()
        except Exception:
            params = {}
    for key in keys:
        params.pop(key, None)
    try:
        st.set_query_params(**params)
    except Exception:
        try:
            st.experimental_set_query_params(**params)
        except Exception:
            pass

