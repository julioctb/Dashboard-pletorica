"""
Catálogo de vacaciones por antigüedad.

La tabla de vacaciones fue reformada en 2023, incrementando
significativamente los días de descanso.

Fuente: Ley Federal del Trabajo, Art. 76
Reforma: DOF 27-dic-2022, vigente desde 01-ene-2023
"""

from decimal import Decimal
from typing import ClassVar


class CatalogoVacaciones:
    """
    Tabla de días de vacaciones por antigüedad según LFT.

    Reforma 2023: Se duplicaron los días de vacaciones.
    - Año 1: 12 días (antes 6)
    - Año 5: 20 días (antes 14)

    Uso:
        from app.core.catalogs import CatalogoVacaciones

        dias = CatalogoVacaciones.obtener_dias(antiguedad=3)  # 16 días
    """

    # ═══════════════════════════════════════════════════════════════
    # METADATOS
    # ═══════════════════════════════════════════════════════════════
    FUENTE: ClassVar[str] = "LFT Art. 76"
    REFORMA: ClassVar[str] = "DOF 27-dic-2022"
    VIGENCIA: ClassVar[str] = "Desde 01-ene-2023"

    # ═══════════════════════════════════════════════════════════════
    # TABLA DE VACACIONES POR ANTIGÜEDAD
    # ═══════════════════════════════════════════════════════════════

    # Años 1-5: incremento de 2 días por año
    # Años 6-10: 22 días (fijo)
    # Años 11-15: 24 días (fijo)
    # Años 16-20: 26 días (fijo)
    # Años 21-25: 28 días (fijo)
    # Años 26-30: 30 días (fijo)
    # Años 31+: 30 días base + 2 días por cada 5 años adicionales

    TABLA: ClassVar[dict[int, int]] = {
        1: 12,   2: 14,   3: 16,   4: 18,   5: 20,
        6: 22,   7: 22,   8: 22,   9: 22,  10: 22,
       11: 24,  12: 24,  13: 24,  14: 24,  15: 24,
       16: 26,  17: 26,  18: 26,  19: 26,  20: 26,
       21: 28,  22: 28,  23: 28,  24: 28,  25: 28,
       26: 30,  27: 30,  28: 30,  29: 30,  30: 30,
    }

    # Valores límite
    DIAS_MINIMO: ClassVar[int] = 12  # Primer año
    DIAS_MAXIMO_TABLA: ClassVar[int] = 30  # Hasta año 30

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def obtener_dias(cls, antiguedad: int) -> int:
        """
        Obtiene los días de vacaciones según antigüedad.

        Args:
            antiguedad: Años de antigüedad del trabajador

        Returns:
            Días de vacaciones correspondientes

        Ejemplos:
            >>> CatalogoVacaciones.obtener_dias(1)
            12
            >>> CatalogoVacaciones.obtener_dias(5)
            20
            >>> CatalogoVacaciones.obtener_dias(35)
            32
        """
        if antiguedad <= 0:
            return cls.DIAS_MINIMO

        if antiguedad <= 30:
            return cls.TABLA.get(antiguedad, cls.DIAS_MINIMO)

        # Más de 30 años: 30 días + 2 por cada 5 años adicionales
        anos_extra = antiguedad - 30
        dias_extra = (anos_extra // 5) * 2
        return cls.DIAS_MAXIMO_TABLA + dias_extra

    @classmethod
    def provision_mensual(cls, salario_diario: Decimal, antiguedad: int) -> Decimal:
        """
        Calcula la provisión mensual de vacaciones.

        Fórmula: (Salario_Diario × Días_Vacaciones) / 12 meses

        Args:
            salario_diario: Salario diario del trabajador
            antiguedad: Años de antigüedad

        Returns:
            Provisión mensual para vacaciones
        """
        dias = cls.obtener_dias(antiguedad)
        vacaciones_anuales = salario_diario * dias
        return vacaciones_anuales / 12

    @classmethod
    def incremento_por_ano(cls, antiguedad: int) -> int:
        """
        Calcula el incremento de días respecto al año anterior.

        Args:
            antiguedad: Año actual de antigüedad

        Returns:
            Días de incremento (0 si no hay incremento)
        """
        if antiguedad <= 1:
            return 0
        dias_actual = cls.obtener_dias(antiguedad)
        dias_anterior = cls.obtener_dias(antiguedad - 1)
        return dias_actual - dias_anterior
