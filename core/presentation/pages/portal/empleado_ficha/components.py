"""Componentes UI para la ficha de empleado del portal."""

from __future__ import annotations

import reflex as rx

from core.presentation.components.ui import (
    document_status_badge,
    employee_status_badge,
    empty_state_card,
    form_select,
    form_textarea,
    metadata_divider,
    metadata_item,
    metric_card,
    modal_formulario,
    page_header,
    segmented_tab_trigger,
    segmented_tabs,
    tabla_action_button,
    tabla_cta_button,
    table_shell,
    table_text_sm,
)
from core.presentation.components.shared import EMPLOYEE_EXPEDIENTE_UPLOAD_ID
from core.presentation.theme import Colors, Radius, Spacing, StatusColors, Typography
from core.presentation.pages.portal.incapacidades import (
    IncapacidadState,
    modal_registro_incapacidad,
    seccion_incapacidades_empleado,
)

from .state import EmpleadoFichaState


TABS_FICHA = [
    ("resumen", "Resumen"),
    ("datos_personales", "Datos personales"),
    ("datos_laborales", "Datos laborales"),
    ("expediente", "Expediente"),
    ("historial", "Historial"),
]


def _section_label(texto: str) -> rx.Component:
    """Label de sección en uppercase muted."""
    return rx.text(
        texto,
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_MUTED,
        text_transform="uppercase",
        letter_spacing="0.04em",
    )


