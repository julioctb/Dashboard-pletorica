from typing import Any

import reflex as rx

from core.core.ui_options import ESTADOS_DISPLAY, TIPO_SALARIO_CALCULO
from core.presentation.components.ui import form_input, form_select
from core.presentation.layouts.backoffice import page_header, page_layout
from core.presentation.pages.backoffice.simulador.simulador_state import SimuladorState
from core.presentation.theme import (
    ButtonStyles,
    CardStyles,
    Colors,
    Radius,
    Spacing,
    Typography,
)


OPCIONES_ESTADOS = [{"value": valor, "label": valor} for valor in ESTADOS_DISPLAY.values()]
OPCIONES_TIPO_CALCULO = [{"value": valor, "label": valor} for valor in TIPO_SALARIO_CALCULO.values()]

MAX_CONTENT_WIDTH = "720px"
DETAIL_VALUE_MIN_WIDTH = "96px"

SECTION_STYLE = {
    **CardStyles.BASE,
    "padding": Spacing.BASE,
    "width": "100%",
}

SUMMARY_CARD_STYLE = {
    "background": Colors.SECONDARY_LIGHT,
    "border_radius": Radius.LG,
    "padding": Spacing.BASE,
    "width": "100%",
    "text_align": "center",
}

BREAKDOWN_CARD_STYLE = {
    **CardStyles.BASE,
    "padding": "0",
    "overflow": "hidden",
    "width": "100%",
}


def _conditional_value(condition: Any, when_true: str, when_false: str) -> Any:
    if isinstance(condition, bool):
        return when_true if condition else when_false
    return rx.cond(condition, when_true, when_false)

def _field_input(
    *,
    label: str,
    value: Any,
    on_change,
    placeholder: str,
    hint: str = "",
    flex: str,
    min_width: str,
    disabled: Any = False,
    **props,
) -> rx.Component:
    return rx.box(
        form_input(
            label=label,
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            disabled=disabled,
            hint=hint,
            label_variant="wizard",
            spacing="1",
            style={
                "background": _conditional_value(disabled, Colors.SECONDARY_LIGHT, Colors.SURFACE),
                "color": _conditional_value(disabled, Colors.TEXT_SECONDARY, Colors.TEXT_PRIMARY),
                "opacity": "1",
            },
            **props,
        ),
        flex=flex,
        min_width=min_width,
        width="100%",
    )


def _field_select(
    *,
    label: str,
    value: Any,
    on_change,
    placeholder: str,
    options: list[dict[str, str]],
    hint: str = "",
    flex: str,
    min_width: str,
) -> rx.Component:
    return rx.box(
        form_select(
            label=label,
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            options=options,
            hint=hint,
            label_variant="wizard",
            spacing="1",
        ),
        flex=flex,
        min_width=min_width,
        width="100%",
    )


def _section_card(title: str, *children: rx.Component) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(
                title,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                line_height=Typography.LINE_HEIGHT_TIGHT,
            ),
            *children,
            width="100%",
            align_items="stretch",
            gap=Spacing.MD,
        ),
        style=SECTION_STYLE,
    )


def formulario_empresa() -> rx.Component:
    """Seccion de configuracion de empresa."""
    return _section_card(
        "Configuracion empresa",
        rx.flex(
            _field_select(
                label="Estado",
                placeholder="Selecciona un estado",
                value=SimuladorState.estado_display,
                on_change=SimuladorState.set_estado_display,
                options=OPCIONES_ESTADOS,
                flex="1 1 240px",
                min_width="240px",
            ),
            _field_input(
                label="Prima de riesgo (%)",
                placeholder="2.5984",
                value=SimuladorState.prima_riesgo.to(str),
                on_change=SimuladorState.set_prima_riesgo,
                hint="Segun giro de la empresa",
                type="number",
                step="0.0001",
                flex="1 1 240px",
                min_width="240px",
            ),
            width="100%",
            wrap="wrap",
            column_gap=Spacing.MD,
            row_gap=Spacing.MD,
        ),
    )


