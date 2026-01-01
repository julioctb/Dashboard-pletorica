"""
Módulo de formatters - Formateo de resultados para presentación.

Responsabilidad: Transformar resultados de cálculos en formatos legibles
para diferentes canales de salida (terminal, web, PDF, etc.).

Exporta:
- ResultadoFormatter: Formateador de ResultadoCuotas

Uso:
    from app.core.formatters import ResultadoFormatter

    # Para terminal
    ResultadoFormatter.imprimir(resultado)

    # Para UI web (Reflex)
    ui_data = ResultadoFormatter.formatear_para_ui(resultado)
"""

from .resultado_formatter import ResultadoFormatter

__all__ = [
    "ResultadoFormatter",
]
