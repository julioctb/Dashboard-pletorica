"""
Página de cálculo de nómina (vista Contabilidad).

Ruta: /nominas/calculo
Acceso: es_contabilidad | es_admin_empresa

Contabilidad recibe períodos enviados por RRHH, agrega bonos de productividad,
ejecuta el cálculo fiscal completo (ISR + IMSS + subsidio) y cierra el período.
"""
import reflex as rx

from app.presentation.pages.nominas.nomina_contabilidad_state import NominaContabilidadState
from app.presentation.pages.nominas.contabilidad_modals import (
    modal_bono_empleado,
    dialog_ejecutar_calculo,
    dialog_cerrar_periodo,
    dialog_devolver_rrhh,
)
from app.presentation.components.ui import (
    tabla_vacia,
    table_shell,
    table_cell_text_sm,
    skeleton_tabla,
)
from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Colors, Spacing, Typography, Radius


# =============================================================================
# BADGE ESTATUS NOMINA EMPLEADO
# =============================================================================

def _badge_estatus_empleado(estatus: rx.Var) -> rx.Component:
    return rx.match(
        estatus,
        ('PENDIENTE',   rx.badge('Pendiente',   color_scheme='gray',  size='1')),
        ('EN_PROCESO',  rx.badge('En proceso',  color_scheme='blue',  size='1')),
        ('CALCULADO',   rx.badge('Calculado',   color_scheme='green', size='1')),
        ('APROBADO',    rx.badge('Aprobado',    color_scheme='teal',  size='1')),
        rx.badge(estatus, size='1'),
    )


# =============================================================================
# PANEL RESUMEN DEL PERÍODO
# =============================================================================

def _stat_card(label: str, value: rx.Var, color: str = Colors.TEXT_PRIMARY) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color=Colors.TEXT_MUTED),
        rx.text(value, size="4", weight="bold", color=color),
        spacing="0",
        align="start",
    )


