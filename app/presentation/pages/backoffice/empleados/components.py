"""
Componentes UI para la pagina de Empleados.

Tabla, cards, badges, acciones y filtros.
"""
import reflex as rx

from app.presentation.pages.backoffice.empleados.state import (
    EmpleadosState,
    EmpleadoListadoUI,
    DescuentoActivoUI,
)
from app.core.ui_helpers import FILTRO_TODOS
from app.presentation.components.reusable import employee_table
from app.presentation.components.ui import (
    acciones_filtros,
    filtros_inline,
    tabla_vacia,
    tabla_action_button,
    tabla_action_buttons,
    badge_onboarding,
    identifier_badge,
    table_text_sm,
    select_items_from_options,
)
from app.presentation.theme import Colors, Spacing, Shadows, Typography


# =============================================================================
# BADGES
# =============================================================================

def estatus_badge(estatus: str) -> rx.Component:
    """Badge para estatus de empleado"""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("ACTIVO", color_scheme="green", size="1")),
        ("INACTIVO", rx.badge("INACTIVO", color_scheme="red", size="1")),
        ("SUSPENDIDO", rx.badge("SUSPENDIDO", color_scheme="amber", size="1")),
        rx.badge(estatus, color_scheme="gray", size="1"),
    )


def restriccion_badge(is_restricted) -> rx.Component:
    """Badge que indica si el empleado esta restringido."""
    return rx.cond(
        is_restricted,
        rx.badge(
            rx.hstack(
                rx.icon("ban", size=12),
                rx.text("RESTRINGIDO"),
                spacing="1",
            ),
            color_scheme="red",
            variant="solid",
            size="1",
        ),
        rx.fragment(),
    )


def _badge_descuento(descuento: DescuentoActivoUI) -> rx.Component:
    """Badge compacto para descuentos activos del empleado."""
    return rx.tooltip(
        rx.badge(
            descuento["badge"],
            color_scheme=descuento["color_scheme"],
            variant="soft",
            size="1",
        ),
        content=descuento["tooltip"],
    )


def descuentos_badges(descuentos: list[DescuentoActivoUI]) -> rx.Component:
    """Badges agrupados de descuentos activos hoy."""
    return rx.cond(
        descuentos.length() > 0,
        rx.hstack(
            rx.foreach(descuentos, _badge_descuento),
            spacing="1",
            wrap="wrap",
            width="100%",
        ),
        rx.text("-", size="2", color=Colors.TEXT_MUTED),
    )


