"""
Catálogo de límites de validación.

Define los rangos válidos para campos numéricos
y parámetros del sistema.
"""

from decimal import Decimal
from typing import ClassVar


class LimitesValidacion:
    """
    Límites para validación de campos.

    Centraliza los rangos aceptables para validaciones
    de datos de entrada.

    Uso:
        from app.core.catalogs import LimitesValidacion

        if not (LimitesValidacion.PRIMA_RIESGO_MIN <= prima <= LimitesValidacion.PRIMA_RIESGO_MAX):
            raise ValueError("Prima fuera de rango")
    """

    # ═══════════════════════════════════════════════════════════════
    # PRIMA DE RIESGO DE TRABAJO
    # ═══════════════════════════════════════════════════════════════

    # Rango según clasificación de actividades IMSS
    # Clase I (mínimo): 0.5% - Oficinas, comercio
    # Clase V (máximo): 15% - Minería, construcción

    PRIMA_RIESGO_MIN: ClassVar[Decimal] = Decimal("0.005")   # 0.5%
    PRIMA_RIESGO_MAX: ClassVar[Decimal] = Decimal("0.15")    # 15%
    PRIMA_RIESGO_DEFAULT: ClassVar[Decimal] = Decimal("0.025984")  # 2.5984%

    # En formato porcentaje (para UI)
    PRIMA_RIESGO_MIN_PORCENTAJE: ClassVar[Decimal] = Decimal("0.5")
    PRIMA_RIESGO_MAX_PORCENTAJE: ClassVar[Decimal] = Decimal("15")

    # ═══════════════════════════════════════════════════════════════
    # DÍAS DE TRABAJO
    # ═══════════════════════════════════════════════════════════════

    DIAS_MES_MIN: ClassVar[int] = 1
    DIAS_MES_MAX: ClassVar[int] = 31
    DIAS_MES_DEFAULT: ClassVar[Decimal] = Decimal("30.4")  # Promedio mensual

    # ═══════════════════════════════════════════════════════════════
    # ANTIGÜEDAD
    # ═══════════════════════════════════════════════════════════════

    ANTIGUEDAD_MIN: ClassVar[int] = 1
    ANTIGUEDAD_MAX: ClassVar[int] = 50  # Razonable para una carrera laboral

    # ═══════════════════════════════════════════════════════════════
    # PRESTACIONES (superiores a la ley)
    # ═══════════════════════════════════════════════════════════════

    # Aguinaldo: mínimo 15, máximo razonable 90 días
    AGUINALDO_DIAS_MIN: ClassVar[int] = 15
    AGUINALDO_DIAS_MAX: ClassVar[int] = 90

    # Prima vacacional: mínimo 25%, máximo razonable 100%
    PRIMA_VACACIONAL_MIN: ClassVar[Decimal] = Decimal("0.25")
    PRIMA_VACACIONAL_MAX: ClassVar[Decimal] = Decimal("1.0")

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE VALIDACIÓN
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def validar_prima_riesgo(cls, prima: Decimal) -> bool:
        """Valida que la prima de riesgo esté en rango."""
        return cls.PRIMA_RIESGO_MIN <= prima <= cls.PRIMA_RIESGO_MAX

    @classmethod
    def validar_prima_riesgo_porcentaje(cls, prima: Decimal) -> bool:
        """Valida prima de riesgo en formato porcentaje (0.5 - 15)."""
        return cls.PRIMA_RIESGO_MIN_PORCENTAJE <= prima <= cls.PRIMA_RIESGO_MAX_PORCENTAJE

    @classmethod
    def normalizar_prima_riesgo(cls, prima: Decimal) -> Decimal:
        """
        Normaliza prima de riesgo a formato decimal.

        Si el valor es > 1, asume que está en porcentaje y lo convierte.

        Args:
            prima: Prima en formato decimal (0.025) o porcentaje (2.5)

        Returns:
            Prima en formato decimal
        """
        if prima > 1:
            return prima / 100
        return prima

    @classmethod
    def validar_aguinaldo(cls, dias: int) -> bool:
        """Valida que los días de aguinaldo estén en rango."""
        return cls.AGUINALDO_DIAS_MIN <= dias <= cls.AGUINALDO_DIAS_MAX

    @classmethod
    def validar_prima_vacacional(cls, prima: Decimal) -> bool:
        """Valida que la prima vacacional esté en rango."""
        return cls.PRIMA_VACACIONAL_MIN <= prima <= cls.PRIMA_VACACIONAL_MAX
