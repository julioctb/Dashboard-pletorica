"""Componentes compartidos del módulo de incapacidades en portal."""

from __future__ import annotations

import reflex as rx

from core.core.enums import EstatusIncapacidad, OrigenIncapacidad
from core.core.ui_helpers import FILTRO_TODOS
from core.presentation.components.ui import (
    empty_state_card,
    feedback_callout,
    filtros_inline,
    form_date,
    form_input,
    form_select,
    form_textarea,
    input_busqueda,
    metric_card,
    modal_formulario,
    tabla_cta_button,
    table_cell_actions,
    table_cell_badge,
    table_cell_text_sm,
    table_pagination,
    table_shell,
    table_text_sm,
)
from core.presentation.theme import Colors, Radius, Spacing, StatusColors, Typography

from .state import IncapacidadState


ENCABEZADOS_INCAPACIDADES = [
    {"nombre": "Empleado", "ancho": "250px"},
    {"nombre": "Tipo", "ancho": "190px"},
    {"nombre": "Origen", "ancho": "130px", "header_align": "center"},
    {"nombre": "Periodo", "ancho": "180px"},
    {"nombre": "Plaza", "ancho": "210px"},
    {"nombre": "Certificados", "ancho": "170px"},
    {"nombre": "Estatus", "ancho": "120px", "header_align": "center"},
    {"nombre": "Acciones", "ancho": "120px", "header_align": "center"},
]


def _section_label(texto: str) -> rx.Component:
    return rx.text(
        texto,
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_MUTED,
        text_transform="uppercase",
        letter_spacing="0.04em",
    )


def _badge_estatus(estatus: str) -> rx.Component:
    return rx.match(
        estatus,
        (
            EstatusIncapacidad.ACTIVA.value,
            rx.badge(
                EstatusIncapacidad.ACTIVA.descripcion,
                color_scheme=StatusColors.ACTIVO_SCHEME,
                variant="soft",
                size="1",
            ),
        ),
        (
            EstatusIncapacidad.VENCIDA.value,
            rx.badge(
                EstatusIncapacidad.VENCIDA.descripcion,
                color_scheme=Colors.WARNING_SCHEME,
                variant="soft",
                size="1",
            ),
        ),
        rx.badge(
            EstatusIncapacidad.CERRADA.descripcion,
            color_scheme=Colors.NEUTRAL_SCHEME,
            variant="soft",
            size="1",
        ),
    )


def _badge_origen(origen: str, origen_label) -> rx.Component:
    return rx.match(
        origen,
        (
            OrigenIncapacidad.FORMAL.value,
            rx.badge(
                origen_label,
                color_scheme="blue",
                variant="soft",
                size="1",
            ),
        ),
        rx.badge(
            origen_label,
            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            variant="outline",
            size="1",
        ),
    )


def _celda_centrada(component: rx.Component) -> rx.Component:
    return rx.table.cell(
        rx.center(
            component,
            width="100%",
        ),
    )


