"""
Calculadora de Provisiones Mensuales.

Calcula las provisiones que la empresa debe hacer mensualmente
para cubrir prestaciones futuras según la Ley Federal del Trabajo (LFT).

Responsabilidades:
- Cálculo de provisión de aguinaldo
- Cálculo de provisión de vacaciones
- Cálculo de provisión de prima vacacional

Fecha: 2025-12-31 (Fase 2 de refactorización)
"""

from app.core.fiscales import ConstantesFiscales


class CalculadoraProvisiones:
    """
    Calculadora de provisiones mensuales según LFT.

    Las provisiones son montos que la empresa debe reservar cada mes
    para cubrir el pago de:
    - Aguinaldo (mínimo 15 días, pagadero en diciembre)
    - Vacaciones (según tabla por antigüedad)
    - Prima vacacional (mínimo 25% del salario de vacaciones)
    """

    def __init__(self, constantes: type[ConstantesFiscales] = ConstantesFiscales):
        """
        Inicializa calculadora con constantes fiscales.

        Args:
            constantes: Clase con constantes fiscales (default: ConstantesFiscales)
        """
        self.const = constantes

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
        dias_vac_ley = self.const.dias_vacaciones(antiguedad_anos)
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

    def calcular_aguinaldo_anual(
        self,
        salario_diario: float,
        dias_aguinaldo: int
    ) -> float:
        """
        Calcula el monto total de aguinaldo anual.

        Útil para proyecciones o cálculo de finiquitos.

        Args:
            salario_diario: Salario diario del trabajador
            dias_aguinaldo: Días de aguinaldo a pagar

        Returns:
            Monto total de aguinaldo

        Ejemplo:
            >>> calc = CalculadoraProvisiones()
            >>> calc.calcular_aguinaldo_anual(315.04, 15)
            4725.60  # 15 días de salario
        """
        return round(salario_diario * dias_aguinaldo, 2)

    def calcular_vacaciones_anuales(
        self,
        salario_diario: float,
        antiguedad_anos: int,
        dias_adicionales: int = 0
    ) -> float:
        """
        Calcula el monto total de vacaciones anuales.

        Útil para proyecciones o cálculo de finiquitos.

        Args:
            salario_diario: Salario diario del trabajador
            antiguedad_anos: Años de antigüedad
            dias_adicionales: Días adicionales a los de ley

        Returns:
            Monto total de vacaciones

        Ejemplo:
            >>> calc = CalculadoraProvisiones()
            >>> # 1 año de antigüedad = 12 días de vacaciones (reforma 2023)
            >>> calc.calcular_vacaciones_anuales(315.04, 1)
            3780.48  # 12 días de salario
        """
        dias_vac = self.const.dias_vacaciones(antiguedad_anos) + dias_adicionales
        return round(salario_diario * dias_vac, 2)

    def calcular_prima_vacacional_anual(
        self,
        salario_diario: float,
        antiguedad_anos: int,
        prima_vacacional: float,
        dias_adicionales: int = 0
    ) -> float:
        """
        Calcula el monto total de prima vacacional anual.

        Args:
            salario_diario: Salario diario del trabajador
            antiguedad_anos: Años de antigüedad
            prima_vacacional: Prima como decimal (ej: 0.25)
            dias_adicionales: Días adicionales a los de ley

        Returns:
            Monto total de prima vacacional

        Ejemplo:
            >>> calc = CalculadoraProvisiones()
            >>> # 1 año = 12 días vac, prima 25%
            >>> calc.calcular_prima_vacacional_anual(315.04, 1, 0.25)
            945.12  # 25% de (12 días × $315.04)
        """
        vacaciones = self.calcular_vacaciones_anuales(
            salario_diario,
            antiguedad_anos,
            dias_adicionales
        )
        return round(vacaciones * prima_vacacional, 2)
