"""
Catálogo de conceptos de nómina.

Uso:
    from app.core.catalogs import CatalogoConceptosNomina
"""
from app.core.catalogs.nomina.conceptos import CatalogoConceptosNomina, ConceptoNominaDef
from app.core.catalogs.nomina.enums import CategoriaConcepto
from app.core.catalogs.nomina.periodos import (
    PeriodoNominaCalculado,
    calcular_fecha_pago_mensual,
    calcular_fecha_pago_quincena,
    calcular_fecha_pago_semanal,
    calcular_rango_mensual,
    calcular_rango_quincena,
    calcular_rango_semana,
    compactar_nombre_quincena,
    construir_mes_nomina,
    construir_quincena_nomina,
    construir_semana_nomina,
    detectar_periodo_actual,
    etiquetar_quincena,
    formatear_rango_periodo_corto,
    generar_catalogo_meses,
    generar_catalogo_periodos,
    generar_catalogo_quincenas,
    generar_catalogo_semanas,
    nombre_mes_es,
    resolver_mes_por_key,
    resolver_periodo_por_key,
    resolver_quincena_por_key,
    resolver_semana_por_key,
)

__all__ = [
    "CatalogoConceptosNomina",
    "ConceptoNominaDef",
    "CategoriaConcepto",
    "PeriodoNominaCalculado",
    "calcular_fecha_pago_mensual",
    "calcular_fecha_pago_quincena",
    "calcular_fecha_pago_semanal",
    "calcular_rango_mensual",
    "calcular_rango_quincena",
    "calcular_rango_semana",
    "compactar_nombre_quincena",
    "construir_mes_nomina",
    "construir_quincena_nomina",
    "construir_semana_nomina",
    "detectar_periodo_actual",
    "etiquetar_quincena",
    "formatear_rango_periodo_corto",
    "generar_catalogo_meses",
    "generar_catalogo_periodos",
    "generar_catalogo_quincenas",
    "generar_catalogo_semanas",
    "nombre_mes_es",
    "resolver_mes_por_key",
    "resolver_periodo_por_key",
    "resolver_quincena_por_key",
    "resolver_semana_por_key",
]
