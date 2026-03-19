"""Componentes UI para la pagina unificada de Empleados en portal."""

import reflex as rx

from app.core.enums import EstatusPlaza
from app.presentation.components.ui import (
    empty_state_card,
    employee_status_badge,
    filter_pill,
    metric_card,
    segmented_tab_trigger,
    segmented_tabs,
    select_items_from_options,
    status_badge_reactive,
    tabla_cta_button,
    table_cell_actions,
    table_cell_badge,
    table_cell_text_sm,
    table_pagination,
    table_shell,
    table_text_sm,
)
from app.presentation.theme import Colors, Radius, Spacing, StatusColors, Typography

from .state import MisEmpleadosState, VISTA_PERSONAL_EMPLEADO, VISTA_PERSONAL_PLAZA


def _celda_centrada(component: rx.Component) -> rx.Component:
    return rx.table.cell(
        rx.center(
            component,
            width="100%",
        ),
    )


def _celda_dos_lineas(
    principal,
    secundario="",
    *,
    tone: str = "primary",
    fallback: str = "—",
) -> rx.Component:
    return rx.table.cell(
        rx.cond(
            principal != "",
            rx.vstack(
                table_text_sm(
                    principal,
                    weight=Typography.WEIGHT_MEDIUM,
                    tone=tone,
                ),
                rx.cond(
                    secundario != "",
                    table_text_sm(
                        secundario,
                        tone="muted",
                    ),
                    rx.fragment(),
                ),
                spacing="0",
                align="start",
                width="100%",
            ),
            table_text_sm(fallback, tone="muted"),
        ),
    )


