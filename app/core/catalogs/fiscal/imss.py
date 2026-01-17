"""
Catálogo de tasas IMSS (Instituto Mexicano del Seguro Social).

Contiene todas las tasas de cotización para las diferentes ramas
del seguro social, tanto patronales como obreras.

Fuente: Ley del Seguro Social
Artículos: 25, 106, 107, 147, 168
"""

from decimal import Decimal
from typing import ClassVar
from dataclasses import dataclass
from enum import Enum


class RamaSeguro(str, Enum):
    """Ramas del seguro social."""
    ENFERMEDAD_MATERNIDAD = "enfermedad_maternidad"
    INVALIDEZ_VIDA = "invalidez_vida"
    RETIRO = "retiro"
    CESANTIA_VEJEZ = "cesantia_vejez"
    GUARDERIAS = "guarderias"
    RIESGO_TRABAJO = "riesgo_trabajo"


@dataclass(frozen=True)
class TasaIMSS:
    """Representa una tasa de cotización IMSS."""
    concepto: str
    patronal: Decimal
    obrero: Decimal
    base: str
    rama: RamaSeguro

    @property
    def total(self) -> Decimal:
        """Suma de tasa patronal + obrera."""
        return self.patronal + self.obrero


class CatalogoIMSS:
    """
    Tasas de cotización IMSS 2026.

    Incluye todas las ramas del seguro social con sus respectivas
    cuotas patronales y obreras.

    Uso:
        from app.core.catalogs import CatalogoIMSS

        cuota = sbc * CatalogoIMSS.CUOTA_FIJA
        total_pat = CatalogoIMSS.total_patronal_fijo()
    """

    # ═══════════════════════════════════════════════════════════════
    # METADATOS
    # ═══════════════════════════════════════════════════════════════
    ANO: ClassVar[int] = 2026
    FUENTE: ClassVar[str] = "Ley del Seguro Social"
    ARTICULOS: ClassVar[list[str]] = ["Art. 25", "Art. 106", "Art. 147"]
    NOTAS: ClassVar[str] = "Cesantía en transición por reforma 2020-2030"

    # ═══════════════════════════════════════════════════════════════
    # ENFERMEDAD Y MATERNIDAD
    # ═══════════════════════════════════════════════════════════════

    # Cuota fija (solo patronal, sobre UMA hasta 3 UMA)
    CUOTA_FIJA: ClassVar[Decimal] = Decimal("0.204")  # 20.4%

    # Excedente de 3 UMA
    EXCEDENTE_PATRONAL: ClassVar[Decimal] = Decimal("0.011")   # 1.10%
    EXCEDENTE_OBRERO: ClassVar[Decimal] = Decimal("0.004")     # 0.40%

    # Prestaciones en dinero
    PREST_DINERO_PATRONAL: ClassVar[Decimal] = Decimal("0.007")   # 0.70%
    PREST_DINERO_OBRERO: ClassVar[Decimal] = Decimal("0.0025")    # 0.25%

    # Gastos médicos para pensionados
    GASTOS_MED_PATRONAL: ClassVar[Decimal] = Decimal("0.0105")    # 1.05%
    GASTOS_MED_OBRERO: ClassVar[Decimal] = Decimal("0.00375")     # 0.375%

    # ═══════════════════════════════════════════════════════════════
    # INVALIDEZ Y VIDA
    # ═══════════════════════════════════════════════════════════════
    INVALIDEZ_VIDA_PATRONAL: ClassVar[Decimal] = Decimal("0.0175")   # 1.75%
    INVALIDEZ_VIDA_OBRERO: ClassVar[Decimal] = Decimal("0.00625")    # 0.625%

    # ═══════════════════════════════════════════════════════════════
    # GUARDERÍAS Y PRESTACIONES SOCIALES (solo patronal)
    # ═══════════════════════════════════════════════════════════════
    GUARDERIAS: ClassVar[Decimal] = Decimal("0.01")  # 1.00%

    # ═══════════════════════════════════════════════════════════════
    # RETIRO, CESANTÍA Y VEJEZ
    # ═══════════════════════════════════════════════════════════════
    RETIRO: ClassVar[Decimal] = Decimal("0.02")  # 2.00% (solo patronal)

    # Cesantía y Vejez - REFORMA GRADUAL 2020-2030
    # 2026: incremento de 0.175% respecto a 2025
    CESANTIA_VEJEZ_PATRONAL: ClassVar[Decimal] = Decimal("0.03513")  # 3.513%
    CESANTIA_VEJEZ_OBRERO: ClassVar[Decimal] = Decimal("0.01125")    # 1.125%

    # Histórico de tasas patronales de cesantía (para referencia)
    CESANTIA_VEJEZ_HISTORICO: ClassVar[dict[int, Decimal]] = {
        2026: Decimal("0.03513"),  # +0.175%
        2025: Decimal("0.03338"),  # +0.175%
        2024: Decimal("0.03163"),  # +0.175%
        2023: Decimal("0.02988"),
        # ... continúa hasta 2030 donde será 8.625%
    }

    # ═══════════════════════════════════════════════════════════════
    # DATOS ESTRUCTURADOS (para iteración/reportes)
    # ═══════════════════════════════════════════════════════════════

    TASAS: ClassVar[list[TasaIMSS]] = [
        TasaIMSS("Cuota fija", Decimal("0.204"), Decimal("0"), "SBC hasta 3 UMA", RamaSeguro.ENFERMEDAD_MATERNIDAD),
        TasaIMSS("Excedente 3 UMA", Decimal("0.011"), Decimal("0.004"), "SBC excedente", RamaSeguro.ENFERMEDAD_MATERNIDAD),
        TasaIMSS("Prest. en dinero", Decimal("0.007"), Decimal("0.0025"), "SBC", RamaSeguro.ENFERMEDAD_MATERNIDAD),
        TasaIMSS("Gastos médicos", Decimal("0.0105"), Decimal("0.00375"), "SBC", RamaSeguro.ENFERMEDAD_MATERNIDAD),
        TasaIMSS("Invalidez y vida", Decimal("0.0175"), Decimal("0.00625"), "SBC", RamaSeguro.INVALIDEZ_VIDA),
        TasaIMSS("Guarderías", Decimal("0.01"), Decimal("0"), "SBC", RamaSeguro.GUARDERIAS),
        TasaIMSS("Retiro", Decimal("0.02"), Decimal("0"), "SBC", RamaSeguro.RETIRO),
        TasaIMSS("Cesantía y vejez", Decimal("0.03513"), Decimal("0.01125"), "SBC", RamaSeguro.CESANTIA_VEJEZ),
    ]

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE CÁLCULO
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def total_patronal_fijo(cls) -> Decimal:
        """
        Total de cuotas patronales fijas (sin riesgo de trabajo).

        El riesgo de trabajo varía por empresa, por eso no se incluye.
        """
        return (
            cls.CUOTA_FIJA +
            cls.EXCEDENTE_PATRONAL +
            cls.PREST_DINERO_PATRONAL +
            cls.GASTOS_MED_PATRONAL +
            cls.INVALIDEZ_VIDA_PATRONAL +
            cls.GUARDERIAS +
            cls.RETIRO +
            cls.CESANTIA_VEJEZ_PATRONAL
        )

    @classmethod
    def total_obrero(cls) -> Decimal:
        """Total de cuotas que se descuentan al trabajador."""
        return (
            cls.EXCEDENTE_OBRERO +
            cls.PREST_DINERO_OBRERO +
            cls.GASTOS_MED_OBRERO +
            cls.INVALIDEZ_VIDA_OBRERO +
            cls.CESANTIA_VEJEZ_OBRERO
        )

    @classmethod
    def total_patronal_con_riesgo(cls, prima_riesgo: Decimal) -> Decimal:
        """
        Total patronal incluyendo riesgo de trabajo.

        Args:
            prima_riesgo: Prima de riesgo de la empresa (0.005 - 0.15)
        """
        return cls.total_patronal_fijo() + prima_riesgo
