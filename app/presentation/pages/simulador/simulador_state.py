"""Estado para el simulador de costo patronal"""
import reflex as rx

from app.presentation.components.shared.base_state import BaseState
from app.entities.costo_patronal import ConfiguracionEmpresa, Trabajador
from app.core.calculations import CalculadoraCostoPatronal
from app.core.catalogos import obtener_clave_estado


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
    tipo_salario_calculo: str = ""
    salario_mensual: float = 0.0
    antiguedad_anos: int = 1
    dias_cotizados: float = 30.0

    # ─────────────────────────────────────────────────────────────────
    # RESULTADO
    # ─────────────────────────────────────────────────────────────────
    resultado: dict = {}
    calculado: bool = False
    is_calculating: bool = False

    # ─────────────────────────────────────────────────────────────────
    # SETTERS (conversión de string a número)
    # ─────────────────────────────────────────────────────────────────
    def set_salario_mensual(self, value: str):
        try:
            self.salario_mensual= float(value)
        except ValueError:
            pass

    def set_prima_riesgo(self, value: str):
        try:
            self.prima_riesgo = float(value) if value else 0.0
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
    
    def set_tipo_salario_calculo(self, value: str):
            self.tipo_salario_calculo = value

    def set_estado_display(self, display_name: str):
        """Setter que convierte nombre display a ID interno"""
        self.estado = obtener_clave_estado(display_name) or "puebla"

    # ─────────────────────────────────────────────────────────────────
    # MÉTODOS
    # ─────────────────────────────────────────────────────────────────
    
    @rx.var
    def calc_salario_diario(self) -> float:
        if self.tipo_salario_calculo == 'Salario Mínimo':
            return 315.04
        return round(self.salario_mensual / 30,2) if self.salario_mensual else 0.0

    def calcular(self):
        """Ejecuta el cálculo de costo patronal"""
        self.is_calculating = True
        try:
            # 1. Crear configuración de empresa
            config = ConfiguracionEmpresa(
                nombre=self.nombre_empresa,
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
                salario_diario=self.calc_salario_diario,
                antiguedad_anos=self.antiguedad_anos,
                dias_cotizados_mes=int(self.dias_cotizados),
            )

            # 3. Crear calculadora y ejecutar
            calc = CalculadoraCostoPatronal(config)

            if self.tipo_salario_calculo == 'Salario Neto (inverso)':
                salario_neto_deseado = float(self.salario_mensual)

                try:
                    # ✅ Desempaquetar tupla (resultado, iteraciones)
                    resultado, iteraciones = calc.calcular_desde_neto(
                        salario_neto_deseado=salario_neto_deseado,
                        trabajador=trabajador
                    )

                    # ⚠️ Validar convergencia
                    if iteraciones >= 50:
                        self.mostrar_mensaje(
                            "Advertencia: El cálculo puede no ser exacto. Intenta con un salario diferente.",
                            "warning"
                        )

                except ValueError as e:
                    # 🚨 Error de validación (salario neto < salario mínimo)
                    self.mostrar_mensaje(str(e), "error")
                    self.calculado = False
                    return
            else:
                resultado = calc.calcular(trabajador)

            # 4. Guardar resultado como dict (valores ya formateados)
            self.resultado = {
                # Salarios
                "salario_diario": f"$ {resultado.salario_diario:,.2f}",
                "salario_mensual": f"$ {resultado.salario_mensual:,.2f}",
                "factor_integracion": f"{resultado.factor_integracion:.4f}",
                "sbc_diario": f"$ {resultado.sbc_diario:,.2f}",
                "sbc_mensual": f"$ {resultado.sbc_mensual:,.2f}",
                "dias_cotizados": str(resultado.dias_cotizados),
                # IMSS Patronal
                "imss_cuota_fija": f"$ {resultado.imss_cuota_fija:,.2f}",
                "imss_excedente_pat": f"$ {resultado.imss_excedente_pat:,.2f}",
                "imss_prest_dinero_pat": f"$ {resultado.imss_prest_dinero_pat:,.2f}",
                "imss_gastos_med_pens_pat": f"$ {resultado.imss_gastos_med_pens_pat:,.2f}",
                "imss_invalidez_vida_pat": f"$ {resultado.imss_invalidez_vida_pat:,.2f}",
                "imss_guarderias": f"$ {resultado.imss_guarderias:,.2f}",
                "imss_retiro": f"$ {resultado.imss_retiro:,.2f}",
                "imss_cesantia_vejez_pat": f"$ {resultado.imss_cesantia_vejez_pat:,.2f}",
                "imss_riesgo_trabajo": f"$ {resultado.imss_riesgo_trabajo:,.2f}",
                # IMSS Obrero
                "imss_excedente_obr": f"$ {resultado.imss_excedente_obr:,.2f}",
                "imss_prest_dinero_obr": f"$ {resultado.imss_prest_dinero_obr:,.2f}",
                "imss_gastos_med_pens_obr": f"$ {resultado.imss_gastos_med_pens_obr:,.2f}",
                "imss_invalidez_vida_obr": f"$ {resultado.imss_invalidez_vida_obr:,.2f}",
                "imss_cesantia_vejez_obr": f"$ {resultado.imss_cesantia_vejez_obr:,.2f}",
                # Art. 36 LSS
                "imss_obrero_absorbido": f"$ {resultado.imss_obrero_absorbido:,.2f}",
                "es_salario_minimo": resultado.es_salario_minimo,
                # Otros
                "infonavit": f"$ {resultado.infonavit:,.2f}",
                "isn": f"$ {resultado.isn:,.2f}",
                # Provisiones
                "provision_aguinaldo": f"$ {resultado.provision_aguinaldo:,.2f}",
                "provision_vacaciones": f"$ {resultado.provision_vacaciones:,.2f}",
                "provision_prima_vac": f"$ {resultado.provision_prima_vac:,.2f}",
                # ISR
                "isr_a_retener": f"$ {resultado.isr_a_retener:,.2f}",
                # Totales (propiedades calculadas)
                "total_imss_patronal": f"$ {resultado.total_imss_patronal:,.2f}",
                "total_imss_obrero": f"$ {resultado.total_imss_obrero:,.2f}",
                "total_provisiones": f"$ {resultado.total_provisiones:,.2f}",
                "total_carga_patronal": f"$ {resultado.total_carga_patronal:,.2f}",
                "costo_total": f"$ {resultado.costo_total:,.2f}",
                "factor_costo": f"{resultado.factor_costo:.4f}",
                "salario_neto": f"$ {resultado.salario_neto:,.2f}",
                "total_descuentos_trabajador": f"$ {resultado.total_descuentos_trabajador:,.2f}"
            }

            # 5. Marcar como calculado
            self.calculado = True

            # 📋 Mensaje informativo para Art. 36 LSS
            if resultado.es_salario_minimo and self.aplicar_art_36:
                self.mostrar_mensaje(
                    "✅ Cálculo realizado. Nota: Salario mínimo - El patrón absorbe la cuota IMSS obrera (Art. 36 LSS)",
                    "success"
                )
            else:
                self.mostrar_mensaje("Cálculo realizado correctamente", "success")

        except ValueError as e:
            # 🚨 Error de validación (salario menor al mínimo, datos inválidos, etc.)
            error_msg = str(e)

            # Si es error de salario mínimo, mostrar mensaje conciso
            if "SALARIO ILEGAL" in error_msg or "salario mínimo" in error_msg.lower():
                self.mostrar_mensaje(
                    "⚠️ Salario ilegal: El salario ingresado es menor al mínimo legal ($315.04/día). "
                    "Pagar menos del salario mínimo viola la Constitución.",
                    "error"
                )
            else:
                # Otros errores de validación
                self.mostrar_mensaje(f"Error de validación: {error_msg}", "error")

            self.calculado = False

        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
            self.calculado = False
        finally:
            self.is_calculating = False

    def limpiar(self):
        """Limpia los resultados"""
        self.salario_mensual = 0.0
        self.tipo_salario_calculo = ""
        self.resultado = {}
        self.calculado = False
        self.limpiar_mensajes()