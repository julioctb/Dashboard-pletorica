"""
Componentes UI para la pagina de Empleados.

Tabla, cards, badges, acciones y filtros.
"""
import reflex as rx

from app.presentation.pages.empleados.empleados_state import EmpleadosState
from app.presentation.components.reusable import employee_filters_bar, employee_table
from app.presentation.components.ui import (
    tabla_vacia,
    tabla_action_button,
    tabla_action_buttons,
    badge_onboarding,
    table_text_sm,
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


# =============================================================================
# ACCIONES
# =============================================================================

def acciones_empleado(empleado: dict) -> rx.Component:
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
    {"nombre": "Clave", "ancho": "100px"},
    {"nombre": "Nombre", "ancho": "200px"},
    {"nombre": "CURP", "ancho": "180px"},
    {"nombre": "Empresa", "ancho": "150px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Onboarding", "ancho": "130px"},
    {"nombre": "Acciones", "ancho": "120px"},
]


def fila_empleado(empleado: dict) -> rx.Component:
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
        total_caption="Mostrando " + EmpleadosState.total_empleados.to(str) + " empleado(s)",
        footer_component=_boton_ver_mas(),
        loading_rows=5,
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_empleado(empleado: dict) -> rx.Component:
    """Card individual para un empleado"""
    _abrir = lambda: EmpleadosState.abrir_modal_detalle(empleado)
    return rx.card(
        rx.vstack(
            # Zona clickeable para abrir detalle
            rx.vstack(
                # Header con clave y estatus
                rx.hstack(
                    rx.hstack(
                        rx.badge(empleado["clave"], variant="outline", size="2"),
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

                # Empresa
                rx.hstack(
                    rx.icon("building-2", size=14, color=Colors.TEXT_MUTED),
                    rx.text(empleado["empresa_nombre"], font_size=Typography.SIZE_SM),
                    spacing="2",
                    align="center",
                ),

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
                    "Mostrando ", EmpleadosState.total_empleados, " empleado(s)",
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
    return employee_filters_bar(
        # Filtro por empresa
        rx.select.root(
            rx.select.trigger(placeholder="Empresa", width="180px"),
            rx.select.content(
                rx.select.item("Todas", value="TODAS"),
                rx.foreach(
                    EmpleadosState.opciones_empresas,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=EmpleadosState.filtro_empresa_id,
            on_change=EmpleadosState.set_filtro_empresa_id,
        ),
        # Filtro por estatus
        rx.select.root(
            rx.select.trigger(placeholder="Estatus", width="140px"),
            rx.select.content(
                rx.foreach(
                    EmpleadosState.opciones_estatus,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=EmpleadosState.filtro_estatus,
            on_change=EmpleadosState.set_filtro_estatus,
        ),
        # Botón aplicar filtros
        rx.button(
            rx.icon("search", size=14),
            "Filtrar",
            on_click=EmpleadosState.aplicar_filtros,
            variant="soft",
            size="2",
        ),
        # Botón limpiar filtros
        rx.button(
            rx.icon("x", size=14),
            "Limpiar",
            on_click=EmpleadosState.limpiar_filtros,
            variant="ghost",
            size="2",
        ),
    )
