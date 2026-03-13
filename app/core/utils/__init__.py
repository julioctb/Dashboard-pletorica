"""
Utilidades del core - funciones puras reutilizables.
"""
from .codigo_generator import (
    generar_candidatos_codigo,
    generar_codigo_nivel1,
    generar_codigo_nivel2,
    extraer_palabras_significativas,
    normalizar_texto,
    PALABRAS_IGNORAR,
)
from .date_input import (
    DATE_INPUT_DISPLAY_FORMAT,
    format_date_input_display,
    get_date_input_inline_error,
    normalize_date_input,
    parse_date_input,
)

__all__ = [
    "generar_candidatos_codigo",
    "generar_codigo_nivel1",
    "generar_codigo_nivel2",
    "extraer_palabras_significativas",
    "normalizar_texto",
    "PALABRAS_IGNORAR",
    "DATE_INPUT_DISPLAY_FORMAT",
    "format_date_input_display",
    "get_date_input_inline_error",
    "normalize_date_input",
    "parse_date_input",
]