def metricas_empleados() -> rx.Component:
    return rx.grid(
        metric_card(
            titulo="Plazas totales",
            valor=MisEmpleadosState.metrica_plazas_totales,
            icono=None,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            align="center",
            footer=rx.text(
                MisEmpleadosState.metrica_hint_plazas,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
        ),
        metric_card(
            titulo="Ocupadas",
            valor=MisEmpleadosState.metrica_plazas_ocupadas,
            icono=None,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            value_color=Colors.SUCCESS,
            align="center",
            footer=rx.text(
                MisEmpleadosState.metrica_hint_cobertura,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
        ),
        metric_card(
            titulo="Vacantes",
            valor=MisEmpleadosState.metrica_plazas_vacantes,
            icono=None,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            value_color=Colors.INFO,
            align="center",
        ),
        metric_card(
            titulo="Propuestas por alta",
            valor=MisEmpleadosState.metrica_propuestas_alta,
            icono=None,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            value_color=Colors.WARNING,
            align="center",
            footer=rx.text(
                MisEmpleadosState.metrica_hint_propuestas,
                font_size=Typography.SIZE_XS,
                color=Colors.WARNING,
            ),
        ),
        metric_card(
            titulo="Suspendidas",
            valor=MisEmpleadosState.metrica_plazas_suspendidas,
            icono=None,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            align="center",
        ),
        columns=rx.breakpoints(initial="2", sm="3", md="5"),
        spacing="3",
        width="100%",
    )


def selector_vista_personal() -> rx.Component:
    return segmented_tabs(
        segmented_tab_trigger(
            "Por empleado",
            VISTA_PERSONAL_EMPLEADO,
            active_background=Colors.PORTAL_PRIMARY,
            active_hover_background=Colors.PORTAL_PRIMARY_HOVER,
        ),
        segmented_tab_trigger(
            "Por plaza",
            VISTA_PERSONAL_PLAZA,
            active_background=Colors.PORTAL_PRIMARY,
            active_hover_background=Colors.PORTAL_PRIMARY_HOVER,
        ),
        value=MisEmpleadosState.vista_personal,
        on_change=MisEmpleadosState.set_vista_personal,
    )


def filtros_estatus_empleados() -> rx.Component:
    return rx.flex(
        filter_pill(
            "Todos",
            MisEmpleadosState.stats_total.to(str),
            MisEmpleadosState.filtrar_todos,
            MisEmpleadosState.filtro_es_todos,
        ),
        filter_pill(
            "Activos",
            MisEmpleadosState.stats_activos.to(str),
            MisEmpleadosState.filtrar_activos,
            MisEmpleadosState.filtro_es_activos,
            Colors.SUCCESS,
        ),
        filter_pill(
            "En alta",
            MisEmpleadosState.stats_en_alta.to(str),
            MisEmpleadosState.filtrar_en_alta,
            MisEmpleadosState.filtro_es_en_alta,
            Colors.WARNING,
        ),
        filter_pill(
            "Suspendidos",
            MisEmpleadosState.stats_suspendidos.to(str),
            MisEmpleadosState.filtrar_suspendidos,
            MisEmpleadosState.filtro_es_suspendidos,
            Colors.TEXT_MUTED,
        ),
        filter_pill(
            "En baja",
            MisEmpleadosState.stats_en_baja.to(str),
            MisEmpleadosState.filtrar_en_baja,
            MisEmpleadosState.filtro_es_en_baja,
            Colors.ERROR,
        ),
        wrap="wrap",
        gap=Spacing.SM,
        width="100%",
    )


def filtro_contrato_empleados() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(
            placeholder="Todos los contratos",
            width="260px",
        ),
        rx.select.content(
            select_items_from_options(MisEmpleadosState.opciones_contratos_activos),
        ),
        value=MisEmpleadosState.filtro_contrato_id,
        on_change=MisEmpleadosState.set_filtro_contrato_id,
        size="2",
    )


def _celda_texto_centrada(
    valor,
    *,
    color: str = Colors.TEXT_SECONDARY,
    fallback: str = "—",
    font_variant_numeric: str | None = None,
) -> rx.Component:
    texto_props = {
        "font_size": Typography.SIZE_XS,
        "color": color,
    }
    if font_variant_numeric is not None:
        texto_props["font_variant_numeric"] = font_variant_numeric

    fallback_props = dict(texto_props)
    fallback_props["color"] = Colors.TEXT_MUTED

    return rx.table.cell(
        rx.cond(
            valor != "",
            rx.text(valor, **texto_props),
            rx.text(fallback, **fallback_props),
        ),
        text_align="center",
    )


def _docs_color_texto(tone) -> rx.Var | str:
    return rx.match(
        tone,
        ("success", Colors.SUCCESS),
        ("warning", Colors.WARNING),
        Colors.TEXT_MUTED,
    )


def _docs_color_barra(tone) -> rx.Var | str:
    return rx.match(
        tone,
        ("success", Colors.SUCCESS),
        ("warning", Colors.WARNING),
        Colors.BORDER,
    )


def _docs_cell(emp: dict) -> rx.Component:
    docs_tone = emp.get("docs_tone", "muted")
    return rx.table.cell(
        rx.center(
            rx.flex(
                rx.text(
                    emp.get("docs_resumen_ui", "0/0"),
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    font_variant_numeric="tabular-nums",
                    color=_docs_color_texto(docs_tone),
                ),
                rx.box(
                    rx.box(
                        width=emp.get("docs_porcentaje_ui", "0%"),
                        height="100%",
                        border_radius=Radius.FULL,
                        background=_docs_color_barra(docs_tone),
                    ),
                    width=Spacing.XXL,
                    height=Spacing.XS,
                    background=Colors.SECONDARY_LIGHT,
                    border_radius=Radius.FULL,
                    overflow="hidden",
                ),
                align="center",
                justify="center",
                gap=Spacing.XS,
                width="100%",
                cursor="pointer",
                on_click=MisEmpleadosState.ver_expediente(emp),
            ),
            width="100%",
        ),
        text_align="center",
    )


def _accion_empleado(emp: dict) -> rx.Component:
    on_click_editar = MisEmpleadosState.abrir_modal_editar(emp)
    on_click_detalle = MisEmpleadosState.ver_expediente(emp)
    on_click_baja = MisEmpleadosState.ver_baja_empleado(emp)
    accion_ver_perfil = tabla_cta_button(
        "Ver perfil",
        on_click_detalle,
        color_scheme=Colors.NEUTRAL_SCHEME,
    )
    accion_ver_y_editar = rx.cond(
        MisEmpleadosState.puede_gestionar_personal,
        rx.hstack(
            accion_ver_perfil,
            tabla_cta_button(
                "Editar",
                on_click_editar,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            spacing="1",
            align="center",
            justify="center",
            wrap="wrap",
        ),
        accion_ver_perfil,
    )
    return rx.match(
        emp.get("estatus_personal", ""),
        (
            "INACTIVO",
            tabla_cta_button(
                "Completar datos",
                on_click_editar,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
        ),
        (
            "EN_ALTA",
            tabla_cta_button(
                "Completar datos",
                on_click_editar,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
        ),
        (
            "BAJA",
            tabla_cta_button(
                "Ver baja",
                on_click_baja,
                color_scheme=Colors.WARNING_SCHEME,
            ),
        ),
        (
            "EN_BAJA",
            tabla_cta_button(
                "Ver baja",
                on_click_baja,
                color_scheme=Colors.WARNING_SCHEME,
            ),
        ),
        (
            "ACTIVO",
            accion_ver_y_editar,
        ),
        (
            "SUSPENDIDO",
            accion_ver_y_editar,
        ),
        accion_ver_perfil,
    )


def fila_empleado(emp: dict) -> rx.Component:
    return rx.table.row(
        _celda_dos_lineas(
            emp.get("nombre_completo_ui", ""),
            emp.get("contacto_secundario_ui", ""),
            fallback="Sin nombre",
        ),
        _celda_texto_centrada(
            emp.get("contrato_codigo", ""),
        ),
        _celda_texto_centrada(
            emp.get("categoria_nombre", ""),
        ),
        _celda_texto_centrada(
            emp.get("sede_nombre_ui", ""),
            color=Colors.TEXT_PRIMARY,
        ),
        _celda_texto_centrada(
            emp.get("telefono_ui", ""),
            color=Colors.TEXT_SECONDARY,
            font_variant_numeric="tabular-nums",
        ),
        rx.table.cell(
            rx.center(
                employee_status_badge(emp.get("estatus_personal", "")),
                width="100%",
            ),
            text_align="center",
        ),
        _docs_cell(emp),
        rx.table.cell(
            rx.center(
                _accion_empleado(emp),
                width="100%",
            ),
            text_align="center",
        ),
    )


ENCABEZADOS_EMPLEADOS = [
    {"nombre": "Nombre", "ancho": "220px", "header_align": "left"},
    {"nombre": "Contrato", "ancho": "120px", "header_align": "center"},
    {"nombre": "Categoría", "ancho": "120px", "header_align": "center"},
    {"nombre": "Sede", "ancho": "140px", "header_align": "center"},
    {"nombre": "Teléfono", "ancho": "120px", "header_align": "center"},
    {"nombre": "Estatus", "ancho": "90px", "header_align": "center"},
    {"nombre": "Docs", "ancho": "80px", "header_align": "center"},
    {"nombre": "Acción", "ancho": "120px", "header_align": "center"},
]


def _table_headers_empleados() -> list[rx.Component]:
    return [
        rx.table.column_header_cell(
            rx.text(
                col["nombre"],
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_SECONDARY,
                text_transform="uppercase",
                letter_spacing="0.04em",
            ),
            width=col.get("ancho", "auto"),
            text_align=col.get("header_align", "left"),
        )
        for col in ENCABEZADOS_EMPLEADOS
    ]


def tabla_empleados() -> rx.Component:
    return table_shell(
        loading=MisEmpleadosState.loading,
        headers=ENCABEZADOS_EMPLEADOS,
        header_cells=_table_headers_empleados(),
        rows=MisEmpleadosState.empleados_paginados,
        row_renderer=fila_empleado,
        has_rows=MisEmpleadosState.total_empleados_filtrados > 0,
        empty_component=empty_state_card(
            title="No hay empleados para este filtro",
            description="Ajuste la búsqueda, cambie el contrato o registre un nuevo empleado.",
            icon="users",
            action_button=rx.button(
                rx.icon("plus", size=16),
                "Nuevo empleado",
                on_click=MisEmpleadosState.abrir_modal_crear,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                variant="soft",
            ),
        ),
        total_caption=MisEmpleadosState.resumen_paginacion_empleados,
        footer_component=table_pagination(
            current_page=MisEmpleadosState.pagina_empleados_actual,
            total_pages=MisEmpleadosState.total_paginas_empleados,
            page_numbers=MisEmpleadosState.paginas_visibles_empleados,
            on_page_change=MisEmpleadosState.ir_a_pagina,
            on_previous=MisEmpleadosState.pagina_anterior,
            on_next=MisEmpleadosState.pagina_siguiente,
            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
        ),
        loading_rows=5,
        table_size="1",
    )


def _badge_resumen_contrato(texto, color_scheme: str) -> rx.Component:
    return rx.badge(
        texto,
        color_scheme=color_scheme,
        variant="soft",
        size="1",
    )


def _badge_estado_plaza(estatus) -> rx.Component:
    return rx.match(
        estatus,
        (
            EstatusPlaza.OCUPADA.value,
            rx.badge("Ocupada", color_scheme=StatusColors.OCUPADA_SCHEME, variant="soft", size="1"),
        ),
        (
            EstatusPlaza.VACANTE.value,
            rx.badge("Vacante", color_scheme=StatusColors.VACANTE_SCHEME, variant="soft", size="1"),
        ),
        (
            EstatusPlaza.SUSPENDIDA.value,
            rx.badge("Suspendida", color_scheme=StatusColors.SUSPENDIDA_SCHEME, variant="soft", size="1"),
        ),
        rx.badge("Sin estatus", color_scheme=Colors.NEUTRAL_SCHEME, variant="soft", size="1"),
    )


def _borde_izquierdo_plaza(estatus) -> rx.Var | str:
    return rx.match(
        estatus,
        (
            EstatusPlaza.OCUPADA.value,
            f"3px solid {Colors.SUCCESS}",
        ),
        (
            EstatusPlaza.VACANTE.value,
            f"3px solid {Colors.INFO}",
        ),
        f"3px solid {Colors.TEXT_MUTED}",
    )


def _accion_plaza(plaza: dict) -> rx.Component:
    return rx.match(
        plaza.get("estatus", ""),
        (
            EstatusPlaza.OCUPADA.value,
            rx.hstack(
                tabla_cta_button(
                    "Ver perfil",
                    MisEmpleadosState.ver_perfil_plaza(plaza),
                    color_scheme=Colors.NEUTRAL_SCHEME,
                ),
                tabla_cta_button(
                    "Reasignar",
                    MisEmpleadosState.abrir_modal_asignacion_plaza(plaza),
                ),
                spacing="1",
                align="center",
                justify="center",
                wrap="wrap",
            ),
        ),
        (
            EstatusPlaza.VACANTE.value,
            tabla_cta_button(
                "Asignar",
                MisEmpleadosState.abrir_modal_asignacion_plaza(plaza),
                color_scheme="blue",
                variant="soft",
                style={
                    "background": Colors.INFO_LIGHT,
                    "color": Colors.INFO,
                    "border": "none",
                },
            ),
        ),
        (
            EstatusPlaza.SUSPENDIDA.value,
            tabla_cta_button(
                "Reactivar",
                MisEmpleadosState.reactivar_plaza_portal(plaza),
                color_scheme=Colors.WARNING_SCHEME,
            ),
        ),
        tabla_cta_button(
            "Ver",
            MisEmpleadosState.abrir_modal_asignacion_plaza(plaza),
        ),
    )


def fila_plaza(plaza: dict, contrato_id) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.center(
                rx.checkbox(
                    checked=plaza.get("seleccionada", False),
                    on_change=lambda checked: MisEmpleadosState.toggle_plaza_seleccionada(
                        contrato_id,
                        plaza.get("id"),
                        checked,
                    ),
                    size="1",
                ),
                width="100%",
            ),
        ),
        _celda_centrada(
            table_text_sm(
                plaza.get("numero_plaza", ""),
                tone="muted",
                font_variant_numeric="tabular-nums",
            ),
        ),
        table_cell_text_sm(
            plaza.get("categoria_nombre", ""),
            tone="secondary",
            fallback="—",
        ),
        rx.table.cell(
            table_text_sm(
                plaza.get("sede_display", ""),
                tone="secondary",
                fallback="sin sede",
            ),
        ),
        _celda_dos_lineas(
            plaza.get("empleado_nombre", ""),
            "",
            fallback="—",
        ),
        table_cell_badge(
            _badge_estado_plaza(plaza.get("estatus", "")),
        ),
        table_cell_actions(
            _accion_plaza(plaza),
        ),
        border_left=_borde_izquierdo_plaza(plaza.get("estatus", "")),
        background=rx.cond(
            plaza.get("seleccionada", False),
            Colors.PRIMARY_LIGHTER,
            Colors.SURFACE,
        ),
    )


ENCABEZADOS_PLAZAS = [
    {"nombre": "", "ancho": "36px", "header_align": "center"},
    {"nombre": "#", "ancho": "52px", "header_align": "center"},
    {"nombre": "Categoría", "ancho": "220px"},
    {"nombre": "Sede", "ancho": "220px"},
    {"nombre": "Empleado asignado", "ancho": "260px"},
    {"nombre": "Estado", "ancho": "140px"},
    {"nombre": "Acción", "ancho": "140px"},
]


def _barra_acciones_masivas(bloque: dict) -> rx.Component:
    return rx.cond(
        bloque.get("tiene_seleccion", False),
        rx.flex(
            table_text_sm(
                bloque.get("seleccion_label", ""),
                weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.flex(
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Asignar sede...",
                        width="180px",
                    ),
                    rx.select.content(
                        select_items_from_options(MisEmpleadosState.opciones_sedes_plaza),
                    ),
                    value=bloque.get("sede_masiva_value", ""),
                    on_change=lambda value: MisEmpleadosState.set_sede_masiva_contrato(
                        bloque.get("contrato_id"),
                        value,
                    ),
                    size="1",
                ),
                rx.button(
                    "Aplicar",
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                    on_click=MisEmpleadosState.aplicar_sede_masiva_contrato(
                        bloque.get("contrato_id"),
                    ),
                ),
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Cambiar categoria...",
                        width="220px",
                    ),
                    rx.select.content(
                        select_items_from_options(
                            MisEmpleadosState.opciones_categorias_masivas_actuales,
                        ),
                    ),
                    value=bloque.get("categoria_masiva_value", ""),
                    on_change=lambda value: MisEmpleadosState.set_categoria_masiva_contrato(
                        bloque.get("contrato_id"),
                        value,
                    ),
                    size="1",
                ),
                rx.button(
                    "Aplicar",
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                    on_click=MisEmpleadosState.aplicar_categoria_masiva_contrato(
                        bloque.get("contrato_id"),
                    ),
                ),
                rx.button(
                    "Deseleccionar",
                    size="1",
                    variant="ghost",
                    on_click=MisEmpleadosState.limpiar_seleccion_plazas(
                        bloque.get("contrato_id"),
                    ),
                ),
                wrap="wrap",
                justify="end",
                gap=Spacing.SM,
                flex="1",
            ),
            width="100%",
            justify="between",
            align="center",
            wrap="wrap",
            gap=Spacing.SM,
            padding_x=Spacing.MD,
            padding_y=Spacing.SM,
            background=Colors.PRIMARY_LIGHTER,
            border_radius=Radius.LG,
        ),
        rx.fragment(),
    )