def _identificacion_badge(status: str) -> rx.Component:
    """Badge semáforo para RFC/NSS/CP según estado precomputado."""
    return rx.match(
        status,
        (
            "completo",
            rx.tooltip(
                rx.badge(
                    rx.hstack(rx.icon("check", size=12), rx.text("Completo", size="1")),
                    color_scheme=Colors.SUCCESS_SCHEME,
                    variant="soft",
                    size="1",
                ),
                content="RFC, NSS y CP registrados",
            ),
        ),
        (
            "falta_rfc",
            rx.tooltip(
                rx.badge(
                    rx.hstack(rx.icon("circle_alert", size=12), rx.text("Falta RFC", size="1")),
                    color_scheme=Colors.WARNING_SCHEME,
                    variant="soft",
                    size="1",
                ),
                content="Falta RFC",
            ),
        ),
        (
            "falta_nss",
            rx.tooltip(
                rx.badge(
                    rx.hstack(rx.icon("circle_alert", size=12), rx.text("Falta NSS", size="1")),
                    color_scheme=Colors.WARNING_SCHEME,
                    variant="soft",
                    size="1",
                ),
                content="Falta NSS",
            ),
        ),
        (
            "falta_cp",
            rx.tooltip(
                rx.badge(
                    rx.hstack(rx.icon("circle_alert", size=12), rx.text("Falta CP", size="1")),
                    color_scheme=Colors.WARNING_SCHEME,
                    variant="soft",
                    size="1",
                ),
                content="Falta código postal",
            ),
        ),
        (
            "falta_rfc_nss",
            rx.tooltip(
                rx.badge(
                    rx.hstack(rx.icon("triangle_alert", size=12), rx.text("Falta RFC y NSS", size="1")),
                    color_scheme=Colors.ERROR_SCHEME,
                    variant="soft",
                    size="1",
                ),
                content="Faltan RFC y NSS",
            ),
        ),
        (
            "falta_rfc_cp",
            rx.tooltip(
                rx.badge(
                    rx.hstack(rx.icon("triangle_alert", size=12), rx.text("Falta RFC y CP", size="1")),
                    color_scheme=Colors.ERROR_SCHEME,
                    variant="soft",
                    size="1",
                ),
                content="Faltan RFC y código postal",
            ),
        ),
        (
            "falta_nss_cp",
            rx.tooltip(
                rx.badge(
                    rx.hstack(rx.icon("triangle_alert", size=12), rx.text("Falta NSS y CP", size="1")),
                    color_scheme=Colors.ERROR_SCHEME,
                    variant="soft",
                    size="1",
                ),
                content="Faltan NSS y código postal",
            ),
        ),
        (
            "faltan_tres",
            rx.tooltip(
                rx.badge(
                    rx.hstack(rx.icon("triangle_alert", size=12), rx.text("Faltan datos", size="1")),
                    color_scheme=Colors.ERROR_SCHEME,
                    variant="soft",
                    size="1",
                ),
                content="Faltan RFC, NSS y código postal",
            ),
        ),
        rx.badge(
            rx.text("—", size="1"),
            color_scheme=Colors.NEUTRAL_SCHEME,
            variant="soft",
            size="1",
        ),
    )


def identificacion_cell(status: str) -> rx.Component:
    """Celda de identificación RFC/NSS/CP para tabla."""
    return rx.center(_identificacion_badge(status), width="100%")


# =============================================================================
# ACCIONES
# =============================================================================

def acciones_empleado(empleado: EmpleadoListadoUI) -> rx.Component:
    """Acciones para cada empleado usando tabla_action_button."""
    # Condiciones de visibilidad
    es_activo = empleado["estatus"] == "ACTIVO"
    es_suspendido = empleado["estatus"] == "SUSPENDIDO"
    es_inactivo = empleado["estatus"] == "INACTIVO"
    es_restringido = empleado["is_restricted"]

    # Condiciones con permisos
    puede_editar = (es_activo | es_suspendido) & ~es_restringido & EmpleadosState.puede_operar_empleados
    puede_suspender = es_activo & ~es_restringido & EmpleadosState.puede_operar_empleados
    puede_reactivar = (es_suspendido | es_inactivo) & ~es_restringido & EmpleadosState.puede_operar_empleados
    puede_restringir = EmpleadosState.es_admin & ~es_restringido
    puede_liberar = EmpleadosState.es_admin & es_restringido

    return tabla_action_buttons([
        # Ver detalle
        tabla_action_button(
            icon="eye",
            tooltip="Ver detalle",
            on_click=lambda: EmpleadosState.abrir_modal_detalle(empleado),
        ),
        # Editar
        tabla_action_button(
            icon="pencil",
            tooltip="Editar",
            on_click=lambda: EmpleadosState.abrir_modal_editar(empleado),
            color_scheme="blue",
            visible=puede_editar,
        ),
        # Suspender
        tabla_action_button(
            icon="pause",
            tooltip="Suspender",
            on_click=lambda: EmpleadosState.suspender_desde_lista(empleado["id"]),
            color_scheme="amber",
            visible=puede_suspender,
        ),
        # Reactivar
        tabla_action_button(
            icon="play",
            tooltip="Reactivar",
            on_click=lambda: EmpleadosState.reactivar_desde_lista(empleado["id"]),
            color_scheme="green",
            visible=puede_reactivar,
        ),
        # Restringir
        tabla_action_button(
            icon="ban",
            tooltip="Restringir",
            on_click=lambda: EmpleadosState.abrir_modal_restriccion_desde_lista(empleado),
            color_scheme="red",
            visible=puede_restringir,
        ),
        # Liberar restriccion
        tabla_action_button(
            icon="circle-check",
            tooltip="Liberar restriccion",
            on_click=lambda: EmpleadosState.abrir_modal_liberacion_desde_lista(empleado),
            color_scheme="green",
            visible=puede_liberar,
        ),
    ])


