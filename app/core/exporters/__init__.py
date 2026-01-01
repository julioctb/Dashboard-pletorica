"""
Módulo de exporters - Exportación de resultados.

Responsabilidad: Generar archivos en diferentes formatos (Excel, PDF, CSV, etc.)
a partir de resultados de cálculos.

Exporta:
- ExcelExporter: Exportador a formato Excel (.xlsx)

Uso:
    from app.core.exporters import ExcelExporter

    exporter = ExcelExporter()
    archivo = exporter.exportar(resultados, "nomina_enero.xlsx")
"""

from .excel_exporter import ExcelExporter

__all__ = [
    "ExcelExporter",
]
