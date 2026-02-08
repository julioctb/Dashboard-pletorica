"""Tabla de listado de requisiciones."""
import reflex as rx
from app.presentation.pages.requisiciones.requisiciones_state import RequisicionesState
from app.presentation.components.requisiciones.requisicion_estado_badge import estado_requisicion_badge
from app.presentation.components.ui import tabla_vacia, skeleton_tabla
from app.presentation.theme import Colors, Typography


# =============================================================================
# ACCIONES POR REQUISICION
# =============================================================================

def _acciones_requisicion(req: dict) -> rx.Component:
    """Acciones disponibles segun el estado de la requisicion."""
    return rx.hstack(
        # Ver detalle (siempre)
        rx.tooltip(
            rx.icon_button(
                rx.icon("eye", size=14),
                size="1",
                variant="ghost",
                color_scheme="gray",
                on_click=lambda: RequisicionesState.abrir_modal_detalle(req),
            ),
            content="Ver detalle",
        ),
        # Editar (solo BORRADOR)
        rx.cond(
            req["estado"] == "BORRADOR",
            rx.tooltip(
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="blue",
                    on_click=lambda: RequisicionesState.abrir_modal_editar(req),
                ),
                content="Editar",
            ),
        ),
        # Enviar (solo BORRADOR)
        rx.cond(
            req["estado"] == "BORRADOR",
            rx.tooltip(
                rx.icon_button(
                    rx.icon("send", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="blue",
                    on_click=lambda: RequisicionesState.abrir_confirmar_estado(req, "enviar"),
                ),
                content="Enviar",
            ),
        ),
        # Iniciar revision (solo ENVIADA)
        rx.cond(
            req["estado"] == "ENVIADA",
            rx.tooltip(
                rx.icon_button(
                    rx.icon("search", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="orange",
                    on_click=lambda: RequisicionesState.abrir_confirmar_estado(req, "revisar"),
                ),
                content="Iniciar revision",
            ),
        ),
        # Aprobar (solo EN_REVISION)
        rx.cond(
            req["estado"] == "EN_REVISION",
            rx.tooltip(
                rx.icon_button(
                    rx.icon("check", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="green",
                    on_click=lambda: RequisicionesState.abrir_confirmar_estado(req, "aprobar"),
                ),
                content="Aprobar",
            ),
        ),
        # Adjudicar (solo APROBADA)
        rx.cond(
            req["estado"] == "APROBADA",
            rx.tooltip(
                rx.icon_button(
                    rx.icon("award", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="purple",
                    on_click=lambda: RequisicionesState.abrir_modal_adjudicar(req),
                ),
                content="Adjudicar",
            ),
        ),
        # Devolver (ENVIADA o EN_REVISION)
        rx.cond(
            (req["estado"] == "ENVIADA") | (req["estado"] == "EN_REVISION"),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("undo-2", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="orange",
                    on_click=lambda: RequisicionesState.abrir_confirmar_estado(req, "devolver"),
                ),
                content="Devolver a borrador",
            ),
        ),
        # Cancelar (estados no finales)
        rx.cond(
            (req["estado"] != "CONTRATADA") & (req["estado"] != "CANCELADA"),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("x", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=lambda: RequisicionesState.abrir_confirmar_estado(req, "cancelar"),
                ),
                content="Cancelar",
            ),
        ),
        # Eliminar (solo BORRADOR)
        rx.cond(
            req["estado"] == "BORRADOR",
            rx.tooltip(
                rx.icon_button(
                    rx.icon("trash-2", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=lambda: RequisicionesState.abrir_confirmar_eliminar(req),
                ),
                content="Eliminar",
            ),
        ),
        spacing="1",
        justify="center",
    )


# =============================================================================
# FILA DE TABLA
# =============================================================================

def _fila_requisicion(req: dict) -> rx.Component:
    """Fila de la tabla para una requisicion."""
    return rx.table.row(
        # Numero (borrador muestra placeholder)
        rx.table.cell(
            rx.cond(
                req["estado"] == "BORRADOR",
                rx.text(
                    "(Borrador)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                    font_style="italic",
                ),
                rx.text(
                    req["numero_requisicion"],
                    font_weight=Typography.WEIGHT_BOLD,
                    font_size=Typography.SIZE_SM,
                ),
            ),
        ),
        # Fecha
        rx.table.cell(
            rx.text(req["fecha_elaboracion"], font_size=Typography.SIZE_SM, white_space="nowrap"),
            text_align="center",
        ),
        # Estado
        rx.table.cell(
            estado_requisicion_badge(req["estado"], show_icon=True),
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
    {"nombre": "Estado", "ancho": "110px", "centrar": "0"},
    {"nombre": "Tipo", "ancho": "100px", "centrar": "0"},
    {"nombre": "Objeto", "ancho": "280px", "centrar": "0"},
    {"nombre": "Dependencia", "ancho": "180px", "centrar": "0"},
    {"nombre": "Acciones", "ancho": "160px", "centrar": "1"},
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
