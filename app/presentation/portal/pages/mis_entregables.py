"""
Página del Portal del Cliente - Mis Entregables.
Vista global con filtros compactos y tabla densa para actuar sin scroll extra.
"""

import reflex as rx

from app.presentation.layout import page_header, page_layout, page_toolbar
from app.presentation.portal.pages.mis_entregables_state import MisEntregablesState
from app.presentation.components.ui import (
    empty_state_card,
    filter_pill,
    filtros_inline,
    select_items_from_options,
    skeleton_tabla,
    status_badge_reactive,
)
from app.presentation.theme import Colors, Spacing, Typography, Radius, Transitions


# =============================================================================
# FILTROS POR ESTATUS
# =============================================================================
ENCABEZADOS_TABLA = [
    {"nombre": "Período", "ancho": "220px"},
    {"nombre": "Contrato", "ancho": "170px"},
    {"nombre": "Tipo de entregable", "ancho": "220px"},
    {"nombre": "Estado", "ancho": "180px"},
    {"nombre": "Acción", "ancho": "140px", "header_align": "right"},
]
def _seccion_estadisticas() -> rx.Component:
    """Pills compactas que actúan como filtros de la tabla."""
    return rx.flex(
        filter_pill(
            "Todos",
            MisEntregablesState.stats_total,
            MisEntregablesState.filtrar_todos,
            MisEntregablesState.filtro_es_todos,
        ),
        filter_pill(
            "Acción requerida",
            MisEntregablesState.stats_accion_requerida,
            MisEntregablesState.filtrar_accion_requerida,
            MisEntregablesState.filtro_es_accion_requerida,
            Colors.WARNING,
        ),
        filter_pill(
            "En revisión",
            MisEntregablesState.stats_en_revision,
            MisEntregablesState.filtrar_en_revision,
            MisEntregablesState.filtro_es_en_revision,
            Colors.INFO,
        ),
        filter_pill(
            "Rechazados",
            MisEntregablesState.stats_rechazados,
            MisEntregablesState.filtrar_rechazados,
            MisEntregablesState.filtro_es_rechazado,
            Colors.ERROR,
        ),
        filter_pill(
            "Por prefacturar",
            MisEntregablesState.stats_por_prefacturar,
            MisEntregablesState.filtrar_por_prefacturar,
            MisEntregablesState.filtro_es_por_prefacturar,
            Colors.WARNING,
        ),
        filter_pill(
            "Por facturar",
            MisEntregablesState.stats_por_facturar,
            MisEntregablesState.filtrar_por_facturar,
            MisEntregablesState.filtro_es_por_facturar,
            Colors.INFO,
        ),
        filter_pill(
            "Pagados",
            MisEntregablesState.stats_pagados,
            MisEntregablesState.filtrar_pagados,
            MisEntregablesState.filtro_es_pagado,
            Colors.SUCCESS,
        ),
        wrap="wrap",
        gap=Spacing.SM,
        width="100%",
    )


# =============================================================================
# BARRA DE FILTROS
# =============================================================================
def _barra_filtros() -> rx.Component:
    return filtros_inline(
        rx.select.root(
            rx.select.trigger(placeholder="Todos los contratos", width="200px"),
            rx.select.content(select_items_from_options(MisEntregablesState.opciones_contratos)),
            value=MisEntregablesState.filtro_contrato_id,
            on_change=MisEntregablesState.set_filtro_contrato,
            size="2",
        ),
    )


# =============================================================================
# TABLA DE ENTREGABLES
# =============================================================================
def _texto_celda(
    valor,
    *,
    tone: str = "primary",
    weight: str = Typography.WEIGHT_REGULAR,
    size: str = Typography.SIZE_SM,
) -> rx.Component:
    color_map = {
        "primary": Colors.TEXT_PRIMARY,
        "secondary": Colors.TEXT_SECONDARY,
        "muted": Colors.TEXT_MUTED,
    }
    return rx.text(
        valor,
        color=color_map.get(tone, Colors.TEXT_PRIMARY),
        font_size=size,
        font_weight=weight,
        line_height=Typography.LINE_HEIGHT_TIGHT,
    )


