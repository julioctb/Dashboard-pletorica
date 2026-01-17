import reflex as rx
from app.presentation.pages.simulador.simulador_state import SimuladorState
from app.presentation.components.ui.headers import page_header
from app.presentation.components.ui.form_field import form_field, form_section
from app.core.ui_options import ESTADOS_DISPLAY, TIPO_SALARIO_CALCULO
from app.core.validation import (
    CAMPO_SIM_ESTADO,
    CAMPO_SIM_PRIMA_RIESGO,
    CAMPO_SIM_DIAS_AGUINALDO,
    CAMPO_SIM_PRIMA_VACACIONAL,
    CAMPO_SIM_TIPO_CALCULO,
    CAMPO_SIM_SALARIO_MENSUAL,
    CAMPO_SIM_SALARIO_DIARIO,
    CAMPO_SIM_ANTIGUEDAD,
    CAMPO_SIM_DIAS_COTIZADOS,
)


def formulario_empresa() -> rx.Component:
    """Formulario de configuración de empresa"""
    return rx.card(
        rx.vstack(
            rx.heading("Configuración Empresa", size="4", margin_bottom="0.5em"),

            # Estado y Prima de riesgo
            rx.hstack(
                form_field(
                    config=CAMPO_SIM_ESTADO,
                    value=SimuladorState.estado,
                    on_change=SimuladorState.set_estado_display,
                    options=list(ESTADOS_DISPLAY.values()),
                    default_value="Puebla",
                ),
                form_field(
                    config=CAMPO_SIM_PRIMA_RIESGO,
                    value=SimuladorState.prima_riesgo.to(str),
                    on_change=SimuladorState.set_prima_riesgo,
                    step="0.0001",
                ),
                spacing="3",
                width="100%",
            ),

            rx.heading("Prestaciones", size="3", margin_top="0.5em"),

            # Días aguinaldo y Prima vacacional
            rx.hstack(
                form_field(
                    config=CAMPO_SIM_DIAS_AGUINALDO,
                    value=SimuladorState.dias_aguinaldo.to(str),
                    on_change=SimuladorState.set_dias_aguinaldo,
                ),
                form_field(
                    config=CAMPO_SIM_PRIMA_VACACIONAL,
                    value=SimuladorState.prima_vacacional.to(str),
                    on_change=SimuladorState.set_prima_vacacional,
                ),
                spacing="3",
                width="100%",
            ),

            spacing="2",
            width="100%",
        ),
        width="100%",
    )


