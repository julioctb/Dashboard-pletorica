import reflex as rx
from app.presentation.pages.simulador.simulador_state import SimuladorState

from app.presentation.components.ui.headers import page_header

# Mapping de estados: valor_interno -> Nombre Display
ESTADOS_DISPLAY = {
    "aguascalientes": "Aguascalientes",
    "baja_california": "Baja California",
    "baja_california_sur": "Baja California Sur",
    "campeche": "Campeche",
    "chiapas": "Chiapas",
    "chihuahua": "Chihuahua",
    "ciudad_de_mexico": "Ciudad de México",
    "coahuila": "Coahuila",
    "colima": "Colima",
    "durango": "Durango",
    "estado_de_mexico": "Estado de México",
    "guanajuato": "Guanajuato",
    "guerrero": "Guerrero",
    "hidalgo": "Hidalgo",
    "jalisco": "Jalisco",
    "michoacan": "Michoacán",
    "morelos": "Morelos",
    "nayarit": "Nayarit",
    "nuevo_leon": "Nuevo León",
    "oaxaca": "Oaxaca",
    "puebla": "Puebla",
    "queretaro": "Querétaro",
    "quintana_roo": "Quintana Roo",
    "san_luis_potosi": "San Luis Potosí",
    "sinaloa": "Sinaloa",
    "sonora": "Sonora",
    "tabasco": "Tabasco",
    "tamaulipas": "Tamaulipas",
    "tlaxcala": "Tlaxcala",
    "veracruz": "Veracruz",
    "yucatan": "Yucatán",
    "zacatecas": "Zacatecas"
}

def formulario_empresa() -> rx.Component:
    """Formulario de configuración de empresa"""
    return rx.card(
        rx.heading("Configuración Empresa", size="4", margin_bottom="1em"),
        
        rx.vstack(
            # Estado (select) - Nombres legibles
            rx.box(
                rx.text("Estado", size="2", weight="bold"),
                rx.select(
                    list(ESTADOS_DISPLAY.values()),
                    placeholder="Selecciona un estado",
                    default_value="Puebla",
                    on_change=SimuladorState.set_estado_display,
                ),
                width="100%",
            ),
            
            # Prima de riesgo
            rx.box(
                rx.text("Prima de riesgo (%)", size="2", weight="bold"),
                rx.input(
                    value=SimuladorState.prima_riesgo.to(str),
                    on_change=SimuladorState.set_prima_riesgo,
                    type="number",
                    step="0.0001",
                ),
                width="100%",
            ),
            
            # Factor de integración
            rx.box(
                rx.text("Factor de integración (0 = automático)", size="2", weight="bold"),
                rx.input(
                    value=SimuladorState.factor_integracion.to(str),
                    on_change=SimuladorState.set_factor_integracion,
                    type="number",
                    step="0.0001",
                ),
                width="100%",
            ),
            
            # Días de aguinaldo
            rx.box(
                rx.text("Días de aguinaldo", size="2", weight="bold"),
                rx.input(
                    value=SimuladorState.dias_aguinaldo.to(str),
                    on_change=SimuladorState.set_dias_aguinaldo,
                    type="number",
                ),
                width="100%",
            ),
            
            # Prima vacacional
            rx.box(
                rx.text("Prima vacacional (%)", size="2", weight="bold"),
                rx.input(
                    value=SimuladorState.prima_vacacional.to(str),
                    on_change=SimuladorState.set_prima_vacacional,
                    type="number",
                ),
                width="100%",
            ),
            
            # Checkboxes
            rx.hstack(
                rx.checkbox(
                    "Zona frontera",
                    checked=SimuladorState.zona_frontera,
                    on_change=SimuladorState.set_zona_frontera,
                ),
                rx.checkbox(
                    "Aplicar Art. 36 LSS",
                    checked=SimuladorState.aplicar_art_36,
                    on_change=SimuladorState.set_aplicar_art_36,
                ),
                spacing="4",
            ),
            
            spacing="3",
            width="100%",
        ),
        
        width="100%",
    )

