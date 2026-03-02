"""
Componentes UI para la pagina de asistencias del portal.
"""
import reflex as rx

from app.core.enums import TipoIncidencia
from app.presentation.components.ui import (
    boton_cancelar,
    boton_guardar,
    empty_state_card,
    metric_card,
    table_shell,
    tabla_action_button,
)
from app.presentation.theme import Colors, Typography

from .state import AsistenciasState


def selector_panel() -> rx.Component:
    return rx.cond(
        AsistenciasState.mostrar_selector_panel,
        rx.hstack(
            rx.cond(
                AsistenciasState.puede_operar_jornada,
                rx.button(
                    "Operacion",
                    variant=rx.cond(AsistenciasState.panel_es_operacion, "solid", "soft"),
                    color_scheme="blue",
                    on_click=AsistenciasState.cambiar_panel_activo("operacion"),
                    size="2",
                ),
                rx.fragment(),
            ),
            rx.cond(
                AsistenciasState.puede_precargar_rrhh,
                rx.button(
                    "Precargas RH",
                    variant=rx.cond(AsistenciasState.panel_es_rrhh, "solid", "soft"),
                    color_scheme="orange",
                    on_click=AsistenciasState.cambiar_panel_activo("rrhh"),
                    size="2",
                ),
                rx.fragment(),
            ),
            rx.cond(
                AsistenciasState.puede_configurar_catalogos,
                rx.button(
                    "Configuracion",
                    variant=rx.cond(
                        AsistenciasState.panel_es_configuracion,
                        "solid",
                        "soft",
                    ),
                    color_scheme="teal",
                    on_click=AsistenciasState.cambiar_panel_activo("configuracion"),
                    size="2",
                ),
                rx.fragment(),
            ),
            spacing="2",
            wrap="wrap",
        ),
        rx.fragment(),
    )


def callout_contexto() -> rx.Component:
    return rx.callout(
        rx.text(
            AsistenciasState.texto_contexto_panel,
            font_size=Typography.SIZE_SM,
        ),
        icon=rx.cond(
            AsistenciasState.panel_es_configuracion,
            "settings-2",
            rx.cond(
                AsistenciasState.panel_es_rrhh,
                "folder-input",
                "clipboard-check",
            ),
        ),
        color_scheme=rx.cond(
            AsistenciasState.panel_es_configuracion,
            "teal",
            rx.cond(AsistenciasState.panel_es_rrhh, "orange", "blue"),
        ),
        size="1",
        width="100%",
    )


def _badge_jornada(estatus: str) -> rx.Component:
    return rx.match(
        estatus,
        ("ABIERTA", rx.badge("Abierta", color_scheme="green", variant="soft", size="1")),
        ("CERRADA", rx.badge("Cerrada", color_scheme="orange", variant="soft", size="1")),
        ("CONSOLIDADA", rx.badge("Consolidada", color_scheme="blue", variant="solid", size="1")),
        rx.badge("Sin jornada", color_scheme="gray", variant="outline", size="1"),
    )


def _badge_resultado(resultado: str) -> rx.Component:
    return rx.match(
        resultado,
        ("ASISTENCIA", rx.badge("Asistencia", color_scheme="green", variant="soft", size="1")),
        ("SIN_NOVEDAD", rx.badge("Sin novedad", color_scheme="gray", variant="outline", size="1")),
        ("RETARDO", rx.badge("Retardo", color_scheme="yellow", variant="soft", size="1")),
        ("FALTA", rx.badge("Falta", color_scheme="red", variant="solid", size="1")),
        ("FALTA_JUSTIFICADA", rx.badge("Falta just.", color_scheme="blue", variant="soft", size="1")),
        ("HORA_EXTRA", rx.badge("Hora extra", color_scheme="violet", variant="soft", size="1")),
        ("SALIDA_ANTICIPADA", rx.badge("Salida ant.", color_scheme="orange", variant="soft", size="1")),
        ("PERMISO_CON_GOCE", rx.badge("Permiso c/goce", color_scheme="blue", variant="soft", size="1")),
        ("PERMISO_SIN_GOCE", rx.badge("Permiso s/goce", color_scheme="orange", variant="soft", size="1")),
        ("INCAPACIDAD_ENFERMEDAD", rx.badge("Incapacidad", color_scheme="indigo", variant="soft", size="1")),
        ("INCAPACIDAD_RIESGO_TRABAJO", rx.badge("Riesgo trabajo", color_scheme="indigo", variant="soft", size="1")),
        ("INCAPACIDAD_MATERNIDAD", rx.badge("Maternidad", color_scheme="pink", variant="soft", size="1")),
        ("VACACIONES", rx.badge("Vacaciones", color_scheme="teal", variant="soft", size="1")),
        ("DIA_FESTIVO", rx.badge("Dia festivo", color_scheme="cyan", variant="soft", size="1")),
        ("COMISION", rx.badge("Comision", color_scheme="purple", variant="soft", size="1")),
        ("OTRO", rx.badge("Otro", color_scheme="gray", variant="soft", size="1")),
        rx.badge("Pendiente", color_scheme="gray", variant="outline", size="1"),
    )


