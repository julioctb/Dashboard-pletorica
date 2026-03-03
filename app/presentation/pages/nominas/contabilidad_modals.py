"""
Modales del módulo de Nóminas — vista Contabilidad.

- modal_bono_empleado      : Agrega bono de productividad / puntualidad / asistencia
- dialog_ejecutar_calculo  : Confirma cálculo fiscal completo
- dialog_cerrar_periodo    : Confirma cierre irreversible del período
- dialog_devolver_rrhh     : Confirma devolución a RRHH para correcciones
"""
import reflex as rx

from app.presentation.pages.nominas.nomina_contabilidad_state import NominaContabilidadState
from app.presentation.components.ui import (
    form_input,
    form_select,
    boton_guardar,
    boton_cancelar,
    modal_confirmar_accion,
)
from app.presentation.theme import Colors, Spacing


# =============================================================================
# MODAL — BONO POR EMPLEADO
# =============================================================================

def modal_bono_empleado() -> rx.Component:
    """Modal para agregar un bono (CONTABILIDAD) a un empleado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("star", size=18, color=Colors.SUCCESS),
                    rx.text("Bono — "),
                    rx.text(
                        NominaContabilidadState.nombre_empleado_bono,
                        color=Colors.PRIMARY,
                    ),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.vstack(
                form_select(
                    label="Tipo de bono",
                    required=True,
                    value=NominaContabilidadState.form_concepto_bono_clave,
                    on_change=NominaContabilidadState.set_form_concepto_bono_clave,
                    options=NominaContabilidadState.opciones_conceptos_contabilidad,
                ),
                form_input(
                    label="Monto",
                    required=True,
                    placeholder="Ej: 2500.00",
                    value=NominaContabilidadState.form_monto_bono,
                    on_change=NominaContabilidadState.set_form_monto_bono,
                    error=NominaContabilidadState.error_monto_bono,
                ),
                form_input(
                    label="Notas (opcional)",
                    placeholder="Ej: Evaluación Q1 2026",
                    value=NominaContabilidadState.form_notas_bono,
                    on_change=NominaContabilidadState.set_form_notas_bono,
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                boton_cancelar(on_click=NominaContabilidadState.cerrar_modal_bono),
                boton_guardar(
                    texto="Aplicar bono",
                    texto_guardando="Guardando...",
                    on_click=NominaContabilidadState.guardar_bono,
                    saving=NominaContabilidadState.saving,
                ),
                spacing="3",
                justify="end",
                margin_top="4",
                width="100%",
            ),
            max_width="440px",
        ),
        open=NominaContabilidadState.mostrar_modal_bono,
        on_open_change=rx.noop,
    )


# =============================================================================
# DIALOG — EJECUTAR CÁLCULO
# =============================================================================

def dialog_ejecutar_calculo() -> rx.Component:
    """Confirmación antes de ejecutar el cálculo fiscal."""
    return modal_confirmar_accion(
        open=NominaContabilidadState.mostrar_dialog_ejecutar,
        titulo="Ejecutar cálculo de nómina",
        mensaje=(
            "Se calcularán ISR, IMSS, subsidio al empleo y todos los conceptos "
            "automáticos para cada empleado del período."
        ),
        nota_adicional="Los bonos y descuentos manuales capturados por RRHH y Contabilidad se conservan.",
        on_confirmar=NominaContabilidadState.ejecutar_calculo,
        on_cancelar=NominaContabilidadState.cerrar_dialog_ejecutar,
        loading=NominaContabilidadState.calculando,
        texto_confirmar="Ejecutar cálculo",
        color_confirmar="blue",
        icono_detalle="calculator",
        color_detalle="blue",
        max_width="480px",
    )


# =============================================================================
# DIALOG — CERRAR PERÍODO
# =============================================================================

def dialog_cerrar_periodo() -> rx.Component:
    """Confirmación de cierre irreversible del período."""
    return modal_confirmar_accion(
        open=NominaContabilidadState.mostrar_dialog_cerrar,
        titulo="Cerrar período de nómina",
        mensaje="¿Confirmas el cierre del período? Esta acción es irreversible.",
        detalle_contenido=rx.text(
            "Una vez cerrado, ningún rol podrá modificar los movimientos. "
            "El período quedará disponible solo para consulta y reportes.",
            size="2",
        ),
        on_confirmar=NominaContabilidadState.cerrar_periodo,
        on_cancelar=NominaContabilidadState.cerrar_dialog_cerrar,
        loading=NominaContabilidadState.saving,
        texto_confirmar="Cerrar período",
        color_confirmar="green",
        icono_detalle="lock",
        color_detalle="orange",
        max_width="460px",
    )


# =============================================================================
# DIALOG — DEVOLVER A RRHH
# =============================================================================

def dialog_devolver_rrhh() -> rx.Component:
    """Confirmación para devolver el período a RRHH para correcciones."""
    return modal_confirmar_accion(
        open=NominaContabilidadState.mostrar_dialog_devolver,
        titulo="Devolver a RRHH",
        mensaje="El período será devuelto para que RRHH realice las correcciones necesarias.",
        nota_adicional="Los bonos capturados por Contabilidad se conservarán.",
        on_confirmar=NominaContabilidadState.devolver_a_rrhh,
        on_cancelar=NominaContabilidadState.cerrar_dialog_devolver,
        loading=NominaContabilidadState.saving,
        texto_confirmar="Devolver a RRHH",
        color_confirmar="orange",
        icono_detalle="arrow-left",
        color_detalle="orange",
        max_width="440px",
    )