def formulario_trabajador() -> rx.Component:
    """Formulario de datos del trabajador"""
    return rx.card(
        rx.heading("Datos del Trabajador", size="4", margin_bottom="1em"),
        
        rx.vstack(
            # Salario diario
            rx.box(
                rx.text("Salario diario ($)", size="2", weight="bold"),
                rx.input(
                    value=SimuladorState.salario_diario.to(str),
                    on_change=SimuladorState.set_salario_diario,
                    type="number",
                    step="0.01",
                ),
                width="100%",
            ),
            
            # Antigüedad
            rx.box(
                rx.text("Antigüedad (años)", size="2", weight="bold"),
                rx.input(
                    value=SimuladorState.antiguedad_anos.to(str),
                    on_change=SimuladorState.set_antiguedad_anos,
                    type="number",
                    min="1",
                ),
                width="100%",
            ),
            
            # Días cotizados
            rx.box(
                rx.text("Días cotizados", size="2", weight="bold"),
                rx.input(
                    value=SimuladorState.dias_cotizados.to(str),
                    on_change=SimuladorState.set_dias_cotizados,
                    type="number",
                    step="0.1",
                ),
                width="100%",
            ),
            
            spacing="3",
            width="100%",
        ),
        
        width="100%",
    )

def seccion_resultados() -> rx.Component:
    """Muestra los resultados del cálculo"""
    return rx.cond(
        SimuladorState.calculado,
        rx.vstack(
            # ═══════════════════════════════════════════════════════════════
            # RESUMEN - DESTACADO (Primero para máxima visibilidad)
            # ═══════════════════════════════════════════════════════════════
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
                        # Costo Total
                        rx.vstack(
                            rx.text("💰 Costo Total Patronal", size="2", color="var(--gray-11)", weight="medium"),
                            rx.text(
                                SimuladorState.resultado['costo_total'],
                                size="7",
                                weight="bold",
                                color="var(--green-11)"
                            ),
                            align="start",
                            spacing="1"
                        ),

                        # Factor de Costo
                        rx.vstack(
                            rx.text("📊 Factor de Costo", size="2", color="var(--gray-11)", weight="medium"),
                            rx.text(
                                SimuladorState.resultado['factor_costo'],
                                size="6",
                                weight="bold",
                                color="var(--blue-11)"
                            ),
                            align="start",
                            spacing="1"
                        ),

                        # Salario Neto
                        rx.vstack(
                            rx.text("💵 Salario Neto Trabajador", size="2", color="var(--gray-11)", weight="medium"),
                            rx.text(
                                SimuladorState.resultado['salario_neto'],
                                size="6",
                                weight="bold",
                                color="var(--gray-12)"
                            ),
                            align="start",
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
                width="100%"
            ),

            # Separador visual
            rx.divider(margin_y="1.5em"),

            rx.heading("Desglose Detallado", size="4", margin_bottom="1em", color="var(--gray-12)"),

            # ═══════════════════════════════════════════════════════════════
            # DETALLES - Debajo del resumen
            # ═══════════════════════════════════════════════════════════════
            rx.vstack(
                # Salarios
                rx.card(
                    rx.heading("Salarios", size="3", margin_bottom="0.5em"),
                    rx.hstack(
                        rx.text("Salario diario:", weight="bold"),
                        rx.text(SimuladorState.resultado['salario_diario']),
                    ),
                    rx.hstack(
                        rx.text("Salario mensual:", weight="bold"),
                        rx.text(SimuladorState.resultado['salario_mensual']),
                    ),
                    rx.hstack(
                        rx.text("Factor de integración:", weight="bold"),
                        rx.text(SimuladorState.resultado['factor_integracion']),
                    ),
                    rx.hstack(
                        rx.text("SBC diario:", weight="bold"),
                        rx.text(SimuladorState.resultado['sbc_diario']),
                    ),
                    width="100%",
                ),
                
                # IMSS Patronal
                rx.card(
                    rx.heading("IMSS Patronal", size="3", margin_bottom="0.5em"),
                    rx.hstack(
                        rx.text("Cuota fija:", weight="bold"),
                        rx.text(SimuladorState.resultado['imss_cuota_fija']),
                    ),
                    rx.hstack(
                        rx.text("Excedente:", weight="bold"),
                        rx.text(SimuladorState.resultado['imss_excedente_pat']),
                    ),
                    rx.hstack(
                        rx.text("Prest. en dinero:", weight="bold"),
                        rx.text(SimuladorState.resultado['imss_prest_dinero_pat']),
                    ),
                    rx.hstack(
                        rx.text("Gastos médicos:", weight="bold"),
                        rx.text(SimuladorState.resultado['imss_gastos_med_pens_pat']),
                    ),
                    rx.hstack(
                        rx.text("Invalidez y vida:", weight="bold"),
                        rx.text(SimuladorState.resultado['imss_invalidez_vida_pat']),
                    ),
                    rx.hstack(
                        rx.text("Guarderías:", weight="bold"),
                        rx.text(SimuladorState.resultado['imss_guarderias']),
                    ),
                    rx.hstack(
                        rx.text("Retiro:", weight="bold"),
                        rx.text(SimuladorState.resultado['imss_retiro']),
                    ),
                    rx.hstack(
                        rx.text("Cesantía y vejez:", weight="bold"),
                        rx.text(SimuladorState.resultado['imss_cesantia_vejez_pat']),
                    ),
                    rx.hstack(
                        rx.text("Riesgo de trabajo:", weight="bold"),
                        rx.text(SimuladorState.resultado['imss_riesgo_trabajo']),
                    ),
                    rx.divider(),
                    rx.hstack(
                        rx.text("TOTAL IMSS PATRONAL:", weight="bold"),
                        rx.text(SimuladorState.resultado['total_imss_patronal'], color="blue"),
                    ),
                    width="100%",
                ),
                
                # Art. 36 LSS (solo si es salario mínimo)
                rx.cond(
                    SimuladorState.resultado.get('es_salario_minimo', False),
                    rx.card(
                        rx.heading("Art. 36 LSS - Cuota obrera absorbida", size="3", margin_bottom="0.5em"),
                        rx.hstack(
                            rx.text("IMSS obrero absorbido:", weight="bold"),
                            rx.text(SimuladorState.resultado['imss_obrero_absorbido'], color="orange"),
                        ),
                        width="100%",
                    ),
                    rx.box(),
                ),
                
                # Otros conceptos
                rx.card(
                    rx.heading("Otros Conceptos", size="3", margin_bottom="0.5em"),
                    rx.hstack(
                        rx.text("INFONAVIT:", weight="bold"),
                        rx.text(SimuladorState.resultado['infonavit']),
                    ),
                    rx.hstack(
                        rx.text("ISN:", weight="bold"),
                        rx.text(SimuladorState.resultado['isn']),
                    ),
                    width="100%",
                ),
                
                # Provisiones
                rx.card(
                    rx.heading("Provisiones Mensuales", size="3", margin_bottom="0.5em"),
                    rx.hstack(
                        rx.text("Aguinaldo:", weight="bold"),
                        rx.text(SimuladorState.resultado['provision_aguinaldo']),
                    ),
                    rx.hstack(
                        rx.text("Vacaciones:", weight="bold"),
                        rx.text(SimuladorState.resultado['provision_vacaciones']),
                    ),
                    rx.hstack(
                        rx.text("Prima vacacional:", weight="bold"),
                        rx.text(SimuladorState.resultado['provision_prima_vac']),
                    ),
                    rx.divider(),
                    rx.hstack(
                        rx.text("TOTAL PROVISIONES:", weight="bold"),
                        rx.text(SimuladorState.resultado['total_provisiones'], color="blue"),
                    ),
                    width="100%",
                ),

                spacing="3",
                width="100%",
            ),

            spacing="4",
            width="100%",
            margin_top="2em",
        ),
        rx.box(),  # No mostrar nada si no hay cálculo
    )

def simulador_page() -> rx.Component:
    """Pagina del simulador del costo patronal"""

    return rx.vstack(
        page_header(
            icono='calculator',
            titulo='Simulador de Costo Patronal',
            subtitulo='Proyección 2026'
        ),

        #Formularios en 2 columnas
        rx.hstack(
            formulario_empresa(),
            formulario_trabajador(),
            spacing='4',
            width='100%',
            align='start'
        ),

        #Botones
        rx.hstack(
            rx.button(
                'Calcular',
                on_click=SimuladorState.calcular,
                loading=SimuladorState.is_calculating,
                color_scheme='green',
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

        #Resultados
        seccion_resultados()
    )