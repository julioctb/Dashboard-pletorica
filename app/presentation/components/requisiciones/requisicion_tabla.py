"""Tabla de listado de requisiciones."""
import reflex as rx
from app.presentation.pages.requisiciones.requisiciones_state import RequisicionesState
from app.presentation.components.requisiciones.requisicion_estado_badge import estado_requisicion_badge
from app.presentation.components.ui import tabla_vacia, skeleton_tabla
from app.presentation.components.ui.action_buttons import (
    tabla_action_button,
    tabla_action_buttons,
)
from app.presentation.theme import Colors, Typography


# =============================================================================
# ACCIONES POR REQUISICION
# =============================================================================

def _acciones_requisicion(req: dict) -> rx.Component:
    """Acciones disponibles segun el estado y permisos del usuario."""
    es_borrador = req["estado"] == "BORRADOR"
    es_enviada = req["estado"] == "ENVIADA"
    es_en_revision = req["estado"] == "EN REVISION"
    es_aprobada = req["estado"] == "APROBADA"
    es_final = (req["estado"] == "CONTRATADA") | (req["estado"] == "CANCELADA")

    return tabla_action_buttons([
        # Ver detalle (siempre)
        tabla_action_button(
            icon="eye",
            tooltip="Ver detalle",
            on_click=lambda: RequisicionesState.abrir_detalle_completo(req),
        ),
        # Editar (BORRADOR + operar)
        tabla_action_button(
            icon="pencil",
            tooltip="Editar",
            on_click=lambda: RequisicionesState.abrir_modal_editar(req),
            color_scheme="blue",
            visible=es_borrador & RequisicionesState.puede_operar_requisiciones,
        ),
        # Enviar (BORRADOR + operar)
        tabla_action_button(
            icon="send",
            tooltip="Enviar",
            on_click=lambda: RequisicionesState.abrir_confirmar_estado(req, "enviar"),
            color_scheme="blue",
            visible=es_borrador & RequisicionesState.puede_operar_requisiciones,
        ),
        # Iniciar revision (ENVIADA + autorizar)
        tabla_action_button(
            icon="search",
            tooltip="Iniciar revision",
            on_click=lambda: RequisicionesState.abrir_detalle_completo(req),
            color_scheme="orange",
            visible=es_enviada & RequisicionesState.puede_autorizar_requisiciones,
        ),
        # Aprobar (EN_REVISION + autorizar)
        tabla_action_button(
            icon="check",
            tooltip="Aprobar",
            on_click=lambda: RequisicionesState.abrir_confirmar_estado(req, "aprobar"),
            color_scheme="green",
            visible=es_en_revision & RequisicionesState.puede_autorizar_requisiciones,
        ),
        # Rechazar (EN_REVISION + autorizar)
        tabla_action_button(
            icon="circle-x",
            tooltip="Rechazar",
            on_click=lambda: RequisicionesState.abrir_modal_rechazar(req),
            color_scheme="red",
            visible=es_en_revision & RequisicionesState.puede_autorizar_requisiciones,
        ),
        # Adjudicar (APROBADA + operar)
        tabla_action_button(
            icon="award",
            tooltip="Adjudicar",
            on_click=lambda: RequisicionesState.abrir_modal_adjudicar(req),
            color_scheme="purple",
            visible=es_aprobada & RequisicionesState.puede_operar_requisiciones,
        ),
        # Cancelar (no final + operar)
        tabla_action_button(
            icon="x",
            tooltip="Cancelar",
            on_click=lambda: RequisicionesState.abrir_confirmar_estado(req, "cancelar"),
            color_scheme="red",
            visible=~es_final & RequisicionesState.puede_operar_requisiciones,
        ),
        # Eliminar (BORRADOR + operar)
        tabla_action_button(
            icon="trash-2",
            tooltip="Eliminar",
            on_click=lambda: RequisicionesState.abrir_confirmar_eliminar(req),
            color_scheme="red",
            visible=es_borrador & RequisicionesState.puede_operar_requisiciones,
        ),
    ])


# =============================================================================
# FILA DE TABLA
# =============================================================================

def _fila_requisicion(req: dict) -> rx.Component:
    """Fila de la tabla para una requisicion."""
    return rx.table.row(
        # Numero (muestra folio si existe, sino "(Sin folio)")
        rx.table.cell(
            rx.cond(
                req["numero_requisicion"],
                rx.text(
                    req["numero_requisicion"],
                    font_weight=Typography.WEIGHT_BOLD,
                    font_size=Typography.SIZE_SM,
                ),
                rx.text(
                    "(Sin folio)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                    font_style="italic",
                ),
            ),
        ),
        # Fecha
        rx.table.cell(
            rx.text(req["fecha_elaboracion"], font_size=Typography.SIZE_SM, white_space="nowrap"),
            text_align="center",
        ),
        # Estado (con indicador de rechazo previo si aplica)
        rx.table.cell(
            rx.hstack(
                estado_requisicion_badge(req["estado"], show_icon=True),
                # Indicador de rechazo previo (numero_revision > 0)
                rx.cond(
                    req["numero_revision"].to(int) > 0,
                    rx.tooltip(
                        rx.badge(
                            rx.icon("rotate-ccw", size=12),
                            rx.text(req["numero_revision"], size="1"),
                            color_scheme="orange",
                            variant="soft",
                            size="1",
                        ),
                        content="Rechazada previamente. Editar para ver motivo.",
                    ),
                ),
                spacing="2",
                align="center",
            ),
        ),
        # Tipo
        rx.table.cell(
            rx.text(req["tipo_contratacion"], font_size=Typography.SIZE_SM),
        ),
        # Objeto (2 lineas max)
        rx.table.cell(
            rx.text(
                req["objeto_contratacion"],
                font_size=Typography.SIZE_SM,
                style={
                    "max_width": "280px",
                    "overflow": "hidden",
                    "text_overflow": "ellipsis",
                    "display": "-webkit-box",
                    "-webkit-line-clamp": "2",
                    "-webkit-box-orient": "vertical",
                },
            ),
        ),
        # Dependencia
        rx.table.cell(
            rx.text(req["dependencia_requirente"], font_size=Typography.SIZE_SM),
        ),
        # Acciones
        rx.table.cell(
            _acciones_requisicion(req),
            text_align="center",
        ),
    )


# =============================================================================
# ENCABEZADOS Y TABLA
# =============================================================================

ENCABEZADOS_REQUISICIONES = [
    {"nombre": "Numero", "ancho": "140px", "centrar": "0"},
    {"nombre": "Fecha", "ancho": "110px", "centrar": "0"},
    {"nombre": "Estado", "ancho": "150px", "centrar": "0"},
    {"nombre": "Tipo", "ancho": "100px", "centrar": "0"},
    {"nombre": "Objeto", "ancho": "280px", "centrar": "0"},
    {"nombre": "Dependencia", "ancho": "180px", "centrar": "0"},
    {"nombre": "Acciones", "ancho": "200px", "centrar": "1"},
]


def requisicion_tabla() -> rx.Component:
    """Tabla de requisiciones con skeleton de carga."""
    return rx.cond(
        RequisicionesState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_REQUISICIONES, filas=5),
        rx.cond(
            RequisicionesState.total_filtrado > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_REQUISICIONES,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                    text_align=rx.cond(col["centrar"] == "1", "center", "start"),
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            RequisicionesState.requisiciones_filtradas,
                            _fila_requisicion,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.text(
                    "Mostrando ",
                    RequisicionesState.total_filtrado,
                    " requisicion(es)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=RequisicionesState.abrir_modal_crear),
        ),
    )
