"""UI reutilizable para la documentación anual de empresas."""

from __future__ import annotations

import reflex as rx

from app.presentation.components.backoffice.empresas.empresa_documentacion_state_mixin import (
    EMPRESA_DOCUMENTACION_UPLOAD_ID,
)
from app.presentation.components.reusable.document_list_kit import (
    document_section_container,
    document_section_header,
)
from app.presentation.components.reusable.document_row_primitives import (
    documento_requerido_badge,
)
from app.presentation.components.ui import (
    form_input,
    select_items_from_options,
    tabla_action_button,
    tabla_action_buttons,
    table_cell_text_sm,
    table_shell,
)
from app.presentation.theme import Colors, Spacing, Typography


def _status_badge(estatus) -> rx.Component:
    return rx.match(
        estatus,
        ("Subido", rx.badge("Subido", color_scheme="green", variant="soft", size="1")),
        ("No aplica", rx.badge("No aplica", color_scheme="gray", variant="soft", size="1")),
        rx.badge("Pendiente", color_scheme="orange", variant="soft", size="1"),
    )


def _scope_badge(es_anual) -> rx.Component:
    return rx.cond(
        es_anual,
        rx.badge("Anual", color_scheme="blue", variant="soft", size="1"),
        rx.badge("Vigente", color_scheme="cyan", variant="soft", size="1"),
    )


def _metric_card(label, value, tone: str = "default") -> rx.Component:
    color = {
        "default": Colors.TEXT_PRIMARY,
        "success": "var(--green-10)",
        "warning": "var(--orange-10)",
    }.get(tone, Colors.TEXT_PRIMARY)

    return rx.card(
        rx.vstack(
            rx.text(label, size="1", color=Colors.TEXT_SECONDARY),
            rx.text(value, size="6", weight="bold", color=color),
            spacing="1",
            align="start",
        ),
        width="100%",
    )


def _acciones_documento(item, state, *, can_edit, readonly: bool) -> rx.Component:
    botones = []

    if not readonly:
        botones.append(
            tabla_action_button(
                icon="upload",
                tooltip=rx.cond(
                    item["es_anual"],
                    rx.cond(item["subido"], "Reemplazar PDF del año", "Subir PDF del año"),
                    rx.cond(item["subido"], "Actualizar documento vigente", "Subir documento vigente"),
                ),
                on_click=state.abrir_modal_subir(item),
                color_scheme="blue",
                visible=can_edit,
            )
        )

    botones.append(
        tabla_action_button(
            icon="eye",
            tooltip="Ver PDF",
            on_click=state.ver_documento_empresa(item),
            color_scheme="gray",
            visible=item["subido"],
        )
    )
    botones.append(
        tabla_action_button(
            icon="download",
            tooltip="Descargar PDF",
            on_click=state.descargar_documento_empresa(item),
            color_scheme="gray",
            visible=item["subido"],
        )
    )

    return tabla_action_buttons(botones)