def _botones_accion() -> rx.Component:
    """Botones contextuales según estatus del período."""
    return rx.hstack(
        # Recibir (solo si ENVIADO_A_CONTABILIDAD)
        rx.cond(
            NominaContabilidadState.periodo_es_enviado,
            rx.button(
                rx.icon("inbox", size=15),
                "Recibir período",
                on_click=NominaContabilidadState.confirmar_recibir,
                loading=NominaContabilidadState.saving,
                color_scheme="purple",
                size="2",
            ),
            rx.fragment(),
        ),
        # Devolver a RRHH (solo si EN_PROCESO o ENVIADO)
        rx.cond(
            NominaContabilidadState.puede_devolver,
            rx.tooltip(
                rx.button(
                    rx.icon("arrow-left", size=15),
                    "Devolver a RRHH",
                    on_click=NominaContabilidadState.abrir_dialog_devolver,
                    variant="soft",
                    color_scheme="orange",
                    size="2",
                ),
                content="Devuelve para correcciones de RRHH",
            ),
            rx.fragment(),
        ),
        # Ejecutar cálculo (solo si EN_PROCESO con empleados)
        rx.cond(
            NominaContabilidadState.puede_calcular,
            rx.button(
                rx.cond(
                    NominaContabilidadState.calculando,
                    rx.spinner(size="1"),
                    rx.icon("circle-play", size=15),
                ),
                rx.cond(
                    NominaContabilidadState.calculando,
                    "Calculando...",
                    "Ejecutar cálculo",
                ),
                on_click=NominaContabilidadState.abrir_dialog_ejecutar,
                color_scheme="blue",
                size="2",
                disabled=NominaContabilidadState.calculando,
            ),
            rx.fragment(),
        ),
        # Cerrar período (solo si CALCULADO)
        rx.cond(
            NominaContabilidadState.puede_cerrar,
            rx.button(
                rx.icon("lock", size=15),
                "Cerrar período",
                on_click=NominaContabilidadState.abrir_dialog_cerrar,
                color_scheme="green",
                size="2",
            ),
            rx.fragment(),
        ),
        # Badge readonly si CERRADO
        rx.cond(
            NominaContabilidadState.periodo_cerrado,
            rx.badge(
                rx.icon("lock", size=13),
                "Cerrado — Solo lectura",
                color_scheme="gray",
                size="2",
                variant="soft",
            ),
            rx.fragment(),
        ),
        # Generar layouts de dispersión (CALCULADO o CERRADO)
        rx.cond(
            NominaContabilidadState.puede_dispersar,
            rx.button(
                rx.cond(
                    NominaContabilidadState.generando_layouts,
                    rx.spinner(size="1"),
                    rx.icon("building-2", size=15),
                ),
                rx.cond(
                    NominaContabilidadState.generando_layouts,
                    "Generando...",
                    "Generar layouts",
                ),
                on_click=NominaContabilidadState.generar_layouts_dispersion,
                color_scheme="indigo",
                size="2",
                disabled=NominaContabilidadState.generando_layouts,
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
    )


def _panel_resumen() -> rx.Component:
    """Card con totales del período y botones de acción."""
    return rx.box(
        rx.hstack(
            _stat_card(
                "Empleados",
                NominaContabilidadState.total_empleados_periodo.to(str),
            ),
            rx.separator(orientation="vertical", size="2"),
            _stat_card(
                "Total percepciones",
                "$" + NominaContabilidadState.total_percepciones_periodo.to(str),
                Colors.SUCCESS,
            ),
            rx.separator(orientation="vertical", size="2"),
            _stat_card(
                "Total deducciones",
                "$" + NominaContabilidadState.total_deducciones_periodo.to(str),
                Colors.ERROR,
            ),
            rx.separator(orientation="vertical", size="2"),
            _stat_card(
                "Neto a dispersar",
                "$" + NominaContabilidadState.total_neto_periodo.to(str),
                Colors.PRIMARY,
            ),
            rx.spacer(),
            _botones_accion(),
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


# =============================================================================
# TABLA DE EMPLEADOS
# =============================================================================

ENCABEZADOS_CALCULO = [
    {"nombre": "Clave",        "ancho": "70px"},
    {"nombre": "Nombre",       "ancho": "200px"},
    {"nombre": "Percepciones", "ancho": "110px"},
    {"nombre": "Deducciones",  "ancho": "110px"},
    {"nombre": "Neto",         "ancho": "110px"},
    {"nombre": "Estatus",      "ancho": "100px"},
    {"nombre": "Acciones",     "ancho": "100px"},
]


def _fila_empleado_calculo(empleado: dict) -> rx.Component:
    """Fila de la tabla de cálculo por empleado."""
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
            rx.text(
                "$" + empleado['total_percepciones'].to(str),
                size="2",
                color=Colors.SUCCESS,
            ),
        ),
        rx.table.cell(
            rx.text(
                "$" + empleado['total_deducciones'].to(str),
                size="2",
                color=Colors.ERROR,
            ),
        ),
        rx.table.cell(
            rx.text(
                "$" + empleado['total_neto'].to(str),
                size="2",
                weight="bold",
                color=Colors.PRIMARY,
            ),
        ),
        rx.table.cell(
            _badge_estatus_empleado(empleado['estatus']),
        ),
        rx.table.cell(
            rx.hstack(
                # Bono (solo si EN_PROCESO)
                rx.cond(
                    NominaContabilidadState.puede_agregar_bonos,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("star", size=15),
                            size="2",
                            variant="soft",
                            color_scheme="green",
                            on_click=NominaContabilidadState.abrir_modal_bono(empleado),
                        ),
                        content="Agregar bono",
                    ),
                    rx.fragment(),
                ),
                # Detalle de movimientos
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("receipt", size=15),
                        size="2",
                        variant="soft",
                        color_scheme="blue",
                        on_click=NominaContabilidadState.ver_detalle_empleado(empleado),
                    ),
                    content="Ver desglose",
                ),
                spacing="1",
            ),
        ),
    )


def _tabla_empleados_calculo() -> rx.Component:
    return table_shell(
        loading=NominaContabilidadState.loading,
        headers=ENCABEZADOS_CALCULO,
        rows=NominaContabilidadState.empleados_periodo,
        row_renderer=_fila_empleado_calculo,
        has_rows=NominaContabilidadState.tiene_empleados,
        empty_component=tabla_vacia(
            mensaje="No hay empleados en este período",
        ),
        total_caption=(
            NominaContabilidadState.empleados_periodo.length().to(str) + " empleado(s)"
        ),
        loading_rows=5,
    )


