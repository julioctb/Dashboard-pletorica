"""
Componentes UI para la pagina de asistencias del portal.
"""
import reflex as rx

from core.core.enums import TipoIncidencia
from core.presentation.components.ui import (
    boton_cancelar,
    boton_guardar,
    compact_date_input,
    empty_state_card,
    form_date,
    input_busqueda,
    metric_card,
    segmented_tab_trigger,
    segmented_tabs,
    table_shell,
)
from core.presentation.components.ui.modals import modal_formulario
from core.presentation.components.ui import form_input, form_select, form_textarea
from core.presentation.theme import Colors, Radius, Spacing, Typography

from .state import AsistenciasState

EMPTY_STATE_MAX_WIDTH = "320px"
TOOLBAR_SEARCH_FLEX = "1 1 280px"
TOOLBAR_SEARCH_MIN_WIDTH = "240px"
TOOLBAR_DATE_WIDTH = "150px"
STATUS_DOT_SIZE = "8px"
INCIDENCIA_DETAIL_MIN_HEIGHT = "120px"
INCIDENCIA_MODAL_WIDTH = "min(560px, 96vw)"
HORARIO_DESCRIPTION_MIN_HEIGHT = "90px"
HORARIO_DAY_LABEL_MIN_WIDTH = "150px"
HORARIO_MODAL_WIDTH = "min(760px, 96vw)"
SUPERVISION_NOTES_MIN_HEIGHT = "100px"
SUPERVISION_MODAL_WIDTH = "min(620px, 96vw)"
ASISTENCIAS_COLUMN_WIDTH_EMPLEADO = "260px"
ASISTENCIAS_COLUMN_WIDTH_SEDE = "220px"
ASISTENCIAS_COLUMN_WIDTH_RESULTADO = "140px"
ASISTENCIAS_COLUMN_WIDTH_DETALLE = "220px"
ASISTENCIAS_COLUMN_WIDTH_ACCIONES = "190px"
HORARIOS_COLUMN_WIDTH_NOMBRE = "220px"
HORARIOS_COLUMN_WIDTH_HORA = "100px"
HORARIOS_COLUMN_WIDTH_ESTADO = "100px"
HORARIOS_COLUMN_WIDTH_ACCION = "110px"
ASIGNACIONES_COLUMN_WIDTH_SUPERVISOR = "240px"
ASIGNACIONES_COLUMN_WIDTH_SEDE = "220px"
ASIGNACIONES_COLUMN_WIDTH_EMPLEADOS = "110px"
ASIGNACIONES_COLUMN_WIDTH_ESTADO = "110px"
ASIGNACIONES_COLUMN_WIDTH_ACCION = "110px"


def _field_label(texto: str) -> rx.Component:
    return rx.text(
        texto,
        font_size=Typography.SIZE_SM,
        font_weight=Typography.WEIGHT_MEDIUM,
        color=Colors.TEXT_PRIMARY,
    )


def _field_micro_label(texto: str) -> rx.Component:
    return rx.text(
        texto,
        font_size=Typography.SIZE_SM,
        color=Colors.TEXT_SECONDARY,
    )


def _muted_dash() -> rx.Component:
    return rx.text(
        "—",
        font_size=Typography.SIZE_SM,
        color=Colors.TEXT_MUTED,
    )


def _action_button(
    texto: str,
    *,
    on_click=None,
    variant: str = "outline",
    color_scheme: str = "gray",
    disabled=False,
) -> rx.Component:
    return rx.button(
        texto,
        variant=variant,
        color_scheme=color_scheme,
        size="1",
        on_click=on_click,
        disabled=disabled,
        white_space="nowrap",
    )


def _count_badge(valor, etiqueta: str, color_scheme: str) -> rx.Component:
    return rx.badge(
        rx.hstack(
            rx.text(valor),
            rx.text(etiqueta),
            spacing="1",
            align="center",
        ),
        color_scheme=color_scheme,
        variant="soft",
        size="1",
    )


def _section_header(
    titulo: str,
    subtitulo: str,
    badges: list[rx.Component],
    action: rx.Component | None = None,
) -> rx.Component:
    return rx.flex(
        rx.vstack(
            rx.hstack(
                rx.text(
                    titulo,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                ),
                *badges,
                spacing="2",
                wrap="wrap",
                align="center",
            ),
            rx.text(
                subtitulo,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            spacing="1",
            align="start",
            min_width="0",
        ),
        action if action is not None else rx.fragment(),
        width="100%",
        justify="between",
        align="center",
        wrap="wrap",
        gap=Spacing.SM,
    )


def _minimal_empty_state(title: str, description: str, icon: str) -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=28, color=Colors.TEXT_MUTED),
            rx.text(
                title,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_SECONDARY,
                text_align="center",
            ),
            rx.text(
                description,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
                text_align="center",
            ),
            spacing="2",
            align="center",
            max_width=EMPTY_STATE_MAX_WIDTH,
        ),
        width="100%",
        padding=Spacing.LG,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.LG,
    )


