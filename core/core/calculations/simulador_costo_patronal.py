"""
Calculadora de Costo Patronal - México
Versión Configurable - 2026

Permite ajustar todas las variables por empresa:
- Factor de integración personalizado
- Prima de riesgo específica
- Prestaciones superiores a la ley
- Días de pago por mes (30 o 30.4)

REFACTORIZACIÓN:
- Fase 1 (2025-12-31): Entidades movidas a app/entities/costo_patronal.py
- Fase 2 (2025-12-31): Calculadores especializados separados (IMSS, ISR, Provisiones)
- Fase 3 (2026-01-17): Migración a catálogos (eliminación de facade fiscales.py)
- Orquestador: Este archivo coordina los calculadores especializados
"""

from core.core.catalogs import CatalogoUMA, CatalogoINFONAVIT
from core.domain.models.costo_patronal import (
    ConfiguracionEmpresa,
    Trabajador,
    ResultadoCuotas
)
from core.core.calculations.calculadora_imss import CalculadoraIMSS
from core.core.calculations.calculadora_isr import CalculadoraISR
from core.core.calculations.calculadora_provisiones import CalculadoraProvisiones


# NOTA: Las clases ConfiguracionEmpresa, Trabajador y ResultadoCuotas
# fueron movidas a app/entities/costo_patronal.py en Fase 1 de refactorización


# =============================================================================
# CALCULADORA PRINCIPAL
# =============================================================================