# =============================================================================
# CALLOUT READONLY
# =============================================================================

def _callout_readonly() -> rx.Component:
    return rx.cond(
        NominaContabilidadState.periodo_cerrado,
        rx.callout(
            "Este período está cerrado. Los datos son de solo lectura.",
            icon="lock",
            color_scheme="gray",
            size="1",
            width="100%",
        ),
        rx.fragment(),
    )


# =============================================================================
# CALLOUT PENDIENTE DE RECIBIR
# =============================================================================

def _callout_pendiente_recibir() -> rx.Component:
    return rx.cond(
        NominaContabilidadState.periodo_es_enviado,
        rx.callout(
            "Este período fue enviado por RRHH y está pendiente de recibir. "
            "Haz clic en 'Recibir período' para comenzar a trabajar en él.",
            icon="inbox",
            color_scheme="purple",
            size="1",
            width="100%",
        ),
        rx.fragment(),
    )


# =============================================================================
# SECCIÓN DISPERSIÓN BANCARIA
# =============================================================================

def _fila_layout(layout: dict) -> rx.Component:
    """Fila de un layout bancario generado."""
    return rx.hstack(
        rx.badge(layout['banco'], color_scheme="indigo", size="2"),
        rx.text(layout['nombre_archivo'], size="2", color=Colors.TEXT_MUTED),
        rx.text(layout['total_empleados'].to(str) + " emp.", size="2"),
        rx.text(
            "$" + layout['total_monto'].to(str),
            size="2",
            weight="bold",
            color=Colors.SUCCESS,
        ),
        rx.spacer(),
        rx.cond(
            layout['url_descarga'] != "",
            rx.link(
                rx.icon_button(
                    rx.icon("download", size=15),
                    size="2",
                    variant="soft",
                    color_scheme="indigo",
                ),
                href=layout['url_descarga'],
                is_external=True,
            ),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("download", size=15),
                    size="2",
                    variant="soft",
                    color_scheme="gray",
                    disabled=True,
                ),
                content="Archivo no disponible",
            ),
        ),
        spacing="3",
        align="center",
        padding=Spacing.SM,
        background=Colors.BG_APP,
        border_radius=Radius.MD,
        width="100%",
    )


def _seccion_layouts() -> rx.Component:
    """Sección de dispersión bancaria (visible si CALCULADO o CERRADO)."""
    return rx.cond(
        NominaContabilidadState.puede_dispersar,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("banknote", size=16, color=Colors.PRIMARY),
                    rx.text("Dispersión bancaria", size="3", weight="bold"),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    NominaContabilidadState.tiene_layouts,
                    rx.vstack(
                        rx.foreach(
                            NominaContabilidadState.layouts_dispersion,
                            _fila_layout,
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.text(
                        "Haz clic en 'Generar layouts' para crear los archivos de pago.",
                        size="2",
                        color=Colors.TEXT_MUTED,
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            padding=Spacing.LG,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            width="100%",
        ),
        rx.fragment(),
    )


# =============================================================================
# PÁGINA
# =============================================================================

def calculo_nomina_page() -> rx.Component:
    """Página de cálculo de nómina — vista Contabilidad."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo=rx.hstack(
                    rx.link(
                        "Nóminas",
                        href=NominaContabilidadState.nomina_base_path,
                        size="4",
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.icon("chevron-right", size=14, color=Colors.TEXT_MUTED),
                    rx.text(
                        NominaContabilidadState.periodo_nombre,
                        size="4",
                        weight="bold",
                    ),
                    spacing="2",
                    align="center",
                ),
                subtitulo="Bonos, cálculo fiscal y cierre de período",
                icono="calculator",
            ),
            content=rx.vstack(
                _panel_resumen(),
                _callout_pendiente_recibir(),
                _callout_readonly(),
                _tabla_empleados_calculo(),
                _seccion_layouts(),
                # Modales y dialogs
                modal_bono_empleado(),
                dialog_ejecutar_calculo(),
                dialog_cerrar_periodo(),
                dialog_devolver_rrhh(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=NominaContabilidadState.on_mount_calculo,
    )
