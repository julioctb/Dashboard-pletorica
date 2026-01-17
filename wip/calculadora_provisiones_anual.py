"""
Calculadora de Provisiones Anuales - WIP

Estos métodos fueron extraídos de app/core/calculations/calculadora_provisiones.py
porque actualmente no se usan en el simulador mensual.

Útiles para:
- Cálculo de finiquitos
- Cálculo de PTU (Participación de Trabajadores en Utilidades)
- Proyecciones anuales

Estado: WIP - Pendiente integración con wip/payroll.py
Fecha: 2026-01-03
Actualizado: 2026-01-17 (Migración a catálogos)
"""

from app.core.catalogs import CatalogoVacaciones


class CalculadoraProvisionesAnual:
    """
    Calculadora de provisiones anuales (finiquitos, PTU).

    Separada del calculador mensual para mantener el código limpio.
    Integrar cuando se implemente el motor de nómina completo.
    """

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
            >>> calc = CalculadoraProvisionesAnual()
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
            >>> calc = CalculadoraProvisionesAnual()
            >>> # 1 año de antigüedad = 12 días de vacaciones (reforma 2023)
            >>> calc.calcular_vacaciones_anuales(315.04, 1)
            3780.48  # 12 días de salario
        """
        dias_vac = CatalogoVacaciones.obtener_dias(antiguedad_anos) + dias_adicionales
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
            >>> calc = CalculadoraProvisionesAnual()
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
