"""Helpers centralizados para captura manual y normalización de fechas en UI."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


DATE_INPUT_DISPLAY_FORMAT = "%d/%m/%Y"


def _autoformat_date_digits(raw: str) -> str:
    """Inserta diagonales automáticamente al capturar fechas manuales."""
    if not raw:
        return ""

    if all(ch.isdigit() or ch == "/" for ch in raw):
        digits = "".join(ch for ch in raw if ch.isdigit())[:8]
        trailing_slash = raw.endswith("/")
        if len(digits) <= 2:
            if trailing_slash and len(digits) == 2:
                return f"{digits}/"
            return digits
        if len(digits) <= 4:
            partial = f"{digits[:2]}/{digits[2:]}"
            if trailing_slash and len(digits) == 4:
                return f"{partial}/"
            return partial
        return f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"

    return raw


def parse_date_input(value: Any) -> date | None:
    """Convierte fechas ISO o DD/MM/AAAA a ``date``.

    Retorna ``None`` para valores vacíos o formatos inválidos.
    """
    if value in (None, ""):
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    raw = str(value).strip()
    if not raw:
        return None

    for parser in (
        date.fromisoformat,
        lambda v: datetime.strptime(v, DATE_INPUT_DISPLAY_FORMAT).date(),
    ):
        try:
            return parser(raw)
        except ValueError:
            continue

    return None


def normalize_date_input(value: Any) -> str:
    """Normaliza un input de fecha a ISO cuando ya es válido.

    Si el valor aún es parcial o inválido, se conserva para no romper la captura
    manual mientras el usuario sigue escribiendo.
    """
    if value in (None, ""):
        return ""

    raw = _autoformat_date_digits(str(value).strip())

    parsed = parse_date_input(raw)
    if parsed is not None:
        return parsed.isoformat()

    return raw


def format_date_input_display(value: Any) -> str:
    """Formatea una fecha válida al patrón visible DD/MM/AAAA."""
    parsed = parse_date_input(value)
    if parsed is None:
        return str(value or "").strip()
    return parsed.strftime(DATE_INPUT_DISPLAY_FORMAT)


def get_date_input_inline_error(value: Any) -> str:
    """Devuelve error inline cuando el año capturado es incompleto."""
    raw = str(value or "").strip()
    if not raw:
        return ""

    parts = raw.split("/")
    if len(parts) != 3:
        return ""

    year = parts[2].strip()
    if year and year.isdigit() and len(year) < 4:
        return "Capture el año completo en formato AAAA"

    return ""
