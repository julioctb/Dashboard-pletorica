"""
Constantes fiscales y de negocio para México 2026.

NOTA: Este módulo ahora es un facade que re-exporta desde los catálogos.
Para nuevo código, importar directamente desde app.core.catalogs.

Ejemplo:
    # Nuevo (recomendado):
    from app.core.catalogs import CatalogoUMA, CatalogoIMSS

    # Legacy (compatible):
    from app.core.fiscales import ConstantesFiscales
"""

from app.core.catalogs import (
    CatalogoUMA,
    CatalogoIMSS,
    CatalogoISR,
    CatalogoISN,
    CatalogoINFONAVIT,
    CatalogoVacaciones,
    CatalogoPrestaciones,
)


class ConstantesFiscales:
    """
    Constantes fiscales 2026.

    DEPRECADO: Usar directamente los catálogos:
        from app.core.catalogs import CatalogoUMA, CatalogoIMSS

    Esta clase se mantiene para compatibilidad con código existente.
    """

    # Año fiscal
    ANO = CatalogoUMA.ANO

    # ─────────────────────────────────────────────────────────────────────────
    # UMA - Re-exportado desde CatalogoUMA
    # ─────────────────────────────────────────────────────────────────────────
    UMA_DIARIO = float(CatalogoUMA.DIARIO)
    UMA_MENSUAL = float(CatalogoUMA.MENSUAL)

    # ─────────────────────────────────────────────────────────────────────────
    # SALARIOS MÍNIMOS - Re-exportado desde CatalogoPrestaciones
    # ─────────────────────────────────────────────────────────────────────────
    SALARIO_MINIMO_GENERAL = float(CatalogoPrestaciones.SALARIO_MINIMO_GENERAL)
    SALARIO_MINIMO_FRONTERA = float(CatalogoPrestaciones.SALARIO_MINIMO_FRONTERA)

    # ─────────────────────────────────────────────────────────────────────────
    # IMSS - Re-exportado desde CatalogoIMSS
    # ─────────────────────────────────────────────────────────────────────────

    # Enfermedades y Maternidad
    IMSS_CUOTA_FIJA = float(CatalogoIMSS.CUOTA_FIJA)
    IMSS_EXCEDENTE_PAT = float(CatalogoIMSS.EXCEDENTE_PATRONAL)
    IMSS_EXCEDENTE_OBR = float(CatalogoIMSS.EXCEDENTE_OBRERO)
    IMSS_PREST_DINERO_PAT = float(CatalogoIMSS.PREST_DINERO_PATRONAL)
    IMSS_PREST_DINERO_OBR = float(CatalogoIMSS.PREST_DINERO_OBRERO)
    IMSS_GASTOS_MED_PENS_PAT = float(CatalogoIMSS.GASTOS_MED_PATRONAL)
    IMSS_GASTOS_MED_PENS_OBR = float(CatalogoIMSS.GASTOS_MED_OBRERO)

    # Invalidez y Vida
    IMSS_INVALIDEZ_VIDA_PAT = float(CatalogoIMSS.INVALIDEZ_VIDA_PATRONAL)
    IMSS_INVALIDEZ_VIDA_OBR = float(CatalogoIMSS.INVALIDEZ_VIDA_OBRERO)

    # Guarderías y Prestaciones Sociales
    IMSS_GUARDERIAS = float(CatalogoIMSS.GUARDERIAS)

    # Retiro, Cesantía y Vejez
    IMSS_RETIRO = float(CatalogoIMSS.RETIRO)
    IMSS_CESANTIA_VEJEZ_PAT = float(CatalogoIMSS.CESANTIA_VEJEZ_PATRONAL)
    IMSS_CESANTIA_VEJEZ_OBR = float(CatalogoIMSS.CESANTIA_VEJEZ_OBRERO)

    # ─────────────────────────────────────────────────────────────────────────
    # INFONAVIT - Re-exportado desde CatalogoINFONAVIT
    # ─────────────────────────────────────────────────────────────────────────
    INFONAVIT_PAT = float(CatalogoINFONAVIT.TASA_PATRONAL)

    # ─────────────────────────────────────────────────────────────────────────
    # TOPES - Re-exportado desde CatalogoUMA
    # ─────────────────────────────────────────────────────────────────────────
    TOPE_SBC_DIARIO = float(CatalogoUMA.TOPE_SBC)
    TRES_UMA = float(CatalogoUMA.TRES_UMA)

    # ─────────────────────────────────────────────────────────────────────────
    # SUBSIDIO AL EMPLEO - Re-exportado desde CatalogoISR
    # ─────────────────────────────────────────────────────────────────────────
    SUBSIDIO_PORCENTAJE = float(CatalogoISR.SUBSIDIO_PORCENTAJE)
    SUBSIDIO_EMPLEO_MENSUAL = float(CatalogoISR.SUBSIDIO_MENSUAL)
    LIMITE_SUBSIDIO_MENSUAL = float(CatalogoISR.LIMITE_SUBSIDIO)

    # ─────────────────────────────────────────────────────────────────────────
    # TABLA ISR - Re-exportado desde CatalogoISR
    # ─────────────────────────────────────────────────────────────────────────
    TABLA_ISR_MENSUAL = [
        (float(r.limite_inferior), float(r.limite_superior), float(r.cuota_fija), float(r.tasa_excedente))
        for r in CatalogoISR.TABLA_MENSUAL
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # VACACIONES - Re-exportado desde CatalogoVacaciones
    # ─────────────────────────────────────────────────────────────────────────
    DIAS_VACACIONES_POR_ANO = CatalogoVacaciones.TABLA

    @classmethod
    def dias_vacaciones(cls, antiguedad_anos: int) -> int:
        """Obtiene días de vacaciones por antigüedad."""
        return CatalogoVacaciones.obtener_dias(antiguedad_anos)


# ═══════════════════════════════════════════════════════════════════════════
# ISN POR ESTADO - Re-exportado desde CatalogoISN
# ═══════════════════════════════════════════════════════════════════════════

ISN_POR_ESTADO = {k: float(v) for k, v in CatalogoISN.TASAS.items()}
