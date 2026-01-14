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

__all__ = [
    "generar_candidatos_codigo",
    "generar_codigo_nivel1",
    "generar_codigo_nivel2",
    "extraer_palabras_significativas",
    "normalizar_texto",
    "PALABRAS_IGNORAR",
]
