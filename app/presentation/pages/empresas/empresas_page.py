"""
Pagina principal de Empresas.
Muestra una tabla o cards con las empresas y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.empresas.empresas_state import EmpresasState
from app.core.enums import TipoEmpresa
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
    entity_card,
    switch_inactivos,
)
from app.presentation.theme import Colors, Spacing, Shadows, Typography
from app.presentation.components.empresas.empresa_modals import (
    modal_empresa,
    modal_detalle_empresa,
)


# =============================================================================
# ACCIONES Y BADGES
# =============================================================================

def acciones_empresa(empresa: dict) -> rx.Component:
    """Acciones para cada empresa usando componente genérico."""
    # Botones adicionales condicionales
    acciones_extra = [
        # Reactivar (si inactivo)
        rx.cond(
            empresa["estatus"] == "INACTIVO",
            rx.tooltip(
                rx.icon_button(
                    rx.icon("rotate-ccw", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="green",
                    cursor="pointer",
                    on_click=EmpresasState.cambiar_estatus_empresa(empresa["id"], "ACTIVO"),
                ),
                content="Reactivar",
            ),
            rx.fragment(),
        ),
        # Desactivar (si activo)
        rx.cond(
            empresa["estatus"] == "ACTIVO",
            rx.tooltip(
                rx.icon_button(
                    rx.icon("power-off", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    cursor="pointer",
                    on_click=EmpresasState.cambiar_estatus_empresa(empresa["id"], "INACTIVO"),
                ),
                content="Desactivar",
            ),
            rx.fragment(),
        ),
    ]

    return action_buttons_reactive(
        item=empresa,
        ver_action=EmpresasState.abrir_modal_detalle(empresa["id"]),
        editar_action=EmpresasState.abrir_modal_editar(empresa["id"]),
        puede_editar=empresa["estatus"] == "ACTIVO",
        acciones_extra=acciones_extra,
    )


def tipo_empresa_badge(tipo: str) -> rx.Component:
    """Badge para tipo de empresa."""
    return rx.match(
        tipo,
        ("NOMINA", rx.badge("NOMINA", color_scheme="blue", size="1")),
        ("MANTENIMIENTO", rx.badge("MANTENIMIENTO", color_scheme="green", size="1")),
        rx.badge(tipo, color_scheme="gray", size="1"),
    )


# =============================================================================
# TABLA
# =============================================================================

def fila_empresa(empresa: dict) -> rx.Component:
    """Fila de la tabla para una empresa."""
    return rx.table.row(
        # Codigo
        rx.table.cell(
            rx.text(
                empresa["codigo_corto"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_SM,
            ),
        ),
        # Nombre comercial
        rx.table.cell(
            rx.text(
                empresa["nombre_comercial"],
                font_size=Typography.SIZE_SM,
            ),
        ),
        # Razon social
        rx.table.cell(
            rx.text(
                empresa["razon_social"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        # Tipo
        rx.table.cell(
            tipo_empresa_badge(empresa["tipo_empresa"]),
        ),
        # Estatus
        rx.table.cell(
            status_badge_reactive(empresa["estatus"], show_icon=True),
        ),
        # Acciones
        rx.table.cell(
            acciones_empresa(empresa),
        ),
        cursor="pointer",
        _hover={"background": Colors.SURFACE_HOVER},
    )


ENCABEZADOS_EMPRESAS = [
    {"nombre": "Codigo", "ancho": "80px"},
    {"nombre": "Nombre comercial", "ancho": "200px"},
    {"nombre": "Razon social", "ancho": "200px"},
    {"nombre": "Tipo", "ancho": "100px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "120px"},
]


def tabla_empresas() -> rx.Component:
    """Vista de tabla de empresas"""
    return rx.cond(
        EmpresasState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_EMPRESAS, filas=5),
        rx.cond(
            EmpresasState.tiene_empresas,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_EMPRESAS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            EmpresasState.empresas_filtradas,
                            fila_empresa,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                # Contador
                rx.text(
                    "Mostrando ", EmpresasState.total_empresas, " empresa(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=EmpresasState.abrir_modal_crear),
        ),
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_empresa(empresa: dict) -> rx.Component:
    """Card individual para una empresa."""
    return rx.card(
        rx.vstack(
            # Header con codigo y estatus
            rx.hstack(
                rx.hstack(
                    rx.badge(empresa["codigo_corto"], variant="outline", size="2"),
                    tipo_empresa_badge(empresa["tipo_empresa"]),
                    spacing="2",
                ),
                rx.spacer(),
                status_badge_reactive(empresa["estatus"], show_icon=True),
                width="100%",
                align="center",
            ),

            # Nombre comercial
            rx.text(
                empresa["nombre_comercial"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_BASE,
                color=Colors.TEXT_PRIMARY,
            ),

            # Razon social
            rx.text(
                empresa["razon_social"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),

            # Email (si existe)
            rx.cond(
                empresa["email"],
                rx.hstack(
                    rx.icon("mail", size=14, color=Colors.TEXT_MUTED),
                    rx.text(
                        empresa["email"],
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="2",
                    align="center",
                ),
            ),

            # Acciones
            rx.hstack(
                acciones_empresa(empresa),
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


def grid_empresas() -> rx.Component:
    """Vista de cards de empresas"""
    return rx.cond(
        EmpresasState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            EmpresasState.tiene_empresas,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        EmpresasState.empresas_filtradas,
                        card_empresa,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(300px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", EmpresasState.total_empresas, " empresa(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=EmpresasState.abrir_modal_crear),
        ),
    )


# =============================================================================
# FILTROS
# =============================================================================

def filtros_empresas() -> rx.Component:
    """Filtros para empresas."""
    return rx.hstack(
        # Filtro por tipo
        rx.select.root(
            rx.select.trigger(placeholder="Tipo empresa", width="180px"),
            rx.select.content(
                rx.select.item("Todos", value="TODOS"),
                rx.foreach(
                    [e.value for e in TipoEmpresa],
                    lambda v: rx.select.item(v, value=v)
                )
            ),
            value=EmpresasState.filtro_tipo,
            on_change=EmpresasState.set_filtro_tipo,
        ),
        # Switch mostrar inactivas (usando componente reutilizable)
        switch_inactivos(
            checked=~EmpresasState.solo_activas,
            on_change=lambda v: EmpresasState.set_solo_activas(~v),
            label="Mostrar inactivas",
        ),
        spacing="3",
        align="center",
    )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def empresas_page() -> rx.Component:
    """Pagina de Empresas usando el nuevo layout"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Empresas",
                subtitulo="Administre las empresas del sistema",
                icono="building-2",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nueva Empresa",
                    on_click=EmpresasState.abrir_modal_crear,
                    color_scheme="blue",
                ),
            ),
            toolbar=page_toolbar(
                search_value=EmpresasState.filtro_busqueda,
                search_placeholder="Buscar por nombre, RFC o codigo...",
                on_search_change=EmpresasState.set_filtro_busqueda,
                on_search_clear=lambda: EmpresasState.set_filtro_busqueda(""),
                filters=filtros_empresas(),
                show_view_toggle=True,
                current_view=EmpresasState.view_mode,
                on_view_table=EmpresasState.set_view_table,
                on_view_cards=EmpresasState.set_view_cards,
            ),
            content=rx.vstack(
                # Contenido segun vista
                rx.cond(
                    EmpresasState.is_table_view,
                    tabla_empresas(),
                    grid_empresas(),
                ),

                # Modales
                modal_empresa(),
                modal_detalle_empresa(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=EmpresasState.on_mount_empresas,
    )