# =============================================================================
# TABLA
# =============================================================================

ENCABEZADOS_EMPLEADOS = [
    {"nombre": "Clave", "ancho": "80px"},
    {"nombre": "Nombre", "ancho": "180px"},
    {"nombre": "CURP", "ancho": "150px"},
    {"nombre": "Empresa", "ancho": "120px"},
    {"nombre": "Identificación", "ancho": "110px"},
    {"nombre": "Estatus", "ancho": "90px"},
    {"nombre": "Descuentos", "ancho": "110px"},
    {"nombre": "Onboarding", "ancho": "110px"},
    {"nombre": "Acciones", "ancho": "100px"},
]


def fila_empleado(empleado: EmpleadoListadoUI) -> rx.Component:
    """Fila de la tabla para un empleado"""
    _abrir = lambda: EmpleadosState.abrir_modal_detalle(empleado)
    _cell_style = {"cursor": "pointer"}
    return rx.table.row(
        # Clave
        rx.table.cell(
            rx.text(
                empleado["clave"],
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_SM,
            ),
            on_click=_abrir, style=_cell_style,
        ),
        # Nombre completo
        rx.table.cell(
            table_text_sm(empleado["nombre_completo"]),
            on_click=_abrir, style=_cell_style,
        ),
        # CURP
        rx.table.cell(
            table_text_sm(empleado["curp"], tone="muted"),
            on_click=_abrir, style=_cell_style,
        ),
        # Identificación (RFC/NSS)
        rx.table.cell(
            identificacion_cell(empleado["identificacion_status"]),
            on_click=_abrir, style=_cell_style,
        ),
        # Empresa
        rx.table.cell(
            table_text_sm(empleado["empresa_nombre"]),
            on_click=_abrir, style=_cell_style,
        ),
        # Estatus
        rx.table.cell(
            rx.hstack(
                estatus_badge(empleado["estatus"]),
                restriccion_badge(empleado["is_restricted"]),
                spacing="1",
            ),
            on_click=_abrir, style=_cell_style,
        ),
        # Descuentos
        rx.table.cell(
            descuentos_badges(empleado["descuentos_activos_hoy"]),
            on_click=_abrir, style=_cell_style,
        ),
        # Onboarding
        rx.table.cell(
            rx.cond(
                empleado["estatus_onboarding"] != "",
                badge_onboarding(empleado["estatus_onboarding"]),
                rx.fragment(),
            ),
            on_click=_abrir, style=_cell_style,
        ),
        # Acciones (sin on_click para evitar bubbling)
        rx.table.cell(
            acciones_empleado(empleado),
        ),
        _hover={"background": Colors.SURFACE_HOVER},
    )


def _boton_ver_mas() -> rx.Component:
    """Boton para cargar mas empleados."""
    return rx.cond(
        EmpleadosState.hay_mas,
        rx.center(
            rx.button(
                rx.icon("chevrons-down", size=16),
                "Ver más",
                on_click=EmpleadosState.cargar_mas,
                variant="soft",
                size="2",
                loading=EmpleadosState.cargando_mas,
            ),
            width="100%",
        ),
    )