def _encabezado_contrato_plaza(bloque: dict) -> rx.Component:
    return rx.flex(
        rx.hstack(
            rx.icon(
                "chevron-right",
                size=16,
                color=Colors.TEXT_MUTED,
                transform=bloque.get("rotacion_chevron", "rotate(0deg)"),
                transition="transform 0.2s",
            ),
            rx.vstack(
                table_text_sm(
                    bloque.get("contrato_codigo", "Sin contrato"),
                    weight=Typography.WEIGHT_MEDIUM,
                ),
                table_text_sm(
                    bloque.get("tipo_servicio_nombre", ""),
                    tone="muted",
                ),
                spacing="0",
                align="start",
            ),
            spacing="2",
            align="center",
        ),
        rx.flex(
            _badge_resumen_contrato(
                f"{bloque.get('plazas_ocupadas', 0)} ocupadas",
                StatusColors.OCUPADA_SCHEME,
            ),
            _badge_resumen_contrato(
                f"{bloque.get('plazas_vacantes', 0)} vacantes",
                StatusColors.VACANTE_SCHEME,
            ),
            rx.cond(
                bloque.get("mostrar_badge_suspendidas", False),
                _badge_resumen_contrato(
                    f"{bloque.get('plazas_suspendidas', 0)} suspendidas",
                    Colors.NEUTRAL_SCHEME,
                ),
                rx.fragment(),
            ),
            table_text_sm(
                bloque.get("resumen_plazas", ""),
                tone="muted",
            ),
            wrap="wrap",
            justify="end",
            gap=Spacing.SM,
            align="center",
        ),
        padding_x=Spacing.MD,
        padding_y=Spacing.SM,
        width="100%",
        justify="between",
        align="center",
        wrap="wrap",
        gap=Spacing.SM,
        cursor="pointer",
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        _hover={"background": Colors.SECONDARY_LIGHT},
        on_click=MisEmpleadosState.toggle_contrato_plaza(bloque.get("contrato_id")),
    )


