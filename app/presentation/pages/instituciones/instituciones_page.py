"""
Pagina principal de Instituciones.
Muestra tabla o cards con las instituciones y acciones CRUD + gestion de empresas.
"""
import reflex as rx
from app.presentation.pages.instituciones.instituciones_state import InstitucionesState
from app.presentation.layout import (
    page_layout,
    page_header,
    page_toolbar,
)
from app.presentation.components.ui import (
    table_cell_actions,
    table_cell_badge,
    table_shell,
    status_badge_reactive,
    tabla_vacia,
    tabla_action_button,
    tabla_action_buttons,
)
from app.presentation.theme import Colors, Spacing, Shadows, Typography
from app.presentation.pages.instituciones.instituciones_modals import (
    modal_institucion,
    modal_gestionar_empresas,
    modal_confirmar_desactivar,
)


# =============================================================================
# ACCIONES
# =============================================================================

def acciones_institucion(institucion: dict) -> rx.Component:
    """Acciones para cada institucion"""
    es_activo = institucion["estatus"] == "ACTIVO"
    es_inactivo = institucion["estatus"] == "INACTIVO"

    return tabla_action_buttons([
        # Gestionar empresas
        tabla_action_button(
            icon="building-2",
            tooltip="Gestionar Empresas",
            on_click=lambda: InstitucionesState.abrir_modal_empresas(institucion),
            color_scheme="purple",
            visible=es_activo,
        ),
        # Editar
        tabla_action_button(
            icon="pencil",
            tooltip="Editar",
            on_click=lambda: InstitucionesState.abrir_modal_editar(institucion),
            color_scheme="blue",
            visible=es_activo,
        ),
        # Desactivar
        tabla_action_button(
            icon="trash-2",
            tooltip="Desactivar",
            on_click=lambda: InstitucionesState.abrir_confirmar_desactivar(institucion),
            color_scheme="red",
            visible=es_activo,
        ),
        # Reactivar
        tabla_action_button(
            icon="rotate-ccw",
            tooltip="Reactivar",
            on_click=lambda: InstitucionesState.activar_institucion(institucion),
            color_scheme="green",
            visible=es_inactivo,
        ),
    ])


# =============================================================================
# TABLA
# =============================================================================

def fila_institucion(institucion: dict) -> rx.Component:
    """Fila de la tabla para una institucion"""
    return rx.table.row(
        # Codigo
        rx.table.cell(
            rx.text(
                institucion["codigo"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_SM,
            ),
        ),
        # Nombre
        rx.table.cell(
            rx.text(institucion["nombre"], font_size=Typography.SIZE_SM),
        ),
        # Empresas
        rx.table.cell(
            rx.badge(
                institucion["cantidad_empresas"],
                variant="soft",
                size="1",
            ),
        ),
        # Estatus
        table_cell_badge(status_badge_reactive(institucion["estatus"], show_icon=True)),
        # Acciones
        table_cell_actions(acciones_institucion(institucion)),
    )


ENCABEZADOS_INSTITUCIONES = [
    {"nombre": "Codigo", "ancho": "120px"},
    {"nombre": "Nombre", "ancho": "auto"},
    {"nombre": "Empresas", "ancho": "100px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "130px"},
]


def tabla_instituciones() -> rx.Component:
    """Vista de tabla de instituciones"""
    return table_shell(
        loading=InstitucionesState.loading,
        headers=ENCABEZADOS_INSTITUCIONES,
        rows=InstitucionesState.instituciones,
        row_renderer=fila_institucion,
        has_rows=InstitucionesState.total_instituciones > 0,
        empty_component=tabla_vacia(onclick=InstitucionesState.abrir_modal_crear),
        total_caption="Mostrando " + InstitucionesState.total_instituciones.to(str) + " institucion(es)",
        loading_rows=5,
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_institucion(institucion: dict) -> rx.Component:
    """Card individual para una institucion"""
    return rx.card(
        rx.vstack(
            # Header con codigo y estatus
            rx.hstack(
                rx.badge(institucion["codigo"], variant="outline", size="2"),
                rx.spacer(),
                status_badge_reactive(institucion["estatus"], show_icon=True),
                width="100%",
                align="center",
            ),
            # Nombre
            rx.text(
                institucion["nombre"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_LG,
            ),
            # Cantidad de empresas
            rx.hstack(
                rx.icon("building-2", size=14, color=Colors.TEXT_MUTED),
                rx.text(
                    institucion["cantidad_empresas"],
                    " empresa(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="2",
                align="center",
            ),
            # Acciones
            rx.hstack(
                acciones_institucion(institucion),
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


def grid_instituciones() -> rx.Component:
    """Vista de cards de instituciones"""
    return rx.cond(
        InstitucionesState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            InstitucionesState.total_instituciones > 0,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        InstitucionesState.instituciones,
                        card_institucion,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(280px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", InstitucionesState.total_instituciones, " institucion(es)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=InstitucionesState.abrir_modal_crear),
        ),
    )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def instituciones_page() -> rx.Component:
    """Pagina de Instituciones usando el layout estandar"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Instituciones",
                subtitulo="Administre las instituciones y sus empresas asociadas",
                icono="building",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nueva Institucion",
                    on_click=InstitucionesState.abrir_modal_crear,
                    color_scheme="blue",
                ),
            ),
            toolbar=page_toolbar(
                search_value=InstitucionesState.filtro_busqueda,
                search_placeholder="Buscar por codigo, nombre...",
                on_search_change=InstitucionesState.on_change_busqueda,
                on_search_clear=InstitucionesState.limpiar_busqueda,
                show_view_toggle=True,
                current_view=InstitucionesState.view_mode,
                on_view_table=InstitucionesState.set_view_table,
                on_view_cards=InstitucionesState.set_view_cards,
            ),
            content=rx.vstack(
                # Contenido segun vista
                rx.cond(
                    InstitucionesState.is_table_view,
                    tabla_instituciones(),
                    grid_instituciones(),
                ),

                # Modales
                modal_institucion(),
                modal_gestionar_empresas(),
                modal_confirmar_desactivar(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=InstitucionesState.on_mount_instituciones,
    )