def _incapacidad_card(item: rx.Var) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        item["tipo_label"],
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_SEMIBOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    rx.text(
                        item["periodo_label"],
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                ),
                rx.hstack(
                    _badge_estatus(item["estatus"]),
                    rx.cond(
                        item["origen"] == OrigenIncapacidad.POR_ACUERDO.value,
                        rx.badge(
                            item["origen_label"],
                            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                            variant="outline",
                            size="1",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                align="start",
                gap=Spacing.MD,
            ),
            rx.hstack(
                rx.text(
                    item["dias_certificados_label"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                rx.text("·", font_size=Typography.SIZE_XS, color=Colors.TEXT_MUTED),
                rx.text(
                    item["total_certificados_label"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                rx.cond(
                    item["requiere_cobertura"],
                    rx.badge(
                        "Cobertura requerida",
                        color_scheme=Colors.WARNING_SCHEME,
                        variant="outline",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                wrap="wrap",
                gap=Spacing.SM,
                align="center",
                width="100%",
            ),
            rx.cond(
                item["plaza_detalle"] != "",
                rx.text(
                    item["plaza_detalle"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.fragment(),
            ),
            spacing="2",
            width="100%",
            align="start",
        ),
        width="100%",
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
    )


def lista_incapacidades_empleado() -> rx.Component:
    return rx.vstack(
        rx.cond(
            IncapacidadState.error_incapacidades != "",
            feedback_callout(
                IncapacidadState.error_incapacidades,
                "warning",
            ),
            rx.fragment(),
        ),
        rx.cond(
            IncapacidadState.cargando_incapacidades,
            rx.center(
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text(
                        "Cargando incapacidades...",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_MUTED,
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                padding_y=Spacing.LG,
            ),
            rx.cond(
                IncapacidadState.tiene_incapacidades,
                rx.vstack(
                    rx.foreach(
                        IncapacidadState.incapacidades_empleado,
                        _incapacidad_card,
                    ),
                    spacing="3",
                    width="100%",
                ),
                empty_state_card(
                    title="Sin incapacidades registradas",
                    description=(
                        "Cuando Recursos Humanos registre una incapacidad, "
                        "aparecerá aquí junto con su impacto operativo."
                    ),
                    icon="heart-pulse",
                ),
            ),
        ),
        spacing="3",
        width="100%",
    )


def seccion_incapacidades_empleado(
    empleado_id,
    empleado_nombre,
    plaza_id=0,
    contrato_id=0,
) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            _section_label("Incapacidades"),
            rx.spacer(),
            rx.button(
                rx.icon("heart-pulse", size=14),
                "Registrar incapacidad",
                variant="outline",
                size="2",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                cursor="pointer",
                on_click=IncapacidadState.abrir_modal_registro(
                    empleado_id,
                    empleado_nombre,
                    plaza_id,
                    contrato_id,
                ),
            ),
            width="100%",
            align="center",
            gap=Spacing.SM,
        ),
        lista_incapacidades_empleado(),
        spacing="3",
        width="100%",
        align="stretch",
    )


def metricas_incapacidades_empresa() -> rx.Component:
    return rx.grid(
        metric_card(
            titulo="Activas",
            valor=IncapacidadState.conteo_activas_empresa.to(str),
            icono="heart-pulse",
            color_scheme=StatusColors.ACTIVO_SCHEME,
            descripcion="Con sincronización operativa vigente",
        ),
        metric_card(
            titulo="Vencidas",
            valor=IncapacidadState.conteo_vencidas_empresa.to(str),
            icono="triangle-alert",
            color_scheme=Colors.WARNING_SCHEME,
            descripcion="Pendientes de cierre o renovación",
        ),
        metric_card(
            titulo="Total",
            valor=IncapacidadState.conteo_total_empresa.to(str),
            icono="clipboard-list",
            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            descripcion="Historial completo de la empresa",
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
        spacing="4",
        width="100%",
    )


def filtros_incapacidades_empresa() -> rx.Component:
    return filtros_inline(
        rx.select.root(
            rx.select.trigger(placeholder="Estatus", width="200px"),
            rx.select.content(
                rx.select.item("Todos", value=FILTRO_TODOS),
                rx.select.item("Activas", value=EstatusIncapacidad.ACTIVA.value),
                rx.select.item("Vencidas", value=EstatusIncapacidad.VENCIDA.value),
                rx.select.item("Cerradas", value=EstatusIncapacidad.CERRADA.value),
            ),
            value=IncapacidadState.filtro_estatus_empresa,
            on_change=IncapacidadState.set_filtro_estatus_empresa,
            size="2",
        ),
    )


def _fila_incapacidad_empresa(item: rx.Var) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                table_text_sm(
                    item["empleado_nombre"],
                    weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.cond(
                    item["empleado_clave"] != "",
                    rx.text(
                        item["empleado_clave"],
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                        font_family="var(--font-mono)",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align="start",
            )
        ),
        rx.table.cell(
            rx.vstack(
                table_text_sm(item["tipo_label"]),
                rx.cond(
                    item["requiere_cobertura"],
                    rx.badge(
                        "Cobertura requerida",
                        color_scheme=Colors.WARNING_SCHEME,
                        variant="outline",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align="start",
            )
        ),
        _celda_centrada(_badge_origen(item["origen"], item["origen_label"])),
        rx.table.cell(
            rx.vstack(
                table_text_sm(item["fecha_inicio_fmt"]),
                table_text_sm(
                    item["fecha_fin_estimada_fmt"],
                    tone="secondary",
                ),
                spacing="1",
                align="start",
            )
        ),
        table_cell_text_sm(
            item["plaza_detalle"],
            tone="secondary",
            fallback="Sin plaza activa",
        ),
        rx.table.cell(
            rx.vstack(
                table_text_sm(item["total_certificados_label"]),
                table_text_sm(
                    item["folio_imss_label"],
                    tone="secondary",
                ),
                spacing="1",
                align="start",
            )
        ),
        table_cell_badge(_badge_estatus(item["estatus"])),
        table_cell_actions(
            rx.center(
                tabla_cta_button(
                    "Ver ficha",
                    IncapacidadState.ir_a_ficha_empleado(item),
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                ),
                width="100%",
            )
        ),
    )


def tabla_incapacidades_empresa() -> rx.Component:
    return rx.vstack(
        rx.cond(
            IncapacidadState.error_incapacidades_empresa != "",
            feedback_callout(
                IncapacidadState.error_incapacidades_empresa,
                "warning",
            ),
            rx.fragment(),
        ),
        table_shell(
            loading=IncapacidadState.loading,
            headers=ENCABEZADOS_INCAPACIDADES,
            rows=IncapacidadState.incapacidades_empresa_paginadas,
            row_renderer=_fila_incapacidad_empresa,
            has_rows=IncapacidadState.incapacidades_empresa_paginadas.length() > 0,
            empty_component=empty_state_card(
                title="No hay incapacidades registradas",
                description=(
                    "Registra incapacidades directamente desde esta sección "
                    "para sincronizar operación y nómina."
                ),
                icon="heart-pulse",
                action_button=rx.button(
                    rx.icon("plus", size=16),
                    "Registrar incapacidad",
                    on_click=IncapacidadState.abrir_modal_registro_global,
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                ),
            ),
            total_caption=IncapacidadState.resumen_paginacion_incapacidades,
            footer_component=table_pagination(
                current_page=IncapacidadState.pagina_incapacidades_actual,
                total_pages=IncapacidadState.total_paginas_incapacidades,
                page_numbers=IncapacidadState.paginas_visibles_incapacidades,
                on_page_change=IncapacidadState.ir_a_pagina_incapacidades,
                on_previous=IncapacidadState.pagina_anterior_incapacidades,
                on_next=IncapacidadState.pagina_siguiente_incapacidades,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            loading_rows=6,
        ),
        spacing="3",
        width="100%",
    )


def _descripcion_modal() -> rx.Component:
    return rx.cond(
        IncapacidadState.mostrar_selector_empleado_modal,
        rx.text(
            "Seleccione al empleado y capture el periodo de la incapacidad para sincronizar asistencias y nómina.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.text(
            "Empleado: ",
            rx.text.span(
                IncapacidadState.empleado_contexto_nombre,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
    )


def _selector_empleado_modal() -> rx.Component:
    return rx.cond(
        IncapacidadState.mostrar_selector_empleado_modal,
        rx.vstack(
            _section_label("Empleado"),
            input_busqueda(
                value=IncapacidadState.busqueda_empleado_modal,
                on_change=IncapacidadState.set_busqueda_empleado_modal,
                on_clear=IncapacidadState.limpiar_busqueda_empleado_modal,
                placeholder="Buscar empleado activo por nombre o clave...",
                width="100%",
                toolbar_style=True,
            ),
            rx.cond(
                IncapacidadState.error_empleados_modal != "",
                feedback_callout(
                    IncapacidadState.error_empleados_modal,
                    "warning",
                ),
                rx.fragment(),
            ),
            rx.cond(
                IncapacidadState.cargando_empleados_modal,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text(
                        "Cargando empleados activos...",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_MUTED,
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.fragment(),
            ),
            form_select(
                label="Seleccionar empleado",
                required=True,
                placeholder="Seleccione un empleado activo",
                value=IncapacidadState.empleado_seleccionado_modal_id,
                on_change=IncapacidadState.set_empleado_seleccionado_modal_id,
                options=IncapacidadState.opciones_empleados_modal,
                hint="Solo se muestran empleados activos de la empresa actual.",
                label_variant="portal",
                style_variant="portal",
            ),
            rx.cond(
                (~IncapacidadState.cargando_empleados_modal)
                & (~IncapacidadState.tiene_empleados_modal)
                & (IncapacidadState.error_empleados_modal == ""),
                rx.text(
                    "No se encontraron empleados activos con ese criterio.",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        rx.fragment(),
    )


def _resumen_contexto_modal() -> rx.Component:
    return rx.cond(
        IncapacidadState.empleado_contexto_id > 0,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(
                        "user-round",
                        size=16,
                        color=f"var(--{Colors.PORTAL_ACCENT_SCHEME}-9)",
                    ),
                    rx.text(
                        IncapacidadState.empleado_contexto_nombre,
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_SEMIBOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    rx.cond(
                        IncapacidadState.empleado_contexto_clave != "",
                        rx.badge(
                            IncapacidadState.empleado_contexto_clave,
                            variant="outline",
                            size="1",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.cond(
                    IncapacidadState.contexto_empleado_resumen != "",
                    rx.text(
                        IncapacidadState.contexto_empleado_resumen,
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.text(
                        "Se resolverá el contexto laboral vigente al guardar.",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                ),
                spacing="2",
                width="100%",
                align="start",
            ),
            width="100%",
            padding=Spacing.MD,
            background=Colors.SECONDARY_LIGHT,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
        ),
        rx.fragment(),
    )


def modal_registro_incapacidad() -> rx.Component:
    return modal_formulario(
        open=IncapacidadState.modal_abierto,
        titulo="Registrar incapacidad",
        descripcion=_descripcion_modal(),
        icono="heart-pulse",
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
        color_guardar=Colors.PORTAL_ACCENT_SCHEME,
        texto_guardar="Registrar incapacidad",
        texto_guardando="Registrando...",
        on_guardar=IncapacidadState.guardar_incapacidad,
        on_cancelar=IncapacidadState.cerrar_modal_registro,
        puede_guardar=IncapacidadState.puede_guardar_incapacidad,
        loading=IncapacidadState.form_saving,
        max_width="640px",
        contenido=rx.vstack(
            rx.cond(
                IncapacidadState.form_error != "",
                feedback_callout(
                    IncapacidadState.form_error,
                    "error",
                ),
                rx.fragment(),
            ),
            feedback_callout(
                "El registro se sincronizará con asistencias y nómina en cada fecha del rango capturado.",
                "info",
            ),
            _selector_empleado_modal(),
            _resumen_contexto_modal(),
            rx.cond(
                IncapacidadState.contexto_empleado_error != "",
                feedback_callout(
                    IncapacidadState.contexto_empleado_error,
                    "error",
                ),
                rx.fragment(),
            ),
            form_select(
                label="Origen",
                required=True,
                placeholder="Seleccione origen",
                value=IncapacidadState.form_origen,
                on_change=IncapacidadState.set_form_origen,
                options=[
                    {
                        "value": OrigenIncapacidad.FORMAL.value,
                        "label": OrigenIncapacidad.FORMAL.descripcion,
                    },
                    {
                        "value": OrigenIncapacidad.POR_ACUERDO.value,
                        "label": OrigenIncapacidad.POR_ACUERDO.descripcion,
                    },
                ],
                label_variant="portal",
                style_variant="portal",
            ),
            form_select(
                label="Tipo de incapacidad",
                required=True,
                placeholder="Seleccione tipo",
                value=IncapacidadState.form_tipo,
                on_change=IncapacidadState.set_form_tipo,
                options=IncapacidadState.tipos_disponibles,
                label_variant="portal",
                style_variant="portal",
            ),
            rx.grid(
                form_date(
                    label="Fecha de inicio",
                    required=True,
                    value=IncapacidadState.form_fecha_inicio,
                    on_change=IncapacidadState.set_form_fecha_inicio,
                    label_variant="portal",
                ),
                form_date(
                    label="Fecha fin estimada",
                    value=IncapacidadState.form_fecha_fin_estimada,
                    on_change=IncapacidadState.set_form_fecha_fin_estimada,
                    hint="Puede dejarse vacía si capturará los días del certificado.",
                    label_variant="portal",
                ),
                columns=rx.breakpoints(initial="1", sm="2"),
                spacing="3",
                width="100%",
            ),
            rx.cond(
                IncapacidadState.es_formal,
                form_input(
                    label="Folio IMSS",
                    required=True,
                    placeholder="Folio del certificado",
                    value=IncapacidadState.form_folio_imss,
                    on_change=IncapacidadState.set_form_folio_imss,
                    label_variant="portal",
                    style_variant="portal",
                ),
                rx.fragment(),
            ),
            rx.grid(
                form_input(
                    label="Días del certificado",
                    placeholder="Ej. 3",
                    type="number",
                    min="1",
                    value=IncapacidadState.form_dias_certificado,
                    on_change=IncapacidadState.set_form_dias_certificado,
                    hint="Si no captura fecha fin, se calculará con este dato.",
                    label_variant="portal",
                    style_variant="portal",
                ),
                rx.cond(
                    IncapacidadState.es_por_acuerdo,
                    form_input(
                        label="% de pago empresa",
                        placeholder="100",
                        type="number",
                        min="0",
                        max="100",
                        step="0.01",
                        value=IncapacidadState.form_porcentaje_pago,
                        on_change=IncapacidadState.set_form_porcentaje_pago,
                        label_variant="portal",
                        style_variant="portal",
                    ),
                    rx.box(width="100%"),
                ),
                columns=rx.breakpoints(initial="1", sm="2"),
                spacing="3",
                width="100%",
            ),
            rx.vstack(
                rx.checkbox(
                    "Requiere cobertura temporal",
                    checked=IncapacidadState.form_requiere_cobertura,
                    on_change=IncapacidadState.set_form_requiere_cobertura,
                    size="2",
                ),
                rx.text(
                    "Por ahora solo se registra la bandera; la asignación de cobertura se implementará en una fase posterior.",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="1",
                width="100%",
                align="start",
            ),
            form_textarea(
                label="Notas",
                placeholder="Observaciones adicionales",
                value=IncapacidadState.form_notas,
                on_change=IncapacidadState.set_form_notas,
                label_variant="portal",
                style_variant="portal",
                rows="4",
            ),
            spacing="4",
            width="100%",
        ),
    )
