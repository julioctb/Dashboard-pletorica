"""
Página principal de Historial Laboral.

Esta página es de SOLO LECTURA.
Muestra la bitácora automática de movimientos de empleados.
Los registros se crean automáticamente desde empleado_service.
"""
import reflex as rx
from app.presentation.pages.historial_laboral.historial_laboral_state import HistorialLaboralState
from app.presentation.layout import (
    page_layout,
    page_header,
    page_toolbar,
)
from app.presentation.components.ui import (skeleton_tabla,
)
from app.presentation.theme import Colors, Spacing, Shadows
from app.presentation.pages.historial_laboral.historial_laboral_modals import modal_detalle


# =============================================================================
# HELPERS
# =============================================================================

def estatus_badge(estatus: str) -> rx.Component:
    """Badge para estatus del empleado en el historial"""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("Activo", color_scheme="green", size="1")),
        ("INACTIVO", rx.badge("Inactivo", color_scheme="gray", size="1")),
        ("SUSPENDIDO", rx.badge("Suspendido", color_scheme="amber", size="1")),
        rx.badge(estatus, color_scheme="gray", size="1"),
    )


def tipo_movimiento_badge(tipo: str) -> rx.Component:
    """Badge para tipo de movimiento"""
    return rx.match(
        tipo,
        ("Alta en sistema", rx.badge("Alta", color_scheme="blue", variant="soft", size="1")),
        ("Asignación a plaza", rx.badge("Asignación", color_scheme="green", variant="soft", size="1")),
        ("Cambio de plaza", rx.badge("Cambio", color_scheme="cyan", variant="soft", size="1")),
        ("Suspensión", rx.badge("Suspensión", color_scheme="amber", variant="soft", size="1")),
        ("Reactivación", rx.badge("Reactivación", color_scheme="teal", variant="soft", size="1")),
        ("Baja del sistema", rx.badge("Baja", color_scheme="red", variant="soft", size="1")),
        # Default: usar rx.cond en lugar de "or" para variables reactivas
        rx.cond(
            tipo,
            rx.badge(tipo, color_scheme="gray", variant="soft", size="1"),
            rx.badge("N/A", color_scheme="gray", variant="soft", size="1"),
        ),
    )


def acciones_historial(registro: dict) -> rx.Component:
    """Acciones para cada registro de historial (solo ver detalle)"""
    return rx.hstack(
        rx.tooltip(
            rx.icon_button(
                rx.icon("eye", size=14),
                size="1",
                variant="ghost",
                color_scheme="gray",
                on_click=lambda: HistorialLaboralState.abrir_modal_detalle(registro),
            ),
            content="Ver detalle",
        ),
        spacing="1",
    )


# =============================================================================
# TABLA
# =============================================================================

def fila_historial(registro: dict) -> rx.Component:
    """Fila de la tabla para un registro de historial"""
    return rx.table.row(
        # Empleado
        rx.table.cell(
            rx.vstack(
                rx.text(registro["empleado_clave"], weight="bold", size="2"),
                rx.text(registro["empleado_nombre"], size="1", color="gray"),
                spacing="0",
                align_items="start",
            ),
        ),
        # Tipo de Movimiento
        rx.table.cell(
            tipo_movimiento_badge(registro["tipo_movimiento"]),
        ),
        # Plaza (puede ser None)
        rx.table.cell(
            rx.cond(
                registro["plaza_numero"],
                rx.vstack(
                    rx.text(f"#{registro['plaza_numero']}", size="2"),
                    rx.text(registro["categoria_nombre"], size="1", color="gray"),
                    spacing="0",
                    align_items="start",
                ),
                rx.text("Sin plaza", size="2", color="gray", style={"fontStyle": "italic"}),
            ),
        ),
        # Empresa (puede ser None)
        rx.table.cell(
            rx.cond(
                registro["empresa_nombre"],
                rx.text(registro["empresa_nombre"], size="2"),
                rx.text("-", size="2", color="gray"),
            ),
        ),
        # Período
        rx.table.cell(
            rx.text(registro["periodo_texto"], size="2"),
        ),
        # Duración
        rx.table.cell(
            rx.text(registro["duracion_texto"], size="2"),
        ),
        # Estatus
        rx.table.cell(
            estatus_badge(registro["estatus"]),
        ),
        # Acciones
        rx.table.cell(
            acciones_historial(registro),
        ),
        cursor="pointer",
        _hover={"background": Colors.SURFACE_HOVER},
        on_click=lambda: HistorialLaboralState.abrir_modal_detalle(registro),
    )


ENCABEZADOS_HISTORIAL = [
    {"nombre": "Empleado", "ancho": "170px"},
    {"nombre": "Movimiento", "ancho": "120px"},
    {"nombre": "Plaza", "ancho": "130px"},
    {"nombre": "Empresa", "ancho": "140px"},
    {"nombre": "Período", "ancho": "140px"},
    {"nombre": "Duración", "ancho": "100px"},
    {"nombre": "Estatus", "ancho": "90px"},
    {"nombre": "", "ancho": "50px"},
]


