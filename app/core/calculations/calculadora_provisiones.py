"""
Calculadora de Provisiones Mensuales.

Calcula las provisiones que la empresa debe hacer mensualmente
para cubrir prestaciones futuras según la Ley Federal del Trabajo (LFT).

Responsabilidades:
- Cálculo de provisión de aguinaldo
- Cálculo de provisión de vacaciones
- Cálculo de provisión de prima vacacional

Fecha: 2025-12-31 (Fase 2 de refactorización)
Actualizado: 2026-01-17 (Migración a catálogos)
"""

from app.core.catalogs import CatalogoVacaciones


class CalculadoraProvisiones:
    """
    Calculadora de provisiones mensuales según LFT.

    Las provisiones son montos que la empresa debe reservar cada mes
    para cubrir el pago de:
    - Aguinaldo (mínimo 15 días, pagadero en diciembre)
    - Vacaciones (según tabla por antigüedad)
    - Prima vacacional (mínimo 25% del salario de vacaciones)
    """

    def calcular(
        self,
        salario_diario: float,
        antiguedad_anos: int,
        dias_aguinaldo: int,
        prima_vacacional: float,
        dias_vacaciones_adicionales: int = 0
    ) -> dict[str, float]:
        """
        Calcula las tres provisiones mensuales.

        Las provisiones se calculan dividiendo el costo anual entre 12 meses,
        de modo que al final del año la empresa tenga el monto completo
        reservado para pagar aguinaldo, vacaciones y prima.

        Args:
            salario_diario: Salario diario del trabajador
            antiguedad_anos: Años de antigüedad (determina días de vacaciones)
            dias_aguinaldo: Días de aguinaldo (mínimo legal: 15)
            prima_vacacional: Prima vacacional como decimal (ej: 0.25 = 25%)
            dias_vacaciones_adicionales: Días adicionales a los de ley (default: 0)

        Returns:
            Diccionario con las tres provisiones:
            {
                "aguinaldo": float,         # Provisión mensual de aguinaldo
                "vacaciones": float,        # Provisión mensual de vacaciones
                "prima_vacacional": float,  # Provisión mensual de prima vac
                "total": float              # Suma de las tres provisiones
            }

        Ejemplo:
            >>> calc = CalculadoraProvisiones()
            >>> # Trabajador con 1 año, salario $315.04/día
            >>> provisiones = calc.calcular(
            ...     salario_diario=315.04,
            ...     antiguedad_anos=1,
            ...     dias_aguinaldo=15,
            ...     prima_vacacional=0.25
            ... )
            >>> provisiones["aguinaldo"]     # ~393.80 (15 días / 12 meses)
            >>> provisiones["vacaciones"]    # ~315.04 (12 días / 12 meses)
            >>> provisiones["prima_vacacional"]  # ~78.76 (25% de vacaciones)
            >>> provisiones["total"]         # ~787.60
        """
        # ═════════════════════════════════════════════════════════════════════
        # DÍAS DE VACACIONES SEGÚN LFT (REFORMA 2023)
        # ═════════════════════════════════════════════════════════════════════
        dias_vac_ley = CatalogoVacaciones.obtener_dias(antiguedad_anos)
        dias_vac_totales = dias_vac_ley + dias_vacaciones_adicionales

        # ═════════════════════════════════════════════════════════════════════
        # PROVISIÓN AGUINALDO
        # Fórmula: (Salario_Diario × Días_Aguinaldo) / 12 meses
        # ═════════════════════════════════════════════════════════════════════
        aguinaldo = (salario_diario * dias_aguinaldo) / 12

        # ═════════════════════════════════════════════════════════════════════
        # PROVISIÓN VACACIONES
        # Fórmula: (Salario_Diario × Días_Vacaciones) / 12 meses
        # ═════════════════════════════════════════════════════════════════════
        vacaciones = (salario_diario * dias_vac_totales) / 12

        # ═════════════════════════════════════════════════════════════════════
        # PROVISIÓN PRIMA VACACIONAL
        # Fórmula: Provisión_Vacaciones × Prima_Vacacional%
        # Mínimo legal: 25% (0.25)
        # ═════════════════════════════════════════════════════════════════════
        prima_vac = vacaciones * prima_vacacional

        return {
            "aguinaldo": round(aguinaldo, 2),
            "vacaciones": round(vacaciones, 2),
            "prima_vacacional": round(prima_vac, 2),
            "total": round(aguinaldo + vacaciones + prima_vac, 2)
        }