def _row_text_color(activo, *, secondary: bool = False):
    return rx.cond(
        activo,
        Colors.TEXT_SECONDARY if secondary else Colors.TEXT_PRIMARY,
        Colors.TEXT_MUTED,
    )


def selector_panel() -> rx.Component:
    return rx.cond(
        AsistenciasState.mostrar_selector_panel,
        segmented_tabs(
            rx.cond(
                AsistenciasState.puede_ver_operacion,
                segmented_tab_trigger("Operación", "operacion"),
                rx.fragment(),
            ),
            rx.cond(
                AsistenciasState.puede_ver_configuracion,
                segmented_tab_trigger("Configuración", "configuracion"),
                rx.fragment(),
            ),
            value=AsistenciasState.panel_activo,
            on_change=AsistenciasState.cambiar_panel_activo,
        ),
        rx.fragment(),
    )


def _contrato_option_label(contrato: dict) -> rx.Component:
    return rx.cond(
        contrato.get("descripcion", "") != "",
        contrato["codigo"].to(str) + " · " + contrato["descripcion"].to(str),
        contrato["codigo"].to(str),
    )


def _badge_resultado(resultado: str) -> rx.Component:
    return rx.match(
        resultado,
        ("ASISTENCIA", rx.badge("Asistencia", color_scheme="green", variant="soft", size="1")),
        ("PENDIENTE", rx.badge("Pendiente", color_scheme="amber", variant="soft", size="1")),
        ("SIN_NOVEDAD", rx.badge("Pendiente", color_scheme="amber", variant="soft", size="1")),
        ("RETARDO", rx.badge("Retardo", color_scheme="amber", variant="soft", size="1")),
        ("FALTA", rx.badge("Falta", color_scheme="red", variant="soft", size="1")),
        ("FALTA_JUSTIFICADA", rx.badge("Falta just.", color_scheme="red", variant="soft", size="1")),
        ("HORA_EXTRA", rx.badge("Hora extra", color_scheme="amber", variant="soft", size="1")),
        ("SALIDA_ANTICIPADA", rx.badge("Salida ant.", color_scheme="amber", variant="soft", size="1")),
        ("PERMISO_CON_GOCE", rx.badge("Permiso c/goce", color_scheme="blue", variant="soft", size="1")),
        ("PERMISO_SIN_GOCE", rx.badge("Permiso s/goce", color_scheme="blue", variant="soft", size="1")),
        ("INCAPACIDAD_ENFERMEDAD", rx.badge("Incapacidad", color_scheme="blue", variant="soft", size="1")),
        ("INCAPACIDAD_RIESGO_TRABAJO", rx.badge("Incapacidad", color_scheme="blue", variant="soft", size="1")),
        ("INCAPACIDAD_MATERNIDAD", rx.badge("Incapacidad", color_scheme="blue", variant="soft", size="1")),
        ("VACACIONES", rx.badge("Vacaciones", color_scheme="blue", variant="soft", size="1")),
        ("DIA_FESTIVO", rx.badge("Dia festivo", color_scheme="blue", variant="soft", size="1")),
        ("COMISION", rx.badge("Comision", color_scheme="blue", variant="soft", size="1")),
        ("CERRADA", rx.badge("Cerrada", color_scheme="gray", variant="outline", size="1")),
        ("OTRO", rx.badge("Otro", color_scheme="gray", variant="soft", size="1")),
        rx.badge("Pendiente", color_scheme="amber", variant="soft", size="1"),
    )


def _badge_activo(activo, *, activo_label: str = "Activo", inactivo_label: str = "Inactivo") -> rx.Component:
    return rx.cond(
        activo,
        rx.badge(activo_label, color_scheme="green", variant="soft", size="1"),
        rx.badge(inactivo_label, color_scheme="gray", variant="outline", size="1"),
    )


