"""
Página principal de Plazas.
Muestra las plazas de un contrato o categoría con vista de tabla o cards.
"""
import reflex as rx
from app.presentation.pages.plazas.plazas_state import PlazasState
from app.presentation.layout import (
    page_layout,
    page_header,
    page_toolbar,
)
from app.presentation.components.ui import (
    status_badge_reactive,
    tabla_vacia,
    skeleton_tabla,
    breadcrumb_dynamic,
    switch_inactivos,
    tabla_action_button,
    tabla_action_buttons,
)
from app.presentation.components.plazas.plazas_modals import (
    modal_plaza,
    modal_detalle_plaza,
    modal_confirmar_cancelar,
    modal_crear_lote,
    modal_asignar_empleado,
)
from app.presentation.theme import Colors, Spacing, Shadows, Radius, Typography


# =============================================================================
# TABLA DE PLAZAS
# =============================================================================

def acciones_plaza(plaza: dict) -> rx.Component:
    """Acciones especificas para cada plaza segun su estatus"""
    # Condiciones de visibilidad
    es_vacante = plaza["estatus"] == "VACANTE"
    es_ocupada = plaza["estatus"] == "OCUPADA"
    es_suspendida = plaza["estatus"] == "SUSPENDIDA"
    es_cancelada = plaza["estatus"] == "CANCELADA"

    return tabla_action_buttons([
        # Ver detalle
        tabla_action_button(
            icon="eye",
            tooltip="Ver detalle",
            on_click=lambda: PlazasState.abrir_modal_detalle(plaza),
        ),
        # Editar
        tabla_action_button(
            icon="pencil",
            tooltip="Editar",
            on_click=lambda: PlazasState.abrir_modal_editar(plaza),
            color_scheme="blue",
            visible=~es_cancelada,
        ),
        # Asignar empleado (solo si esta vacante)
        tabla_action_button(
            icon="user-plus",
            tooltip="Asignar empleado",
            on_click=lambda: PlazasState.abrir_asignar_empleado(plaza),
            color_scheme="green",
            visible=es_vacante,
        ),
        # Liberar plaza (solo si esta ocupada)
        tabla_action_button(
            icon="user-minus",
            tooltip="Liberar plaza",
            on_click=lambda: PlazasState.liberar_plaza(plaza["id"]),
            color_scheme="orange",
            visible=es_ocupada,
        ),
        # Suspender (si esta vacante u ocupada)
        tabla_action_button(
            icon="pause",
            tooltip="Suspender",
            on_click=lambda: PlazasState.suspender_plaza(plaza["id"]),
            color_scheme="amber",
            visible=es_vacante | es_ocupada,
        ),
        # Reactivar (solo si esta suspendida)
        tabla_action_button(
            icon="play",
            tooltip="Reactivar",
            on_click=lambda: PlazasState.reactivar_plaza(plaza["id"]),
            color_scheme="green",
            visible=es_suspendida,
        ),
        # Cancelar (si no esta cancelada)
        tabla_action_button(
            icon="x",
            tooltip="Cancelar",
            on_click=lambda: PlazasState.abrir_confirmar_cancelar(plaza),
            color_scheme="red",
            visible=~es_cancelada,
        ),
    ])