def formulario_prestaciones() -> rx.Component:
    """Seccion de prestaciones."""
    return _section_card(
        "Prestaciones",
        rx.flex(
            _field_input(
                label="Dias de aguinaldo",
                placeholder="15",
                value=SimuladorState.dias_aguinaldo.to(str),
                on_change=SimuladorState.set_dias_aguinaldo,
                hint="Minimo legal: 15 dias",
                type="number",
                flex="1 1 240px",
                min_width="240px",
            ),
            _field_input(
                label="Prima vacacional (%)",
                placeholder="25",
                value=SimuladorState.prima_vacacional.to(str),
                on_change=SimuladorState.set_prima_vacacional,
                hint="Minimo legal: 25%",
                type="number",
                flex="1 1 240px",
                min_width="240px",
            ),
            width="100%",
            wrap="wrap",
            column_gap=Spacing.MD,
            row_gap=Spacing.MD,
        ),
    )


def formulario_trabajador() -> rx.Component:
    """Seccion de parametros del trabajador."""
    return _section_card(
        "Parametros del trabajador",
        rx.vstack(
            rx.flex(
                _field_select(
                    label="Tipo de calculo",
                    placeholder="Selecciona un tipo",
                    value=SimuladorState.tipo_salario_calculo,
                    on_change=SimuladorState.set_tipo_salario_calculo,
                    options=OPCIONES_TIPO_CALCULO,
                    flex="1 1 180px",
                    min_width="180px",
                ),
                _field_input(
                    label="Salario mensual ($)",
                    placeholder="0.00",
                    value=SimuladorState.salario_mensual,
                    on_change=SimuladorState.set_salario_mensual,
                    disabled=(
                        (SimuladorState.tipo_salario_calculo == "Salario Mínimo")
                        | (SimuladorState.tipo_salario_calculo == "")
                    ),
                    type="number",
                    step="0.01",
                    flex="1 1 180px",
                    min_width="180px",
                ),
                _field_input(
                    label="Salario diario ($)",
                    placeholder="0.00",
                    value=SimuladorState.calc_salario_diario,
                    on_change=SimuladorState.noop,
                    hint="Calculado automaticamente",
                    disabled=True,
                    type="number",
                    step="0.01",
                    flex="1 1 180px",
                    min_width="180px",
                ),
                width="100%",
                wrap="wrap",
                column_gap=Spacing.MD,
                row_gap=Spacing.MD,
            ),
            rx.flex(
                _field_input(
                    label="Antiguedad (anos)",
                    placeholder="1",
                    value=SimuladorState.antiguedad_anos.to(str),
                    on_change=SimuladorState.set_antiguedad_anos,
                    hint="Minimo 1 ano",
                    type="number",
                    min="1",
                    flex="1 1 240px",
                    min_width="240px",
                ),
                _field_input(
                    label="Dias cotizados",
                    placeholder="30",
                    value=SimuladorState.dias_cotizados.to(str),
                    on_change=SimuladorState.set_dias_cotizados,
                    hint="Dias del mes a cotizar",
                    type="number",
                    step="0.1",
                    flex="1 1 240px",
                    min_width="240px",
                ),
                width="100%",
                wrap="wrap",
                column_gap=Spacing.MD,
                row_gap=Spacing.MD,
            ),
            width="100%",
            gap=Spacing.MD,
        ),
    )


def acciones_simulador() -> rx.Component:
    """Botones de accion con jerarquia visual clara."""
    return rx.flex(
        rx.button(
            "Calcular",
            on_click=SimuladorState.calcular,
            loading=SimuladorState.is_calculating,
            style={
                **ButtonStyles.PRIMARY,
                "padding_x": Spacing.LG,
                "padding_y": Spacing.SM,
            },
        ),
        rx.button(
            "Limpiar",
            on_click=SimuladorState.limpiar,
            variant="ghost",
            style={
                **ButtonStyles.GHOST,
                "color": Colors.TEXT_SECONDARY,
                "padding_x": Spacing.SM,
                "padding_y": Spacing.SM,
            },
        ),
        width="100%",
        wrap="wrap",
        align="center",
        column_gap=Spacing.SM,
        row_gap=Spacing.SM,
        margin_top=Spacing.BASE,
        margin_bottom=Spacing.LG,
    )