def _tabla_contrato_plaza(bloque: dict) -> rx.Component:
    return rx.vstack(
        _barra_acciones_masivas(bloque),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(
                        rx.center(
                            rx.checkbox(
                                checked=bloque.get("seleccion_todas_visibles", False),
                                on_change=lambda checked: MisEmpleadosState.seleccionar_todas_plazas_visibles(
                                    bloque.get("contrato_id"),
                                    checked,
                                ),
                                size="1",
                            ),
                            width="100%",
                        ),
                        width="36px",
                        text_align="center",
                    ),
                    *[
                        rx.table.column_header_cell(
                            col["nombre"],
                            width=col["ancho"],
                            text_align=col.get("header_align", "left"),
                        )
                        for col in ENCABEZADOS_PLAZAS[1:]
                    ],
                ),
            ),
            rx.table.body(
                rx.foreach(
                    MisEmpleadosState.plazas_visibles_contrato_actual,
                    lambda plaza: fila_plaza(plaza, bloque.get("contrato_id")),
                ),
            ),
            width="100%",
            size="1",
            variant="surface",
        ),
        rx.vstack(
            table_text_sm(
                MisEmpleadosState.resumen_pagina_contrato_actual,
                tone="secondary",
            ),
            table_pagination(
                current_page=MisEmpleadosState.pagina_plaza_actual,
                total_pages=MisEmpleadosState.total_paginas_plaza_actual,
                page_numbers=MisEmpleadosState.page_numbers_plaza_actual,
                on_page_change=lambda page: MisEmpleadosState.ir_a_pagina_plaza_contrato(
                    bloque.get("contrato_id"),
                    page,
                ),
                on_previous=MisEmpleadosState.pagina_anterior_plaza_contrato(
                    bloque.get("contrato_id"),
                ),
                on_next=MisEmpleadosState.pagina_siguiente_plaza_contrato(
                    bloque.get("contrato_id"),
                ),
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            spacing="2",
            width="100%",
        ),
        spacing="2",
        width="100%",
    )