def _badge_activo(activo) -> rx.Component:
    return rx.cond(
        activo,
        rx.badge("Activo", color_scheme="green", variant="soft", size="1"),
        rx.badge("Inactivo", color_scheme="gray", variant="outline", size="1"),
    )


def _selector_contrato() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder="Contrato", width="260px"),
        rx.select.content(
            rx.foreach(
                AsistenciasState.contratos_disponibles,
                lambda contrato: rx.select.item(
                    contrato["codigo"],
                    value=contrato["id"].to(str),
                ),
            )
        ),
        value=rx.cond(
            AsistenciasState.contrato_seleccionado_id > 0,
            AsistenciasState.contrato_seleccionado_id.to(str),
            "",
        ),
        on_change=AsistenciasState.cambiar_contrato,
        size="2",
    )


def filtros_asistencias() -> rx.Component:
    return rx.hstack(
        selector_panel(),
        _selector_contrato(),
        rx.cond(
            ~AsistenciasState.panel_es_configuracion,
            rx.input(
                type="date",
                value=AsistenciasState.fecha_operacion,
                on_change=AsistenciasState.cambiar_fecha_operacion,
                width="180px",
                size="2",
            ),
            rx.fragment(),
        ),
        rx.button(
            rx.icon("refresh-cw", size=14),
            "Recargar",
            on_click=AsistenciasState.recargar_panel,
            variant="soft",
            size="2",
        ),
        spacing="3",
        wrap="wrap",
        align="center",
    )