def metric_card_resumen(label: str, value: Any) -> rx.Component:
    """Card compacta para metricas principales."""
    return rx.box(
        rx.vstack(
            rx.text(
                label,
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing=Typography.LETTER_SPACING_WIDE,
                line_height=Typography.LINE_HEIGHT_TIGHT,
            ),
            rx.text(
                value,
                font_size=Typography.SIZE_2XL,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                font_variant_numeric="tabular-nums",
                letter_spacing=Typography.LETTER_SPACING_TIGHT,
                line_height="1",
            ),
            width="100%",
            align="center",
            gap=Spacing.SM,
        ),
        style=SUMMARY_CARD_STYLE,
        flex="1 1 200px",
        min_width="200px",
    )


def resumen_destacado() -> rx.Component:
    """Resumen ejecutivo posterior al calculo."""
    return rx.cond(
        SimuladorState.calculado,
        rx.flex(
            metric_card_resumen("Costo patronal", SimuladorState.resultado["total_carga_patronal"]),
            metric_card_resumen("Neto trabajador", SimuladorState.resultado["salario_neto"]),
            metric_card_resumen("Costo total empresa", SimuladorState.resultado["costo_total"]),
            width="100%",
            wrap="wrap",
            column_gap=Spacing.MD,
            row_gap=Spacing.MD,
        ),
        rx.fragment(),
    )


def desglose_header(title: str) -> rx.Component:
    return rx.box(
        rx.text(
            title,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_SECONDARY,
            text_transform="uppercase",
            letter_spacing=Typography.LETTER_SPACING_WIDE,
            line_height=Typography.LINE_HEIGHT_TIGHT,
        ),
        width="100%",
        padding_x=Spacing.BASE,
        padding_y=Spacing.MD,
        border_bottom=f"1px solid {Colors.BORDER}",
    )


def desglose_row(
    label: str,
    value: Any,
    *,
    is_total: bool = False,
) -> rx.Component:
    label_color = Colors.TEXT_PRIMARY if is_total else Colors.TEXT_SECONDARY
    weight = Typography.WEIGHT_MEDIUM if is_total else Typography.WEIGHT_REGULAR
    border_color = Colors.BORDER_STRONG if is_total else Colors.BORDER
    return rx.flex(
        rx.text(
            label,
            font_size=Typography.SIZE_SM,
            font_weight=weight,
            color=label_color,
            line_height=Typography.LINE_HEIGHT_TIGHT,
        ),
        rx.text(
            value,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_PRIMARY,
            text_align="right",
            font_variant_numeric="tabular-nums",
            min_width=DETAIL_VALUE_MIN_WIDTH,
            line_height=Typography.LINE_HEIGHT_TIGHT,
        ),
        width="100%",
        justify="between",
        align="center",
        padding_x=Spacing.BASE,
        padding_y=Spacing.SM,
        border_bottom=f"1px solid {border_color}",
        column_gap=Spacing.MD,
    )


def desglose_grupo(title: str, *rows: rx.Component) -> rx.Component:
    return rx.vstack(
        desglose_header(title),
        *rows,
        width="100%",
        spacing="0",
        align_items="stretch",
    )