def barra_contrato() -> rx.Component:
    return rx.flex(
        rx.text(
            "Contrato",
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing=Typography.LETTER_SPACING_WIDE,
            flex_shrink="0",
        ),
        rx.box(
            rx.select.root(
                rx.select.trigger(
                    placeholder="Seleccionar contrato...",
                    width="100%",
                ),
                rx.select.content(
                    rx.foreach(
                        AsistenciasState.contratos_disponibles,
                        lambda contrato: rx.select.item(
                            _contrato_option_label(contrato),
                            value=contrato["id"].to(str),
                        ),
                    ),
                ),
                value=rx.cond(
                    AsistenciasState.contrato_seleccionado_id > 0,
                    AsistenciasState.contrato_seleccionado_id.to(str),
                    "",
                ),
                on_change=AsistenciasState.cambiar_contrato,
            ),
            flex="1",
            min_width="0",
        ),
        width="100%",
        align="center",
        gap=Spacing.SM,
        padding_x=Spacing.MD,
        padding_y=Spacing.SM,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.LG,
    )


def toolbar_asistencias() -> rx.Component:
    return rx.vstack(
        rx.flex(
            rx.box(
                input_busqueda(
                    value=AsistenciasState.filtro_busqueda,
                    on_change=AsistenciasState.set_filtro_busqueda,
                    on_clear=lambda: AsistenciasState.set_filtro_busqueda(""),
                    placeholder=AsistenciasState.placeholder_busqueda,
                    width="100%",
                    toolbar_style=True,
                ),
                flex=TOOLBAR_SEARCH_FLEX,
                min_width=TOOLBAR_SEARCH_MIN_WIDTH,
            ),
            selector_panel(),
            rx.cond(
                AsistenciasState.panel_es_operacion,
                compact_date_input(
                    value=AsistenciasState.fecha_operacion,
                    on_change=AsistenciasState.cambiar_fecha_operacion,
                    width=TOOLBAR_DATE_WIDTH,
                    size="2",
                    flex_shrink="0",
                ),
                rx.fragment(),
            ),
            width="100%",
            align="center",
            justify="between",
            wrap="wrap",
            gap=Spacing.SM,
        ),
        barra_contrato(),
        width="100%",
        spacing="3",
        margin_bottom=Spacing.BASE,
    )


def _accion_empleado(empleado: dict) -> rx.Component:
    accion_bloqueada = _action_button(
        "Abra jornada para registrar",
        variant="outline",
        color_scheme="gray",
        disabled=True,
    )
    accion = rx.match(
        empleado.get("resultado_dia", "PENDIENTE"),
        (
            "PENDIENTE",
            _action_button(
                "Registrar",
                variant="outline",
                color_scheme="blue",
                on_click=AsistenciasState.abrir_modal_incidencia(empleado),
            ),
        ),
        (
            "SIN_NOVEDAD",
            _action_button(
                "Registrar",
                variant="outline",
                color_scheme="blue",
                on_click=AsistenciasState.abrir_modal_incidencia(empleado),
            ),
        ),
        ("CERRADA", _muted_dash()),
        _action_button(
            "Editar",
            variant="ghost",
            color_scheme="gray",
            on_click=AsistenciasState.abrir_modal_incidencia(empleado),
        ),
    )
    return rx.cond(
        AsistenciasState.puede_editar_incidencias,
        accion,
        rx.cond(
            AsistenciasState.panel_es_operacion
            & AsistenciasState.puede_operar_jornada
            & ~AsistenciasState.tiene_jornada_abierta
            & ~AsistenciasState.puede_precargar_rrhh,
            accion_bloqueada,
            _muted_dash(),
        ),
    )


