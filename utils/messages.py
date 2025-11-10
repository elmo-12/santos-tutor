"""Funciones utilitarias relacionadas con el manejo de mensajes del chat."""

import json
import re
from typing import Any, List

import pandas as pd

LATEX_INLINE_PATTERN = re.compile(r"\((\\[^()\n]*?)\)")
LATEX_PAREN_PATTERN = re.compile(r"\\\((.*?)\\\)", re.DOTALL)
LATEX_BRACKET_PATTERN = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
MATH_TOKEN_PATTERN = re.compile(r"(\$\$.*?\$\$|\$.*?\$)", re.DOTALL)


def _normalize_math_segments(text: str) -> str:
    """Convierte segmentos como (\frac{1}{2}) en delimitadores LaTeX estándar."""

    def _wrap(match: re.Match) -> str:
        trimmed = match.group(1).strip().rstrip("\\")
        if trimmed.startswith(("\\(", "\\[", "$")):
            return match.group(0)
        return f"${trimmed}$"

    text = LATEX_INLINE_PATTERN.sub(_wrap, text)
    text = LATEX_PAREN_PATTERN.sub(lambda m: f"${m.group(1).strip()}$", text)
    text = LATEX_BRACKET_PATTERN.sub(lambda m: f"$${m.group(1).strip()}$$", text)
    return text


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
                    return _normalize_math_segments(content)
            return _normalize_math_segments(content)
        return _normalize_math_segments(str(content))
    except Exception:
        try:
            return _normalize_math_segments(str(content))
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


def render_markdown_with_math(text: str):
    """Renderiza texto con soporte para segmentos LaTeX usando st.markdown/st.latex."""
    from streamlit import latex, markdown  # lazy import to evitar ciclos

    normalized = _normalize_math_segments(text)
    normalized = re.sub(r"(?m)^\s*\\\s*$", "", normalized)
    normalized = re.sub(r"\\\s*\n", "\n", normalized)
    normalized = normalized.replace("\\\\", "")
    parts = MATH_TOKEN_PATTERN.split(normalized)

    for part in parts:
        if not part:
            continue
        stripped = part.strip()
        if not stripped:
            continue
        if stripped == "\\":
            continue
        clean = stripped
        while clean.endswith("\\"):
            clean = clean[:-1].rstrip()
        sanitized_part = re.sub(r"\\\s*\n", "\n", part)
        if clean.startswith("$$") and clean.endswith("$$") and len(clean) > 4:
            latex(clean[2:-2].strip())
        elif clean.startswith("$") and clean.endswith("$") and len(clean) > 2:
            latex(clean[1:-1].strip())
        else:
            markdown(sanitized_part, unsafe_allow_html=True)

