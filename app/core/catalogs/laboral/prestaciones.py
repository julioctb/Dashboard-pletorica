"""
Catálogo de prestaciones mínimas según LFT.

La Ley Federal del Trabajo establece los mínimos que el patrón
debe otorgar a sus trabajadores.

Fuente: Ley Federal del Trabajo
Artículos: 76, 80, 87
"""

from decimal import Decimal
from typing import ClassVar
from dataclasses import dataclass


@dataclass(frozen=True)
class PrestacionMinima:
    """Representa una prestación mínima de ley."""
    nombre: str
    valor: Decimal
    unidad: str  # "dias", "porcentaje"
    articulo_lft: str
    descripcion: str


class CatalogoPrestaciones:
    """
    Prestaciones mínimas según Ley Federal del Trabajo.

    Estos son los mínimos legales. Las empresas pueden
    otorgar prestaciones superiores.

    Uso:
        from app.core.catalogs import CatalogoPrestaciones

        dias = CatalogoPrestaciones.AGUINALDO_DIAS  # 15
        prima = CatalogoPrestaciones.PRIMA_VACACIONAL  # Decimal("0.25")
    """

    # ═══════════════════════════════════════════════════════════════
    # METADATOS
    # ═══════════════════════════════════════════════════════════════
    FUENTE: ClassVar[str] = "Ley Federal del Trabajo"
    ULTIMA_REFORMA: ClassVar[str] = "2023 (vacaciones)"

    # ═══════════════════════════════════════════════════════════════
    # AGUINALDO (Art. 87 LFT)
    # ═══════════════════════════════════════════════════════════════

    # Mínimo legal: 15 días de salario
    AGUINALDO_DIAS: ClassVar[int] = 15
    AGUINALDO_DIAS_DECIMAL: ClassVar[Decimal] = Decimal("15")

    # ═══════════════════════════════════════════════════════════════
    # PRIMA VACACIONAL (Art. 80 LFT)
    # ═══════════════════════════════════════════════════════════════

    # Mínimo legal: 25% del salario de vacaciones
    PRIMA_VACACIONAL: ClassVar[Decimal] = Decimal("0.25")
    PRIMA_VACACIONAL_PORCENTAJE: ClassVar[int] = 25

    # ═══════════════════════════════════════════════════════════════
    # VACACIONES BASE (Art. 76 LFT)
    # ═══════════════════════════════════════════════════════════════

    # Mínimo primer año: 12 días (reforma 2023)
    VACACIONES_PRIMER_ANO: ClassVar[int] = 12

    # ═══════════════════════════════════════════════════════════════
    # SALARIO MÍNIMO (para referencia)
    # ═══════════════════════════════════════════════════════════════

    SALARIO_MINIMO_GENERAL: ClassVar[Decimal] = Decimal("315.04")
    SALARIO_MINIMO_FRONTERA: ClassVar[Decimal] = Decimal("440.87")

    # ═══════════════════════════════════════════════════════════════
    # DATOS ESTRUCTURADOS
    # ═══════════════════════════════════════════════════════════════

    PRESTACIONES: ClassVar[list[PrestacionMinima]] = [
        PrestacionMinima(
            nombre="Aguinaldo",
            valor=Decimal("15"),
            unidad="dias",
            articulo_lft="Art. 87",
            descripcion="Mínimo 15 días de salario, pagadero antes del 20 de diciembre"
        ),
        PrestacionMinima(
            nombre="Prima vacacional",
            valor=Decimal("0.25"),
            unidad="porcentaje",
            articulo_lft="Art. 80",
            descripcion="Mínimo 25% del salario correspondiente a vacaciones"
        ),
        PrestacionMinima(
            nombre="Vacaciones (1er año)",
            valor=Decimal("12"),
            unidad="dias",
            articulo_lft="Art. 76",
            descripcion="12 días el primer año, incrementa según antigüedad"
        ),
    ]

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE CÁLCULO
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def calcular_aguinaldo(cls, salario_diario: Decimal, dias: int = None) -> Decimal:
        """
        Calcula el monto de aguinaldo.

        Args:
            salario_diario: Salario diario del trabajador
            dias: Días de aguinaldo (default: mínimo legal 15)

        Returns:
            Monto de aguinaldo
        """
        dias_aguinaldo = dias if dias is not None else cls.AGUINALDO_DIAS
        return salario_diario * dias_aguinaldo

    @classmethod
    def calcular_prima_vacacional(
        cls,
        salario_diario: Decimal,
        dias_vacaciones: int,
        prima: Decimal = None
    ) -> Decimal:
        """
        Calcula el monto de prima vacacional.

        Args:
            salario_diario: Salario diario del trabajador
            dias_vacaciones: Días de vacaciones
            prima: Porcentaje de prima (default: mínimo legal 25%)

        Returns:
            Monto de prima vacacional
        """
        porcentaje = prima if prima is not None else cls.PRIMA_VACACIONAL
        salario_vacaciones = salario_diario * dias_vacaciones
        return salario_vacaciones * porcentaje

    @classmethod
    def provision_mensual_aguinaldo(
        cls,
        salario_diario: Decimal,
        dias: int = None
    ) -> Decimal:
        """
        Calcula la provisión mensual de aguinaldo.

        Fórmula: (Salario_Diario × Días_Aguinaldo) / 12 meses

        Args:
            salario_diario: Salario diario
            dias: Días de aguinaldo (default: 15)

        Returns:
            Provisión mensual
        """
        aguinaldo_anual = cls.calcular_aguinaldo(salario_diario, dias)
        return aguinaldo_anual / 12

    @classmethod
    def es_salario_legal(cls, salario_diario: Decimal, zona_frontera: bool = False) -> bool:
        """
        Verifica si el salario cumple con el mínimo legal.

        Args:
            salario_diario: Salario a verificar
            zona_frontera: Si aplica salario de zona fronteriza

        Returns:
            True si el salario es legal
        """
        minimo = cls.SALARIO_MINIMO_FRONTERA if zona_frontera else cls.SALARIO_MINIMO_GENERAL
        return salario_diario >= minimo