def tabla_empleados() -> rx.Component:
    """Vista de tabla de empleados"""
    return employee_table(
        loading=EmpleadosState.loading,
        headers=ENCABEZADOS_EMPLEADOS,
        rows=EmpleadosState.empleados_filtrados,
        row_renderer=fila_empleado,
        has_rows=EmpleadosState.tiene_empleados,
        empty_component=tabla_vacia(onclick=EmpleadosState.abrir_modal_crear),
        total_caption="Mostrando " + EmpleadosState.total_empleados_filtrados.to(str) + " empleado(s)",
        footer_component=_boton_ver_mas(),
        loading_rows=5,
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_empleado(empleado: EmpleadoListadoUI) -> rx.Component:
    """Card individual para un empleado"""
    _abrir = lambda: EmpleadosState.abrir_modal_detalle(empleado)
    return rx.card(
        rx.vstack(
            # Zona clickeable para abrir detalle
            rx.vstack(
                # Header con clave y estatus
                rx.hstack(
                    rx.hstack(
                        identifier_badge(empleado["clave"]),
                        spacing="2",
                    ),
                    rx.spacer(),
                    estatus_badge(empleado["estatus"]),
                    restriccion_badge(empleado["is_restricted"]),
                    width="100%",
                    align="center",
                ),

                # Nombre completo
                rx.text(
                    empleado["nombre_completo"],
                    font_weight=Typography.WEIGHT_BOLD,
                    font_size=Typography.SIZE_BASE,
                ),

                # CURP
                rx.hstack(
                    rx.icon("fingerprint", size=14, color=Colors.TEXT_MUTED),
                    rx.text(
                        empleado["curp"],
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="2",
                    align="center",
                ),

                # Identificación RFC/NSS
                _identificacion_badge(empleado["identificacion_status"]),

                # Empresa
                rx.hstack(
                    rx.icon("building-2", size=14, color=Colors.TEXT_MUTED),
                    rx.text(empleado["empresa_nombre"], font_size=Typography.SIZE_SM),
                    spacing="2",
                    align="center",
                ),

                descuentos_badges(empleado["descuentos_activos_hoy"]),

                # Email (si existe)
                rx.cond(
                    empleado["email"],
                    rx.hstack(
                        rx.icon("mail", size=14, color=Colors.TEXT_MUTED),
                        rx.text(empleado["email"], font_size=Typography.SIZE_SM),
                        spacing="2",
                        align="center",
                    ),
                ),

                # Teléfono (si existe)
                rx.cond(
                    empleado["telefono"],
                    rx.hstack(
                        rx.icon("phone", size=14, color=Colors.TEXT_MUTED),
                        rx.text(empleado["telefono"], font_size=Typography.SIZE_SM),
                        spacing="2",
                        align="center",
                    ),
                ),

                spacing="3",
                width="100%",
                cursor="pointer",
                on_click=_abrir,
            ),

            # Acciones (fuera de la zona clickeable para evitar bubbling)
            rx.hstack(
                acciones_empleado(empleado),
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


def grid_empleados() -> rx.Component:
    """Vista de cards de empleados"""
    return rx.cond(
        EmpleadosState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            EmpleadosState.tiene_empleados,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        EmpleadosState.empleados_filtrados,
                        card_empleado,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(300px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", EmpleadosState.total_empleados_filtrados, " empleado(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                _boton_ver_mas(),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=EmpleadosState.abrir_modal_crear),
        ),
    )


# =============================================================================
# FILTROS
# =============================================================================

def filtros_empleados() -> rx.Component:
    """Filtros para empleados"""
    return filtros_inline(
        # Filtro por empresa
        rx.cond(
            EmpleadosState.mostrar_filtro_empresa,
            rx.select.root(
                rx.select.trigger(placeholder="Empresa", width="180px"),
                rx.select.content(
                    rx.select.item("Todas", value=FILTRO_TODOS),
                    select_items_from_options(EmpleadosState.opciones_empresas),
                ),
                value=EmpleadosState.filtro_empresa_id,
                on_change=EmpleadosState.set_filtro_empresa_id,
                size="2",
            ),
            rx.fragment(),
        ),
        # Filtro por estatus
        rx.select.root(
            rx.select.trigger(placeholder="Estatus", width="140px"),
            rx.select.content(select_items_from_options(EmpleadosState.opciones_estatus)),
            value=EmpleadosState.filtro_estatus,
            on_change=EmpleadosState.set_filtro_estatus,
            size="2",
        ),
        acciones_filtros(
            on_apply=EmpleadosState.aplicar_filtros,
            on_clear=EmpleadosState.limpiar_filtros,
        ),
    )
