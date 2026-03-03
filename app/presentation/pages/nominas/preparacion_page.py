"""
Página de preparación de nómina (vista RRHH).

Ruta: /nominas/preparacion
Acceso: es_rrhh | es_contabilidad | es_admin_empresa

RRHH captura descuentos manuales (INFONAVIT, FONACOT, préstamos, pensión)
y envía el período a Contabilidad cuando está listo.
"""
import reflex as rx

from app.presentation.pages.nominas.nomina_rrhh_state import NominaRRHHState
from app.presentation.pages.nominas.nomina_modals import (
    modal_descuentos_empleado,
    dialog_iniciar_preparacion,
    dialog_enviar_contabilidad,
)
from app.presentation.components.ui import (
    tabla_vacia,
    table_shell,
    table_cell_text_sm,
    skeleton_tabla,
    breadcrumb_dynamic,
)
from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Colors, Spacing, Typography, Radius


# =============================================================================
# BADGE ESTATUS (reutilizable, mismo que periodos_page)
# =============================================================================

def _badge_estatus_periodo(estatus: rx.Var) -> rx.Component:
    return rx.match(
        estatus,
        ('BORRADOR', rx.badge('Borrador', color_scheme='gray', size='1')),
        ('EN_PREPARACION_RRHH', rx.badge('Preparando', color_scheme='blue', size='1')),
        ('ENVIADO_A_CONTABILIDAD', rx.badge('Enviado', color_scheme='orange', size='1')),
        ('EN_PROCESO_CONTABILIDAD', rx.badge('En proceso', color_scheme='purple', size='1')),
        ('CALCULADO', rx.badge('Calculado', color_scheme='green', size='1')),
        ('CERRADO', rx.badge('Cerrado', color_scheme='gray', size='1', variant='surface')),
        rx.badge(estatus, size='1'),
    )


# =============================================================================
# RESUMEN DEL PERÍODO
# =============================================================================