def desglose_detallado() -> rx.Component:
    """Lista agrupada de conceptos."""
    return rx.cond(
        SimuladorState.calculado,
        rx.vstack(
            rx.text(
                "Desglose detallado",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                line_height=Typography.LINE_HEIGHT_TIGHT,
            ),
            rx.card(
                rx.vstack(
                    desglose_grupo(
                        "Salarios",
                        desglose_row("Factor de integracion", SimuladorState.resultado["factor_integracion"]),
                        desglose_row("SBC diario", SimuladorState.resultado["sbc_diario"]),
                        desglose_row("Salario diario", SimuladorState.resultado["salario_diario"]),
                        desglose_row("Salario mensual", SimuladorState.resultado["salario_mensual"], is_total=True),
                    ),
                    desglose_grupo(
                        "IMSS patronal",
                        desglose_row("Cuota fija", SimuladorState.resultado["imss_cuota_fija"]),
                        desglose_row("Excedente", SimuladorState.resultado["imss_excedente_pat"]),
                        desglose_row("Prest. en dinero", SimuladorState.resultado["imss_prest_dinero_pat"]),
                        desglose_row("Gastos medicos", SimuladorState.resultado["imss_gastos_med_pens_pat"]),
                        desglose_row("Invalidez y vida", SimuladorState.resultado["imss_invalidez_vida_pat"]),
                        desglose_row("Guarderias", SimuladorState.resultado["imss_guarderias"]),
                        desglose_row("Retiro", SimuladorState.resultado["imss_retiro"]),
                        desglose_row("Cesantia y vejez", SimuladorState.resultado["imss_cesantia_vejez_pat"]),
                        desglose_row("Riesgo de trabajo", SimuladorState.resultado["imss_riesgo_trabajo"]),
                        desglose_row("Total IMSS patronal", SimuladorState.resultado["total_imss_patronal"], is_total=True),
                    ),
                    rx.cond(
                        SimuladorState.resultado.get("es_salario_minimo", False),
                        desglose_row(
                            "IMSS obrero absorbido (Art. 36 LSS)",
                            SimuladorState.resultado["imss_obrero_absorbido"],
                            is_total=True,
                        ),
                        rx.fragment(),
                    ),
                    desglose_row("Infonavit (5%)", SimuladorState.resultado["infonavit"]),
                    desglose_row("ISN", SimuladorState.resultado["isn"]),
                    desglose_grupo(
                        "Provisiones mensuales",
                        desglose_row("Aguinaldo", SimuladorState.resultado["provision_aguinaldo"]),
                        desglose_row("Vacaciones", SimuladorState.resultado["provision_vacaciones"]),
                        desglose_row("Prima vacacional", SimuladorState.resultado["provision_prima_vac"]),
                        desglose_row("Total provisiones", SimuladorState.resultado["total_provisiones"], is_total=True),
                    ),
                    desglose_grupo(
                        "Descuentos al trabajador",
                        desglose_row("IMSS obrero", SimuladorState.resultado["total_imss_obrero"]),
                        desglose_row("ISR a retener", SimuladorState.resultado["isr_a_retener"]),
                        desglose_row(
                            "Total descuentos",
                            SimuladorState.resultado["total_descuentos_trabajador"],
                            is_total=True,
                        ),
                    ),
                    width="100%",
                    spacing="0",
                    align_items="stretch",
                ),
                style=BREAKDOWN_CARD_STYLE,
            ),
            width="100%",
            align_items="stretch",
            gap=Spacing.SM,
        ),
        rx.fragment(),
    )


def simulador_page() -> rx.Component:
    """Pagina del simulador del costo patronal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Simulador de Costo Patronal",
                subtitulo="Configure parametros y revise el desglose del costo patronal",
                icono="calculator",
                accion_principal=rx.badge(
                    "2026",
                    color_scheme="blue",
                    variant="soft",
                    size="1",
                ),
            ),
            content=rx.vstack(
                formulario_empresa(),
                formulario_prestaciones(),
                formulario_trabajador(),
                acciones_simulador(),
                resumen_destacado(),
                desglose_detallado(),
                width="100%",
                max_width=MAX_CONTENT_WIDTH,
                margin_x="auto",
                align_items="stretch",
                gap=Spacing.MD,
            ),
        ),
        on_mount=SimuladorState.on_mount_simulador,
        width="100%",
    )