def acciones_jornada() -> rx.Component:
    return rx.hstack(
        rx.cond(
            AsistenciasState.puede_abrir_jornada,
            rx.button(
                rx.icon("play", size=15),
                "Abrir jornada",
                on_click=AsistenciasState.abrir_jornada,
                color_scheme="green",
                size="2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AsistenciasState.puede_cerrar_jornada,
            rx.button(
                rx.icon("badge-check", size=15),
                "Cerrar y consolidar",
                on_click=AsistenciasState.cerrar_jornada,
                color_scheme="blue",
                size="2",
            ),
            rx.fragment(),
        ),
        spacing="2",
        wrap="wrap",
    )


def resumen_jornada() -> rx.Component:
    return rx.vstack(
        callout_contexto(),
        rx.hstack(
            metric_card(
                titulo="Empleados esperados",
                valor=AsistenciasState.total_empleados_jornada,
                icono="users",
                color_scheme="blue",
                descripcion="Plantilla derivada de plazas ocupadas",
            ),
            metric_card(
                titulo="Incidencias",
                valor=AsistenciasState.total_incidencias,
                icono="triangle-alert",
                color_scheme="orange",
                descripcion="Novedades capturadas por excepcion",
            ),
            metric_card(
                titulo="Sedes cubiertas",
                valor=AsistenciasState.total_sedes_supervision,
                icono="map-pinned",
                color_scheme="teal",
                descripcion="Territorio activo del supervisor",
            ),
            metric_card(
                titulo="Estatus jornada",
                valor=AsistenciasState.nombre_jornada,
                icono="clipboard-check",
                color_scheme="indigo",
                descripcion=AsistenciasState.descripcion_horario,
            ),
            spacing="4",
            width="100%",
            wrap="wrap",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            AsistenciasState.titulo_supervision,
                            font_size=Typography.SIZE_BASE,
                            font_weight=Typography.WEIGHT_BOLD,
                        ),
                        rx.text(
                            rx.cond(
                                AsistenciasState.panel_es_rrhh,
                                "Vista administrativa para precargas de Recursos Humanos",
                                rx.cond(
                                    AsistenciasState.supervisor_actual,
                                    "Captura basada en sedes asignadas",
                                    "Vista sin filtro de supervisor",
                                ),
                            ),
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.spacer(),
                    _badge_jornada(AsistenciasState.jornada_actual.get("estatus", "")),
                    acciones_jornada(),
                    width="100%",
                    align="center",
                    wrap="wrap",
                ),
                rx.cond(
                    AsistenciasState.panel_es_operacion
                    & (AsistenciasState.total_sedes_supervision > 0),
                    rx.flex(
                        rx.foreach(
                            AsistenciasState.sedes_supervision,
                            lambda sede: rx.badge(
                                sede["nombre"],
                                color_scheme="gray",
                                variant="soft",
                                size="1",
                            ),
                        ),
                        gap="2",
                        wrap="wrap",
                        width="100%",
                    ),
                    rx.text(
                        rx.cond(
                            AsistenciasState.panel_es_rrhh,
                            "RH puede precargar incidencias para todo el contrato seleccionado.",
                            "No hay sedes restringiendo la captura actual.",
                        ),
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def fila_empleado(empleado: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(
                    empleado.get("clave", "-"),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.PORTAL_PRIMARY_TEXT,
                ),
                rx.text(
                    empleado.get("nombre_completo", "-"),
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="0",
                align="start",
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
        rx.table.cell(
            rx.cond(
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
                    rx.text(
                        empleado.get("motivo", "-"),
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ),
            ),
        ),
        rx.table.cell(
            rx.hstack(
                tabla_action_button(
                    icon="pencil",
                    tooltip=rx.cond(
                        AsistenciasState.panel_es_rrhh,
                        "Precargar incidencia RH",
                        "Registrar incidencia",
                    ),
                    on_click=AsistenciasState.abrir_modal_incidencia(empleado),
                    color_scheme="blue",
                    visible=AsistenciasState.puede_editar_incidencias,
                ),
                tabla_action_button(
                    icon="eraser",
                    tooltip=rx.cond(
                        AsistenciasState.panel_es_rrhh,
                        "Eliminar precarga RH",
                        "Limpiar incidencia",
                    ),
                    on_click=AsistenciasState.limpiar_incidencia(empleado),
                    color_scheme="red",
                    visible=AsistenciasState.puede_editar_incidencias
                    & (empleado.get("incidencia_id", 0) != 0),
                ),
                spacing="1",
            ),
        ),
    )


ENCABEZADOS_ASISTENCIAS = [
    {"nombre": "Empleado", "ancho": "260px"},
    {"nombre": "Sede / Categoria", "ancho": "220px"},
    {"nombre": "Resultado", "ancho": "140px"},
    {"nombre": "Detalle", "ancho": "220px"},
    {"nombre": "Acciones", "ancho": "120px"},
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


def _tarjeta_horario(horario: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            horario.get("nombre", "Horario"),
                            font_size=Typography.SIZE_BASE,
                            font_weight=Typography.WEIGHT_BOLD,
                        ),
                        _badge_activo(horario.get("es_horario_activo", False)),
                        spacing="2",
                        wrap="wrap",
                        align="center",
                    ),
                    rx.text(
                        rx.cond(
                            horario.get("descripcion", ""),
                            horario.get("descripcion", ""),
                            "Sin descripcion adicional",
                        ),
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.icon("pencil", size=14),
                        "Editar",
                        variant="soft",
                        size="2",
                        on_click=AsistenciasState.abrir_modal_horario_editar(horario),
                    ),
                    rx.cond(
                        horario.get("es_horario_activo", False),
                        rx.button(
                            rx.icon("circle-pause", size=14),
                            "Desactivar",
                            variant="soft",
                            color_scheme="red",
                            size="2",
                            on_click=AsistenciasState.desactivar_horario(horario["id"]),
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    wrap="wrap",
                ),
                width="100%",
                align="start",
                wrap="wrap",
            ),
            rx.hstack(
                rx.badge(
                    "Entrada +",
                    horario["tolerancia_entrada_min"].to(str),
                    " min",
                    color_scheme="blue",
                    variant="soft",
                    size="1",
                ),
                rx.badge(
                    "Salida +",
                    horario["tolerancia_salida_min"].to(str),
                    " min",
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                spacing="2",
                wrap="wrap",
            ),
            rx.text(
                rx.cond(
                    horario.get("dias_resumen", ""),
                    horario["dias_resumen"].to(str),
                    "Sin dias configurados",
                ),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def _tarjeta_asignacion(asignacion: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            asignacion.get("supervisor_nombre", "Supervisor"),
                            font_size=Typography.SIZE_BASE,
                            font_weight=Typography.WEIGHT_BOLD,
                        ),
                        _badge_activo(asignacion.get("activo", False)),
                        spacing="2",
                        wrap="wrap",
                        align="center",
                    ),
                    rx.text(
                        asignacion.get("supervisor_clave", ""),
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.icon("pencil", size=14),
                        "Editar",
                        variant="soft",
                        size="2",
                        on_click=AsistenciasState.abrir_modal_supervision_editar(asignacion),
                    ),
                    rx.cond(
                        asignacion.get("activo", False),
                        rx.button(
                            rx.icon("circle-pause", size=14),
                            "Desactivar",
                            variant="soft",
                            color_scheme="red",
                            size="2",
                            on_click=AsistenciasState.desactivar_supervision(asignacion["id"]),
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    wrap="wrap",
                ),
                width="100%",
                align="start",
                wrap="wrap",
            ),
            rx.text(
                asignacion.get("sede_nombre", "Sin sede"),
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.text(
                rx.cond(
                    asignacion.get("sede_codigo", ""),
                    "Codigo sede: " + asignacion["sede_codigo"].to(str),
                    "Codigo sede: -",
                ),
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            rx.hstack(
                rx.badge(
                    rx.cond(
                        asignacion.get("fecha_inicio", ""),
                        "Inicio " + asignacion["fecha_inicio"].to(str),
                        "Inicio -",
                    ),
                    color_scheme="teal",
                    variant="soft",
                    size="1",
                ),
                rx.cond(
                    asignacion.get("fecha_fin", "") != "",
                    rx.badge(
                        "Fin " + asignacion["fecha_fin"].to(str),
                        color_scheme="gray",
                        variant="soft",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                wrap="wrap",
            ),
            rx.text(
                rx.cond(
                    asignacion.get("notas", ""),
                    asignacion.get("notas", ""),
                    "Sin notas operativas",
                ),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            spacing="2",
            width="100%",
        ),
        width="100%",
    )


def configuracion_asistencias() -> rx.Component:
    return rx.vstack(
        callout_contexto(),
        rx.hstack(
            metric_card(
                titulo="Horarios del contrato",
                valor=AsistenciasState.total_horarios_configuracion,
                icono="clock-3",
                color_scheme="teal",
                descripcion="Versiones de horario para el contrato seleccionado",
            ),
            metric_card(
                titulo="Horarios activos",
                valor=AsistenciasState.total_horarios_activos,
                icono="badge-check",
                color_scheme="green",
                descripcion="Solo uno deberia quedar activo por contrato",
            ),
            metric_card(
                titulo="Asignaciones",
                valor=AsistenciasState.total_asignaciones_supervision,
                icono="route",
                color_scheme="blue",
                descripcion="Territorios supervisor-sede registrados",
            ),
            metric_card(
                titulo="Asignaciones activas",
                valor=AsistenciasState.total_asignaciones_activas,
                icono="map-pinned",
                color_scheme="orange",
                descripcion="Sedes actualmente cubiertas por supervision",
            ),
            spacing="4",
            width="100%",
            wrap="wrap",
        ),
        rx.hstack(
            rx.button(
                rx.icon("plus", size=15),
                "Nuevo horario",
                on_click=AsistenciasState.abrir_modal_horario_crear,
                color_scheme="teal",
                size="2",
            ),
            rx.button(
                rx.icon("plus", size=15),
                "Nueva asignacion",
                on_click=AsistenciasState.abrir_modal_supervision_crear,
                color_scheme="blue",
                size="2",
            ),
            spacing="2",
            wrap="wrap",
            width="100%",
        ),
        rx.grid(
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Horarios del contrato",
                                font_size=Typography.SIZE_BASE,
                                font_weight=Typography.WEIGHT_BOLD,
                            ),
                            rx.text(
                                "Controla el horario base y la version activa usada por la jornada.",
                                font_size=Typography.SIZE_SM,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            spacing="1",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.badge(
                            AsistenciasState.contrato_seleccionado_id.to(str),
                            color_scheme="teal",
                            variant="soft",
                            size="1",
                        ),
                        width="100%",
                        align="start",
                        wrap="wrap",
                    ),
                    rx.cond(
                        AsistenciasState.horarios_filtrados.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                AsistenciasState.horarios_filtrados,
                                _tarjeta_horario,
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        empty_state_card(
                            title="Sin horarios registrados",
                            description="Crea el primer horario activo para el contrato seleccionado.",
                            icon="clock-3",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                ),
                width="100%",
                height="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Asignaciones supervisor-sede",
                                font_size=Typography.SIZE_BASE,
                                font_weight=Typography.WEIGHT_BOLD,
                            ),
                            rx.text(
                                "Define el territorio estable de cada supervisor para la captura diaria.",
                                font_size=Typography.SIZE_SM,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            spacing="1",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.badge(
                            AsistenciasState.total_asignaciones_activas.to(str) + " activas",
                            color_scheme="blue",
                            variant="soft",
                            size="1",
                        ),
                        width="100%",
                        align="start",
                        wrap="wrap",
                    ),
                    rx.cond(
                        AsistenciasState.asignaciones_filtradas.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                AsistenciasState.asignaciones_filtradas,
                                _tarjeta_asignacion,
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        empty_state_card(
                            title="Sin asignaciones registradas",
                            description="Asigna supervisores a sedes para habilitar la captura supervisada.",
                            icon="route",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                ),
                width="100%",
                height="100%",
            ),
            columns=rx.breakpoints(initial="1", lg="2"),
            spacing="4",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def modal_incidencia() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(AsistenciasState.titulo_modal_incidencia),
            rx.dialog.description(
                rx.cond(
                    AsistenciasState.empleado_seleccionado,
                    "Empleado: " + AsistenciasState.empleado_seleccionado["nombre_completo"].to(str),
                    "Captura la novedad del dia",
                )
            ),
            rx.vstack(
                rx.select.root(
                    rx.select.trigger(placeholder="Tipo de incidencia"),
                    rx.select.content(
                        rx.foreach(
                            [item.value for item in TipoIncidencia],
                            lambda valor: rx.select.item(valor.replace("_", " "), value=valor),
                        )
                    ),
                    value=AsistenciasState.form_tipo_incidencia,
                    on_change=AsistenciasState.set_form_tipo_incidencia,
                    size="2",
                    width="100%",
                ),
                rx.hstack(
                    rx.input(
                        type="number",
                        min="0",
                        step="1",
                        value=AsistenciasState.form_minutos_retardo,
                        on_change=AsistenciasState.set_form_minutos_retardo,
                        placeholder="Minutos retardo",
                        width="100%",
                    ),
                    rx.input(
                        type="number",
                        min="0",
                        step="0.5",
                        value=AsistenciasState.form_horas_extra,
                        on_change=AsistenciasState.set_form_horas_extra,
                        placeholder="Horas extra",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                rx.text_area(
                    value=AsistenciasState.form_motivo,
                    on_change=AsistenciasState.set_form_motivo,
                    placeholder="Motivo o detalle operativo",
                    min_height="120px",
                    width="100%",
                ),
                rx.hstack(
                    boton_cancelar(
                        on_click=AsistenciasState.cerrar_modal_incidencia,
                        disabled=AsistenciasState.saving,
                    ),
                    boton_guardar(
                        texto=AsistenciasState.texto_guardar_incidencia,
                        texto_guardando=rx.cond(
                            AsistenciasState.panel_es_rrhh,
                            "Guardando precarga...",
                            "Guardando incidencia...",
                        ),
                        on_click=AsistenciasState.guardar_incidencia,
                        saving=AsistenciasState.saving,
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            width="min(560px, 96vw)",
        ),
        open=AsistenciasState.modal_incidencia_abierto,
    )


def modal_horario() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(AsistenciasState.titulo_modal_horario),
            rx.dialog.description(
                "Configura el horario contractual base usado por la jornada y la consolidacion."
            ),
            rx.vstack(
                rx.input(
                    value=AsistenciasState.form_horario_nombre,
                    on_change=AsistenciasState.set_form_horario_nombre,
                    placeholder="Ej. Horario Jardineria 2025",
                    width="100%",
                ),
                rx.text_area(
                    value=AsistenciasState.form_horario_descripcion,
                    on_change=AsistenciasState.set_form_horario_descripcion,
                    placeholder="Descripcion operativa del horario",
                    min_height="90px",
                    width="100%",
                ),
                rx.hstack(
                    rx.input(
                        type="number",
                        min="0",
                        max="60",
                        value=AsistenciasState.form_horario_tolerancia_entrada,
                        on_change=AsistenciasState.set_form_horario_tolerancia_entrada,
                        placeholder="Tolerancia entrada",
                        width="100%",
                    ),
                    rx.input(
                        type="number",
                        min="0",
                        max="60",
                        value=AsistenciasState.form_horario_tolerancia_salida,
                        on_change=AsistenciasState.set_form_horario_tolerancia_salida,
                        placeholder="Tolerancia salida",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                rx.hstack(
                    rx.switch(
                        checked=AsistenciasState.form_horario_activo,
                        on_change=AsistenciasState.set_form_horario_activo,
                    ),
                    rx.text("Marcar como horario activo del contrato", size="2"),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.vstack(
                    rx.foreach(
                        AsistenciasState.form_horario_dias_ui,
                        lambda dia: rx.card(
                            rx.hstack(
                                rx.hstack(
                                    rx.switch(
                                        checked=dia["habilitado"],
                                        on_change=lambda value: AsistenciasState.set_form_horario_dia_habilitado(
                                            dia["clave"],
                                            value,
                                        ),
                                    ),
                                    rx.text(
                                        dia["label"],
                                        font_weight=Typography.WEIGHT_MEDIUM,
                                    ),
                                    spacing="2",
                                    align="center",
                                    min_width="150px",
                                ),
                                rx.input(
                                    type="time",
                                    value=dia["entrada"],
                                    on_change=lambda value: AsistenciasState.set_form_horario_dia_hora(
                                        dia["clave"],
                                        "entrada",
                                        value,
                                    ),
                                    disabled=~dia["habilitado"],
                                    width="100%",
                                ),
                                rx.input(
                                    type="time",
                                    value=dia["salida"],
                                    on_change=lambda value: AsistenciasState.set_form_horario_dia_hora(
                                        dia["clave"],
                                        "salida",
                                        value,
                                    ),
                                    disabled=~dia["habilitado"],
                                    width="100%",
                                ),
                                spacing="3",
                                width="100%",
                                wrap="wrap",
                                align="center",
                            ),
                            width="100%",
                        ),
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.hstack(
                    boton_cancelar(
                        on_click=AsistenciasState.cerrar_modal_horario,
                        disabled=AsistenciasState.saving,
                    ),
                    boton_guardar(
                        texto=AsistenciasState.texto_guardar_horario,
                        texto_guardando="Guardando horario...",
                        on_click=AsistenciasState.guardar_horario,
                        saving=AsistenciasState.saving,
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            width="min(760px, 96vw)",
        ),
        open=AsistenciasState.modal_horario_abierto,
    )


def modal_supervision() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(AsistenciasState.titulo_modal_supervision),
            rx.dialog.description(
                "Relaciona supervisores operativos con las sedes que deben cubrir."
            ),
            rx.vstack(
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
                rx.hstack(
                    rx.input(
                        type="date",
                        value=AsistenciasState.form_supervision_fecha_inicio,
                        on_change=AsistenciasState.set_form_supervision_fecha_inicio,
                        width="100%",
                    ),
                    rx.input(
                        type="date",
                        value=AsistenciasState.form_supervision_fecha_fin,
                        on_change=AsistenciasState.set_form_supervision_fecha_fin,
                        width="100%",
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
                rx.text_area(
                    value=AsistenciasState.form_supervision_notas,
                    on_change=AsistenciasState.set_form_supervision_notas,
                    placeholder="Notas de cobertura, excepciones o contexto",
                    min_height="100px",
                    width="100%",
                ),
                rx.hstack(
                    boton_cancelar(
                        on_click=AsistenciasState.cerrar_modal_supervision,
                        disabled=AsistenciasState.saving,
                    ),
                    boton_guardar(
                        texto=AsistenciasState.texto_guardar_supervision,
                        texto_guardando="Guardando asignacion...",
                        on_click=AsistenciasState.guardar_supervision,
                        saving=AsistenciasState.saving,
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            width="min(620px, 96vw)",
        ),
        open=AsistenciasState.modal_supervision_abierto,
    )