def _detalle_empleado(empleado: dict) -> rx.Component:
    return rx.cond(
        empleado.get("resultado_dia", "") == "RETARDO",
        rx.text(
            str(empleado.get("minutos_retardo", 0)) + " min",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.cond(
            empleado.get("resultado_dia", "") == "HORA_EXTRA",
            rx.text(
                str(empleado.get("horas_extra", 0)) + " h",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.cond(
                empleado.get("motivo", ""),
                rx.text(
                    empleado.get("motivo", ""),
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                _muted_dash(),
            ),
        ),
    )


def barra_jornada() -> rx.Component:
    return rx.flex(
        rx.hstack(
            rx.box(
                width=STATUS_DOT_SIZE,
                height=STATUS_DOT_SIZE,
                border_radius=Radius.FULL,
                background=rx.cond(
                    AsistenciasState.tiene_jornada_abierta,
                    Colors.SUCCESS,
                    Colors.WARNING,
                ),
                flex_shrink="0",
            ),
            rx.text(
                AsistenciasState.texto_estado_jornada,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
            spacing="2",
            align="center",
        ),
        rx.cond(
            AsistenciasState.puede_abrir_jornada,
            rx.button(
                "Abrir jornada",
                on_click=AsistenciasState.abrir_jornada,
                color_scheme="blue",
                size="2",
            ),
            rx.cond(
                AsistenciasState.puede_cerrar_jornada,
                rx.button(
                    "Cerrar jornada",
                    on_click=AsistenciasState.cerrar_jornada,
                    color_scheme="blue",
                    size="2",
                ),
                rx.fragment(),
            ),
        ),
        width="100%",
        align="center",
        justify="between",
        wrap="wrap",
        gap=Spacing.SM,
        padding=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.LG,
    )


def metricas_jornada() -> rx.Component:
    return rx.grid(
        metric_card(
            titulo="Empleados esperados",
            valor=AsistenciasState.total_empleados_jornada,
            icono="users",
            color_scheme="blue",
            descripcion="Plazas ocupadas del contrato",
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
        ),
        metric_card(
            titulo="Incidencias",
            valor=AsistenciasState.total_incidencias,
            icono="triangle-alert",
            color_scheme="amber",
            descripcion="Novedades por excepcion",
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
        ),
        metric_card(
            titulo="Sedes cubiertas",
            valor=AsistenciasState.total_sedes_supervision,
            icono="map-pinned",
            color_scheme="blue",
            descripcion="Territorio activo",
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
        ),
        columns=rx.breakpoints(initial="1", md="3"),
        spacing="3",
        width="100%",
    )


def _barra_jornada_skeleton() -> rx.Component:
    return rx.flex(
        rx.hstack(
            rx.skeleton(width=STATUS_DOT_SIZE, height=STATUS_DOT_SIZE, border_radius=Radius.FULL),
            rx.skeleton(width="180px", height="14px"),
            spacing="2",
            align="center",
        ),
        rx.skeleton(width="120px", height="32px", border_radius=Radius.MD),
        width="100%",
        align="center",
        justify="between",
        wrap="wrap",
        gap=Spacing.SM,
        padding=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.LG,
    )


def _metric_card_skeleton() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.skeleton(width="120px", height="12px"),
            rx.skeleton(width="60px", height="24px"),
            rx.skeleton(width="140px", height="12px"),
            spacing="2",
            width="100%",
        ),
        padding=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.LG,
        width="100%",
    )


def _metricas_jornada_skeleton() -> rx.Component:
    return rx.grid(
        *[_metric_card_skeleton() for _ in range(3)],
        columns=rx.breakpoints(initial="1", md="3"),
        spacing="3",
        width="100%",
    )


def resumen_jornada() -> rx.Component:
    return rx.cond(
        AsistenciasState.loading,
        rx.vstack(
            _barra_jornada_skeleton(),
            _metricas_jornada_skeleton(),
            spacing="4",
            width="100%",
        ),
        rx.vstack(
            barra_jornada(),
            metricas_jornada(),
            spacing="4",
            width="100%",
        ),
    )


def fila_empleado(empleado: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                empleado.get("nombre_completo", "-"),
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(
                    empleado.get("sede_nombre", "Sin sede"),
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text(
                    empleado.get("categoria_nombre", ""),
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="0",
                align="start",
            ),
        ),
        rx.table.cell(_badge_resultado(empleado.get("resultado_dia", "PENDIENTE"))),
        rx.table.cell(_detalle_empleado(empleado)),
        rx.table.cell(_accion_empleado(empleado)),
    )


ENCABEZADOS_ASISTENCIAS = [
    {"nombre": "Empleado", "ancho": ASISTENCIAS_COLUMN_WIDTH_EMPLEADO},
    {"nombre": "Sede / Categoría", "ancho": ASISTENCIAS_COLUMN_WIDTH_SEDE},
    {"nombre": "Resultado", "ancho": ASISTENCIAS_COLUMN_WIDTH_RESULTADO},
    {"nombre": "Detalle", "ancho": ASISTENCIAS_COLUMN_WIDTH_DETALLE},
    {"nombre": "Acciones", "ancho": ASISTENCIAS_COLUMN_WIDTH_ACCIONES},
]


def tabla_asistencias() -> rx.Component:
    return table_shell(
        loading=AsistenciasState.loading,
        headers=ENCABEZADOS_ASISTENCIAS,
        rows=AsistenciasState.empleados_filtrados,
        row_renderer=fila_empleado,
        has_rows=AsistenciasState.empleados_filtrados.length() > 0,
        empty_component=empty_state_card(
            title="No hay personal esperado",
            description="Selecciona un contrato con plazas ocupadas o valida las sedes asignadas al supervisor.",
            icon="clipboard-list",
        ),
        total_caption=(
            "Mostrando " + AsistenciasState.empleados_filtrados.length().to(str) + " empleado(s)"
        ),
        loading_rows=6,
    )


def _table_time_text(valor) -> rx.Component:
    return rx.text(
        rx.cond(valor != "", valor, "—"),
        font_size=Typography.SIZE_SM,
        color=Colors.TEXT_PRIMARY,
        font_family="monospace",
    )


def fila_horario(horario: dict) -> rx.Component:
    es_activo = horario.get("es_horario_activo", False)
    return rx.table.row(
        rx.table.cell(
            rx.text(
                horario.get("nombre", "Horario"),
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=_row_text_color(es_activo),
            ),
        ),
        rx.table.cell(_table_time_text(horario.get("hora_entrada_ref", ""))),
        rx.table.cell(_table_time_text(horario.get("hora_salida_ref", ""))),
        rx.table.cell(
            rx.text(
                horario.get("dias_resumen", "Sin dias configurados"),
                font_size=Typography.SIZE_SM,
                color=_row_text_color(es_activo, secondary=True),
            ),
        ),
        rx.table.cell(_badge_activo(es_activo)),
        rx.table.cell(
            _action_button(
                rx.cond(es_activo, "Editar", "Activar"),
                variant="outline",
                color_scheme="gray",
                on_click=AsistenciasState.abrir_modal_horario_editar(horario),
            ),
        ),
    )


ENCABEZADOS_HORARIOS = [
    {"nombre": "Nombre", "ancho": HORARIOS_COLUMN_WIDTH_NOMBRE},
    {"nombre": "Entrada", "ancho": HORARIOS_COLUMN_WIDTH_HORA},
    {"nombre": "Salida", "ancho": HORARIOS_COLUMN_WIDTH_HORA},
    {"nombre": "Dias", "ancho": "auto"},
    {"nombre": "Estado", "ancho": HORARIOS_COLUMN_WIDTH_ESTADO},
    {"nombre": "Accion", "ancho": HORARIOS_COLUMN_WIDTH_ACCION},
]


def tabla_horarios() -> rx.Component:
    return table_shell(
        loading=AsistenciasState.loading,
        headers=ENCABEZADOS_HORARIOS,
        rows=AsistenciasState.horarios_filtrados,
        row_renderer=fila_horario,
        has_rows=AsistenciasState.horarios_filtrados.length() > 0,
        empty_component=_minimal_empty_state(
            "Sin horarios registrados",
            "Crea el primer horario activo para este contrato.",
            "clock-3",
        ),
        loading_rows=4,
    )


def fila_asignacion(asignacion: dict) -> rx.Component:
    activa = asignacion.get("activo", False)
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(
                    asignacion.get("supervisor_nombre", "Supervisor"),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=_row_text_color(activa),
                ),
                rx.text(
                    asignacion.get("supervisor_clave", ""),
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="0",
                align="start",
            ),
        ),
        rx.table.cell(
            rx.text(
                asignacion.get("sede_nombre", "Sin sede"),
                font_size=Typography.SIZE_SM,
                color=_row_text_color(activa, secondary=True),
            ),
        ),
        rx.table.cell(
            rx.text(
                asignacion.get("empleados_asignados", 0).to(str),
                font_size=Typography.SIZE_SM,
                color=_row_text_color(activa),
                font_family="monospace",
            ),
        ),
        rx.table.cell(_badge_activo(activa, activo_label="Activa", inactivo_label="Inactiva")),
        rx.table.cell(
            rx.cond(
                AsistenciasState.configuracion_solo_lectura,
                _muted_dash(),
                _action_button(
                    rx.cond(activa, "Editar", "Activar"),
                    variant="outline",
                    color_scheme="gray",
                    on_click=AsistenciasState.abrir_modal_supervision_editar(asignacion),
                ),
            ),
        ),
    )


