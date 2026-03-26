"""Compatibilidad para helpers quincenales sobre el motor generico de periodos."""

from core.core.catalogs.nomina.periodos import (
    PeriodoNominaCalculado as QuincenaNomina,
    calcular_fecha_pago_quincena,
    calcular_rango_quincena,
    compactar_nombre_quincena,
    construir_quincena_nomina,
    etiquetar_quincena,
    generar_catalogo_quincenas,
    nombre_mes_es,
    resolver_quincena_por_key,
)

__all__ = [
    "QuincenaNomina",
    "calcular_fecha_pago_quincena",
    "calcular_rango_quincena",
    "compactar_nombre_quincena",
    "construir_quincena_nomina",
    "etiquetar_quincena",
    "generar_catalogo_quincenas",
    "nombre_mes_es",
    "resolver_quincena_por_key",
]