def _ficha_header() -> rx.Component:
    """Header con breadcrumb inline — patrón Nóminas › Periodo."""
    return page_header(
        icono="users",
        titulo_compuesto=rx.hstack(
            rx.link(
                "Empleados",
                href="/portal/empleados",
                size="6",
                weight="bold",
                color=Colors.PORTAL_PRIMARY_TEXT,
                _hover={"text_decoration": "underline"},
            ),
            rx.text("›", color=Colors.TEXT_MUTED, size="5"),
            rx.text(
                EmpleadoFichaState.nombre_completo,
                size="6",
                weight="bold",
            ),
            employee_status_badge(EmpleadoFichaState.estatus_empleado),
            align="center",
            spacing="2",
            wrap="wrap",
        ),
        subtitulo_compuesto=rx.cond(
            EmpleadoFichaState.tiene_plaza,
            rx.hstack(
                rx.text(
                    EmpleadoFichaState.plaza_actual.get("categoria_nombre", ""),
                    size="3",
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text("·", color=Colors.TEXT_MUTED),
                rx.text(
                    EmpleadoFichaState.plaza_actual.get("sede_nombre", ""),
                    size="3",
                    color=Colors.TEXT_SECONDARY,
                ),
                align="center",
                spacing="2",
            ),
            rx.hstack(
                rx.text(
                    "Sin plaza asignada",
                    size="3",
                    color=Colors.TEXT_MUTED,
                    font_style="italic",
                ),
                align="center",
                spacing="2",
            ),
        ),
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
    )


def _tabs_navegacion() -> rx.Component:
    """Tabs segmentadas de navegación principal."""
    return segmented_tabs(
        *[
            segmented_tab_trigger(
                label,
                value,
                active_background=Colors.PORTAL_PRIMARY,
                active_hover_background=Colors.PORTAL_PRIMARY_HOVER,
            )
            for value, label in TABS_FICHA
        ],
        value=EmpleadoFichaState.tab_activa,
        on_change=EmpleadoFichaState.set_tab,
    )


def _metadata_bar() -> rx.Component:
    """Barra horizontal con metadatos clave."""
    return rx.flex(
        metadata_item("CURP", EmpleadoFichaState.empleado.get("curp", "")),
        metadata_divider(),
        metadata_item("RFC", EmpleadoFichaState.empleado.get("rfc", "")),
        metadata_divider(),
        metadata_item("NSS", EmpleadoFichaState.empleado.get("nss", "")),
        metadata_divider(),
        metadata_item("Teléfono", EmpleadoFichaState.empleado.get("telefono", "")),
        metadata_divider(),
        metadata_item("Email", EmpleadoFichaState.empleado.get("email", "")),
        width="100%",
        align="stretch",
        wrap="wrap",
        row_gap=Spacing.SM,
        column_gap=Spacing.SM,
        padding=Spacing.BASE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        background=Colors.SURFACE,
    )


def _plaza_info() -> rx.Component:
    """Bloque de información de plaza activa."""
    return rx.flex(
        _section_label("Información de plaza"),
        rx.grid(
            _info_card(
                "Contrato",
                EmpleadoFichaState.plaza_actual.get("numero_contrato", "—"),
                EmpleadoFichaState.plaza_actual.get("vigencia_texto", "Sin vigencia"),
            ),
            _info_card(
                "Categoría",
                EmpleadoFichaState.plaza_actual.get("categoria_nombre", "Sin categoría"),
                EmpleadoFichaState.plaza_actual.get("plaza_texto", ""),
            ),
            _info_card(
                "Sede",
                EmpleadoFichaState.plaza_actual.get("sede_nombre", "Sin sede"),
                EmpleadoFichaState.plaza_actual.get("sede_codigo", ""),
            ),
            columns=rx.breakpoints(initial="1", md="3"),
            spacing="3",
            width="100%",
        ),
        direction="column",
        gap=Spacing.SM,
        width="100%",
    )


def _info_card(label: str, valor, detalle) -> rx.Component:
    """Card pequeña de detalle."""
    return rx.box(
        _section_label(label),
        rx.text(
            valor,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_PRIMARY,
            margin_top=Spacing.XS,
        ),
        rx.cond(
            detalle != "",
            rx.text(
                detalle,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
                margin_top=Spacing.XS,
            ),
            rx.fragment(),
        ),
        padding=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.MD,
    )


def _row_label_value(label: str, value) -> rx.Component:
    """Fila horizontal de detalle."""
    return rx.flex(
        rx.text(
            label,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.text(
            value,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_PRIMARY,
            text_align="right",
        ),
        justify="between",
        align="center",
        width="100%",
        padding_y=Spacing.XS,
        gap=Spacing.SM,
    )


def _mini_expediente() -> rx.Component:
    """Card de progreso resumido de expediente."""
    return rx.flex(
        _section_label("Expediente"),
        rx.box(
            rx.flex(
                rx.text("Documentos", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                rx.text(
                    EmpleadoFichaState.total_aprobados.to_string()
                    + " de "
                    + EmpleadoFichaState.total_requeridos.to_string(),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.PORTAL_PRIMARY_TEXT,
                ),
                justify="between",
                align="center",
                width="100%",
                margin_bottom=Spacing.SM,
            ),
            rx.box(
                rx.box(
                    width=EmpleadoFichaState.progreso_porcentaje.to_string() + "%",
                    height="100%",
                    background=Colors.PORTAL_PRIMARY,
                    border_radius=Radius.FULL,
                ),
                width="100%",
                height=Spacing.XS,
                background=Colors.SECONDARY_LIGHT,
                border_radius=Radius.FULL,
                overflow="hidden",
            ),
            padding=Spacing.MD,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
        ),
        direction="column",
        gap=Spacing.SM,
    )


def _fechas_card() -> rx.Component:
    """Card con fechas de ingreso del empleado."""
    return rx.flex(
        _section_label("Fechas"),
        rx.box(
            _row_label_value(
                "Ingreso (sistema)",
                EmpleadoFichaState.empleado.get("fecha_ingreso", "—"),
            ),
            _row_label_value(
                "Ingreso vigente",
                EmpleadoFichaState.empleado.get("fecha_ingreso_vigente", "—"),
            ),
            padding=Spacing.MD,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
        ),
        direction="column",
        gap=Spacing.SM,
    )


def _timeline_item(item: dict, idx: int) -> rx.Component:
    """Item compacto para timeline de movimientos."""
    return rx.flex(
        rx.box(
            width=Spacing.SM,
            height=Spacing.SM,
            border_radius=Radius.FULL,
            background=rx.cond(
                idx == 0,
                Colors.PORTAL_PRIMARY,
                Colors.BORDER_STRONG,
            ),
            margin_top=Spacing.XS,
            flex_shrink="0",
        ),
        rx.flex(
            rx.text(
                item.get("tipo_label", ""),
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                item.get("descripcion", ""),
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
            ),
            direction="column",
            flex="1",
        ),
        rx.text(
            item.get("fecha_texto", ""),
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
            white_space="nowrap",
        ),
        align="start",
        gap=Spacing.MD,
        width="100%",
        padding_y=Spacing.SM,
        border_bottom=f"1px solid {Colors.BORDER}",
        _last_child={"border_bottom": "none"},
    )


def _movimientos_recientes() -> rx.Component:
    """Timeline de últimos movimientos."""
    return rx.flex(
        _section_label("Últimos movimientos"),
        rx.box(
            rx.cond(
                EmpleadoFichaState.tiene_historial,
                rx.vstack(
                    rx.foreach(EmpleadoFichaState.historial_reciente, _timeline_item),
                    rx.button(
                        "Ver historial completo",
                        variant="ghost",
                        size="1",
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                        on_click=EmpleadoFichaState.set_tab("historial"),
                        align_self="center",
                    ),
                    spacing="2",
                    width="100%",
                ),
                empty_state_card(
                    title="Sin movimientos",
                    description="No hay movimientos laborales registrados para este empleado.",
                    icon="clock",
                ),
            ),
            padding=Spacing.BASE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
            width="100%",
        ),
        direction="column",
        gap=Spacing.SM,
        width="100%",
    )


def tab_resumen() -> rx.Component:
    """Contenido de la tab Resumen."""
    return rx.flex(
        _metadata_bar(),
        rx.cond(
            EmpleadoFichaState.tiene_plaza,
            _plaza_info(),
            empty_state_card(
                title="Sin plaza asignada",
                description="Este empleado no tiene una plaza activa asignada.",
                icon="triangle-alert",
            ),
        ),
        rx.grid(
            _fechas_card(),
            _mini_expediente(),
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="3",
            width="100%",
        ),
        _movimientos_recientes(),
        direction="column",
        gap=Spacing.LG,
        width="100%",
    )


def _badge_validacion(valor_bool) -> rx.Component:
    """Badge booleano de validación."""
    return rx.cond(
        valor_bool,
        rx.badge(
            "Validado",
            color_scheme=StatusColors.ACTIVO_SCHEME,
            variant="soft",
            size="1",
        ),
        rx.badge("Pendiente", color_scheme=Colors.WARNING_SCHEME, variant="soft", size="1"),
    )


def tab_datos_personales() -> rx.Component:
    """Tab de datos personales y bancarios."""
    return rx.grid(
        rx.flex(
            _section_label("Datos de identidad"),
            rx.box(
                _row_label_value("Nombre completo", EmpleadoFichaState.nombre_completo),
                _row_label_value(
                    "Fecha nacimiento",
                    EmpleadoFichaState.empleado.get("fecha_nacimiento", "—"),
                ),
                _row_label_value("Género", EmpleadoFichaState.empleado.get("genero", "—")),
                _row_label_value(
                    "Entidad nacimiento",
                    EmpleadoFichaState.empleado.get("entidad_nacimiento", "—"),
                ),
                rx.flex(
                    rx.text(
                        "CURP validado",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    _badge_validacion(EmpleadoFichaState.empleado.get("renapo_validado", False)),
                    justify="between",
                    align="center",
                    width="100%",
                    padding_y=Spacing.XS,
                ),
                padding=Spacing.MD,
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.LG,
                background=Colors.SURFACE,
            ),
            direction="column",
            gap=Spacing.SM,
        ),
        rx.flex(
            _section_label("Contacto y bancarios"),
            rx.box(
                _row_label_value("Dirección", EmpleadoFichaState.empleado.get("direccion", "—")),
                _row_label_value(
                    "Contacto emergencia",
                    EmpleadoFichaState.empleado.get("contacto_emergencia", "—"),
                ),
                rx.box(
                    width="100%",
                    border_top=f"1px solid {Colors.BORDER}",
                    margin_y=Spacing.SM,
                ),
                _row_label_value("Banco", EmpleadoFichaState.empleado.get("banco", "—")),
                rx.flex(
                    rx.text("Cuenta", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    rx.text(
                        EmpleadoFichaState.empleado.get("cuenta_bancaria", "—"),
                        font_size=Typography.SIZE_XS,
                        font_family="var(--font-mono)",
                        color=Colors.TEXT_PRIMARY,
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                    padding_y=Spacing.XS,
                ),
                rx.flex(
                    rx.text("CLABE", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    rx.text(
                        EmpleadoFichaState.empleado.get("clabe_interbancaria", "—"),
                        font_size=Typography.SIZE_XS,
                        font_family="var(--font-mono)",
                        color=Colors.TEXT_PRIMARY,
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                    padding_y=Spacing.XS,
                ),
                padding=Spacing.MD,
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.LG,
                background=Colors.SURFACE,
            ),
            direction="column",
            gap=Spacing.SM,
        ),
        columns=rx.breakpoints(initial="1", md="2"),
        spacing="4",
        width="100%",
    )


def tab_datos_laborales() -> rx.Component:
    """Tab de datos laborales y asistencia."""
    return rx.flex(
        rx.grid(
            metric_card(
                titulo="Faltas mes",
                valor=EmpleadoFichaState.faltas_mes,
                icono=None,
                show_icon=False,
                align="center",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            metric_card(
                titulo="Faltas totales",
                valor=EmpleadoFichaState.faltas_totales,
                icono=None,
                show_icon=False,
                align="center",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            metric_card(
                titulo="Incapacidades",
                valor=IncapacidadState.total_incapacidades_empleado,
                icono=None,
                show_icon=False,
                align="center",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            metric_card(
                titulo="Tipo pago",
                valor=EmpleadoFichaState.tipo_pago,
                icono=None,
                show_icon=False,
                align="center",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            columns=rx.breakpoints(initial="2", md="4"),
            spacing="3",
            width="100%",
        ),
        rx.box(
            _row_label_value(
                "Sede actual",
                rx.cond(
                    EmpleadoFichaState.tiene_plaza,
                    EmpleadoFichaState.plaza_actual.get("sede_nombre", "Sin sede"),
                    "Sin plaza asignada",
                ),
            ),
            _row_label_value(
                "Categoría",
                rx.cond(
                    EmpleadoFichaState.tiene_plaza,
                    EmpleadoFichaState.plaza_actual.get("categoria_nombre", "Sin categoría"),
                    "Sin plaza asignada",
                ),
            ),
            _row_label_value("Horario", EmpleadoFichaState.horario),
            padding=Spacing.MD,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
        ),
        seccion_incapacidades_empleado(
            EmpleadoFichaState.empleado.get("id", 0),
            EmpleadoFichaState.nombre_completo,
            EmpleadoFichaState.plaza_actual.get("plaza_id", 0),
            EmpleadoFichaState.plaza_actual.get("contrato_id", 0),
        ),
        direction="column",
        gap=Spacing.LG,
        width="100%",
    )


ENCABEZADOS_DOCUMENTOS = [
    {"nombre": "Documento", "ancho": "32%", "header_align": "left"},
    {"nombre": "Archivo", "ancho": "auto", "header_align": "left"},
    {"nombre": "Ver.", "ancho": "70px", "header_align": "center"},
    {"nombre": "Estado", "ancho": "130px", "header_align": "center"},
    {"nombre": "Acciones", "ancho": "180px", "header_align": "center"},
]


def _archivo_documento_cell(doc: dict) -> rx.Component:
    return rx.cond(
        doc.get("subido", False),
        rx.button(
            doc.get("nombre_archivo", "Documento"),
            on_click=EmpleadoFichaState.ver_documento(doc),
            variant="ghost",
            size="1",
            color_scheme=Colors.NEUTRAL_SCHEME,
            justify="start",
            padding="0",
            height="auto",
            text_align="left",
        ),
        table_text_sm("Sin subir", tone="muted"),
    )


def _acciones_documento(doc: dict, *, obligatorio: bool) -> rx.Component:
    es_pendiente = doc.get("estatus", "") == "PENDIENTE_REVISION"
    color_subir = Colors.PORTAL_ACCENT_SCHEME if obligatorio else Colors.NEUTRAL_SCHEME

    return rx.cond(
        doc.get("subido", False),
        rx.hstack(
            tabla_action_button(
                icon="eye",
                tooltip="Ver archivo",
                on_click=EmpleadoFichaState.ver_documento(doc),
                color_scheme=Colors.NEUTRAL_SCHEME,
            ),
            tabla_action_button(
                icon="download",
                tooltip="Descargar",
                on_click=EmpleadoFichaState.descargar_documento(doc),
                color_scheme=Colors.NEUTRAL_SCHEME,
            ),
            rx.cond(
                es_pendiente,
                tabla_cta_button(
                    text="Aprobar",
                    on_click=EmpleadoFichaState.aprobar_documento(doc),
                    color_scheme="green",
                    variant="soft",
                    size="1",
                ),
                rx.fragment(),
            ),
            rx.cond(
                es_pendiente,
                tabla_cta_button(
                    text="Rechazar",
                    on_click=EmpleadoFichaState.abrir_modal_rechazo(doc),
                    color_scheme="red",
                    variant="soft",
                    size="1",
                ),
                rx.fragment(),
            ),
            spacing="1",
            align="center",
            justify="center",
            wrap="wrap",
        ),
        tabla_cta_button(
            text="Subir",
            on_click=EmpleadoFichaState.abrir_subir(doc.get("tipo_documento", "")),
            color_scheme=color_subir,
            variant="outline",
            size="1",
        ),
    )


def _row_documento(doc: dict, *, obligatorio: bool) -> rx.Component:
    """Fila para tabla de documentos del expediente."""
    return rx.table.row(
        rx.table.cell(
            table_text_sm(
                doc.get("tipo_documento_label", "Documento"),
                tone="primary",
                weight=Typography.WEIGHT_MEDIUM,
            )
        ),
        rx.table.cell(_archivo_documento_cell(doc)),
        rx.table.cell(
            rx.center(
                table_text_sm(doc.get("version_texto", "—"), tone="secondary"),
                width="100%",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.center(
                document_status_badge(
                    doc.get("estatus", ""),
                    missing_label="Sin subir",
                ),
                width="100%",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.center(
                _acciones_documento(doc, obligatorio=obligatorio),
                width="100%",
            ),
            text_align="center",
        ),
    )


def _tabla_documentos(tabla_rows, titulo: str, *, obligatorio: bool) -> rx.Component:
    """Tabla de documentos por sección."""
    return rx.flex(
        _section_label(titulo),
        table_shell(
            loading=EmpleadoFichaState.loading,
            headers=ENCABEZADOS_DOCUMENTOS,
            rows=tabla_rows,
            row_renderer=lambda doc: _row_documento(doc, obligatorio=obligatorio),
            has_rows=tabla_rows.length() > 0,
            empty_component=empty_state_card(
                title="Sin documentos",
                description="No hay documentos en esta sección.",
                icon="file-text",
            ),
            table_size="2",
        ),
        direction="column",
        gap=Spacing.SM,
        width="100%",
    )


def tab_expediente() -> rx.Component:
    """Tab expediente documental gestionable desde la ficha."""
    return rx.flex(
        rx.grid(
            metric_card(
                titulo="Requeridos",
                valor=EmpleadoFichaState.total_requeridos,
                icono=None,
                show_icon=False,
                align="center",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            metric_card(
                titulo="Aprobados",
                valor=EmpleadoFichaState.total_aprobados,
                icono=None,
                show_icon=False,
                align="center",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            metric_card(
                titulo="Pendientes",
                valor=EmpleadoFichaState.total_pendientes,
                icono=None,
                show_icon=False,
                align="center",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            metric_card(
                titulo="Rechazados",
                valor=EmpleadoFichaState.total_rechazados,
                icono=None,
                show_icon=False,
                align="center",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            columns=rx.breakpoints(initial="2", md="4"),
            spacing="3",
            width="100%",
        ),
        rx.flex(
            _section_label("Gestión documental"),
            rx.button(
                rx.icon("upload", size=16),
                "Subir documento",
                variant="soft",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                size="2",
                on_click=EmpleadoFichaState.abrir_modal_subir,
            ),
            justify="between",
            align="center",
            wrap="wrap",
            row_gap=Spacing.SM,
            width="100%",
        ),
        _tabla_documentos(
            EmpleadoFichaState.documentos_obligatorios,
            "Documentos obligatorios",
            obligatorio=True,
        ),
        _tabla_documentos(
            EmpleadoFichaState.documentos_opcionales,
            "Documentos opcionales",
            obligatorio=False,
        ),
        direction="column",
        gap=Spacing.LG,
        width="100%",
    )


def modal_subir_documento_ficha() -> rx.Component:
    """Modal de carga documental embebido en la ficha."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Subir documento",
                            font_size=Typography.SIZE_XL,
                            font_weight=Typography.WEIGHT_SEMIBOLD,
                        ),
                        rx.text(
                            "Seleccione el tipo de documento y cargue un archivo.",
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=18),
                        variant="ghost",
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        on_click=EmpleadoFichaState.cerrar_modal_subir,
                    ),
                    width="100%",
                    align="start",
                ),
                rx.vstack(
                    rx.box(
                        form_select(
                            label="Documento",
                            required=True,
                            placeholder="Seleccionar tipo de documento...",
                            value=EmpleadoFichaState.tipo_documento_subiendo,
                            on_change=EmpleadoFichaState.set_tipo_documento_subiendo,
                            options=EmpleadoFichaState.tipos_documento_disponibles,
                            label_variant="portal",
                            style_variant="portal",
                        ),
                        width="100%",
                    ),
                    rx.cond(
                        EmpleadoFichaState.tipo_documento_subiendo != "",
                        rx.upload(
                            rx.vstack(
                                rx.cond(
                                    EmpleadoFichaState.subiendo_archivo,
                                    rx.spinner(size="2"),
                                    rx.icon(
                                        "cloud-upload",
                                        size=30,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                ),
                                rx.text(
                                    "Arrastre un archivo o haga clic para seleccionar",
                                    font_size=Typography.SIZE_SM,
                                    color=Colors.TEXT_SECONDARY,
                                ),
                                rx.text(
                                    "PDF, PNG o JPG (máximo 1 archivo)",
                                    font_size=Typography.SIZE_XS,
                                    color=Colors.TEXT_MUTED,
                                ),
                                spacing="2",
                                align="center",
                                width="100%",
                                padding_y=Spacing.XL,
                            ),
                            id=EMPLOYEE_EXPEDIENTE_UPLOAD_ID,
                            accept={
                                "application/pdf": [".pdf"],
                                "image/png": [".png"],
                                "image/jpeg": [".jpg", ".jpeg"],
                            },
                            max_files=1,
                            on_drop=EmpleadoFichaState.handle_upload_documento(
                                rx.upload_files(upload_id=EMPLOYEE_EXPEDIENTE_UPLOAD_ID),
                            ),
                            border=f"1px dashed {Colors.BORDER_STRONG}",
                            border_radius=Radius.LG,
                            background=Colors.SECONDARY_LIGHT,
                            width="100%",
                            cursor="pointer",
                        ),
                        rx.callout.root(
                            rx.callout.icon(rx.icon("info", size=16)),
                            rx.callout.text("Seleccione primero el tipo de documento."),
                            color_scheme=Colors.NEUTRAL_SCHEME,
                            variant="soft",
                            width="100%",
                        ),
                    ),
                    spacing="3",
                    width="100%",
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Cerrar",
                        variant="outline",
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        on_click=EmpleadoFichaState.cerrar_modal_subir,
                    ),
                    spacing="2",
                    width="100%",
                    align="center",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="520px",
            width="min(96vw, 520px)",
            padding=Spacing.LG,
        ),
        open=EmpleadoFichaState.mostrar_modal_subir,
        on_open_change=EmpleadoFichaState.set_mostrar_modal_subir,
    )


def modal_rechazo_documento_ficha() -> rx.Component:
    """Modal para capturar observación de rechazo desde la ficha."""
    return modal_formulario(
        open=EmpleadoFichaState.mostrar_modal_rechazo,
        titulo="Rechazar documento",
        descripcion="Ingrese el motivo del rechazo. El empleado podrá ver esta observación.",
        icono="circle-x",
        color_icono="red",
        color_guardar="red",
        texto_guardar="Rechazar",
        texto_guardando="Rechazando...",
        on_guardar=EmpleadoFichaState.confirmar_rechazo,
        on_cancelar=EmpleadoFichaState.cerrar_modal_rechazo,
        loading=EmpleadoFichaState.saving,
        max_width="500px",
        contenido=rx.vstack(
            form_textarea(
                label="Observación",
                required=True,
                value=EmpleadoFichaState.form_observacion_rechazo,
                on_change=EmpleadoFichaState.set_form_observacion_rechazo,
                placeholder="Describa el motivo del rechazo (mín. 5 caracteres)...",
                error=EmpleadoFichaState.error_observacion,
                label_variant="portal",
                style_variant="portal",
                rows="4",
            ),
            spacing="4",
            width="100%",
        ),
    )


def modal_preview_documento_ficha() -> rx.Component:
    """Modal de vista previa para documentos del expediente."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Vista previa",
                            font_size=Typography.SIZE_XL,
                            font_weight=Typography.WEIGHT_SEMIBOLD,
                        ),
                        rx.text(
                            EmpleadoFichaState.preview_nombre_archivo,
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=20),
                        variant="ghost",
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        on_click=EmpleadoFichaState.cerrar_modal_preview,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    EmpleadoFichaState.preview_es_imagen,
                    rx.center(
                        rx.image(
                            src=EmpleadoFichaState.preview_url,
                            max_width="100%",
                            max_height="70vh",
                            object_fit="contain",
                            border_radius=Radius.MD,
                        ),
                        width="100%",
                        padding=Spacing.MD,
                    ),
                    rx.cond(
                        EmpleadoFichaState.preview_es_pdf,
                        rx.el.iframe(
                            src=EmpleadoFichaState.preview_url,
                            width="100%",
                            height="70vh",
                            style={
                                "border": f"1px solid {Colors.BORDER}",
                                "borderRadius": Radius.LG,
                                "background": Colors.SURFACE,
                            },
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("file-text", size=40, color=Colors.TEXT_MUTED),
                                rx.text(
                                    "No hay vista previa embebida para este archivo.",
                                    font_size=Typography.SIZE_SM,
                                    color=Colors.TEXT_SECONDARY,
                                ),
                                spacing="2",
                                padding=Spacing.XL,
                            ),
                            width="100%",
                        ),
                    ),
                ),
                rx.hstack(
                    rx.link(
                        rx.button(
                            rx.icon("external-link", size=14),
                            "Abrir en nueva pestaña",
                            variant="soft",
                            size="2",
                            color_scheme=Colors.NEUTRAL_SCHEME,
                        ),
                        href=EmpleadoFichaState.preview_url,
                        is_external=True,
                    ),
                    rx.button(
                        "Cerrar",
                        variant="outline",
                        size="2",
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        on_click=EmpleadoFichaState.cerrar_modal_preview,
                    ),
                    justify="end",
                    width="100%",
                    spacing="2",
                    wrap="wrap",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="960px",
            width="min(96vw, 960px)",
        ),
        open=EmpleadoFichaState.mostrar_modal_preview,
        on_open_change=rx.noop,
    )


def _timeline_item_completo(item: dict) -> rx.Component:
    """Item detallado de historial laboral."""
    return rx.flex(
        rx.box(
            width=Spacing.SM,
            height=Spacing.SM,
            border_radius=Radius.FULL,
            background=Colors.PORTAL_PRIMARY,
            margin_top=Spacing.XS,
            flex_shrink="0",
        ),
        rx.flex(
            rx.flex(
                rx.text(
                    item.get("tipo_label", ""),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    item.get("fecha_texto", ""),
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                justify="between",
                align="center",
                width="100%",
                wrap="wrap",
                row_gap=Spacing.XS,
            ),
            rx.text(
                item.get("descripcion", ""),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.cond(
                item.get("notas", "") != "",
                rx.text(
                    item.get("notas", ""),
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    font_style="italic",
                ),
                rx.fragment(),
            ),
            direction="column",
            gap=Spacing.XS,
            flex="1",
        ),
        align="start",
        gap=Spacing.MD,
        width="100%",
        padding_y=Spacing.SM,
        border_bottom=f"1px solid {Colors.BORDER}",
        _last_child={"border_bottom": "none"},
    )


def tab_historial() -> rx.Component:
    """Tab con historial completo."""
    return rx.flex(
        rx.cond(
            EmpleadoFichaState.tiene_historial,
            rx.box(
                rx.foreach(EmpleadoFichaState.historial, _timeline_item_completo),
                padding=Spacing.BASE,
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.LG,
                background=Colors.SURFACE,
                width="100%",
            ),
            empty_state_card(
                title="Sin historial",
                description="No se encontraron movimientos registrados para este empleado.",
                icon="clock",
            ),
        ),
        direction="column",
        width="100%",
    )


def contenido_ficha_empleado() -> rx.Component:
    """Contenido principal de la ficha con tabs."""
    return rx.flex(
        rx.cond(
            EmpleadoFichaState.loading,
            rx.center(
                rx.flex(
                    rx.spinner(size="3"),
                    rx.text("Cargando ficha...", color=Colors.TEXT_MUTED),
                    align="center",
                    gap=Spacing.SM,
                ),
                width="100%",
                padding_y=Spacing.XXL,
            ),
            rx.cond(
                EmpleadoFichaState.error != "",
                empty_state_card(
                    title="Error al cargar",
                    description=EmpleadoFichaState.error,
                    icon="triangle-alert",
                ),
                rx.flex(
                    _ficha_header(),
                    _tabs_navegacion(),
                    rx.match(
                        EmpleadoFichaState.tab_activa,
                        ("resumen", tab_resumen()),
                        ("datos_personales", tab_datos_personales()),
                        ("datos_laborales", tab_datos_laborales()),
                        ("expediente", tab_expediente()),
                        ("historial", tab_historial()),
                        tab_resumen(),
                    ),
                    direction="column",
                    gap=Spacing.LG,
                    width="100%",
                ),
            ),
        ),
        modal_registro_incapacidad(),
        modal_subir_documento_ficha(),
        modal_rechazo_documento_ficha(),
        modal_preview_documento_ficha(),
        direction="column",
        gap=Spacing.LG,
        width="100%",
    )