def _badge_estatus_entregable(status: rx.Var) -> rx.Component:
    def _badge(label: str, color_scheme: str) -> rx.Component:
        return rx.badge(
            label,
            color_scheme=color_scheme,
            variant="soft",
            size="1",
        )

    return rx.match(
        status,
        ("PENDIENTE", _badge("Pendiente", "gray")),
        ("EN_REVISION", _badge("En revisión", "sky")),
        ("APROBADO", _badge("Aprobado", "green")),
        ("RECHAZADO", _badge("Rechazado", "red")),
        ("PREFACTURA_ENVIADA", _badge("Prefactura enviada", "sky")),
        ("PREFACTURA_RECHAZADA", _badge("Prefactura rechazada", "red")),
        ("PREFACTURA_APROBADA", _badge("Prefactura aprobada", "green")),
        ("FACTURADO", _badge("Facturado", "amber")),
        ("PAGADO", _badge("Pagado", "green")),
        _badge("Sin estatus", "gray"),
    )


def _tipo_entregable(status: rx.Var) -> rx.Component:
    return rx.match(
        status,
        ("APROBADO", _texto_celda("Prefactura", tone="secondary")),
        ("PREFACTURA_ENVIADA", _texto_celda("Prefactura", tone="secondary")),
        ("PREFACTURA_RECHAZADA", _texto_celda("Prefactura", tone="secondary")),
        ("PREFACTURA_APROBADA", _texto_celda("Factura definitiva", tone="secondary")),
        ("FACTURADO", _texto_celda("Factura definitiva", tone="secondary")),
        ("PAGADO", _texto_celda("Pago registrado", tone="secondary")),
        _texto_celda("Archivos del período", tone="secondary"),
    )


def _boton_accion(
    label: str,
    on_click,
    *,
    color_scheme: str = "gray",
) -> rx.Component:
    return rx.button(
        label,
        size="1",
        variant="outline",
        color_scheme=color_scheme,
        on_click=on_click,
    )


def _accion_entregable(entregable: dict) -> rx.Component:
    return rx.match(
        entregable["estatus"],
        (
            "PENDIENTE",
            _boton_accion(
                "Subir",
                lambda: MisEntregablesState.abrir_entregable(entregable["id"]),
                color_scheme="teal",
            ),
        ),
        (
            "RECHAZADO",
            _boton_accion(
                "Subir",
                lambda: MisEntregablesState.abrir_entregable(entregable["id"]),
                color_scheme="teal",
            ),
        ),
        (
            "APROBADO",
            _boton_accion(
                "Subir",
                lambda: MisEntregablesState.abrir_modal_prefactura(entregable["id"]),
                color_scheme="teal",
            ),
        ),
        (
            "PREFACTURA_RECHAZADA",
            _boton_accion(
                "Subir",
                lambda: MisEntregablesState.abrir_modal_prefactura(entregable["id"]),
                color_scheme="teal",
            ),
        ),
        (
            "PREFACTURA_APROBADA",
            _boton_accion(
                "Subir factura",
                lambda: MisEntregablesState.abrir_modal_factura(entregable["id"]),
                color_scheme="teal",
            ),
        ),
        _boton_accion(
            "Ver",
            lambda: MisEntregablesState.abrir_entregable(entregable["id"]),
        ),
    )


def _encabezado_tabla(
    titulo: str,
    *,
    width: str = "auto",
    align: str = "left",
) -> rx.Component:
    return rx.table.column_header_cell(
        rx.text(
            titulo,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing=Typography.LETTER_SPACING_WIDE,
        ),
        width=width,
        text_align=align,
        padding=f"{Spacing.SM} {Spacing.MD}",
        border_bottom=f"1px solid {Colors.BORDER}",
    )