def _fila_documento_empresa(item, state, *, can_edit, readonly: bool) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                item["numero"].to(str),
                font_weight=Typography.WEIGHT_BOLD,
            )
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(
                    rx.cond(
                        item["tipo_documento_label"] != "",
                        item["tipo_documento_label"],
                        "Documento",
                    ),
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.hstack(
                    documento_requerido_badge(item["obligatorio"]),
                    _scope_badge(item["es_anual"]),
                    rx.cond(
                        item["es_personalizado"],
                        rx.badge("Personalizado", color_scheme="gray", variant="soft", size="1"),
                        rx.fragment(),
                    ),
                    spacing="2",
                    wrap="wrap",
                ),
                spacing="2",
                align="start",
            ),
        ),
        rx.table.cell(
            rx.text(
                rx.cond(
                    item["ayuda"] != "",
                    item["ayuda"],
                    "Sin guía capturada para este documento.",
                ),
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
                white_space="normal",
            ),
        ),
        rx.table.cell(_status_badge(item["estatus"])),
        rx.table.cell(
            rx.cond(
                item["subido"],
                rx.vstack(
                    table_cell_text_sm(
                        rx.cond(
                            item["nombre_archivo"] != "",
                            item["nombre_archivo"],
                            "PDF cargado",
                        )
                    ),
                    rx.hstack(
                        rx.text(
                            "Versión " + item["version"].to(str),
                            size="1",
                            color=Colors.TEXT_MUTED,
                        ),
                        rx.cond(
                            item["origen_documento_texto"] != "",
                            rx.text(
                                item["origen_documento_texto"],
                                size="1",
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        wrap="wrap",
                    ),
                    spacing="2",
                    align="start",
                ),
                rx.text("-", color=Colors.TEXT_MUTED, size="2"),
            )
        ),
        rx.table.cell(
            _acciones_documento(
                item,
                state,
                can_edit=can_edit,
                readonly=readonly,
            )
        ),
        _hover={"background": Colors.SURFACE_HOVER},
    )


_HEADERS_DOCUMENTACION = [
    {"nombre": "#", "ancho": "56px"},
    {"nombre": "Documento", "ancho": "260px"},
    {"nombre": "Criterio / guía", "ancho": "340px"},
    {"nombre": "Estatus", "ancho": "120px"},
    {"nombre": "Archivo", "ancho": "220px"},
    {"nombre": "Acciones", "ancho": "140px"},
]


def resumen_documentacion_empresa(state) -> rx.Component:
    return rx.grid(
        _metric_card("Año", state.anio_seleccionado.to(str)),
        _metric_card("Requeridos", state.documentos_requeridos.to(str)),
        _metric_card("Subidos", state.documentos_subidos_requeridos.to(str), tone="success"),
        _metric_card("Completitud", state.porcentaje_completitud.to(str) + "%", tone="warning"),
        columns=rx.breakpoints(initial="1", sm="2", lg="4"),
        spacing="4",
        width="100%",
    )


def toolbar_documentacion_empresa(state, *, allow_change_year: bool = True) -> rx.Component:
    selector_anio = (
        rx.select.root(
            rx.select.trigger(
                rx.hstack(
                    rx.hstack(
                        rx.icon("calendar-range", size=16, color=Colors.TEXT_MUTED),
                        rx.text(
                            "Año " + state.anio_seleccionado.to(str),
                            font_size=Typography.SIZE_SM,
                            font_weight=Typography.WEIGHT_MEDIUM,
                            color=Colors.TEXT_PRIMARY,
                        ),
                        spacing="2",
                        align="center",
                        min_width="0",
                    ),
                    rx.icon("chevrons-up-down", size=14, color=Colors.TEXT_MUTED),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                width="180px",
            ),
            rx.select.content(select_items_from_options(state.opciones_anio_documentacion)),
            value=state.anio_seleccionado.to(str),
            on_change=state.cambiar_anio_documentacion,
            size="2",
        )
        if allow_change_year
        else rx.badge(
            "Año " + state.anio_seleccionado.to(str),
            color_scheme="blue",
            size="2",
            variant="soft",
        )
    )

    return rx.flex(
        rx.box(
            selector_anio,
        ),
        rx.spacer(),
        rx.vstack(
            rx.text(state.nombre_empresa_documentacion, weight="bold", size="3"),
            rx.text(
                state.empresa_documentacion_identificador,
                size="1",
                color=Colors.TEXT_SECONDARY,
            ),
            spacing="1",
            align="end",
        ),
        wrap="wrap",
        width="100%",
        align="center",
        gap=Spacing.MD,
        margin_bottom=Spacing.MD,
    )


def tabla_documentacion_empresa(state, *, can_edit, readonly: bool = False) -> rx.Component:
    return table_shell(
        loading=state.loading,
        headers=_HEADERS_DOCUMENTACION,
        rows=state.checklist_documentos,
        row_renderer=lambda item: _fila_documento_empresa(
            item,
            state,
            can_edit=can_edit,
            readonly=readonly,
        ),
        has_rows=state.checklist_documentos.length() > 0,
        empty_component=rx.center(
            rx.text("No hay documentos configurados para este expediente.", color=Colors.TEXT_SECONDARY),
            padding="2rem",
        ),
        total_caption="Checklist anual de documentación",
        loading_rows=6,
    )


def share_block_documentacion_empresa(state, *, can_share) -> rx.Component:
    return document_section_container(
        rx.vstack(
            document_section_header(
                title="Compartir expediente",
                subtitle=(
                    "Genera un link de solo lectura para este expediente anual. "
                    "El token se conserva solo al momento de generarlo."
                ),
            ),
            rx.cond(
                state.hay_link_compartible_activo,
                rx.callout.root(
                    rx.callout.icon(rx.icon("link", size=16)),
                    rx.callout.text(
                        "Hay un link activo para este expediente. Expira en: "
                        + state.link_compartible_expira_texto
                    ),
                    color_scheme="blue",
                    variant="soft",
                    width="100%",
                ),
                rx.callout.root(
                    rx.callout.icon(rx.icon("info", size=16)),
                    rx.callout.text(
                        "No hay un link activo para este expediente. Genera uno cuando necesites compartirlo."
                    ),
                    color_scheme="gray",
                    variant="soft",
                    width="100%",
                ),
            ),
            form_input(
                label="Expira el",
                value=state.form_link_expira_local,
                on_change=state.set_form_link_expira_local,
                type="datetime-local",
                disabled=~can_share,
                hint="La fecha se captura en horario local y se guarda en UTC.",
            ),
            rx.cond(
                state.tiene_link_generado_copiable,
                rx.vstack(
                    form_input(
                        label="Link generado",
                        value=state.share_link_generado,
                        read_only=True,
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("copy", size=16),
                            "Copiar",
                            on_click=rx.set_clipboard(state.share_link_generado),
                            size="2",
                            variant="soft",
                        ),
                        rx.button(
                            rx.icon("external-link", size=16),
                            "Abrir",
                            on_click=rx.redirect(state.share_link_generado),
                            size="2",
                            variant="outline",
                        ),
                        spacing="3",
                    ),
                    width="100%",
                    spacing="2",
                ),
                rx.fragment(),
            ),
            rx.hstack(
                rx.button(
                    rx.icon("link", size=16),
                    rx.cond(state.hay_link_compartible_activo, "Regenerar link", "Generar link"),
                    on_click=state.generar_link_compartible_empresa,
                    disabled=~can_share,
                ),
                rx.button(
                    rx.icon("link-2-off", size=16),
                    "Revocar",
                    on_click=state.revocar_link_compartible_empresa,
                    disabled=(~can_share) | (~state.hay_link_compartible_activo),
                    variant="outline",
                    color_scheme="red",
                ),
                spacing="3",
                wrap="wrap",
            ),
            width="100%",
            spacing="4",
            padding=Spacing.LG,
        )
    )


def modal_subir_documento_empresa(state) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Subir PDF"),
            rx.dialog.description(
                state.nombre_documento_subiendo,
                margin_bottom="12px",
            ),
            rx.cond(
                state.ayuda_documento_subiendo != "",
                rx.callout.root(
                    rx.callout.icon(rx.icon("file-text", size=16)),
                    rx.callout.text(state.ayuda_documento_subiendo),
                    color_scheme="blue",
                    variant="soft",
                    width="100%",
                ),
                rx.fragment(),
            ),
            rx.upload(
                rx.vstack(
                    rx.cond(
                        state.subiendo_archivo,
                        rx.vstack(
                            rx.spinner(size="3"),
                            rx.text("Subiendo PDF...", size="2"),
                            spacing="2",
                            align="center",
                        ),
                        rx.vstack(
                            rx.icon("upload", size=24, color=Colors.PRIMARY),
                            rx.text("Arrastra un PDF o haz clic para seleccionarlo", size="2", weight="medium"),
                            rx.text("Solo se aceptan archivos PDF", size="1", color=Colors.TEXT_SECONDARY),
                            spacing="1",
                            align="center",
                        ),
                    ),
                    width="100%",
                    align="center",
                    justify="center",
                    padding="1.5rem",
                ),
                id=EMPRESA_DOCUMENTACION_UPLOAD_ID,
                accept={"application/pdf": [".pdf"]},
                max_files=1,
                no_click=state.subiendo_archivo,
                no_drag=state.subiendo_archivo,
                border=f"2px dashed {Colors.BORDER_STRONG}",
                border_radius="12px",
                width="100%",
            ),
            rx.cond(
                rx.selected_files(EMPRESA_DOCUMENTACION_UPLOAD_ID).length() > 0,
                rx.vstack(
                    rx.foreach(
                        rx.selected_files(EMPRESA_DOCUMENTACION_UPLOAD_ID),
                        lambda archivo: rx.text(archivo, size="1", color=Colors.TEXT_SECONDARY),
                    ),
                    rx.button(
                        rx.cond(
                            state.subiendo_archivo,
                            rx.hstack(rx.spinner(size="1"), rx.text("Subiendo..."), spacing="2"),
                            rx.hstack(rx.icon("upload", size=16), rx.text("Guardar PDF"), spacing="2"),
                        ),
                        on_click=state.handle_upload_documento_empresa(
                            rx.upload_files(upload_id=EMPRESA_DOCUMENTACION_UPLOAD_ID)
                        ),
                        disabled=state.subiendo_archivo,
                    ),
                    width="100%",
                    spacing="2",
                ),
                rx.fragment(),
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    "Cerrar",
                    on_click=state.cerrar_modal_subir,
                    variant="soft",
                ),
                width="100%",
            ),
            spacing="4",
            max_width="560px",
        ),
        open=state.mostrar_modal_subir,
        on_open_change=rx.noop,
    )