def formulario_trabajador() -> rx.Component:
    """Formulario de datos del trabajador"""
    return rx.card(
        rx.vstack(
            rx.heading("Parámetros del Trabajador", size="4", margin_bottom="0.5em"),

            # Tipo de cálculo, Salario mensual, Salario diario
            rx.hstack(
                form_field(
                    config=CAMPO_SIM_TIPO_CALCULO,
                    value=SimuladorState.tipo_salario_calculo,
                    on_change=SimuladorState.set_tipo_salario_calculo,
                    options=list(TIPO_SALARIO_CALCULO.values()),
                ),
                form_field(
                    config=CAMPO_SIM_SALARIO_MENSUAL,
                    value=SimuladorState.salario_mensual,
                    on_change=SimuladorState.set_salario_mensual,
                    disabled=(
                        (SimuladorState.tipo_salario_calculo == "Salario Mínimo") |
                        (SimuladorState.tipo_salario_calculo == "")
                    ),
                    step="0.01",
                ),
                form_field(
                    config=CAMPO_SIM_SALARIO_DIARIO,
                    value=SimuladorState.calc_salario_diario,
                    on_change=SimuladorState.noop,  # Campo calculado, no editable
                    disabled=True,
                    step="0.01",
                ),
                spacing="3",
                width="100%",
            ),

            # Antigüedad y Días cotizados
            rx.hstack(
                form_field(
                    config=CAMPO_SIM_ANTIGUEDAD,
                    value=SimuladorState.antiguedad_anos.to(str),
                    on_change=SimuladorState.set_antiguedad_anos,
                    min="1",
                ),
                form_field(
                    config=CAMPO_SIM_DIAS_COTIZADOS,
                    value=SimuladorState.dias_cotizados.to(str),
                    on_change=SimuladorState.set_dias_cotizados,
                    step="0.1",
                ),
                # Espaciador para alinear (3 columnas arriba, 2 aquí)
                rx.box(width="32%"),
                spacing="3",
                width="100%",
            ),

            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def resumen_destacado() -> rx.Component:
    """Muestra los resultados del cálculo"""
    return rx.cond(
        SimuladorState.calculado,
        rx.vstack(
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.icon("calculator", size=24, color="var(--green-9)"),
                        rx.heading("Resumen del Cálculo", size="6", color="var(--green-11)"),
                        spacing="2",
                        align="center"
                    ),

                    rx.divider(margin_y="0.5em"),

                    # Métricas principales en grid 2 columnas
                    rx.hstack(
                        # Salario Neto
                        rx.vstack(
                            rx.text("💵 Salario Neto Trabajador", size="2", color="var(--gray-11)", weight="medium"),
                            rx.text(
                                SimuladorState.resultado['salario_neto'],
                                size="6",
                                weight="bold",
                                color="var(--gray-12)"
                            ),
                            align="center",
                            spacing="1"
                        ),

                        # Factor de Costo
                        rx.vstack(
                            rx.text("📊 Salario Diario", size="2", color="var(--gray-11)", weight="medium"),
                            rx.text(
                                SimuladorState.resultado['salario_diario'],
                                size="6",
                                weight="bold",
                                color="var(--blue-11)"
                            ),
                            align="center",
                            spacing="1"
                        ),
                        # Costo Total
                        rx.vstack(
                            rx.text("💰 Costo Total Patronal", size="2", color="var(--gray-11)", weight="medium"),
                            rx.text(
                                SimuladorState.resultado['costo_total'],
                                size="7",
                                weight="bold",
                                color="var(--green-11)"
                            ),
                            align="center",
                            spacing="1"
                        ),

                        spacing="6",
                        width="100%",
                        justify="between"
                    ),

                    spacing="3",
                    width="100%"
                ),
                background="var(--green-2)",
                border=f"2px solid var(--green-7)",
                padding="1.5em",
                min_width="600px"
            ),
        ),
    )


