"""
Catálogo de tolerancias numéricas del sistema.

Define los márgenes de error aceptables para cálculos
y comparaciones numéricas en el sistema.
"""

from decimal import Decimal
from typing import ClassVar


class Tolerancias:
    """
    Tolerancias numéricas para cálculos y validaciones.

    Centraliza todos los valores de tolerancia que afectan
    la precisión de los cálculos del sistema.

    Uso:
        from app.core.catalogs import Tolerancias

        if abs(diferencia) <= Tolerancias.SALARIO_NETO_PESOS:
            return resultado
    """

    # ═══════════════════════════════════════════════════════════════
    # CÁLCULO DE SALARIO NETO INVERSO
    # ═══════════════════════════════════════════════════════════════

    # Tolerancia para comparar con salario mínimo (2%)
    SALARIO_MINIMO_PORCENTAJE: ClassVar[Decimal] = Decimal("0.02")

    # Tolerancia en pesos para convergencia de salario neto ($1)
    SALARIO_NETO_PESOS: ClassVar[Decimal] = Decimal("1.0")

    # ═══════════════════════════════════════════════════════════════
    # ALGORITMO DE BISECCIÓN
    # ═══════════════════════════════════════════════════════════════

    # Máximo de iteraciones antes de declarar no convergencia
    BISECCION_MAX_ITERACIONES: ClassVar[int] = 50

    # Factor para estimar salario bruto desde neto
    # Asume ~50% de descuentos como peor caso
    BISECCION_FACTOR_DESCUENTOS: ClassVar[Decimal] = Decimal("2")

    # ═══════════════════════════════════════════════════════════════
    # COMPARACIÓN DE SALARIOS
    # ═══════════════════════════════════════════════════════════════

    # Tolerancia para determinar si es salario mínimo (1%)
    TRABAJADOR_SALARIO_MINIMO: ClassVar[Decimal] = Decimal("0.01")

    # ═══════════════════════════════════════════════════════════════
    # REDONDEO DE MONTOS
    # ═══════════════════════════════════════════════════════════════

    # Decimales para montos en pesos
    DECIMALES_MONEDA: ClassVar[int] = 2

    # Decimales para porcentajes (ej: 0.0192 = 1.92%)
    DECIMALES_PORCENTAJE: ClassVar[int] = 4

    # Decimales para factores (ej: factor de integración)
    DECIMALES_FACTOR: ClassVar[int] = 6

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE UTILIDAD
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def es_salario_minimo(
        cls,
        salario: Decimal,
        salario_minimo: Decimal
    ) -> bool:
        """
        Determina si un salario es efectivamente el mínimo.

        Usa tolerancia del 1% para manejar redondeos.

        Args:
            salario: Salario a comparar
            salario_minimo: Salario mínimo de referencia

        Returns:
            True si está dentro de la tolerancia del mínimo
        """
        tolerancia = salario_minimo * cls.TRABAJADOR_SALARIO_MINIMO
        return abs(salario - salario_minimo) <= tolerancia

    @classmethod
    def redondear_moneda(cls, valor: Decimal) -> Decimal:
        """Redondea un valor a 2 decimales (pesos y centavos)."""
        return round(valor, cls.DECIMALES_MONEDA)

    @classmethod
    def redondear_porcentaje(cls, valor: Decimal) -> Decimal:
        """Redondea un porcentaje a 4 decimales."""
        return round(valor, cls.DECIMALES_PORCENTAJE)

    @classmethod
    def redondear_factor(cls, valor: Decimal) -> Decimal:
        """Redondea un factor a 6 decimales."""
        return round(valor, cls.DECIMALES_FACTOR)