def modal_documento_personalizado(state) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Agregar documento adicional"),
            rx.dialog.description(
                "Define un documento extra o complementario para esta empresa.",
                margin_bottom="12px",
            ),
            rx.vstack(
                form_input(
                    label="Nombre del documento",
                    value=state.form_documento_personalizado_nombre,
                    on_change=state.set_form_documento_personalizado_nombre,
                    placeholder="Ej. Acta constitutiva - reforma 2021",
                    hint="Este nombre aparecerá como nueva fila del checklist.",
                ),
                form_input(
                    label="Guía / notas",
                    value=state.form_documento_personalizado_ayuda,
                    on_change=state.set_form_documento_personalizado_ayuda,
                    placeholder="Describe qué debe subirse aquí",
                    hint="Opcional, pero ayuda a evitar cargas ambiguas.",
                ),
                rx.vstack(
                    rx.checkbox(
                        "Contar como obligatorio",
                        checked=state.form_documento_personalizado_es_obligatorio,
                        on_change=state.set_form_documento_personalizado_es_obligatorio,
                    ),
                    rx.checkbox(
                        "Se actualiza cada año",
                        checked=state.form_documento_personalizado_es_anual,
                        on_change=state.set_form_documento_personalizado_es_anual,
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    "Cancelar",
                    on_click=state.cerrar_modal_documento_personalizado,
                    variant="soft",
                ),
                rx.button(
                    rx.cond(
                        state.guardando_documento_personalizado,
                        rx.hstack(rx.spinner(size="1"), rx.text("Guardando..."), spacing="2"),
                        rx.hstack(rx.icon("plus", size=16), rx.text("Agregar"), spacing="2"),
                    ),
                    on_click=state.crear_documento_personalizado,
                    disabled=state.guardando_documento_personalizado,
                ),
                width="100%",
            ),
            spacing="4",
            max_width="560px",
        ),
        open=state.mostrar_modal_documento_personalizado,
        on_open_change=rx.noop,
    )


