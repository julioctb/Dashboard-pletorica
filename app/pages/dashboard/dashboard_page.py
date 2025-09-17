import reflex as rx
from app.components.modules.dashboard.dashboard_components import (
    dashboard_summary_cards,
    quick_actions_card,
    recent_activity_card
)

def dashboard_page() -> rx.Component:
    """Página principal del dashboard"""
    return rx.vstack(
        # Header del dashboard
        rx.hstack(
            rx.hstack(
                rx.icon("layout-dashboard", size=32, color="var(--blue-9)"),
                rx.vstack(
                    rx.text("Dashboard", size="6", weight="bold"),
                    rx.text("Resumen general del sistema", size="3", color="var(--gray-9)"),
                    align="start",
                    spacing="1"
                ),
                spacing="3",
                align="center"
            ),
            rx.spacer(),
            
            rx.hstack(
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    "Actualizar",
                    variant="soft",
                    size="2"
                ),
                spacing="2"
            ),
            
            width="100%",
            align="center"
        ),
        
        # Tarjetas de resumen
        dashboard_summary_cards(
            total_empresas=2,  # TODO: Obtener datos reales
            total_sedes=7,
            total_empleados=389,
            nomina_pendiente=0
        ),
        
        # Contenido principal en grid
        rx.grid(
            # Acciones rápidas
            quick_actions_card(),
            
            # Actividad reciente
            recent_activity_card([]),
            
            columns="2",
            spacing="4",
            width="100%"
        ),
        
        spacing="4",
        width="100%",
        max_width="100%",
        padding="4"
    )