def _fila_entregable(entregable: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                _texto_celda(
                    f"Período {entregable['numero_periodo']}",
                    weight=Typography.WEIGHT_MEDIUM,
                ),
                _texto_celda(
                    entregable["periodo_texto"],
                    tone="muted",
                    size=Typography.SIZE_XS,
                ),
                spacing="0",
                align="start",
            ),
            padding=f"{Spacing.SM} {Spacing.MD}",
            vertical_align="middle",
        ),
        rx.table.cell(
            _texto_celda(entregable["contrato_codigo"], tone="secondary"),
            padding=f"{Spacing.SM} {Spacing.MD}",
            vertical_align="middle",
        ),
        rx.table.cell(
            _tipo_entregable(entregable["estatus"]),
            padding=f"{Spacing.SM} {Spacing.MD}",
            vertical_align="middle",
        ),
        rx.table.cell(
            _badge_estatus_entregable(entregable["estatus"]),
            padding=f"{Spacing.SM} {Spacing.MD}",
            vertical_align="middle",
        ),
        rx.table.cell(
            rx.hstack(
                _accion_entregable(entregable),
                justify="end",
                width="100%",
            ),
            padding=f"{Spacing.SM} {Spacing.MD}",
            text_align="right",
            vertical_align="middle",
        ),
        border_bottom=f"1px solid {Colors.BORDER}",
        _hover={"background": Colors.SECONDARY_LIGHT},
    )


def _tabla_entregables() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    _encabezado_tabla("Período", width=ENCABEZADOS_TABLA[0]["ancho"]),
                    _encabezado_tabla("Contrato", width=ENCABEZADOS_TABLA[1]["ancho"]),
                    _encabezado_tabla("Tipo de entregable", width=ENCABEZADOS_TABLA[2]["ancho"]),
                    _encabezado_tabla("Estado", width=ENCABEZADOS_TABLA[3]["ancho"]),
                    _encabezado_tabla(
                        "Acción",
                        width=ENCABEZADOS_TABLA[4]["ancho"],
                        align=ENCABEZADOS_TABLA[4]["header_align"],
                    ),
                ),
            ),
            rx.table.body(
                rx.foreach(MisEntregablesState.entregables_filtrados, _fila_entregable),
            ),
            width="100%",
            variant="surface",
            size="1",
        ),
        width="100%",
        min_width="760px",
        background=Colors.SURFACE,
    )


def _empty_state_entregables() -> rx.Component:
    return rx.box(
        empty_state_card(
            title="Sin entregables con este filtro",
            description="Prueba seleccionando otro estado o contrato",
            icon="inbox",
        ),
        width="100%",
    )