def _bloque_contrato_plaza(bloque: dict) -> rx.Component:
    return rx.vstack(
        _encabezado_contrato_plaza(bloque),
        rx.cond(
            bloque.get("expandido", False),
            rx.cond(
                bloque.get("cargando_plazas", False),
                rx.center(
                    rx.spinner(size="2"),
                    width="100%",
                    padding_y=Spacing.LG,
                ),
                rx.cond(
                    bloque.get("tiene_plazas_tabla", False),
                    _tabla_contrato_plaza(bloque),
                    empty_state_card(
                        title="Sin plazas para este contrato",
                        description="No hay plazas disponibles para mostrar con el filtro actual.",
                        icon="briefcase",
                    ),
                ),
            ),
            rx.fragment(),
        ),
        spacing="2",
        width="100%",
    )


def tabla_plazas_por_contrato() -> rx.Component:
    return rx.cond(
        MisEmpleadosState.loading,
        rx.center(
            rx.spinner(size="3"),
            width="100%",
            padding_y=Spacing.XL,
        ),
        rx.cond(
            MisEmpleadosState.tiene_plazas_visibles,
            rx.vstack(
                rx.foreach(
                    MisEmpleadosState.bloques_contrato_plaza,
                    _bloque_contrato_plaza,
                ),
                spacing="3",
                width="100%",
            ),
            empty_state_card(
                title="No hay plazas para este filtro",
                description="Ajuste la búsqueda o cambie el contrato para revisar la asignación de personal.",
                icon="briefcase",
            ),
        ),
    )