def tabla_historial() -> rx.Component:
    """Vista de tabla de historial"""
    return rx.cond(
        HistorialLaboralState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_HISTORIAL, filas=5),
        rx.cond(
            HistorialLaboralState.tiene_historial,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_HISTORIAL,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            HistorialLaboralState.historial_filtrado,
                            fila_historial,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                # Contador
                rx.text(
                    "Mostrando ", HistorialLaboralState.total_filtrado, " registro(s)",
                    size="2",
                    color="gray",
                ),
                width="100%",
                spacing="3",
            ),
            
        ),
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_historial(registro: dict) -> rx.Component:
    """Card individual para un registro de historial"""
    return rx.card(
        rx.vstack(
            # Header con empleado y estatus
            rx.hstack(
                rx.vstack(
                    rx.badge(registro["empleado_clave"], variant="outline", size="2"),
                    rx.text(registro["empleado_nombre"], weight="bold", size="3"),
                    spacing="1",
                    align_items="start",
                ),
                rx.spacer(),
                rx.vstack(
                    estatus_badge(registro["estatus"]),
                    tipo_movimiento_badge(registro["tipo_movimiento"]),
                    spacing="1",
                    align_items="end",
                ),
                width="100%",
                align="start",
            ),

            rx.divider(),

            # Plaza y empresa
            rx.vstack(
                rx.hstack(
                    rx.icon("briefcase", size=14, color=Colors.TEXT_MUTED),
                    rx.cond(
                        registro["plaza_numero"],
                        rx.text(f"Plaza #{registro['plaza_numero']} - {registro['categoria_nombre']}", size="2"),
                        rx.text("Sin plaza asignada", size="2", color="gray", style={"fontStyle": "italic"}),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    registro["empresa_nombre"],
                    rx.hstack(
                        rx.icon("building-2", size=14, color=Colors.TEXT_MUTED),
                        rx.text(registro["empresa_nombre"], size="2"),
                        spacing="2",
                        align="center",
                    ),
                ),
                spacing="2",
                align_items="start",
                width="100%",
            ),

            # Período y duración
            rx.hstack(
                rx.vstack(
                    rx.text("Período", size="1", color="gray"),
                    rx.text(registro["periodo_texto"], size="2"),
                    spacing="0",
                ),
                rx.vstack(
                    rx.text("Duración", size="1", color="gray"),
                    rx.text(registro["duracion_texto"], size="2", weight="medium"),
                    spacing="0",
                ),
                spacing="4",
                width="100%",
            ),

            # Acciones
            rx.hstack(
                acciones_historial(registro),
                width="100%",
                justify="end",
            ),

            spacing="3",
            width="100%",
        ),
        width="100%",
        style={
            "transition": "all 0.2s ease",
            "cursor": "pointer",
            "_hover": {
                "box_shadow": Shadows.MD,
                "border_color": Colors.BORDER_STRONG,
            },
        },
        on_click=lambda: HistorialLaboralState.abrir_modal_detalle(registro),
    )


def grid_historial() -> rx.Component:
    """Vista de cards de historial"""
    return rx.cond(
        HistorialLaboralState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            HistorialLaboralState.tiene_historial,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        HistorialLaboralState.historial_filtrado,
                        card_historial,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(350px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", HistorialLaboralState.total_filtrado, " registro(s)",
                    size="2",
                    color="gray",
                ),
                width="100%",
                spacing="3",
            ),
            
        ),
    )


# =============================================================================
# FILTROS
# =============================================================================

def filtros_historial() -> rx.Component:
    """Filtros para historial"""
    return rx.hstack(
        # Filtro por estatus
        rx.select.root(
            rx.select.trigger(placeholder="Estatus", width="140px"),
            rx.select.content(
                rx.foreach(
                    HistorialLaboralState.opciones_estatus,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=HistorialLaboralState.filtro_estatus,
            on_change=HistorialLaboralState.set_filtro_estatus,
        ),
        # Botón aplicar
        rx.button(
            "Aplicar",
            size="2",
            variant="soft",
            on_click=HistorialLaboralState.aplicar_filtros,
        ),
        spacing="3",
        align="center",
    )


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

def historial_laboral_page() -> rx.Component:
    """Página de Historial Laboral (solo lectura)"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Historial Laboral",
                subtitulo="Bitácora automática de movimientos de empleados",
                icono="history",
                # Sin botón de acción - es solo lectura
            ),
            toolbar=page_toolbar(
                search_value=HistorialLaboralState.search,
                search_placeholder="Buscar por empleado, plaza, empresa o movimiento...",
                on_search_change=HistorialLaboralState.set_search,
                on_search_clear=lambda: HistorialLaboralState.set_search(""),
                filters=filtros_historial(),
                show_view_toggle=True,
                current_view=HistorialLaboralState.view_mode,
                on_view_table=HistorialLaboralState.set_view_table,
                on_view_cards=HistorialLaboralState.set_view_cards,
            ),
            content=rx.vstack(
                # Info banner
                rx.callout(
                    "Los registros de historial se crean automáticamente cuando se realizan cambios en los empleados (alta, suspensión, reactivación, baja).",
                    icon="info",
                    color_scheme="blue",
                    size="1",
                ),

                # Contenido según vista
                rx.cond(
                    HistorialLaboralState.is_table_view,
                    tabla_historial(),
                    grid_historial(),
                ),

                # Modal de detalle
                modal_detalle(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=HistorialLaboralState.on_mount,
    )
