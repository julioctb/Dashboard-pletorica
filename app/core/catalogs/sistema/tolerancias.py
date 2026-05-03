"""
Catálogo de tolerancias numéricas del sistema.

Define los márgenes de error aceptables para cálculos
y comparaciones numéricas en el sistema.
"""

from decimal import Decimal, ROUND_HALF_UP
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

    # Tolerancia absoluta para determinar si es salario mínimo.
    # Art. 36 LSS requiere salario mínimo exacto; se compara a centavos.
    TRABAJADOR_SALARIO_MINIMO: ClassVar[Decimal] = Decimal("0.00")

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

        Compara importes redondeados a centavos para evitar que sueldos por
        arriba del mínimo absorban indebidamente cuotas obreras por Art. 36.

        Args:
            salario: Salario a comparar
            salario_minimo: Salario mínimo de referencia

        Returns:
            True si coincide con el salario mínimo a centavos
        """
        salario_redondeado = Decimal(str(salario)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        minimo_redondeado = Decimal(str(salario_minimo)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        return abs(salario_redondeado - minimo_redondeado) <= cls.TRABAJADOR_SALARIO_MINIMO

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
