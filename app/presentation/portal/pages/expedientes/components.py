"""
Componentes UI para la pagina Expedientes del portal.

Tabla de empleados, detalle de expediente, filas de documentos,
badges y modal de rechazo.
"""
import reflex as rx

from app.presentation.components.ui import (
    table_shell,
    boton_guardar,
    boton_cancelar,
    tabla_action_button,
    badge_onboarding,
    select_estatus_onboarding,
    empty_state_card,
    document_status_badge,
)
from app.presentation.components.reusable import document_table_shell, documento_observacion
from app.presentation.theme import Colors, Typography, Spacing, Radius

from .state import ExpedientesState


# =============================================================================
# BADGES
# =============================================================================

def badge_documento(estatus: str) -> rx.Component:
    """Badge de estatus de documento."""
    return document_status_badge(estatus)


# =============================================================================
# TABLA DE EMPLEADOS (LISTA)
# =============================================================================

def fila_expediente(emp: dict) -> rx.Component:
    """Fila de la tabla de expedientes."""
    return rx.table.row(
        rx.table.cell(
            rx.text(
                emp["clave"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.PORTAL_PRIMARY_TEXT,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp["nombre_completo"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp["curp"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            badge_onboarding(emp.get("estatus_onboarding", "")),
        ),
        rx.table.cell(
            tabla_action_button(
                icon="folder-open",
                tooltip="Ver Expediente",
                on_click=ExpedientesState.ver_expediente(emp),
                color_scheme="blue",
            ),
        ),
    )


ENCABEZADOS_EXPEDIENTES = [
    {"nombre": "Clave", "ancho": "120px"},
    {"nombre": "Nombre", "ancho": "auto"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Estatus", "ancho": "150px"},
    {"nombre": "Acciones", "ancho": "80px"},
]


def tabla_expedientes() -> rx.Component:
    """Tabla de empleados para revision de expedientes."""
    return table_shell(
        loading=ExpedientesState.loading,
        headers=ENCABEZADOS_EXPEDIENTES,
        rows=ExpedientesState.empleados_expedientes_filtrados,
        row_renderer=fila_expediente,
        has_rows=ExpedientesState.total_expedientes > 0,
        empty_component=empty_state_card(
            title="No hay expedientes para revisar",
            description="Cuando existan expedientes pendientes apareceran aqui.",
            icon="folder-check",
        ),
        total_caption="Mostrando " + ExpedientesState.total_expedientes.to(str) + " empleado(s)",
        loading_rows=5,
    )


def filtros_expedientes() -> rx.Component:
    """Filtros para la tabla de expedientes."""
    return select_estatus_onboarding(
        opciones=ExpedientesState.opciones_estatus_expediente,
        value=ExpedientesState.filtro_estatus_expediente,
        on_change=ExpedientesState.set_filtro_estatus_expediente,
        on_reload=ExpedientesState.recargar_expedientes,
    )


# =============================================================================
# DETALLE DEL EXPEDIENTE
# =============================================================================

def fila_documento(doc: dict) -> rx.Component:
    """Fila de documento en el detalle del expediente."""
    es_pendiente = doc.get("estatus", "") == "PENDIENTE_REVISION"

    return rx.table.row(
        rx.table.cell(
            rx.text(
                doc.get("tipo_documento", ""),
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
        ),
        rx.table.cell(
            rx.text(
                doc.get("nombre_archivo", "-"),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                f"v{doc.get('version', 1)}",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            badge_documento(doc.get("estatus", "")),
        ),
        rx.table.cell(
            documento_observacion(doc.get("observacion_rechazo", ""), mode="tooltip"),
        ),
        rx.table.cell(
            rx.cond(
                es_pendiente,
                rx.hstack(
                    tabla_action_button(
                        icon="check",
                        tooltip="Aprobar",
                        on_click=ExpedientesState.aprobar_documento(doc),
                        color_scheme="green",
                    ),
                    tabla_action_button(
                        icon="x",
                        tooltip="Rechazar",
                        on_click=ExpedientesState.abrir_modal_rechazo(doc),
                        color_scheme="red",
                    ),
                    spacing="1",
                ),
                rx.fragment(),
            ),
        ),
    )


ENCABEZADOS_DOCUMENTOS = [
    {"nombre": "Tipo", "ancho": "180px"},
    {"nombre": "Archivo", "ancho": "auto"},
    {"nombre": "Version", "ancho": "80px"},
    {"nombre": "Estatus", "ancho": "120px"},
    {"nombre": "Obs.", "ancho": "60px"},
    {"nombre": "Acciones", "ancho": "100px"},
]


def detalle_expediente() -> rx.Component:
    """Vista de detalle del expediente de un empleado."""
    return rx.vstack(
        # Header con boton volver
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", size=16),
                "Volver a lista",
                on_click=ExpedientesState.volver_a_lista,
                variant="ghost",
                size="2",
            ),
            rx.spacer(),
            spacing="3",
            width="100%",
            align="center",
        ),

        # Info del empleado
        rx.hstack(
            rx.vstack(
                rx.text(
                    ExpedientesState.nombre_empleado_seleccionado,
                    font_size=Typography.SIZE_LG,
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                rx.text(
                    ExpedientesState.clave_empleado_seleccionado,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="1",
            ),
            rx.spacer(),
            # Metricas del expediente
            rx.hstack(
                _metric_card("Requeridos", ExpedientesState.total_docs_requeridos, "blue"),
                _metric_card("Aprobados", ExpedientesState.total_docs_aprobados, "green"),
                _metric_card("Pendientes", ExpedientesState.total_docs_pendientes, "yellow"),
                _metric_card("Rechazados", ExpedientesState.total_docs_rechazados, "red"),
                spacing="3",
            ),
            width="100%",
            align="center",
            padding=Spacing.MD,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.MD,
        ),

        # Barra de progreso
        rx.vstack(
            rx.hstack(
                rx.text(
                    "Progreso del expediente",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.spacer(),
                rx.text(
                    ExpedientesState.porcentaje_expediente,
                    "%",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                width="100%",
            ),
            rx.progress(
                value=ExpedientesState.porcentaje_expediente,
                max=100,
                width="100%",
                color_scheme="teal",
            ),
            width="100%",
            spacing="2",
        ),

        # Tabla de documentos
        document_table_shell(
            headers=ENCABEZADOS_DOCUMENTOS,
            items=ExpedientesState.documentos_empleado,
            row_renderer=fila_documento,
            has_items=ExpedientesState.documentos_empleado.length() > 0,
            empty_title="No hay documentos subidos aun",
            empty_description="El empleado aun no carga documentos para este expediente.",
            empty_icon="file-x",
        ),

        width="100%",
        spacing="4",
        padding=Spacing.LG,
    )


def _metric_card(label: str, value, color_scheme: str) -> rx.Component:
    """Mini card de metrica."""
    return rx.vstack(
        rx.text(
            value,
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
        ),
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
        ),
        spacing="0",
        align="center",
        padding_x=Spacing.MD,
        padding_y=Spacing.SM,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        min_width="80px",
    )


# =============================================================================
# MODAL RECHAZO
# =============================================================================

def modal_rechazo() -> rx.Component:
    """Modal para ingresar observacion de rechazo."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Rechazar Documento"),
            rx.dialog.description(
                "Ingrese el motivo del rechazo. El empleado podra ver esta observacion."
            ),

            rx.vstack(
                rx.text(
                    "Observacion *",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.text_area(
                    value=ExpedientesState.form_observacion_rechazo,
                    on_change=ExpedientesState.set_form_observacion_rechazo,
                    placeholder="Describa el motivo del rechazo (min. 5 caracteres)...",
                    width="100%",
                    rows="4",
                ),
                rx.cond(
                    ExpedientesState.error_observacion != "",
                    rx.text(
                        ExpedientesState.error_observacion,
                        font_size=Typography.SIZE_XS,
                        color=Colors.ERROR,
                    ),
                ),
                spacing="2",
                width="100%",
                padding_y=Spacing.BASE,
            ),

            rx.hstack(
                boton_cancelar(
                    on_click=ExpedientesState.cerrar_modal_rechazo,
                ),
                boton_guardar(
                    texto="Rechazar",
                    texto_guardando="Rechazando...",
                    on_click=ExpedientesState.confirmar_rechazo,
                    saving=ExpedientesState.saving,
                    color_scheme="red",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),

            max_width="500px",
        ),
        open=ExpedientesState.mostrar_modal_rechazo,
        on_open_change=rx.noop,
    )
