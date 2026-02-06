"""
Pagina principal de Tipos de Servicio.
Muestra una tabla o cards con los tipos y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.tipo_servicio.tipo_servicio_state import TipoServicioState
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
from app.presentation.components.tipo_servicio.tipo_servicio_modals import (
    modal_tipo_servicio,
    modal_confirmar_eliminar,
)


# =============================================================================
# ACCIONES
# =============================================================================

def acciones_tipo(tipo: dict) -> rx.Component:
    """Acciones para cada tipo de servicio"""
    # Boton para ver categorias (siempre visible)
    btn_ver_categorias = rx.tooltip(
        rx.link(
            rx.icon_button(
                rx.icon("folder", size=14),
                size="1",
                variant="ghost",
                color_scheme="teal",
            ),
            href="/categorias-puesto?tipo=" + tipo["id"].to(str),
        ),
        content="Ver categorias",
    )

    # Boton para reactivar (solo si inactivo)
    btn_reactivar = rx.cond(
        tipo["estatus"] == "INACTIVO",
        rx.tooltip(
            rx.icon_button(
                rx.icon("rotate-ccw", size=14),
                size="1",
                variant="ghost",
                color_scheme="green",
                on_click=lambda: TipoServicioState.activar_tipo(tipo),
            ),
            content="Reactivar",
        ),
        rx.fragment(),
    )

    return action_buttons_reactive(
        item=tipo,
        editar_action=lambda: TipoServicioState.abrir_modal_editar(tipo),
        eliminar_action=lambda: TipoServicioState.abrir_confirmar_eliminar(tipo),
        puede_editar=tipo["estatus"] == "ACTIVO",
        puede_eliminar=tipo["estatus"] == "ACTIVO",
        acciones_extra=[btn_ver_categorias, btn_reactivar],
    )


# =============================================================================
# TABLA
# =============================================================================

def fila_tipo(tipo: dict) -> rx.Component:
    """Fila de la tabla para un tipo"""
    return rx.table.row(
        # Clave
        rx.table.cell(
            rx.text(
                tipo["clave"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_SM,
            ),
        ),
        # Nombre
        rx.table.cell(
            rx.link(
                rx.text(
                    tipo["nombre"],
                    font_size=Typography.SIZE_SM,
                    _hover={"text_decoration": "underline"},
                ),
                href="/categorias-puesto?tipo=" + tipo["id"].to(str),
                color="inherit",
                underline="none",
            ),
        ),
        # Descripcion
        rx.table.cell(
            rx.cond(
                tipo["descripcion"],
                rx.text(
                    tipo["descripcion"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                rx.text("-", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
            ),
        ),
        # Estatus
        rx.table.cell(
            status_badge_reactive(tipo["estatus"], show_icon=True),
        ),
        # Acciones
        rx.table.cell(
            acciones_tipo(tipo),
        ),
    )


ENCABEZADOS_TIPOS = [
    {"nombre": "Clave", "ancho": "100px"},
    {"nombre": "Nombre", "ancho": "200px"},
    {"nombre": "Descripcion", "ancho": "auto"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "120px"},
]


def tabla_tipos() -> rx.Component:
    """Vista de tabla de tipos"""
    return rx.cond(
        TipoServicioState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_TIPOS, filas=5),
        rx.cond(
            TipoServicioState.total_tipos > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_TIPOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            TipoServicioState.tipos,
                            fila_tipo,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                # Contador
                rx.text(
                    "Mostrando ", TipoServicioState.total_tipos, " tipo(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=TipoServicioState.abrir_modal_crear),
        ),
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_tipo(tipo: dict) -> rx.Component:
    """Card individual para un tipo de servicio"""
    return rx.card(
        rx.vstack(
            # Header con clave y estatus
            rx.hstack(
                rx.badge(tipo["clave"], variant="outline", size="2"),
                rx.spacer(),
                status_badge_reactive(tipo["estatus"], show_icon=True),
                width="100%",
                align="center",
            ),

            # Nombre
            rx.link(
                rx.text(
                    tipo["nombre"],
                    font_weight=Typography.WEIGHT_BOLD,
                    font_size=Typography.SIZE_LG,
                    _hover={"text_decoration": "underline"},
                ),
                href="/categorias-puesto?tipo=" + tipo["id"].to(str),
                color="inherit",
                underline="none",
            ),

            # Descripcion
            rx.cond(
                tipo["descripcion"],
                rx.text(
                    tipo["descripcion"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                    style={"max_width": "100%", "overflow": "hidden", "text_overflow": "ellipsis"},
                ),
            ),

            # Acciones
            rx.hstack(
                acciones_tipo(tipo),
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


def grid_tipos() -> rx.Component:
    """Vista de cards de tipos"""
    return rx.cond(
        TipoServicioState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            TipoServicioState.total_tipos > 0,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        TipoServicioState.tipos,
                        card_tipo,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(280px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", TipoServicioState.total_tipos, " tipo(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=TipoServicioState.abrir_modal_crear),
        ),
    )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def tipo_servicio_page() -> rx.Component:
    """Pagina de Tipos de Servicio usando el nuevo layout"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Tipos de Servicio",
                subtitulo="Administre los tipos de servicio del sistema",
                icono="briefcase",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo Servicio",
                    on_click=TipoServicioState.abrir_modal_crear,
                    color_scheme="blue",
                ),
            ),
            toolbar=page_toolbar(
                search_value=TipoServicioState.filtro_busqueda,
                search_placeholder="Buscar por clave o nombre...",
                on_search_change=TipoServicioState.on_change_busqueda,
                on_search_clear=TipoServicioState.limpiar_busqueda,
                show_view_toggle=True,
                current_view=TipoServicioState.view_mode,
                on_view_table=TipoServicioState.set_view_table,
                on_view_cards=TipoServicioState.set_view_cards,
            ),
            content=rx.vstack(
                # Contenido segun vista
                rx.cond(
                    TipoServicioState.is_table_view,
                    tabla_tipos(),
                    grid_tipos(),
                ),

                # Modales
                modal_tipo_servicio(),
                modal_confirmar_eliminar(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=TipoServicioState.cargar_tipos,
    )