def fila_plaza(plaza: dict) -> rx.Component:
    """Fila de la tabla para una plaza"""
    return rx.table.row(
        # Numero de plaza
        rx.table.cell(
            rx.text(
                "#", plaza["numero_plaza"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_BOLD,
            ),
        ),
        # Codigo
        rx.table.cell(
            rx.cond(
                plaza["codigo"],
                rx.text(plaza["codigo"], font_size=Typography.SIZE_SM),
                rx.text("-", font_size=Typography.SIZE_SM),
            ),
        ),
        # Fecha inicio
        rx.table.cell(
            rx.text(plaza["fecha_inicio_fmt"], font_size=Typography.SIZE_SM),
        ),
        # Salario
        rx.table.cell(
            rx.text(plaza["salario_fmt"], font_size=Typography.SIZE_SM),
        ),
        # Empleado
        rx.table.cell(
            rx.cond(
                plaza["empleado_nombre"],
                rx.text(plaza["empleado_nombre"], font_size=Typography.SIZE_SM),
                rx.text("-", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
            ),
        ),
        # Estatus
        rx.table.cell(
            status_badge_reactive(plaza["estatus"], show_icon=True),
        ),
        # Acciones
        rx.table.cell(
            acciones_plaza(plaza),
        ),
    )


ENCABEZADOS_PLAZAS = [
    {"nombre": "#", "ancho": "60px"},
    {"nombre": "Código", "ancho": "100px"},
    {"nombre": "Fecha Inicio", "ancho": "100px"},
    {"nombre": "Salario", "ancho": "120px"},
    {"nombre": "Empleado", "ancho": "150px"},
    {"nombre": "Estatus", "ancho": "120px"},
    {"nombre": "Acciones", "ancho": "140px"},
]


def tabla_plazas() -> rx.Component:
    """Vista de tabla de plazas"""
    return rx.cond(
        PlazasState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_PLAZAS, filas=5),
        rx.cond(
            PlazasState.total_plazas > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_PLAZAS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            PlazasState.plazas_filtradas,
                            fila_plaza,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                # Contador
                rx.text(
                    "Mostrando ", PlazasState.total_plazas, " plaza(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=PlazasState.abrir_modal_crear),
        ),
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_plaza(plaza: dict) -> rx.Component:
    """Card individual para una plaza"""
    return rx.card(
        rx.vstack(
            # Header con numero y estatus
            rx.hstack(
                rx.hstack(
                    rx.text(
                        "Plaza #", plaza["numero_plaza"],
                        font_size=Typography.SIZE_LG,
                        font_weight=Typography.WEIGHT_BOLD,
                    ),
                    rx.cond(
                        plaza["codigo"],
                        rx.badge(plaza["codigo"], variant="outline", size="1"),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                status_badge_reactive(plaza["estatus"], show_icon=True),
                width="100%",
                align="center",
            ),

            rx.divider(),

            # Datos
            rx.vstack(
                rx.hstack(
                    rx.icon("calendar", size=14, color=Colors.TEXT_MUTED),
                    rx.text("Inicio:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    rx.text(plaza["fecha_inicio_fmt"], font_size=Typography.SIZE_SM),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.icon("dollar-sign", size=14, color=Colors.TEXT_MUTED),
                    rx.text("Salario:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    rx.text(
                        plaza["salario_fmt"],
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_MEDIUM,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    plaza["empleado_nombre"],
                    rx.hstack(
                        rx.icon("user", size=14, color=Colors.TEXT_MUTED),
                        rx.text("Empleado:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                        rx.text(plaza["empleado_nombre"], font_size=Typography.SIZE_SM),
                        spacing="2",
                        align="center",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align_items="start",
                width="100%",
            ),

            # Acciones
            rx.hstack(
                acciones_plaza(plaza),
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


def grid_plazas() -> rx.Component:
    """Vista de cards de plazas"""
    return rx.cond(
        PlazasState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            PlazasState.total_plazas > 0,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        PlazasState.plazas_filtradas,
                        card_plaza,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(300px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", PlazasState.total_plazas, " plaza(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=PlazasState.abrir_modal_crear),
        ),
    )


# =============================================================================
# RESUMEN DE PLAZAS
# =============================================================================

def resumen_plazas() -> rx.Component:
    """Cards de resumen con contadores"""
    return rx.hstack(
        # Total
        rx.card(
            rx.hstack(
                rx.center(
                    rx.icon("users", size=20, color=Colors.PRIMARY),
                    width="40px",
                    height="40px",
                    background=Colors.PRIMARY_LIGHT,
                    border_radius=Radius.MD,
                ),
                rx.vstack(
                    rx.text("Total", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY),
                    rx.text(
                        PlazasState.total_plazas,
                        font_size=Typography.SIZE_XL,
                        font_weight=Typography.WEIGHT_BOLD,
                    ),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
                align="center",
            ),
            size="1",
        ),
        # Vacantes
        rx.card(
            rx.hstack(
                rx.center(
                    rx.icon("user-plus", size=20, color=Colors.INFO),
                    width="40px",
                    height="40px",
                    background=Colors.INFO_LIGHT,
                    border_radius=Radius.MD,
                ),
                rx.vstack(
                    rx.text("Vacantes", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY),
                    rx.text(
                        PlazasState.plazas_vacantes,
                        font_size=Typography.SIZE_XL,
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.INFO,
                    ),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
                align="center",
            ),
            size="1",
        ),
        # Ocupadas
        rx.card(
            rx.hstack(
                rx.center(
                    rx.icon("user-check", size=20, color=Colors.SUCCESS),
                    width="40px",
                    height="40px",
                    background=Colors.SUCCESS_LIGHT,
                    border_radius=Radius.MD,
                ),
                rx.vstack(
                    rx.text("Ocupadas", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY),
                    rx.text(
                        PlazasState.plazas_ocupadas,
                        font_size=Typography.SIZE_XL,
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.SUCCESS,
                    ),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
                align="center",
            ),
            size="1",
        ),
        # Suspendidas
        rx.card(
            rx.hstack(
                rx.center(
                    rx.icon("user-x", size=20, color=Colors.WARNING),
                    width="40px",
                    height="40px",
                    background=Colors.WARNING_LIGHT,
                    border_radius=Radius.MD,
                ),
                rx.vstack(
                    rx.text("Suspendidas", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY),
                    rx.text(
                        PlazasState.plazas_suspendidas,
                        font_size=Typography.SIZE_XL,
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.WARNING,
                    ),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
                align="center",
            ),
            size="1",
        ),
        spacing="3",
        wrap="wrap",
        width="100%",
    )


# =============================================================================
# FILTROS ADICIONALES
# =============================================================================

def filtro_estatus() -> rx.Component:
    """Selector de filtro por estatus"""
    return rx.select.root(
        rx.select.trigger(placeholder="Estatus", width="140px"),
        rx.select.content(
            rx.foreach(
                PlazasState.opciones_estatus,
                lambda opt: rx.select.item(opt["label"], value=opt["value"]),
            ),
        ),
        value=PlazasState.filtro_estatus,
        on_change=PlazasState.set_filtro_estatus,
    )


# =============================================================================
# TABLA INICIAL DE RESUMEN
# =============================================================================

def fila_resumen(item: dict) -> rx.Component:
    """Fila de la tabla de resumen inicial"""
    return rx.table.row(
        # Empresa
        rx.table.cell(
            rx.text(
                item["empresa_nombre"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
        ),
        # Contrato
        rx.table.cell(
            rx.text(item["contrato_codigo"], font_size=Typography.SIZE_SM),
        ),
        # Categoria
        rx.table.cell(
            rx.hstack(
                rx.badge(item["categoria_clave"], variant="outline", size="1"),
                rx.text(item["categoria_nombre"], font_size=Typography.SIZE_SM),
                spacing="2",
                align="center",
            ),
        ),
        # Total plazas
        rx.table.cell(
            rx.text(
                item["total_plazas"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            align="center",
        ),
        # Vacantes
        rx.table.cell(
            rx.badge(
                item["plazas_vacantes"],
                color_scheme="blue",
                variant="soft",
            ),
            align="center",
        ),
        # Ocupadas
        rx.table.cell(
            rx.badge(
                item["plazas_ocupadas"],
                color_scheme="green",
                variant="soft",
            ),
            align="center",
        ),
        # Acciones
        rx.table.cell(
            tabla_action_button(
                icon="arrow-right",
                tooltip="Ver plazas",
                on_click=lambda: PlazasState.seleccionar_categoria_resumen(item),
                color_scheme="blue",
            ),
        ),
        cursor="pointer",
        _hover={"background": Colors.SURFACE_HOVER},
        on_click=lambda: PlazasState.seleccionar_categoria_resumen(item),
    )


ENCABEZADOS_RESUMEN = [
    {"nombre": "Empresa", "ancho": "200px"},
    {"nombre": "Contrato", "ancho": "120px"},
    {"nombre": "Categoría", "ancho": "200px"},
    {"nombre": "Plazas", "ancho": "80px"},
    {"nombre": "Vacantes", "ancho": "80px"},
    {"nombre": "Ocupadas", "ancho": "80px"},
    {"nombre": "", "ancho": "60px"},
]


def tabla_resumen_inicial() -> rx.Component:
    """Tabla de resumen de categorías con plazas"""
    return rx.cond(
        PlazasState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_RESUMEN, filas=5),
        rx.vstack(
            # Tabla de resumen (si hay datos)
            rx.cond(
                PlazasState.tiene_resumen,
                rx.vstack(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.foreach(
                                    ENCABEZADOS_RESUMEN,
                                    lambda col: rx.table.column_header_cell(
                                        col["nombre"],
                                        width=col["ancho"],
                                    ),
                                ),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                PlazasState.resumen_categorias,
                                fila_resumen,
                            ),
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    rx.text(
                        PlazasState.resumen_categorias.length(), " categoria(s) con plazas",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_MUTED,
                    ),
                    width="100%",
                    spacing="3",
                ),
            ),

            # Selector siempre visible para crear nuevas plazas
            selector_contrato_categoria(),

            width="100%",
            spacing="4",
        ),
    )


# =============================================================================
# SELECTOR DE CONTRATO Y CATEGORÍA
# =============================================================================

def selector_contrato_categoria() -> rx.Component:
    """Selector de contrato y categoría cuando no hay contexto de URL"""
    return rx.card(
        rx.vstack(
            # Icono y título
            rx.hstack(
                rx.center(
                    rx.icon("folder-open", size=24, color=Colors.PRIMARY),
                    width="48px",
                    height="48px",
                    background=Colors.PRIMARY_LIGHT,
                    border_radius=Radius.MD,
                ),
                rx.vstack(
                    rx.text(
                        "Seleccionar Contrato y Categoria",
                        font_size=Typography.SIZE_XL,
                        font_weight=Typography.WEIGHT_BOLD,
                    ),
                    rx.text(
                        "Seleccione un contrato con personal para gestionar sus plazas",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="1",
                    align_items="start",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),

            rx.divider(),

            # Selectores
            rx.hstack(
                # Selector de contrato
                rx.vstack(
                    rx.text(
                        "Contrato",
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_MEDIUM,
                    ),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Seleccionar contrato...",
                            width="300px",
                        ),
                        rx.select.content(
                            rx.cond(
                                PlazasState.cargando_contratos,
                                rx.select.item("Cargando...", value="loading", disabled=True),
                                rx.foreach(
                                    PlazasState.opciones_contratos,
                                    lambda opt: rx.select.item(
                                        opt["label"],
                                        value=opt["value"],
                                    ),
                                ),
                            ),
                        ),
                        value=PlazasState.contrato_seleccionado_id,
                        on_change=PlazasState.set_contrato_seleccionado_id,
                    ),
                    spacing="1",
                    align_items="start",
                ),

                # Selector de categoria (solo si hay contrato seleccionado)
                rx.cond(
                    PlazasState.contrato_seleccionado_id != "",
                    rx.vstack(
                        rx.text(
                            "Categoria",
                            font_size=Typography.SIZE_SM,
                            font_weight=Typography.WEIGHT_MEDIUM,
                        ),
                        rx.select.root(
                            rx.select.trigger(
                                placeholder="Seleccionar categoria...",
                                width="300px",
                            ),
                            rx.select.content(
                                rx.cond(
                                    PlazasState.cargando_categorias,
                                    rx.select.item("Cargando...", value="loading", disabled=True),
                                    rx.cond(
                                        PlazasState.categorias_contrato.length() > 0,
                                        rx.foreach(
                                            PlazasState.opciones_categorias,
                                            lambda opt: rx.select.item(
                                                opt["label"],
                                                value=opt["value"],
                                            ),
                                        ),
                                        rx.select.item(
                                            "Sin categorias asignadas",
                                            value="empty",
                                            disabled=True,
                                        ),
                                    ),
                                ),
                            ),
                            value=PlazasState.categoria_seleccionada_id,
                            on_change=PlazasState.set_categoria_seleccionada_id,
                        ),
                        spacing="1",
                        align_items="start",
                    ),
                    rx.fragment(),
                ),

                spacing="4",
                wrap="wrap",
            ),

            # Mensaje de ayuda
            rx.cond(
                PlazasState.contratos_disponibles.length() == 0,
                rx.callout(
                    "No hay contratos con personal disponibles. "
                    "Primero debe crear un contrato con 'tiene_personal' activado.",
                    icon="info",
                    color="blue",
                    size="1",
                ),
                rx.cond(
                    (PlazasState.contrato_seleccionado_id != "") & (PlazasState.categorias_contrato.length() == 0) & (~PlazasState.cargando_categorias),
                    rx.callout(
                        "Este contrato no tiene categorías asignadas. "
                        "Debe asignar categorías de puesto al contrato primero.",
                        icon="triangle-alert",
                        color="amber",
                        size="1",
                    ),
                ),
            ),

            spacing="4",
            width="100%",
            padding="4",
        ),
        width="100%",
    )


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

def plazas_page() -> rx.Component:
    """Página de Plazas usando el nuevo layout"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Plazas",
                subtitulo=rx.cond(
                    PlazasState.mostrar_vista_inicial,
                    "Asignación de Plazas a los Contratos",
                    "",  # Sin subtitulo en vista detalle (usamos breadcrumb)
                ),
                icono="briefcase",
                accion_principal=rx.fragment(),  # Sin botones de acción
            ),
            toolbar=rx.cond(
                PlazasState.tiene_contexto,
                page_toolbar(
                    search_value=PlazasState.filtro_busqueda,
                    search_placeholder="Buscar por código o número...",
                    on_search_change=PlazasState.set_filtro_busqueda,
                    on_search_clear=lambda: PlazasState.set_filtro_busqueda(""),
                    filters=filtro_estatus(),
                    show_view_toggle=True,
                    current_view=PlazasState.view_mode,
                    on_view_table=PlazasState.set_view_table,
                    on_view_cards=PlazasState.set_view_cards,
                ),
                rx.fragment(),  # No mostrar toolbar sin contexto
            ),
            content=rx.vstack(
                # Vista inicial: tabla de resumen
                rx.cond(
                    PlazasState.mostrar_vista_inicial,
                    tabla_resumen_inicial(),
                ),

                # Contenido de plazas (con contexto)
                rx.cond(
                    PlazasState.tiene_contexto,
                    rx.vstack(
                        # Breadcrumb de navegación
                        breadcrumb_dynamic(PlazasState.breadcrumb_items),

                        # Resumen
                       # resumen_plazas(),

                        # Contenido según vista
                        rx.cond(
                            PlazasState.is_table_view,
                            tabla_plazas(),
                            grid_plazas(),
                        ),

                        spacing="4",
                        width="100%",
                    ),
                ),

                # Modales
                modal_plaza(),
                modal_detalle_plaza(),
                modal_confirmar_cancelar(),
                modal_crear_lote(),
                modal_asignar_empleado(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=PlazasState.on_mount_plazas,
    )