ENCABEZADOS_ASIGNACIONES = [
    {"nombre": "Supervisor", "ancho": ASIGNACIONES_COLUMN_WIDTH_SUPERVISOR},
    {"nombre": "Sede", "ancho": ASIGNACIONES_COLUMN_WIDTH_SEDE},
    {"nombre": "Empleados", "ancho": ASIGNACIONES_COLUMN_WIDTH_EMPLEADOS},
    {"nombre": "Estado", "ancho": ASIGNACIONES_COLUMN_WIDTH_ESTADO},
    {"nombre": "Accion", "ancho": ASIGNACIONES_COLUMN_WIDTH_ACCION},
]


def tabla_asignaciones() -> rx.Component:
    return table_shell(
        loading=AsistenciasState.loading,
        headers=ENCABEZADOS_ASIGNACIONES,
        rows=AsistenciasState.asignaciones_configuracion_visibles,
        row_renderer=fila_asignacion,
        has_rows=AsistenciasState.asignaciones_configuracion_visibles.length() > 0,
        empty_component=_minimal_empty_state(
            "Sin asignaciones registradas",
            "Asigna supervisores a sedes para habilitar la captura supervisada.",
            "route",
        ),
        loading_rows=4,
    )


def seccion_horarios() -> rx.Component:
    return rx.vstack(
        _section_header(
            "Horarios del contrato",
            "Versiones de horario y cual se usa en la jornada actual.",
            badges=[
                _count_badge(AsistenciasState.total_horarios_configuracion, "registrados", "blue"),
                _count_badge(AsistenciasState.total_horarios_activos, "activos", "green"),
            ],
            action=rx.button(
                rx.icon("plus", size=14),
                "Nuevo horario",
                on_click=AsistenciasState.abrir_modal_horario_crear,
                color_scheme="blue",
                size="2",
            ),
        ),
        tabla_horarios(),
        spacing="3",
        width="100%",
        margin_bottom=Spacing.LG,
    )


