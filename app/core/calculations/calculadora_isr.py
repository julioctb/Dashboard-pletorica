"""
Calculadora de ISR (Impuesto Sobre la Renta).

Calcula el ISR mensual según la Ley del ISR (LISR), incluyendo
subsidio al empleo y exenciones por salario mínimo.

Responsabilidades:
- Cálculo de ISR mensual según tabla progresiva
- Aplicación de subsidio al empleo
- Exención para salarios mínimos (Art. 96 LISR)

Fecha: 2025-12-31 (Fase 2 de refactorización)
"""

from app.core.fiscales import ConstantesFiscales


class CalculadoraISR:
    """
    Calculadora de ISR mensual con subsidio al empleo.

    Implementa la tabla progresiva del Art. 96 LISR y el subsidio
    al empleo según decreto presidencial vigente.
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
        base_gravable: float,
        es_salario_minimo: bool = False
    ) -> dict[str, float]:
        """
        Calcula ISR mensual con subsidio al empleo.

        Aplica la tabla progresiva del ISR y resta el subsidio al empleo
        cuando aplica. Los trabajadores con salario mínimo están exentos
        según Art. 96 LISR.

        Args:
            base_gravable: Ingreso mensual gravable (salario mensual)
            es_salario_minimo: True si el trabajador gana salario mínimo

        Returns:
            Diccionario con desglose del ISR:
            {
                "base_gravable": float,         # Ingreso mensual
                "isr_antes_subsidio": float,    # ISR calculado antes de subsidio
                "subsidio_empleo": float,       # Subsidio aplicable
                "isr_a_retener": float          # ISR final a retener
            }

        Ejemplo:
            >>> calc = CalculadoraISR()
            >>> # Salario mínimo - Exento
            >>> resultado = calc.calcular(9451.20, es_salario_minimo=True)
            >>> resultado["isr_a_retener"]  # 0.0
            >>> # Salario normal - Con ISR
            >>> resultado = calc.calcular(15000.0, es_salario_minimo=False)
            >>> resultado["isr_a_retener"]  # ~1300
        """
        # ═════════════════════════════════════════════════════════════════════
        # ART. 96 LISR: SALARIOS MÍNIMOS EXENTOS DE RETENCIÓN
        # ═════════════════════════════════════════════════════════════════════
        if es_salario_minimo or base_gravable <= 0:
            return {
                "base_gravable": base_gravable,
                "isr_antes_subsidio": 0.0,
                "subsidio_empleo": 0.0,
                "isr_a_retener": 0.0
            }

        # ═════════════════════════════════════════════════════════════════════
        # CÁLCULO ISR CON TABLA PROGRESIVA
        # ═════════════════════════════════════════════════════════════════════
        isr_calculado = self._buscar_en_tabla_isr(base_gravable)

        # ═════════════════════════════════════════════════════════════════════
        # SUBSIDIO AL EMPLEO
        # ═════════════════════════════════════════════════════════════════════
        subsidio = self._calcular_subsidio_empleo(base_gravable)

        # ═════════════════════════════════════════════════════════════════════
        # ISR A RETENER (nunca negativo)
        # ═════════════════════════════════════════════════════════════════════
        isr_a_retener = max(0, isr_calculado - subsidio)

        return {
            "base_gravable": base_gravable,
            "isr_antes_subsidio": isr_calculado,
            "subsidio_empleo": subsidio,
            "isr_a_retener": isr_a_retener
        }

    def _buscar_en_tabla_isr(self, base_gravable: float) -> float:
        """
        Busca en la tabla progresiva de ISR y calcula el impuesto.

        Fórmula: ISR = Cuota_Fija + (Excedente_Límite_Inferior × Tasa)

        Args:
            base_gravable: Ingreso mensual gravable

        Returns:
            ISR calculado antes de subsidio

        Raises:
            ValueError: Si la tabla ISR está vacía o mal formada
        """
        if not self.const.TABLA_ISR_MENSUAL:
            raise ValueError("Tabla ISR mensual no configurada")

        # Buscar rango en tabla
        for lim_inf, lim_sup, cuota_fija, tasa in self.const.TABLA_ISR_MENSUAL:
            if lim_inf <= base_gravable <= lim_sup:
                excedente = base_gravable - lim_inf
                isr = cuota_fija + (excedente * tasa)
                return round(isr, 2)

        # Si no encontró rango, usar el último (ingresos muy altos)
        # El último rango tiene límite superior = infinity
        lim_inf, _, cuota_fija, tasa = self.const.TABLA_ISR_MENSUAL[-1]
        excedente = base_gravable - lim_inf
        isr = cuota_fija + (excedente * tasa)
        return round(isr, 2)

    def _calcular_subsidio_empleo(self, base_gravable: float) -> float:
        """
        Calcula el subsidio al empleo según decreto vigente.

        El subsidio aplica solo si el ingreso es menor o igual al límite
        establecido. Es un monto fijo calculado como porcentaje de la UMA.

        Args:
            base_gravable: Ingreso mensual gravable

        Returns:
            Monto del subsidio al empleo (0 si no aplica)
        """
        if base_gravable <= self.const.LIMITE_SUBSIDIO_MENSUAL:
            return self.const.SUBSIDIO_EMPLEO_MENSUAL
        return 0.0

    def calcular_anual(self, base_gravable_anual: float) -> dict[str, float]:
        """
        Calcula ISR anual (para finiquitos, PTU, etc.).

        Aplica la tabla anual de ISR. Pendiente de implementación
        en futuras fases.

        Args:
            base_gravable_anual: Ingreso anual gravable

        Returns:
            Diccionario con desglose del ISR anual

        Raises:
            NotImplementedError: Funcionalidad pendiente
        """
        raise NotImplementedError(
            "Cálculo de ISR anual pendiente de implementación. "
            "Actualmente solo soporta ISR mensual."
        )