def _resumen_periodo() -> rx.Component:
    """Card con datos del período activo."""
    return rx.box(
        rx.hstack(
            # Fechas
            rx.vstack(
                rx.text("Período", size="1", color=Colors.TEXT_MUTED),
                rx.text(
                    NominaRRHHState.periodo_actual['fecha_inicio'].to(str) + "  —  "
                    + NominaRRHHState.periodo_actual['fecha_fin'].to(str),
                    size="3",
                    weight="medium",
                ),
                spacing="0",
                align="start",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Periodicidad
            rx.vstack(
                rx.text("Periodicidad", size="1", color=Colors.TEXT_MUTED),
                rx.text(NominaRRHHState.periodo_actual['periodicidad'], size="3"),
                spacing="0",
                align="start",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Empleados
            rx.vstack(
                rx.text("Empleados", size="1", color=Colors.TEXT_MUTED),
                rx.text(
                    NominaRRHHState.empleados_periodo.length().to(str),
                    size="3",
                    weight="medium",
                ),
                spacing="0",
                align="start",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Estatus
            rx.vstack(
                rx.text("Estatus", size="1", color=Colors.TEXT_MUTED),
                _badge_estatus_periodo(NominaRRHHState.periodo_estatus),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            # Botones de acción del período
            _botones_accion_periodo(),
            spacing="6",
            align="center",
            wrap="wrap",
            width="100%",
        ),
        padding=Spacing.LG,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        width="100%",
    )


def _botones_accion_periodo() -> rx.Component:
    """Botones contextuales según el estatus del período."""
    return rx.hstack(
        # Si es BORRADOR → Iniciar preparación
        rx.cond(
            NominaRRHHState.periodo_es_borrador & NominaRRHHState.es_rrhh,
            rx.button(
                rx.icon("circle-play", size=15),
                "Iniciar preparación",
                on_click=NominaRRHHState.abrir_dialog_iniciar,
                color_scheme="blue",
                variant="soft",
                size="2",
            ),
            rx.fragment(),
        ),
        # Si está EN_PREPARACION → Enviar a Contabilidad
        rx.cond(
            NominaRRHHState.puede_enviar_a_contabilidad & NominaRRHHState.es_rrhh,
            rx.button(
                rx.icon("send", size=15),
                "Enviar a Contabilidad",
                on_click=NominaRRHHState.abrir_dialog_envio,
                color_scheme="orange",
                size="2",
            ),
            rx.fragment(),
        ),
        # Si está enviado → info banner
        rx.cond(
            NominaRRHHState.periodo_enviado,
            rx.badge(
                rx.icon("circle-check", size=13),
                "Enviado — Solo lectura",
                color_scheme="orange",
                size="2",
                variant="soft",
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
    )


# =============================================================================
# TABLA DE EMPLEADOS
# =============================================================================

ENCABEZADOS = [
    {"nombre": "Clave", "ancho": "80px"},
    {"nombre": "Nombre", "ancho": "200px"},
    {"nombre": "Días trab.", "ancho": "80px"},
    {"nombre": "Faltas", "ancho": "70px"},
    {"nombre": "H.E. dobles", "ancho": "90px"},
    {"nombre": "H.E. triples", "ancho": "90px"},
    {"nombre": "Domingos", "ancho": "80px"},
    {"nombre": "Descuentos", "ancho": "90px"},
    {"nombre": "Acciones", "ancho": "80px"},
]


def _fila_empleado(empleado: dict) -> rx.Component:
    """Fila de la tabla de empleados en preparación."""
    return rx.table.row(
        table_cell_text_sm(empleado['clave_empleado'], tone="muted"),
        rx.table.cell(
            rx.text(
                empleado['nombre_empleado'],
                size="2",
                weight="medium",
                max_width="200px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
        ),
        rx.table.cell(
            rx.badge(
                empleado['dias_trabajados'].to(str),
                color_scheme='green',
                variant='soft',
                size='1',
            ),
        ),
        rx.table.cell(
            rx.cond(
                empleado['dias_faltas'].to(int) > 0,
                rx.badge(
                    empleado['dias_faltas'].to(str),
                    color_scheme='red',
                    variant='soft',
                    size='1',
                ),
                rx.text("—", size="2", color=Colors.TEXT_MUTED),
            ),
        ),
        table_cell_text_sm(empleado['horas_extra_dobles'].to(str), tone="muted"),
        table_cell_text_sm(empleado['horas_extra_triples'].to(str), tone="muted"),
        table_cell_text_sm(empleado['domingos_trabajados'].to(str), tone="muted"),
        # Descuentos badge (placeholder — no count fácil sin computed var)
        rx.table.cell(
            rx.badge("RRHH", color_scheme="orange", variant="soft", size="1"),
        ),
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("circle-minus", size=15),
                    size="2",
                    variant="soft",
                    color_scheme="orange",
                    on_click=NominaRRHHState.abrir_modal_descuento(empleado),
                ),
                content="Descuentos manuales",
            ),
        ),
    )


def _tabla_empleados() -> rx.Component:
    return table_shell(
        loading=NominaRRHHState.loading,
        headers=ENCABEZADOS,
        rows=NominaRRHHState.empleados_periodo,
        row_renderer=_fila_empleado,
        has_rows=NominaRRHHState.tiene_empleados,
        empty_component=tabla_vacia(
            mensaje="No hay empleados en este período",
        ),
        total_caption=(
            NominaRRHHState.empleados_periodo.length().to(str) + " empleado(s)"
        ),
        loading_rows=5,
    )


# =============================================================================
# CALLOUT READONLY
# =============================================================================

def _callout_readonly() -> rx.Component:
    """Aviso cuando el período ya fue enviado y está en solo lectura."""
    return rx.cond(
        NominaRRHHState.periodo_enviado,
        rx.callout(
            "Este período fue enviado a Contabilidad. "
            "Los datos son de solo lectura para RRHH.",
            icon="lock",
            color_scheme="orange",
            size="1",
            width="100%",
        ),
        rx.fragment(),
    )


# =============================================================================
# PÁGINA
# =============================================================================

def preparacion_nomina_page() -> rx.Component:
    """Página de preparación de nómina."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo=rx.hstack(
                    rx.link(
                        "Nóminas",
                        href=NominaRRHHState.nomina_base_path,
                        size="4",
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.icon("chevron-right", size=14, color=Colors.TEXT_MUTED),
                    rx.text(
                        NominaRRHHState.nombre_periodo_actual,
                        size="4",
                        weight="bold",
                    ),
                    spacing="2",
                    align="center",
                ),
                subtitulo="Captura descuentos y envía a Contabilidad",
                icono="clipboard-list",
            ),
            content=rx.vstack(
                _resumen_periodo(),
                _callout_readonly(),
                _tabla_empleados(),
                # Modales y dialogs
                modal_descuentos_empleado(),
                dialog_iniciar_preparacion(),
                dialog_enviar_contabilidad(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=NominaRRHHState.on_mount_preparacion,
    )