def panel_documentacion_empresa(
    state,
    *,
    can_edit,
    can_share,
    readonly: bool = False,
    show_share_block: bool = True,
    allow_change_year: bool = True,
) -> rx.Component:
    bloque_share = (
        share_block_documentacion_empresa(state, can_share=can_share)
        if show_share_block
        else rx.fragment()
    )
    modal_upload = rx.fragment() if readonly else modal_subir_documento_empresa(state)
    modal_documento_extra = rx.fragment() if readonly else modal_documento_personalizado(state)
    acciones_checklist = (
        rx.cond(
            can_edit,
            rx.button(
                rx.icon("plus", size=16),
                "Agregar documento",
                on_click=state.abrir_modal_documento_personalizado,
                variant="soft",
                size="2",
            ),
            rx.fragment(),
        )
        if not readonly
        else None
    )

    return rx.vstack(
        toolbar_documentacion_empresa(state, allow_change_year=allow_change_year),
        resumen_documentacion_empresa(state),
        document_section_container(
            rx.vstack(
                document_section_header(
                    title="Checklist anual",
                    subtitle=(
                        "Carga los PDFs del expediente del año seleccionado. Los documentos "
                        "marcados como Vigente se reutilizan entre años hasta que cambien; "
                        "si cambió el representante, el acta o la identificación, reemplaza "
                        "la versión vigente. La vigencia legal se muestra como guía, sin "
                        "validación automática en esta versión."
                    ),
                    actions=acciones_checklist,
                ),
                tabla_documentacion_empresa(
                    state,
                    can_edit=can_edit,
                    readonly=readonly,
                ),
                width="100%",
                spacing="4",
                padding=Spacing.LG,
            )
        ),
        bloque_share,
        modal_upload,
        modal_documento_extra,
        width="100%",
        spacing="4",
    )