class CalculadoraCostoPatronal:
    """
    Calculadora principal de costo patronal - Orquestador.

    Coordina los calculadores especializados:
    - CalculadoraIMSS: Cuotas IMSS patronales y obreras
    - CalculadoraISR: Impuesto Sobre la Renta
    - CalculadoraProvisiones: Aguinaldo, vacaciones, prima vacacional

    Responsabilidad: Ensamblar resultados de calculadores especializados
    en un objeto ResultadoCuotas completo.
    """

    def __init__(self, config: ConfiguracionEmpresa):
        """
        Inicializa calculadora con configuración de empresa.

        Args:
            config: Configuración personalizada de la empresa
        """
        self.config = config

        # Calculadores especializados (usan catálogos internamente)
        self.calc_imss = CalculadoraIMSS()
        self.calc_isr = CalculadoraISR()
        self.calc_provisiones = CalculadoraProvisiones()
    
    def calcular(self, trabajador: Trabajador) -> ResultadoCuotas:
        """
        Calcula todas las cuotas para un trabajador.

        Orquesta los calculadores especializados y ensambla el resultado
        completo. Reducido de 129 líneas → 78 líneas mediante delegación.

        Args:
            trabajador: Datos del trabajador a calcular

        Returns:
            ResultadoCuotas con todos los campos calculados

        Raises:
            ValueError: Si el salario diario es menor al salario mínimo legal
        """
        # ═════════════════════════════════════════════════════════════════════
        # VALIDACIÓN: Salario mínimo legal (Art. 123 Constitucional)
        # ═════════════════════════════════════════════════════════════════════
        salario_minimo_aplicable = self.config.salario_minimo_aplicable

        if trabajador.salario_diario < salario_minimo_aplicable:
            # Calcular diferencia
            diferencia = salario_minimo_aplicable - trabajador.salario_diario
            salario_mensual_actual = trabajador.salario_diario * trabajador.dias_cotizados_mes
            salario_minimo_mensual = salario_minimo_aplicable * trabajador.dias_cotizados_mes

            raise ValueError(
                f"⚠️ SALARIO ILEGAL: El salario diario (${trabajador.salario_diario:,.2f}) "
                f"es menor al salario mínimo legal (${salario_minimo_aplicable:.2f}).\n\n"
                f"📋 Detalles:\n"
                f"   • Salario ingresado: ${trabajador.salario_diario:.2f}/día → ${salario_mensual_actual:,.2f}/mes\n"
                f"   • Salario mínimo:    ${salario_minimo_aplicable:.2f}/día → ${salario_minimo_mensual:,.2f}/mes\n"
                f"   • Diferencia:        ${diferencia:.2f}/día\n\n"
                f"🚫 Pagar menos del salario mínimo viola el Art. 123 Constitucional y la Ley Federal del Trabajo.\n"
                f"💡 Ajusta el salario al mínimo legal o superior."
            )

        dias = trabajador.dias_cotizados_mes

        # ═════════════════════════════════════════════════════════════════════
        # SALARIOS Y SBC
        # ═════════════════════════════════════════════════════════════════════
        factor_int = self.config.calcular_factor_integracion(trabajador.antiguedad_anos)
        sbc_diario = trabajador.salario_diario * factor_int
        sbc_diario = min(sbc_diario, float(CatalogoUMA.TOPE_SBC))  # Aplicar tope
        salario_mensual = trabajador.salario_diario * dias

        # ═════════════════════════════════════════════════════════════════════
        # IMSS (delegar a calculadora especializada)
        # ═════════════════════════════════════════════════════════════════════
        imss_pat = self.calc_imss.calcular_patronal(
            sbc_diario,
            dias,
            self.config.prima_riesgo
        )

        es_sm = trabajador.es_salario_minimo(self.config.salario_minimo_aplicable)
        imss_obr, imss_absorbido = self.calc_imss.calcular_obrero(
            sbc_diario,
            dias,
            es_sm,
            self.config.aplicar_art_36_lss
        )

        # ═════════════════════════════════════════════════════════════════════
        # INFONAVIT (5% del SBC)
        # ═════════════════════════════════════════════════════════════════════
        infonavit = sbc_diario * float(CatalogoINFONAVIT.TASA_PATRONAL) * dias

        # ═════════════════════════════════════════════════════════════════════
        # ISN (según estado configurado)
        # ═════════════════════════════════════════════════════════════════════
        isn = salario_mensual * self.config.tasa_isn

        # ═════════════════════════════════════════════════════════════════════
        # PROVISIONES (delegar a calculadora especializada)
        # ═════════════════════════════════════════════════════════════════════
        provisiones = self.calc_provisiones.calcular(
            trabajador.salario_diario,
            trabajador.antiguedad_anos,
            self.config.dias_aguinaldo,
            self.config.prima_vacacional,
            self.config.dias_vacaciones_adicionales
        )

        # ═════════════════════════════════════════════════════════════════════
        # ISR (delegar a calculadora especializada)
        # ═════════════════════════════════════════════════════════════════════
        isr = self.calc_isr.calcular(salario_mensual, es_sm)
        
        # ═════════════════════════════════════════════════════════════════════
        # RESULTADO (ensamblar desde dicts de calculadores especializados)
        # ═════════════════════════════════════════════════════════════════════
        return ResultadoCuotas(
            # Identificación
            trabajador=trabajador.nombre,
            empresa=self.config.nombre,

            # Salarios
            salario_diario=trabajador.salario_diario,
            salario_mensual=salario_mensual,
            factor_integracion=factor_int,
            sbc_diario=sbc_diario,
            sbc_mensual=sbc_diario * dias,
            dias_cotizados=dias,

            # IMSS Patronal (desempaquetar dict)
            imss_cuota_fija=imss_pat["cuota_fija"],
            imss_excedente_pat=imss_pat["excedente"],
            imss_prest_dinero_pat=imss_pat["prest_dinero"],
            imss_gastos_med_pens_pat=imss_pat["gastos_med"],
            imss_invalidez_vida_pat=imss_pat["invalidez_vida"],
            imss_guarderias=imss_pat["guarderias"],
            imss_retiro=imss_pat["retiro"],
            imss_cesantia_vejez_pat=imss_pat["cesantia_vejez"],
            imss_riesgo_trabajo=imss_pat["riesgo_trabajo"],

            # IMSS Obrero (desempaquetar dict)
            imss_excedente_obr=imss_obr["excedente"],
            imss_prest_dinero_obr=imss_obr["prest_dinero"],
            imss_gastos_med_pens_obr=imss_obr["gastos_med"],
            imss_invalidez_vida_obr=imss_obr["invalidez_vida"],
            imss_cesantia_vejez_obr=imss_obr["cesantia_vejez"],

            # Art. 36 LSS
            imss_obrero_absorbido=imss_absorbido,
            es_salario_minimo=es_sm,

            # Otros
            infonavit=infonavit,
            isn=isn,

            # Provisiones (desempaquetar dict)
            provision_aguinaldo=provisiones["aguinaldo"],
            provision_vacaciones=provisiones["vacaciones"],
            provision_prima_vac=provisiones["prima_vacacional"],

            # ISR (desempaquetar dict)
            isr_base_gravable=isr["base_gravable"],
            isr_antes_subsidio=isr["isr_antes_subsidio"],
            subsidio_empleo=isr["subsidio_empleo"],
            isr_a_retener=isr["isr_a_retener"],
        )

    def calcular_desde_neto(self, salario_neto_deseado: float,
                            trabajador: Trabajador) -> tuple[ResultadoCuotas, int]:
        """
        Calcula el salario bruto necesario para alcanzar un neto deseado.
        Usa método iterativo (bisección) para encontrar el salario correcto.

        IMPORTANTE: El salario neto incluye SOLO descuentos fiscales obligatorios:
        - IMSS Obrero (5 ramos)
        - ISR (Impuesto Sobre la Renta)

        NO incluye descuentos variables (INFONAVIT, FONACOT, pensión alimenticia, etc.)

        Args:
            salario_neto_deseado: Salario neto mensual deseado
            trabajador: Datos del trabajador (antiguedad, días cotizados, etc.)

        Returns:
            Tupla (resultado, iteraciones):
            - resultado: ResultadoCuotas con el salario bruto calculado
            - iteraciones: Número de iteraciones hasta convergencia

        Raises:
            ValueError: Si el salario neto deseado es menor al salario mínimo mensual

        Ejemplo:
            >>> config = ConfiguracionEmpresa(...)
            >>> calc = CalculadoraCostoPatronal(config)
            >>> trabajador = Trabajador("Juan", salario_diario=0, antiguedad_anos=1)
            >>> resultado, iter = calc.calcular_desde_neto(12000, trabajador)
            >>> print(f"Salario bruto: ${resultado.salario_diario:.2f}/día")
            Salario bruto: $493.33/día
            >>> print(f"Convergió en {iter} iteraciones")
            Convergió en 9 iteraciones
        """
        # ═════════════════════════════════════════════════════════════════════
        # VALIDACIÓN: Salario neto no puede ser menor al salario mínimo
        # ═════════════════════════════════════════════════════════════════════
        salario_minimo_diario = self.config.salario_minimo_aplicable
        salario_minimo_mensual = salario_minimo_diario * trabajador.dias_cotizados_mes

        if salario_neto_deseado < salario_minimo_mensual:
            raise ValueError(
                f"El salario neto deseado (${salario_neto_deseado:,.2f}) no puede ser menor "
                f"al salario mínimo mensual (${salario_minimo_mensual:,.2f}). "
                f"Salario mínimo diario: ${salario_minimo_diario:.2f}"
            )

        # ═════════════════════════════════════════════════════════════════════
        # CASO ESPECIAL: Si neto deseado ≈ salario mínimo → Art. 36 LSS
        # ═════════════════════════════════════════════════════════════════════
        # Cuando el salario neto deseado está muy cerca del salario mínimo mensual,
        # el resultado correcto es el salario mínimo exacto (con Art. 36 LSS aplicado).
        # Esto evita problemas de convergencia por la discontinuidad:
        #   - Salario = mínimo → Art. 36 aplica → neto = bruto (sin descuentos)
        #   - Salario > mínimo → Art. 36 NO aplica → hay descuentos IMSS e ISR

        tolerancia_salario_minimo = salario_minimo_mensual * 0.02  # 2% de tolerancia

        if abs(salario_neto_deseado - salario_minimo_mensual) <= tolerancia_salario_minimo:
            # El neto deseado está muy cerca del salario mínimo
            # Retornar directamente salario mínimo (aplica Art. 36)
            trabajador_sm = Trabajador(
                nombre=trabajador.nombre,
                salario_diario=salario_minimo_diario,
                antiguedad_anos=trabajador.antiguedad_anos,
                dias_cotizados_mes=trabajador.dias_cotizados_mes,
                zona_frontera=trabajador.zona_frontera,
            )
            resultado = self.calcular(trabajador_sm)

            return resultado, 1  # 1 iteración (directo)

        # ═════════════════════════════════════════════════════════════════════
        # CONFIGURACIÓN DEL ALGORITMO DE BISECCIÓN
        # ═════════════════════════════════════════════════════════════════════
        # Límites de búsqueda
        salario_min = salario_neto_deseado / trabajador.dias_cotizados_mes  # Estimación baja (0% descuentos)
        salario_max = salario_neto_deseado * 2 / trabajador.dias_cotizados_mes  # Estimación alta (50% descuentos)

        max_iteraciones = 50
        tolerancia = 1.0  # $1 de tolerancia

        for i in range(max_iteraciones):
            # Probar con el punto medio
            salario_medio = (salario_min + salario_max) / 2

            # Crear trabajador temporal con este salario
            trabajador_temp = Trabajador(
                nombre=trabajador.nombre,
                salario_diario=salario_medio,
                antiguedad_anos=trabajador.antiguedad_anos,
                dias_cotizados_mes=trabajador.dias_cotizados_mes,
                zona_frontera=trabajador.zona_frontera,
            )

            # Calcular
            resultado = self.calcular(trabajador_temp)

            # Verificar si llegamos al neto deseado
            diferencia = resultado.salario_neto - salario_neto_deseado

            if abs(diferencia) <= tolerancia:
                return resultado, i + 1

            # Ajustar límites según el resultado
            if diferencia < 0:
                # El neto es menor, necesitamos salario bruto más alto
                salario_min = salario_medio
            else:
                # El neto es mayor, necesitamos salario bruto más bajo
                salario_max = salario_medio

        # Si no converge, retornar el mejor resultado
        return resultado, max_iteraciones
