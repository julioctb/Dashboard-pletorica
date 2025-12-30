"""Estado para el simulador de costo patronal"""

from app.presentation.components.shared.base_state import BaseState
from app.core.calculations.simulador_costo_patronal import (
    ConfiguracionEmpresa,
    Trabajador,
    CalculadoraCostoPatronal,
)


class SimuladorState(BaseState):
    """Estado para el simulador de costo patronal"""

    # ─────────────────────────────────────────────────────────────────
    # CONFIGURACIÓN EMPRESA
    # ─────────────────────────────────────────────────────────────────
    nombre_empresa: str = "Simulación"
    estado: str = "puebla"
    prima_riesgo: float = 2.5984
    factor_integracion: float = 0.0
    dias_aguinaldo: int = 15
    prima_vacacional: float = 25.0
    zona_frontera: bool = False
    aplicar_art_36: bool = True

    # ─────────────────────────────────────────────────────────────────
    # DATOS DEL TRABAJADOR
    # ─────────────────────────────────────────────────────────────────
    salario_diario: float = 315.04
    antiguedad_anos: int = 1
    dias_cotizados: float = 30.0

    # ─────────────────────────────────────────────────────────────────
    # RESULTADO
    # ─────────────────────────────────────────────────────────────────
    resultado: dict = {}
    calculado: bool = False

    # ─────────────────────────────────────────────────────────────────
    # SETTERS (conversión de string a número)
    # ─────────────────────────────────────────────────────────────────
    def set_salario_diario(self, value: str):
        try:
            self.salario_diario = float(value) if value else 0.0
        except ValueError:
            pass

    def set_prima_riesgo(self, value: str):
        try:
            self.prima_riesgo = float(value) if value else 0.0
        except ValueError:
            pass

    def set_factor_integracion(self, value: str):
        try:
            self.factor_integracion = float(value) if value else 0.0
        except ValueError:
            pass

    def set_prima_vacacional(self, value: str):
        try:
            self.prima_vacacional = float(value) if value else 0.0
        except ValueError:
            pass

    def set_antiguedad_anos(self, value: str):
        try:
            self.antiguedad_anos = int(value) if value else 1
        except ValueError:
            pass

    def set_dias_cotizados(self, value: str):
        try:
            self.dias_cotizados = float(value) if value else 30.0
        except ValueError:
            pass

    def set_dias_aguinaldo(self, value: str):
        try:
            self.dias_aguinaldo = int(value) if value else 15
        except ValueError:
            pass

    # ─────────────────────────────────────────────────────────────────
    # MÉTODOS
    # ─────────────────────────────────────────────────────────────────
    def calcular(self):
        """Ejecuta el cálculo de costo patronal"""
        try:
            # 1. Crear configuración de empresa
            config = ConfiguracionEmpresa(
                nombre=self.nombre_empresa,
                registro_patronal="SIM-001",
                estado=self.estado,
                prima_riesgo=self.prima_riesgo / 100,
                factor_integracion_fijo=self.factor_integracion if self.factor_integracion > 0 else None,
                dias_aguinaldo=self.dias_aguinaldo,
                prima_vacacional=self.prima_vacacional / 100,
                zona_frontera=self.zona_frontera,
                aplicar_art_36_lss=self.aplicar_art_36,
            )

            # 2. Crear trabajador
            trabajador = Trabajador(
                nombre="Trabajador simulado",
                salario_diario=self.salario_diario,
                antiguedad_anos=self.antiguedad_anos,
                dias_cotizados_mes=int(self.dias_cotizados),
            )

            # 3. Crear calculadora y ejecutar
            calc = CalculadoraCostoPatronal(config)
            resultado = calc.calcular(trabajador)

            # 4. Guardar resultado como dict
            self.resultado = {
                # Salarios
                "salario_diario": resultado.salario_diario,
                "salario_mensual": resultado.salario_mensual,
                "factor_integracion": resultado.factor_integracion,
                "sbc_diario": resultado.sbc_diario,
                "sbc_mensual": resultado.sbc_mensual,
                "dias_cotizados": resultado.dias_cotizados,
                # IMSS Patronal
                "imss_cuota_fija": resultado.imss_cuota_fija,
                "imss_excedente_pat": resultado.imss_excedente_pat,
                "imss_prest_dinero_pat": resultado.imss_prest_dinero_pat,
                "imss_gastos_med_pens_pat": resultado.imss_gastos_med_pens_pat,
                "imss_invalidez_vida_pat": resultado.imss_invalidez_vida_pat,
                "imss_guarderias": resultado.imss_guarderias,
                "imss_retiro": resultado.imss_retiro,
                "imss_cesantia_vejez_pat": resultado.imss_cesantia_vejez_pat,
                "imss_riesgo_trabajo": resultado.imss_riesgo_trabajo,
                # IMSS Obrero
                "imss_excedente_obr": resultado.imss_excedente_obr,
                "imss_prest_dinero_obr": resultado.imss_prest_dinero_obr,
                "imss_gastos_med_pens_obr": resultado.imss_gastos_med_pens_obr,
                "imss_invalidez_vida_obr": resultado.imss_invalidez_vida_obr,
                "imss_cesantia_vejez_obr": resultado.imss_cesantia_vejez_obr,
                # Art. 36 LSS
                "imss_obrero_absorbido": resultado.imss_obrero_absorbido,
                "es_salario_minimo": resultado.es_salario_minimo,
                # Otros
                "infonavit": resultado.infonavit,
                "isn": resultado.isn,
                # Provisiones
                "provision_aguinaldo": resultado.provision_aguinaldo,
                "provision_vacaciones": resultado.provision_vacaciones,
                "provision_prima_vac": resultado.provision_prima_vac,
                # ISR
                "isr_a_retener": resultado.isr_a_retener,
                # Totales (propiedades calculadas)
                "total_imss_patronal": resultado.total_imss_patronal,
                "total_imss_obrero": resultado.total_imss_obrero,
                "total_provisiones": resultado.total_provisiones,
                "total_carga_patronal": resultado.total_carga_patronal,
                "costo_total": resultado.costo_total,
                "factor_costo": resultado.factor_costo,
                "salario_neto": resultado.salario_neto,
            }

            # 5. Marcar como calculado
            self.calculado = True
            self.mostrar_mensaje("Cálculo realizado correctamente", "success")

        except Exception as e:
            self.mostrar_mensaje(f"Error al calcular: {str(e)}", "error")
            self.calculado = False

    def limpiar(self):
        """Limpia los resultados"""
        self.resultado = {}
        self.calculado = False
        self.limpiar_mensajes()