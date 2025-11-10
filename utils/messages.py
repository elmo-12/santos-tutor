"""Funciones utilitarias relacionadas con el manejo de mensajes del chat."""

import json
from typing import Any, List

import pandas as pd


def display_text(content: Any) -> str:
    """Devuelve texto legible a partir de distintos formatos guardados en la BD."""
    try:
        if content is None:
            return ""
        if isinstance(content, dict):
            for key in (
                "text",
                "content",
                "message",
                "respuesta",
                "Respuesta",
                "Mensaje guía",
                "mensaje",
            ):
                if key in content and content[key]:
                    return display_text(content[key])
            return json.dumps(content, ensure_ascii=False)
        if isinstance(content, list):
            return "\n".join(display_text(item) for item in content if item is not None)
        if isinstance(content, str):
            stripped = content.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                try:
                    obj = json.loads(stripped)
                    return display_text(obj)
                except Exception:
                    return content
            return content
        return str(content)
    except Exception:
        try:
            return str(content)
        except Exception:
            return ""


def dedup_messages(messages: List[dict], window_seconds: int = 5) -> List[dict]:
    """Elimina duplicados consecutivos en función del rol y el contenido."""
    try:
        result = []
        last = None

        def _to_ts(message):
            try:
                return pd.to_datetime(message.get("created_at")).timestamp()
            except Exception:
                return None

        for message in messages or []:
            if not result:
                result.append(message)
                last = message
                continue
            same_role = message.get("role") == last.get("role")
            same_text = display_text(message.get("content")) == display_text(last.get("content"))
            if same_role and same_text:
                current_ts, last_ts = _to_ts(message), _to_ts(last)
                if (
                    current_ts is not None
                    and last_ts is not None
                    and abs(current_ts - last_ts) <= window_seconds
                ):
                    continue
            result.append(message)
            last = message
        return result
    except Exception:
        return messages or []

