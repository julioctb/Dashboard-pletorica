"""
Pagina principal de Sedes BUAP.
Muestra una tabla o cards con las sedes y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.sedes.sedes_state import SedesState
from app.presentation.layout import (
    page_layout,
    page_header,
    page_toolbar,
)
from app.presentation.components.ui import (
    status_badge_reactive,
    tabla_vacia,
    skeleton_tabla,
    action_buttons_reactive,
    switch_inactivos,
)
from app.presentation.theme import Colors, Spacing, Shadows, Typography
from app.presentation.components.sedes.sedes_modals import (
    modal_sede,
    modal_confirmar_eliminar,
)


# =============================================================================
# ACCIONES
# =============================================================================

def acciones_sede(sede: dict) -> rx.Component:
    """Acciones para cada sede"""
    # Boton de reactivar (solo visible si inactivo)
    btn_reactivar = rx.cond(
        sede["estatus"] == "INACTIVO",
        rx.tooltip(
            rx.icon_button(
                rx.icon("rotate-ccw", size=14),
                size="1",
                variant="ghost",
                color_scheme="green",
                cursor="pointer",
                on_click=lambda: SedesState.activar_sede(sede),
            ),
            content="Reactivar",
        ),
        rx.fragment(),
    )

    return action_buttons_reactive(
        item=sede,
        editar_action=lambda: SedesState.abrir_modal_editar(sede),
        eliminar_action=lambda: SedesState.abrir_confirmar_eliminar(sede),
        puede_editar=sede["estatus"] == "ACTIVO",
        puede_eliminar=sede["estatus"] == "ACTIVO",
        acciones_extra=[btn_reactivar],
    )


# =============================================================================
# TABLA
# =============================================================================

def fila_sede(sede: dict) -> rx.Component:
    """Fila de la tabla para una sede"""
    return rx.table.row(
        # Codigo
        rx.table.cell(
            rx.text(
                sede["codigo"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_SM,
            ),
        ),
        # Nombre
        rx.table.cell(
            rx.vstack(
                rx.text(sede["nombre"], font_size=Typography.SIZE_SM),
                rx.cond(
                    sede["nombre_corto"],
                    rx.text(
                        sede["nombre_corto"],
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.fragment(),
                ),
                spacing="0",
            ),
        ),
        # Tipo
        rx.table.cell(
            rx.text(sede["tipo_descripcion"], font_size=Typography.SIZE_SM),
        ),
        # Ubicacion (padre o ubicacion fisica)
        rx.table.cell(
            rx.cond(
                sede["sede_padre_nombre"] != "",
                rx.text(
                    sede["sede_padre_nombre"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                rx.text("-", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
            ),
        ),
        # Estatus
        rx.table.cell(
            status_badge_reactive(sede["estatus"], show_icon=True),
        ),
        # Acciones
        rx.table.cell(
            acciones_sede(sede),
        ),
    )


ENCABEZADOS_SEDES = [
    {"nombre": "Codigo", "ancho": "120px"},
    {"nombre": "Nombre", "ancho": "auto"},
    {"nombre": "Tipo", "ancho": "140px"},
    {"nombre": "Ubicacion", "ancho": "160px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "100px"},
]


def tabla_sedes() -> rx.Component:
    """Vista de tabla de sedes"""
    return rx.cond(
        SedesState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_SEDES, filas=5),
        rx.cond(
            SedesState.total_sedes > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_SEDES,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            SedesState.sedes,
                            fila_sede,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                # Contador
                rx.text(
                    "Mostrando ", SedesState.total_sedes, " sede(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=SedesState.abrir_modal_crear),
        ),
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_sede(sede: dict) -> rx.Component:
    """Card individual para una sede"""
    return rx.card(
        rx.vstack(
            # Header con codigo y estatus
            rx.hstack(
                rx.badge(sede["codigo"], variant="outline", size="2"),
                rx.spacer(),
                status_badge_reactive(sede["estatus"], show_icon=True),
                width="100%",
                align="center",
            ),

            # Nombre
            rx.text(
                sede["nombre"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_LG,
            ),

            # Nombre corto
            rx.cond(
                sede["nombre_corto"],
                rx.text(
                    sede["nombre_corto"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.fragment(),
            ),

            # Tipo y ubicacion
            rx.hstack(
                rx.badge(sede["tipo_descripcion"], variant="soft", size="1"),
                rx.cond(
                    sede["sede_padre_nombre"] != "",
                    rx.text(
                        sede["sede_padre_nombre"],
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                wrap="wrap",
            ),

            # Acciones
            rx.hstack(
                acciones_sede(sede),
                width="100%",
                justify="end",
            ),

            spacing="3",
            width="100%",
        ),
        width="100%",
        style={
            "transition": "all 0.2s ease",
            "_hover": {
                "box_shadow": Shadows.MD,
                "border_color": Colors.BORDER_STRONG,
            },
        },
    )


def grid_sedes() -> rx.Component:
    """Vista de cards de sedes"""
    return rx.cond(
        SedesState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            SedesState.total_sedes > 0,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        SedesState.sedes,
                        card_sede,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(280px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", SedesState.total_sedes, " sede(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=SedesState.abrir_modal_crear),
        ),
    )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def sedes_page() -> rx.Component:
    """Pagina de Sedes BUAP usando el layout estandar"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Sedes BUAP",
                subtitulo="Administre las sedes y ubicaciones del sistema",
                icono="building-2",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nueva Sede",
                    on_click=SedesState.abrir_modal_crear,
                    color_scheme="blue",
                ),
            ),
            toolbar=page_toolbar(
                search_value=SedesState.filtro_busqueda,
                search_placeholder="Buscar por codigo, nombre...",
                on_search_change=SedesState.on_change_busqueda,
                on_search_clear=SedesState.limpiar_busqueda,
                show_view_toggle=True,
                current_view=SedesState.view_mode,
                on_view_table=SedesState.set_view_table,
                on_view_cards=SedesState.set_view_cards,
            ),
            content=rx.vstack(
                # Contenido segun vista
                rx.cond(
                    SedesState.is_table_view,
                    tabla_sedes(),
                    grid_sedes(),
                ),

                # Modales
                modal_sede(),
                modal_confirmar_eliminar(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=SedesState.cargar_sedes,
    )
