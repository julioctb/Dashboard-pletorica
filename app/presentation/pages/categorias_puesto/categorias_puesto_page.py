"""
Pagina principal de Categorias de Puesto.
Muestra una tabla o cards con las categorias y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.categorias_puesto.categorias_puesto_state import CategoriasPuestoState
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
from app.presentation.components.categorias_puesto.categorias_puesto_modals import (
    modal_categoria_puesto,
    modal_confirmar_eliminar,
)


# =============================================================================
# ACCIONES
# =============================================================================

def acciones_categoria(categoria: dict) -> rx.Component:
    """Acciones para cada categoria"""
    # Boton de reactivar (solo visible si inactivo)
    boton_reactivar = rx.cond(
        categoria["estatus"] == "INACTIVO",
        rx.tooltip(
            rx.icon_button(
                rx.icon("rotate-ccw", size=14),
                size="1",
                variant="ghost",
                color_scheme="green",
                cursor="pointer",
                on_click=lambda: CategoriasPuestoState.activar_categoria(categoria),
            ),
            content="Reactivar",
        ),
        rx.fragment(),
    )

    return action_buttons_reactive(
        item=categoria,
        editar_action=lambda: CategoriasPuestoState.abrir_modal_editar(categoria),
        eliminar_action=lambda: CategoriasPuestoState.abrir_confirmar_eliminar(categoria),
        puede_editar=categoria["estatus"] == "ACTIVO",
        puede_eliminar=categoria["estatus"] == "ACTIVO",
        acciones_extra=[boton_reactivar],
    )


# =============================================================================
# TABLA
# =============================================================================

def fila_categoria(categoria: dict) -> rx.Component:
    """Fila de la tabla para una categoria"""
    return rx.table.row(
        # Clave
        rx.table.cell(
            rx.text(
                categoria["clave"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_SM,
            ),
        ),
        # Nombre
        rx.table.cell(
            rx.text(categoria["nombre"], font_size=Typography.SIZE_SM),
        ),
        # Orden
        rx.table.cell(
            rx.text(categoria["orden"].to(str), font_size=Typography.SIZE_SM),
        ),
        # Descripcion
        rx.table.cell(
            rx.cond(
                categoria["descripcion"],
                rx.text(
                    categoria["descripcion"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                rx.text("-", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
            ),
        ),
        # Estatus
        rx.table.cell(
            status_badge_reactive(categoria["estatus"], show_icon=True),
        ),
        # Acciones
        rx.table.cell(
            acciones_categoria(categoria),
        ),
    )


ENCABEZADOS_CATEGORIAS = [
    {"nombre": "Clave", "ancho": "80px"},
    {"nombre": "Nombre", "ancho": "180px"},
    {"nombre": "Orden", "ancho": "60px"},
    {"nombre": "Descripcion", "ancho": "auto"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "100px"},
]


def tabla_categorias() -> rx.Component:
    """Vista de tabla de categorias"""
    return rx.cond(
        CategoriasPuestoState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_CATEGORIAS, filas=5),
        rx.cond(
            CategoriasPuestoState.total_categorias > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_CATEGORIAS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            CategoriasPuestoState.categorias,
                            fila_categoria,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                # Contador
                rx.text(
                    "Mostrando ", CategoriasPuestoState.total_categorias, " categoria(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=CategoriasPuestoState.abrir_modal_crear),
        ),
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_categoria(categoria: dict) -> rx.Component:
    """Card individual para una categoria"""
    return rx.card(
        rx.vstack(
            # Header con clave y estatus
            rx.hstack(
                rx.hstack(
                    rx.badge(categoria["clave"], variant="outline", size="2"),
                    rx.badge(
                        rx.hstack(rx.icon("hash", size=12), categoria["orden"].to(str), spacing="1"),
                        variant="soft",
                        size="1",
                    ),
                    spacing="2",
                ),
                rx.spacer(),
                status_badge_reactive(categoria["estatus"], show_icon=True),
                width="100%",
                align="center",
            ),

            # Nombre
            rx.text(
                categoria["nombre"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_BASE,
            ),

            # Descripcion
            rx.cond(
                categoria["descripcion"],
                rx.text(
                    categoria["descripcion"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                    style={"max_width": "100%", "overflow": "hidden", "text_overflow": "ellipsis"},
                ),
                rx.fragment(),
            ),

            # Acciones
            rx.hstack(
                acciones_categoria(categoria),
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


def grid_categorias() -> rx.Component:
    """Vista de cards de categorias"""
    return rx.cond(
        CategoriasPuestoState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            CategoriasPuestoState.total_categorias > 0,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        CategoriasPuestoState.categorias,
                        card_categoria,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(280px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", CategoriasPuestoState.total_categorias, " categoria(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=CategoriasPuestoState.abrir_modal_crear),
        ),
    )


# =============================================================================
# FILTROS
# =============================================================================

def filtros_categorias() -> rx.Component:
    """Filtros para categorias"""
    return rx.hstack(
        # Filtro por tipo de servicio
        rx.select.root(
            rx.select.trigger(placeholder="Tipo de servicio", width="200px"),
            rx.select.content(
                rx.select.item("Todos los tipos", value="0"),
                rx.foreach(
                    CategoriasPuestoState.opciones_tipo_servicio,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=CategoriasPuestoState.filtro_tipo_servicio_id,
            on_change=CategoriasPuestoState.set_filtro_tipo_servicio_id,
        ),
        # Switch para mostrar inactivas
        switch_inactivos(
            checked=CategoriasPuestoState.incluir_inactivas,
            on_change=CategoriasPuestoState.toggle_inactivas,
            label="Mostrar inactivas",
        ),
        # Boton limpiar filtros
        rx.cond(
            CategoriasPuestoState.tiene_filtros_activos,
            rx.button(
                rx.icon("x", size=14),
                "Limpiar",
                on_click=CategoriasPuestoState.limpiar_filtros,
                variant="ghost",
                size="2",
            ),
            rx.fragment(),
        ),
        spacing="3",
        align="center",
    )


# =============================================================================
# BREADCRUMBS
# =============================================================================

def breadcrumbs() -> rx.Component:
    """Breadcrumbs de navegacion"""
    return rx.hstack(
        rx.link(
            rx.hstack(
                rx.icon("home", size=14),
                rx.text("Inicio", font_size=Typography.SIZE_SM),
                spacing="1",
            ),
            href="/",
            color=Colors.TEXT_MUTED,
            underline="none",
            _hover={"color": "blue"},
        ),
        rx.text("/", color=Colors.TEXT_MUTED, font_size=Typography.SIZE_SM),
        rx.link(
            rx.text("Tipos de Servicio", font_size=Typography.SIZE_SM),
            href="/tipos-servicio",
            color=Colors.TEXT_MUTED,
            underline="none",
            _hover={"color": "blue"},
        ),
        rx.cond(
            CategoriasPuestoState.filtro_tipo_servicio_id != "0",
            rx.hstack(
                rx.text("/", color=Colors.TEXT_MUTED, font_size=Typography.SIZE_SM),
                rx.text(
                    CategoriasPuestoState.nombre_tipo_filtrado,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                spacing="1",
            ),
            rx.hstack(
                rx.text("/", color=Colors.TEXT_MUTED, font_size=Typography.SIZE_SM),
                rx.text(
                    "Categorias",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                spacing="1",
            ),
        ),
        spacing="1",
        align="center",
        padding_bottom="2",
    )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def categorias_puesto_page() -> rx.Component:
    """Pagina de Categorias de Puesto usando el nuevo layout"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Categorias de Puesto",
                subtitulo="Administre las categorias de puesto por tipo de servicio",
                icono="folder",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nueva Categoria",
                    on_click=CategoriasPuestoState.abrir_modal_crear,
                    color_scheme="blue",
                ),
            ),
            toolbar=page_toolbar(
                search_value=CategoriasPuestoState.filtro_busqueda,
                search_placeholder="Buscar por clave o nombre...",
                on_search_change=CategoriasPuestoState.on_change_busqueda,
                on_search_clear=CategoriasPuestoState.limpiar_busqueda,
                filters=filtros_categorias(),
                show_view_toggle=True,
                current_view=CategoriasPuestoState.view_mode,
                on_view_table=CategoriasPuestoState.set_view_table,
                on_view_cards=CategoriasPuestoState.set_view_cards,
            ),
            content=rx.vstack(
                # Breadcrumbs
                breadcrumbs(),

                # Contenido segun vista
                rx.cond(
                    CategoriasPuestoState.is_table_view,
                    tabla_categorias(),
                    grid_categorias(),
                ),

                # Modales
                modal_categoria_puesto(),
                modal_confirmar_eliminar(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=CategoriasPuestoState.cargar_datos_iniciales,
    )
