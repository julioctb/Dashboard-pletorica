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
    filtros_inline,
    identifier_badge,
    payroll_period_status_badge,
    tabla_vacia,
    table_pagination,
    table_shell,
)
from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.theme import Colors, Spacing, Typography, Radius


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
                rx.hstack(
                    rx.text(
                        NominaRRHHState.periodo_actual["fecha_inicio_fmt"],
                        size="3",
                        weight="medium",
                    ),
                    rx.text("—", size="3", weight="medium"),
                    rx.text(
                        NominaRRHHState.periodo_actual["fecha_fin_fmt"],
                        size="3",
                        weight="medium",
                    ),
                    spacing="1",
                    align="center",
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
            rx.vstack(
                rx.text("Fecha de pago", size="1", color=Colors.TEXT_MUTED),
                rx.text(
                    NominaRRHHState.periodo_actual["fecha_pago_fmt"],
                    size="3",
                    weight="medium",
                ),
                spacing="0",
                align="start",
            ),
            rx.separator(orientation="vertical", size="2"),
            rx.vstack(
                rx.text("Generada", size="1", color=Colors.TEXT_MUTED),
                rx.text(
                    NominaRRHHState.periodo_actual["fecha_creacion_fmt"],
                    size="3",
                    weight="medium",
                ),
                spacing="0",
                align="start",
            ),
            rx.separator(orientation="vertical", size="2"),
            rx.vstack(
                rx.text("Generado por", size="1", color=Colors.TEXT_MUTED),
                rx.text(
                    NominaRRHHState.periodo_actual["creado_por_nombre_fmt"],
                    size="3",
                    weight="medium",
                ),
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
                payroll_period_status_badge(NominaRRHHState.periodo_estatus),
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
            NominaRRHHState.periodo_es_borrador & NominaRRHHState.puede_abrir_preparacion,
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
            NominaRRHHState.puede_enviar_a_contabilidad & NominaRRHHState.puede_abrir_preparacion,
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
    {"nombre": "Nombre", "ancho": "200px"},
    {"nombre": "Sede", "ancho": "160px", "header_align": "center"},
    {"nombre": "Días trab.", "ancho": "90px", "header_align": "center"},
    {"nombre": "Faltas", "ancho": "80px", "header_align": "center"},
    {"nombre": "H.E. dobles", "ancho": "100px", "header_align": "center"},
    {"nombre": "H.E. triples", "ancho": "100px", "header_align": "center"},
    {"nombre": "Domingos", "ancho": "90px", "header_align": "center"},
    {"nombre": "Descuentos", "ancho": "110px", "header_align": "center"},
    {"nombre": "Acciones", "ancho": "90px", "header_align": "center"},
]


def _badge_descuento_rrhh(descuento: dict) -> rx.Component:
    """Badge con tooltip para descuentos RRHH del período."""
    return rx.tooltip(
        identifier_badge(
            descuento["badge"],
            color_scheme=descuento["color_scheme"],
            variant="soft",
            size="1",
            width="38px",
            justify_content="center",
            text_align="center",
        ),
        content=descuento["tooltip"],
    )


def _celda_descuentos_rrhh(empleado: dict) -> rx.Component:
    """Renderiza descuentos capturados/materializados en el período."""
    descuentos_typed = empleado["descuentos_rrhh"].to(list[dict])
    return _celda_centrada(
        rx.cond(
            descuentos_typed.length() > 0,
            rx.flex(
                rx.foreach(descuentos_typed, _badge_descuento_rrhh),
                gap="1",
                wrap="wrap",
                justify="center",
                width="100%",
            ),
            rx.text("—", size="2", color=Colors.TEXT_MUTED),
        ),
    )


def _celda_centrada(content: rx.Component) -> rx.Component:
    return rx.table.cell(
        rx.flex(
            content,
            justify="center",
            align="center",
            width="100%",
        ),
        text_align="center",
    )


def _texto_celda_centrada(value) -> rx.Component:
    return _celda_centrada(
        rx.text(
            value,
            size="2",
            color=Colors.TEXT_MUTED,
            width="100%",
            text_align="center",
        ),
    )


def _fila_empleado(empleado: dict) -> rx.Component:
    """Fila de la tabla de empleados en preparación."""
    return rx.table.row(
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
        _celda_centrada(
            rx.text(
                empleado["sede_nombre"],
                size="2",
                color=Colors.TEXT_MUTED,
                max_width="160px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                width="100%",
                text_align="center",
            ),
        ),
        _celda_centrada(
            rx.badge(
                empleado['dias_trabajados_ui'].to(str),
                color_scheme='green',
                variant='soft',
                size='1',
            ),
        ),
        _celda_centrada(
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
        _texto_celda_centrada(empleado['horas_extra_dobles'].to(str)),
        _texto_celda_centrada(empleado['horas_extra_triples'].to(str)),
        _texto_celda_centrada(empleado['domingos_trabajados'].to(str)),
        _celda_descuentos_rrhh(empleado),
        _celda_centrada(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("badge-dollar-sign", size=15),
                    size="2",
                    variant="soft",
                    color_scheme="orange",
                    on_click=NominaRRHHState.abrir_modal_descuento(empleado),
                ),
                content="Capturar descuentos manuales",
            ),
        ),
    )


def _tabla_empleados() -> rx.Component:
    return table_shell(
        loading=NominaRRHHState.loading,
        headers=ENCABEZADOS,
        rows=NominaRRHHState.empleados_periodo_paginados,
        row_renderer=_fila_empleado,
        has_rows=NominaRRHHState.tiene_empleados_filtrados,
        empty_component=rx.cond(
            NominaRRHHState.filtro_busqueda_empleados != "",
            tabla_vacia(mensaje="No hay empleados que coincidan con la búsqueda."),
            tabla_vacia(mensaje="No hay empleados en este período"),
        ),
        total_caption=NominaRRHHState.total_caption_empleados_preparacion,
        footer_component=table_pagination(
            current_page=NominaRRHHState.pagina_empleados_preparacion_actual,
            total_pages=NominaRRHHState.total_paginas_empleados_preparacion,
            page_numbers=NominaRRHHState.paginas_visibles_empleados_preparacion,
            on_page_change=NominaRRHHState.ir_a_pagina_empleados_preparacion,
            on_previous=NominaRRHHState.pagina_anterior_empleados_preparacion,
            on_next=NominaRRHHState.pagina_siguiente_empleados_preparacion,
            color_scheme="blue",
        ),
        loading_rows=5,
    )


def _toolbar_tabla_empleados() -> rx.Component:
    return page_toolbar(
        search_value=NominaRRHHState.filtro_busqueda_empleados,
        search_placeholder="Buscar por nombre o sede...",
        on_search_change=NominaRRHHState.set_filtro_busqueda_empleados,
        on_search_clear=lambda: NominaRRHHState.set_filtro_busqueda_empleados(""),
        filters=filtros_inline(
            rx.select.root(
                rx.select.trigger(placeholder="Sede", width="220px"),
                rx.select.content(
                    rx.foreach(
                        NominaRRHHState.opciones_sede_empleados_preparacion,
                        lambda opcion: rx.select.item(
                            opcion["label"],
                            value=opcion["value"],
                        ),
                    )
                ),
                value=NominaRRHHState.filtro_sede_empleados_preparacion,
                on_change=NominaRRHHState.set_filtro_sede_empleados_preparacion,
                size="2",
            ),
        ),
        show_view_toggle=False,
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
                _toolbar_tabla_empleados(),
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