def _lista_entregables() -> rx.Component:
    return rx.cond(
        MisEntregablesState.hay_resultados_filtrados,
        rx.vstack(
            rx.box(
                _tabla_entregables(),
                width="100%",
                overflow_x="auto",
                background=Colors.SURFACE,
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.LG,
            ),
            rx.text(
                "Mostrando ",
                MisEntregablesState.total_mostrados,
                " entregable(s)",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            spacing="3",
            width="100%",
        ),
        _empty_state_entregables(),
    )


# =============================================================================
# MODAL DE ENTREGABLE
# =============================================================================
def _archivo_item(archivo: dict) -> rx.Component:
    """Renderiza un item de archivo."""
    return rx.hstack(
        rx.center(
            rx.cond(
                archivo["es_imagen"],
                rx.icon("image", size=16, color=Colors.PORTAL_PRIMARY),
                rx.icon("file-text", size=16, color=Colors.ERROR),
            ),
            width="32px",
            height="32px",
            border_radius="6px",
            background=rx.cond(
                archivo["es_imagen"],
                Colors.PORTAL_PRIMARY_LIGHT,
                "var(--red-3)",
            ),
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(archivo["nombre"], font_size=Typography.SIZE_SM, weight="medium", no_of_lines=1),
            rx.text(f"{archivo['tamanio_mb']} MB", font_size=Typography.SIZE_XS, color=Colors.TEXT_MUTED),
            spacing="0",
            align="start",
            flex="1",
        ),
        rx.cond(
            MisEntregablesState.entregable_actual["puede_editar"],
            rx.button(
                rx.icon("trash-2", size=14),
                size="1",
                variant="ghost",
                color_scheme="red",
                on_click=MisEntregablesState.eliminar_archivo(archivo["id"]),
            ),
            rx.fragment(),
        ),
        padding=Spacing.SM,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
        width="100%",
        align="center",
        spacing="3",
    )


def _seccion_archivos_modal() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Archivos subidos", font_size=Typography.SIZE_SM, weight="bold"),
            rx.badge(MisEntregablesState.archivos_entregable.length(), color_scheme="gray", size="1"),
            spacing="2",
            align="center",
        ),
        rx.cond(
            MisEntregablesState.archivos_entregable.length() > 0,
            rx.vstack(
                rx.foreach(MisEntregablesState.archivos_entregable.to(list[dict]), _archivo_item),
                spacing="2",
                width="100%",
            ),
            rx.center(
                rx.text("No hay archivos subidos", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
                padding="4",
            ),
        ),
        # Zona de upload (solo si puede editar)
        rx.cond(
            MisEntregablesState.entregable_actual["puede_editar"],
            rx.vstack(
                rx.separator(),
                rx.upload(
                    rx.vstack(
                        rx.cond(
                            MisEntregablesState.subiendo_archivo,
                            rx.vstack(
                                rx.spinner(size="3"),
                                rx.text("Subiendo...", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                                align="center",
                                spacing="2",
                            ),
                            rx.vstack(
                                rx.icon("upload", size=32, color=Colors.PORTAL_PRIMARY),
                                rx.text("Click o arrastra archivos", font_size=Typography.SIZE_LG, weight="medium"),
                                rx.text("JPG, PNG, PDF | Máx 10 archivos", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
                                align="center",
                                spacing="2",
                            ),
                        ),
                        align="center",
                        justify="center",
                        padding=Spacing.XL,
                        width="100%",
                    ),
                    id="upload_entregable",
                    accept={"image/*": [".jpg", ".jpeg", ".png"], "application/pdf": [".pdf"]},
                    max_files=10,
                    no_click=MisEntregablesState.subiendo_archivo,
                    no_drag=MisEntregablesState.subiendo_archivo,
                    border=f"2px dashed {Colors.TEXT_MUTED}",
                    border_radius="8px",
                    cursor=rx.cond(MisEntregablesState.subiendo_archivo, "wait", "pointer"),
                    _hover={"borderColor": Colors.PORTAL_PRIMARY, "background": Colors.PORTAL_PRIMARY_LIGHTER},
                    width="100%",
                ),
                rx.cond(
                    rx.selected_files("upload_entregable").length() > 0,
                    rx.vstack(
                        rx.text("Archivos seleccionados:", font_size=Typography.SIZE_SM, weight="bold"),
                        rx.foreach(
                            rx.selected_files("upload_entregable"),
                            lambda f: rx.hstack(
                                rx.icon("file", size=14, color=Colors.PORTAL_PRIMARY),
                                rx.text(f, font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                                spacing="2",
                                align="center",
                            ),
                        ),
                        rx.hstack(
                            rx.button("Cancelar", on_click=rx.clear_selected_files("upload_entregable"), variant="outline", size="2"),
                            rx.button(
                                rx.cond(
                                    MisEntregablesState.subiendo_archivo,
                                    rx.hstack(rx.spinner(size="1"), rx.text("Subiendo..."), spacing="2"),
                                    rx.hstack(rx.icon("cloud-upload", size=16), rx.text("Subir"), spacing="2"),
                                ),
                                on_click=MisEntregablesState.subir_archivos(rx.upload_files(upload_id="upload_entregable")),
                                disabled=MisEntregablesState.subiendo_archivo,
                                size="2",
                                color_scheme="teal",
                            ),
                            spacing="3",
                            width="100%",
                            justify="end",
                        ),
                        spacing="3",
                        width="100%",
                        padding=Spacing.MD,
                        background=Colors.PORTAL_PRIMARY_LIGHTER,
                        border=f"1px solid {Colors.PORTAL_PRIMARY}",
                        border_radius="8px",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                width="100%",
            ),
            rx.fragment(),
        ),
        spacing="3",
        width="100%",
    )


def _modal_entregable() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                MisEntregablesState.entregable_actual,
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.hstack(
                                rx.badge(MisEntregablesState.entregable_actual["contrato_codigo"], color_scheme="blue", size="1"),
                                rx.text(f"Período {MisEntregablesState.entregable_actual['numero_periodo']}", size="5", weight="bold"),
                                spacing="2",
                                align="center",
                            ),
                            rx.text(MisEntregablesState.entregable_actual["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                            spacing="0",
                        ),
                        rx.spacer(),
                        status_badge_reactive(MisEntregablesState.entregable_actual["estatus"]),
                        width="100%",
                        align="start",
                    ),
                    rx.divider(),
                    # Observaciones de rechazo
                    rx.cond(
                        MisEntregablesState.entregable_actual["observaciones_rechazo"],
                        rx.callout(
                            rx.vstack(
                                rx.text("Observaciones de BUAP:", size="2", weight="bold"),
                                rx.text(MisEntregablesState.entregable_actual["observaciones_rechazo"], size="2"),
                                spacing="1",
                                align="start",
                            ),
                            icon="triangle-alert",
                            color_scheme="red",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    _seccion_archivos_modal(),
                    rx.divider(),
                    rx.hstack(
                        rx.button(
                            "Cerrar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=MisEntregablesState.cerrar_modal_entregable,
                        ),
                        rx.spacer(),
                        rx.cond(
                            MisEntregablesState.puede_entregar,
                            rx.button(
                                rx.icon("send", size=14),
                                "Enviar para revisión",
                                color_scheme="teal",
                                on_click=MisEntregablesState.enviar_para_revision,
                                loading=MisEntregablesState.enviando,
                            ),
                            rx.cond(
                                MisEntregablesState.esta_en_revision,
                                rx.badge("Esperando revisión de BUAP", color_scheme="sky", size="2"),
                                rx.fragment(),
                            ),
                        ),
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.spinner(),
            ),
            max_width="550px",
            padding="5",
        ),
        open=MisEntregablesState.mostrar_modal_entregable,
        on_open_change=MisEntregablesState.set_mostrar_modal,
    )


# =============================================================================
# MODAL: SUBIR PREFACTURA
# =============================================================================
def _modal_prefactura() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                MisEntregablesState.entregable_actual,
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Subir Prefactura", size="5", weight="bold"),
                            rx.hstack(
                                rx.badge(MisEntregablesState.entregable_actual["contrato_codigo"], color_scheme="blue", size="1"),
                                rx.text(f"Periodo {MisEntregablesState.entregable_actual['numero_periodo']}", size="2", color=Colors.TEXT_SECONDARY),
                                spacing="2",
                                align="center",
                            ),
                            spacing="1",
                        ),
                        rx.spacer(),
                        rx.dialog.close(
                            rx.button(rx.icon("x", size=16), variant="ghost", size="1", on_click=MisEntregablesState.cerrar_modal_prefactura),
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.divider(),
                    rx.cond(
                        MisEntregablesState.entregable_actual["monto_aprobado"],
                        rx.callout(
                            rx.text(f"Monto aprobado: ${MisEntregablesState.entregable_actual['monto_aprobado']}", weight="bold"),
                            icon="banknote",
                            color_scheme="green",
                            size="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.callout(
                        rx.text("BUAP validara los datos fiscales antes de solicitar la factura definitiva.", size="2"),
                        icon="info",
                        color_scheme="blue",
                        size="1",
                        width="100%",
                    ),
                    # Upload zone
                    rx.upload(
                        rx.vstack(
                            rx.cond(
                                MisEntregablesState.enviando_prefactura,
                                rx.vstack(rx.spinner(size="3"), rx.text("Subiendo...", size="2"), align="center", spacing="2"),
                                rx.vstack(
                                    rx.icon("file-text", size=32, color=Colors.PORTAL_PRIMARY),
                                    rx.text("Click o arrastra el PDF de prefactura", size="3", weight="medium"),
                                    rx.text("Solo PDF", size="2", color=Colors.TEXT_MUTED),
                                    align="center",
                                    spacing="2",
                                ),
                            ),
                            align="center",
                            justify="center",
                            padding=Spacing.XL,
                            width="100%",
                        ),
                        id="upload_prefactura",
                        accept={"application/pdf": [".pdf"]},
                        max_files=1,
                        border=f"2px dashed {Colors.TEXT_MUTED}",
                        border_radius="8px",
                        cursor="pointer",
                        _hover={"borderColor": Colors.PORTAL_PRIMARY},
                        width="100%",
                    ),
                    rx.cond(
                        rx.selected_files("upload_prefactura").length() > 0,
                        rx.hstack(
                            rx.icon("file", size=14, color=Colors.PORTAL_PRIMARY),
                            rx.foreach(rx.selected_files("upload_prefactura"), lambda f: rx.text(f, size="2")),
                            spacing="2",
                            align="center",
                        ),
                        rx.fragment(),
                    ),
                    rx.divider(),
                    rx.hstack(
                        rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=MisEntregablesState.cerrar_modal_prefactura),
                        rx.spacer(),
                        rx.button(
                            rx.icon("send", size=14),
                            "Enviar Prefactura",
                            color_scheme="teal",
                            disabled=rx.selected_files("upload_prefactura").length() == 0,
                            loading=MisEntregablesState.enviando_prefactura,
                            on_click=MisEntregablesState.subir_prefactura(rx.upload_files(upload_id="upload_prefactura")),
                        ),
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.spinner(),
            ),
            max_width="500px",
            padding="5",
        ),
        open=MisEntregablesState.mostrar_modal_prefactura,
        on_open_change=MisEntregablesState.set_mostrar_modal_prefactura,
    )


# =============================================================================
# MODAL: SUBIR FACTURA + XML
# =============================================================================
def _validacion_xml() -> rx.Component:
    """Muestra resultado de validacion XML CFDI."""
    return rx.cond(
        MisEntregablesState.resultado_validacion_xml,
        rx.vstack(
            rx.text("Validacion CFDI", size="3", weight="bold"),
            rx.hstack(
                rx.cond(
                    MisEntregablesState.resultado_validacion_xml["es_valido"],
                    rx.badge(rx.hstack(rx.icon("check", size=12), "Valido", spacing="1"), color_scheme="green"),
                    rx.badge(rx.hstack(rx.icon("x", size=12), "Con errores", spacing="1"), color_scheme="red"),
                ),
                spacing="2",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text("RFC Emisor:", size="2", weight="medium", min_width="100px"),
                    rx.text(MisEntregablesState.resultado_validacion_xml["rfc_emisor"], size="2"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.text("RFC Receptor:", size="2", weight="medium", min_width="100px"),
                    rx.text(MisEntregablesState.resultado_validacion_xml["rfc_receptor"], size="2"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.text("Monto:", size="2", weight="medium", min_width="100px"),
                    rx.text(f"${MisEntregablesState.resultado_validacion_xml['monto_total']}", size="2"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.text("Folio Fiscal:", size="2", weight="medium", min_width="100px"),
                    rx.text(MisEntregablesState.resultado_validacion_xml["folio_fiscal"], size="2"),
                    spacing="2",
                    align="center",
                ),
                spacing="1",
                padding=Spacing.SM,
                background=Colors.SECONDARY_LIGHT,
                border_radius=Radius.MD,
                width="100%",
            ),
            rx.cond(
                MisEntregablesState.resultado_validacion_xml["errores"].to(list[str]).length() > 0,
                rx.callout(
                    rx.vstack(
                        rx.foreach(
                            MisEntregablesState.resultado_validacion_xml["errores"].to(list[str]),
                            lambda err: rx.text(err, size="2"),
                        ),
                        spacing="1",
                    ),
                    icon="triangle-alert",
                    color_scheme="red",
                    size="1",
                    width="100%",
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
        ),
        rx.fragment(),
    )


def _modal_factura() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                MisEntregablesState.entregable_actual,
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Subir Factura", size="5", weight="bold"),
                            rx.hstack(
                                rx.badge(MisEntregablesState.entregable_actual["contrato_codigo"], color_scheme="blue", size="1"),
                                rx.text(f"Periodo {MisEntregablesState.entregable_actual['numero_periodo']}", size="2", color=Colors.TEXT_SECONDARY),
                                spacing="2",
                                align="center",
                            ),
                            spacing="1",
                        ),
                        rx.spacer(),
                        rx.dialog.close(
                            rx.button(rx.icon("x", size=16), variant="ghost", size="1", on_click=MisEntregablesState.cerrar_modal_factura),
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.divider(),
                    rx.cond(
                        MisEntregablesState.entregable_actual["monto_aprobado"],
                        rx.callout(
                            rx.text(f"Monto aprobado: ${MisEntregablesState.entregable_actual['monto_aprobado']}", weight="bold"),
                            icon="banknote",
                            color_scheme="green",
                            size="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    # 1. Upload Factura PDF
                    rx.vstack(
                        rx.text("1. Factura PDF", size="3", weight="bold"),
                        rx.upload(
                            rx.vstack(
                                rx.icon("file-text", size=24, color=Colors.PORTAL_PRIMARY),
                                rx.text("Subir PDF de factura", size="2", weight="medium"),
                                align="center",
                                spacing="1",
                                padding=Spacing.MD,
                            ),
                            id="upload_factura_pdf",
                            accept={"application/pdf": [".pdf"]},
                            max_files=1,
                            border=f"2px dashed {Colors.TEXT_MUTED}",
                            border_radius="8px",
                            cursor="pointer",
                            _hover={"borderColor": Colors.PORTAL_PRIMARY},
                            width="100%",
                        ),
                        rx.cond(
                            rx.selected_files("upload_factura_pdf").length() > 0,
                            rx.hstack(
                                rx.button(
                                    "Subir PDF",
                                    size="2",
                                    color_scheme="teal",
                                    loading=MisEntregablesState.subiendo_factura_pdf,
                                    on_click=MisEntregablesState.subir_factura_pdf(rx.upload_files(upload_id="upload_factura_pdf")),
                                ),
                                spacing="2",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    # 2. Upload XML CFDI
                    rx.vstack(
                        rx.text("2. XML CFDI", size="3", weight="bold"),
                        rx.upload(
                            rx.vstack(
                                rx.icon("code-xml", size=24, color=Colors.PORTAL_PRIMARY),
                                rx.text("Subir XML del CFDI", size="2", weight="medium"),
                                align="center",
                                spacing="1",
                                padding=Spacing.MD,
                            ),
                            id="upload_factura_xml",
                            accept={"application/xml": [".xml"], "text/xml": [".xml"]},
                            max_files=1,
                            border=f"2px dashed {Colors.TEXT_MUTED}",
                            border_radius="8px",
                            cursor="pointer",
                            _hover={"borderColor": Colors.PORTAL_PRIMARY},
                            width="100%",
                        ),
                        rx.cond(
                            rx.selected_files("upload_factura_xml").length() > 0,
                            rx.hstack(
                                rx.button(
                                    "Subir y Validar XML",
                                    size="2",
                                    color_scheme="teal",
                                    loading=MisEntregablesState.subiendo_factura_xml,
                                    on_click=MisEntregablesState.subir_factura_xml(rx.upload_files(upload_id="upload_factura_xml")),
                                ),
                                spacing="2",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    # 3. Resultado de validacion
                    _validacion_xml(),
                    rx.divider(),
                    rx.hstack(
                        rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=MisEntregablesState.cerrar_modal_factura),
                        rx.spacer(),
                        rx.button(
                            rx.icon("send", size=14),
                            "Enviar Factura",
                            color_scheme="teal",
                            disabled=MisEntregablesState.folio_fiscal_xml == "",
                            loading=MisEntregablesState.enviando_factura,
                            on_click=MisEntregablesState.enviar_factura,
                        ),
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.spinner(),
            ),
            max_width="550px",
            padding="5",
        ),
        open=MisEntregablesState.mostrar_modal_factura,
        on_open_change=MisEntregablesState.set_mostrar_modal_factura,
    )


# =============================================================================
# PAGINA
# =============================================================================
def _contenido_principal() -> rx.Component:
    return rx.vstack(
        _seccion_estadisticas(),
        rx.cond(
            MisEntregablesState.cargando,
            skeleton_tabla(columnas=ENCABEZADOS_TABLA, filas=5),
            _lista_entregables(),
        ),
        _modal_entregable(),
        _modal_prefactura(),
        _modal_factura(),
        spacing="4",
        width="100%",
    )


def mis_entregables_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Mis entregables",
                subtitulo="Suba archivos y envíe para revisión de BUAP",
                icono="package-check",
            ),
            toolbar=page_toolbar(
                search_value=MisEntregablesState.filtro_busqueda,
                search_placeholder="Buscar período o contrato...",
                on_search_change=MisEntregablesState.set_filtro_busqueda,
                on_search_clear=lambda: MisEntregablesState.set_filtro_busqueda(""),
                show_view_toggle=False,
                filters=_barra_filtros(),
            ),
            content=_contenido_principal(),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MisEntregablesState.on_load_mis_entregables,
    )