def seccion_asignaciones() -> rx.Component:
    return rx.vstack(
        _section_header(
            "Asignaciones supervisor - sede",
            "Territorio de cada supervisor para la captura diaria.",
            badges=[
                _count_badge(AsistenciasState.total_asignaciones_visibles, "registradas", "blue"),
                _count_badge(AsistenciasState.total_asignaciones_visibles_activas, "activas", "green"),
            ],
            action=rx.cond(
                AsistenciasState.configuracion_solo_lectura,
                rx.fragment(),
                rx.button(
                    rx.icon("plus", size=14),
                    "Nueva asignacion",
                    on_click=AsistenciasState.abrir_modal_supervision_crear,
                    color_scheme="blue",
                    size="2",
                ),
            ),
        ),
        tabla_asignaciones(),
        spacing="3",
        width="100%",
    )


def configuracion_asistencias() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AsistenciasState.mostrar_horarios_configuracion,
            seccion_horarios(),
            rx.fragment(),
        ),
        rx.cond(
            AsistenciasState.mostrar_asignaciones_configuracion,
            seccion_asignaciones(),
            rx.fragment(),
        ),
        spacing="4",
        width="100%",
    )


def modal_incidencia() -> rx.Component:
    contenido = rx.vstack(
        form_select(
            label="Tipo de incidencia",
            required=True,
            placeholder="Tipo de incidencia",
            value=AsistenciasState.form_tipo_incidencia,
            on_change=AsistenciasState.set_form_tipo_incidencia,
            options=[
                {"value": item.value, "label": item.value.replace("_", " ")}
                for item in TipoIncidencia
            ],
            label_variant="portal",
            style_variant="portal",
        ),
        rx.grid(
            form_input(
                label="Minutos de retardo",
                placeholder="Minutos retardo",
                type="number",
                value=AsistenciasState.form_minutos_retardo,
                on_change=AsistenciasState.set_form_minutos_retardo,
                label_variant="portal",
                style_variant="portal",
            ),
            form_input(
                label="Horas extra",
                placeholder="Horas extra",
                type="number",
                value=AsistenciasState.form_horas_extra,
                on_change=AsistenciasState.set_form_horas_extra,
                label_variant="portal",
                style_variant="portal",
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        form_textarea(
            label="Motivo o detalle operativo",
            placeholder="Motivo o detalle operativo",
            value=AsistenciasState.form_motivo,
            on_change=AsistenciasState.set_form_motivo,
            label_variant="portal",
            style_variant="portal",
            rows="4",
        ),
        spacing="4",
        width="100%",
    )

    boton_limpiar = rx.cond(
        AsistenciasState.empleado_seleccionado.get("incidencia_id", 0) != 0,
        rx.button(
            "Limpiar",
            variant="ghost",
            color_scheme="red",
            size="2",
            on_click=AsistenciasState.limpiar_incidencia_actual,
            disabled=AsistenciasState.saving,
        ),
        rx.fragment(),
    )

    return modal_formulario(
        open=AsistenciasState.modal_incidencia_abierto,
        titulo=AsistenciasState.titulo_modal_incidencia,
        descripcion=rx.cond(
            AsistenciasState.empleado_seleccionado,
            "Empleado: " + AsistenciasState.empleado_seleccionado["nombre_completo"].to(str),
            "Captura la novedad del dia",
        ),
        icono="clipboard-list",
        color_icono="teal",
        color_guardar="teal",
        contenido=contenido,
        on_guardar=AsistenciasState.guardar_incidencia,
        on_cancelar=AsistenciasState.cerrar_modal_incidencia,
        loading=AsistenciasState.saving,
        texto_guardar=AsistenciasState.texto_guardar_incidencia,
        texto_guardando=rx.cond(
            AsistenciasState.modo_precarga_rrhh,
            "Guardando precarga...",
            "Guardando incidencia...",
        ),
        max_width=INCIDENCIA_MODAL_WIDTH,
        extra_footer_left=boton_limpiar,
    )


def _horario_dia_row(dia: dict) -> rx.Component:
    """Fila compacta de un día laborable en el modal de horario."""
    return rx.box(
        rx.flex(
            rx.flex(
                rx.switch(
                    checked=dia["habilitado"],
                    on_change=lambda value: AsistenciasState.set_form_horario_dia_habilitado(
                        dia["clave"],
                        value,
                    ),
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    size="1",
                ),
                rx.text(
                    dia["label"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=rx.cond(dia["habilitado"], Colors.TEXT_PRIMARY, Colors.TEXT_SECONDARY),
                ),
                align="center",
                spacing="2",
            ),
            rx.text(
                rx.cond(
                    dia["habilitado"],
                    dia["entrada"].to(str) + " – " + dia["salida"].to(str),
                    "Descanso",
                ),
                font_size=Typography.SIZE_XS,
                color=rx.cond(dia["habilitado"], Colors.TEXT_SECONDARY, Colors.TEXT_MUTED),
            ),
            justify="between",
            align="center",
            width="100%",
            padding=f"{Spacing.SM} {Spacing.MD}",
            background=Colors.SECONDARY_LIGHT,
        ),
        rx.cond(
            dia["habilitado"],
            rx.grid(
                rx.vstack(
                    rx.text(
                        "Entrada",
                        font_size=Typography.SIZE_XS,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.input(
                        type="time",
                        value=dia["entrada"],
                        on_change=lambda value: AsistenciasState.set_form_horario_dia_hora(
                            dia["clave"],
                            "entrada",
                            value,
                        ),
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text(
                        "Salida",
                        font_size=Typography.SIZE_XS,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.input(
                        type="time",
                        value=dia["salida"],
                        on_change=lambda value: AsistenciasState.set_form_horario_dia_hora(
                            dia["clave"],
                            "salida",
                            value,
                        ),
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                columns="2",
                spacing="3",
                padding=f"{Spacing.SM} {Spacing.MD}",
                width="100%",
            ),
            rx.fragment(),
        ),
        width="100%",
        border_bottom=f"1px solid {Colors.BORDER}",
        opacity=rx.cond(dia["habilitado"], "1", "0.55"),
    )


def modal_horario() -> rx.Component:
    return modal_formulario(
        open=AsistenciasState.modal_horario_abierto,
        titulo=AsistenciasState.titulo_modal_horario,
        descripcion="Configura el horario contractual base usado por la jornada y la consolidación.",
        contenido=rx.vstack(
            # Nombre
            rx.vstack(
                rx.text(
                    "Nombre",
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.input(
                    value=AsistenciasState.form_horario_nombre,
                    on_change=AsistenciasState.set_form_horario_nombre,
                    placeholder="Ej. Horario Jardineria 2025",
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            # Descripción
            rx.vstack(
                rx.text(
                    "Descripción",
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text_area(
                    value=AsistenciasState.form_horario_descripcion,
                    on_change=AsistenciasState.set_form_horario_descripcion,
                    placeholder="Descripción operativa del horario",
                    min_height=HORARIO_DESCRIPTION_MIN_HEIGHT,
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            # Tolerancias en grid 2 columnas
            rx.grid(
                rx.vstack(
                    rx.text(
                        "Tolerancia entrada ",
                        rx.text.span(
                            "(min)",
                            font_weight=Typography.WEIGHT_REGULAR,
                            color=Colors.TEXT_MUTED,
                        ),
                        font_size=Typography.SIZE_XS,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.input(
                        type="number",
                        min="0",
                        max="60",
                        value=AsistenciasState.form_horario_tolerancia_entrada,
                        on_change=AsistenciasState.set_form_horario_tolerancia_entrada,
                        placeholder="0",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text(
                        "Tolerancia salida ",
                        rx.text.span(
                            "(min)",
                            font_weight=Typography.WEIGHT_REGULAR,
                            color=Colors.TEXT_MUTED,
                        ),
                        font_size=Typography.SIZE_XS,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.input(
                        type="number",
                        min="0",
                        max="60",
                        value=AsistenciasState.form_horario_tolerancia_salida,
                        on_change=AsistenciasState.set_form_horario_tolerancia_salida,
                        placeholder="0",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
            # Toggle horario activo
            rx.flex(
                rx.switch(
                    checked=AsistenciasState.form_horario_activo,
                    on_change=AsistenciasState.set_form_horario_activo,
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                ),
                rx.text("Marcar como horario activo del contrato", size="2"),
                spacing="2",
                align="center",
                width="100%",
            ),
            # Divider + título sección días
            rx.divider(border_color=Colors.BORDER),
            rx.text(
                "DÍAS LABORABLES",
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_MUTED,
                letter_spacing="0.04em",
            ),
            # Contenedor único con filas por día
            rx.box(
                rx.foreach(
                    AsistenciasState.form_horario_dias_ui,
                    _horario_dia_row,
                ),
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.LG,
                overflow="hidden",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        on_guardar=AsistenciasState.guardar_horario,
        on_cancelar=AsistenciasState.cerrar_modal_horario,
        loading=AsistenciasState.saving,
        texto_guardar=AsistenciasState.texto_guardar_horario,
        texto_guardando="Guardando horario...",
        max_width="520px",
        icono="clock",
        color_icono="teal",
        scroll_body=True,
        max_body_height="65vh",
        color_guardar="teal",
    )


def modal_supervision() -> rx.Component:
    return modal_formulario(
        open=AsistenciasState.modal_supervision_abierto,
        titulo=AsistenciasState.titulo_modal_supervision,
        descripcion="Relaciona supervisores operativos con las sedes que deben cubrir.",
        icono="shield-check",
        color_icono="teal",
        on_guardar=AsistenciasState.guardar_supervision,
        on_cancelar=AsistenciasState.cerrar_modal_supervision,
        loading=AsistenciasState.saving,
        texto_guardar=AsistenciasState.texto_guardar_supervision,
        texto_guardando="Guardando asignacion...",
        color_guardar="teal",
        max_width=SUPERVISION_MODAL_WIDTH,
        disable_cancelar_guardando=True,
        contenido=rx.vstack(
            rx.vstack(
                _field_label("Supervisor"),
                rx.select.root(
                    rx.select.trigger(placeholder="Supervisor", width="100%"),
                    rx.select.content(
                        rx.foreach(
                            AsistenciasState.supervisores_disponibles,
                            lambda supervisor: rx.select.item(
                                supervisor["nombre"].to(str) + " · " + supervisor["clave"].to(str),
                                value=supervisor["id"].to(str),
                            ),
                        )
                    ),
                    value=AsistenciasState.form_supervision_supervisor_id,
                    on_change=AsistenciasState.set_form_supervision_supervisor_id,
                    size="2",
                ),
                spacing="1",
                width="100%",
            ),
            rx.vstack(
                _field_label("Sede"),
                rx.select.root(
                    rx.select.trigger(placeholder="Sede", width="100%"),
                    rx.select.content(
                        rx.foreach(
                            AsistenciasState.sedes_catalogo,
                            lambda sede: rx.select.item(
                                sede["nombre"].to(str) + " · " + sede["codigo"].to(str),
                                value=sede["id"].to(str),
                            ),
                        )
                    ),
                    value=AsistenciasState.form_supervision_sede_id,
                    on_change=AsistenciasState.set_form_supervision_sede_id,
                    size="2",
                ),
                spacing="1",
                width="100%",
            ),
            rx.hstack(
                form_date(
                    label="Fecha inicio",
                    value=AsistenciasState.form_supervision_fecha_inicio,
                    on_change=AsistenciasState.set_form_supervision_fecha_inicio,
                ),
                form_date(
                    label="Fecha fin",
                    value=AsistenciasState.form_supervision_fecha_fin,
                    on_change=AsistenciasState.set_form_supervision_fecha_fin,
                ),
                spacing="3",
                width="100%",
            ),
            rx.hstack(
                rx.switch(
                    checked=AsistenciasState.form_supervision_activo,
                    on_change=AsistenciasState.set_form_supervision_activo,
                ),
                rx.text("Mantener asignacion activa", size="2"),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.vstack(
                _field_label("Notas"),
                rx.text_area(
                    value=AsistenciasState.form_supervision_notas,
                    on_change=AsistenciasState.set_form_supervision_notas,
                    placeholder="Notas de cobertura, excepciones o contexto",
                    min_height=SUPERVISION_NOTES_MIN_HEIGHT,
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
    )