def desglose_detallado() -> rx.Component:
    """Muestra el desglose de los calculos"""
    return rx.vstack(
        # Tabla de detalle de conceptos
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell('Concepto'),
                    rx.table.column_header_cell('Importe')
                ),
            ),
            rx.table.body(
                # Salarios
                rx.table.row(
                    rx.table.row_header_cell('Salarios', font_weight='bold', col_span=2),
                ),
                fila_tabla_simulador('Factor de Integración:', SimuladorState.resultado['factor_integracion']),
                fila_tabla_simulador('SBC diario:', SimuladorState.resultado['sbc_diario']),
                fila_tabla_simulador('Salario diario:', SimuladorState.resultado['salario_diario']),
                fila_tabla_simulador('Salario mensual:', SimuladorState.resultado['salario_mensual'], color='blue'),

                # IMSS Patronal
                rx.table.row(
                    rx.table.row_header_cell('IMSS Patronal', font_weight='bold', col_span=2),
                ),
                fila_tabla_simulador('Cuota fija:', SimuladorState.resultado['imss_cuota_fija']),
                fila_tabla_simulador('Excedente:', SimuladorState.resultado['imss_excedente_pat']),
                fila_tabla_simulador('Prest. en dinero:', SimuladorState.resultado['imss_prest_dinero_pat']),
                fila_tabla_simulador('Gastos médicos:', SimuladorState.resultado['imss_gastos_med_pens_pat']),
                fila_tabla_simulador('Invalidez y vida:', SimuladorState.resultado['imss_invalidez_vida_pat']),
                fila_tabla_simulador('Guarderías:', SimuladorState.resultado['imss_guarderias']),
                fila_tabla_simulador('Retiro:', SimuladorState.resultado['imss_retiro']),
                fila_tabla_simulador('Cesantía y vejez:', SimuladorState.resultado['imss_cesantia_vejez_pat']),
                fila_tabla_simulador('Riesgo de trabajo:', SimuladorState.resultado['imss_riesgo_trabajo']),
                fila_tabla_simulador('Total IMSS Patronal:', SimuladorState.resultado['total_imss_patronal'], font_weight='bold', color='blue'),

                # Otros conceptos
                fila_tabla_simulador('Infonavit(5%):', SimuladorState.resultado['infonavit'], font_weight='bold', color='blue'),
                fila_tabla_simulador('ISN:', SimuladorState.resultado['isn'], font_weight='bold', color='blue'),

                # Provisiones
                rx.table.row(
                    rx.table.row_header_cell('Provisiones Mensuales', font_weight='bold', col_span=2),
                ),
                fila_tabla_simulador('Aguinaldo:', SimuladorState.resultado['provision_aguinaldo']),
                fila_tabla_simulador('Vacaciones:', SimuladorState.resultado['provision_vacaciones']),
                fila_tabla_simulador('Prima Vacacional:', SimuladorState.resultado['provision_prima_vac']),
                fila_tabla_simulador('Total Provisiones:', SimuladorState.resultado['total_provisiones'], font_weight='bold', color='blue'),

                # Art. 36 LSS (solo si es salario mínimo)
                rx.cond(
                    SimuladorState.resultado.get('es_salario_minimo', False),
                    rx.fragment(
                        rx.table.row(
                            rx.table.row_header_cell('Cuota obrera (Art. 36 LSS)', font_weight='bold', col_span=2),
                        ),
                        fila_tabla_simulador('IMSS obrero absorbido:', SimuladorState.resultado['imss_obrero_absorbido'], font_weight='bold', color='blue'),
                    ),
                    rx.fragment(),
                ),

                # Descuentos al trabajador
                rx.table.row(
                    rx.table.row_header_cell('Descuentos al trabajador', font_weight='bold', col_span=2),
                ),
                fila_tabla_simulador('IMSS Obrero:', SimuladorState.resultado['total_imss_obrero']),
                fila_tabla_simulador('ISR a retener:', SimuladorState.resultado["isr_a_retener"]),
                fila_tabla_simulador('Total Descuentos:', SimuladorState.resultado['total_descuentos_trabajador'], font_weight='bold', color='blue')
            ),
            variant='surface',
            width='300px',
            size='1',
            style={
                "& tbody tr:nth-child(even)": {
                    "background_color": "var(--gray-2)"
                }
            }
        )
    )


def simulador_page() -> rx.Component:
    """Pagina del simulador del costo patronal"""
    return rx.vstack(
        page_header(
            icono='calculator',
            titulo='Simulador de Costo Patronal',
            subtitulo='Proyección 2026'
        ),

        rx.hstack(
            # Columna izquierda: Formularios, resumen y botones (ancho fijo)
            rx.vstack(
                formulario_empresa(),
                formulario_trabajador(),
                # Botones
                rx.hstack(
                    rx.button(
                        'Calcular',
                        on_click=SimuladorState.calcular,
                        loading=SimuladorState.is_calculating,
                        color_scheme='blue',
                        size='3'
                    ),
                    rx.button(
                        'Limpiar',
                        on_click=SimuladorState.limpiar,
                        color_scheme='gray',
                        size='3'
                    ),
                    spacing='3',
                    margin_top='1em'
                ),
                resumen_destacado(),

                spacing='4',
                width='45%',
                min_width='600px',
                align='start',
            ),

            # Columna derecha: Desglose detallado (ancho flexible)
            desglose_detallado(),

            spacing='6',
            align='start',
            width='100%',
        ),
    )


# ═════════════════════════════════════════════════════════════════════════════
# COMPONENTE AUXILIAR: Fila de tabla reutilizable
# ═════════════════════════════════════════════════════════════════════════════

def fila_tabla_simulador(
    concepto: str,
    importe: str | float,
    font_weight: str = "normal",
    color: str = None,
) -> rx.Component:
    """
    Crea una fila de tabla con concepto e importe.

    Args:
        concepto: Texto del concepto (ej: "Salario diario:")
        importe: Importe formateado o valor
        font_weight: Peso de la fuente ("normal" o "bold" para totales)
        color: Color opcional para el importe (ej: "blue" para totales)
    """
    return rx.table.row(
        rx.table.row_header_cell(concepto, font_weight=font_weight),
        rx.table.cell(importe, justify='end', color=color)
    )
