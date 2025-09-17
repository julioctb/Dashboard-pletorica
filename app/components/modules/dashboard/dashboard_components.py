import reflex as rx
from typing import Dict, List
from app.components.ui.cards import base_card

def stat_card(
    title: str, 
    value: str, 
    subtitle: str = "", 
    color: str = "blue",
    icon: str = None
) -> rx.Component:
    """
    Componente para mostrar una tarjeta estadística del dashboard
    
    Args:
        title: Título de la estadística
        value: Valor principal a mostrar
        subtitle: Subtítulo opcional
        color: Esquema de color
        icon: Icono específico (opcional)
    """
    
    # Determinar icono automáticamente si no se proporciona
    if not icon:
        if "empleado" in title.lower():
            icon = "users"
        elif "empresa" in title.lower():
            icon = "building"
        elif "sede" in title.lower():
            icon = "map-pin"
        elif "nomina" in title.lower() or "salario" in title.lower():
            icon = "dollar-sign"
        else:
            icon = "bar-chart-3"
    
    # Contenido de la tarjeta
    content = rx.vstack(
        rx.hstack(
            rx.icon(
                icon, 
                size=24,
                color=f"var(--{color}-9)"
            ),
            rx.spacer(),
            width="100%",
            align="center"
        ),
        rx.text(value, size='6', weight='bold', color=f"var(--{color}-11)"),
        rx.text(title, size='2', weight='medium', color=f"var(--gray-11)"),
        rx.cond(
            subtitle != "",
            rx.text(subtitle, size="1", color="var(--gray-9)")
        ),
        spacing="2",
        align="start"
    )
    
    return rx.card(
        content,
        width="100%",
        padding="4"
    )

def dashboard_stats_grid(stats: List[Dict]) -> rx.Component:
    """
    Grid de estadísticas para el dashboard
    
    Args:
        stats: Lista de diccionarios con {title, value, subtitle, color, icon}
    """
    return rx.grid(
        *[
            stat_card(
                title=stat.get("title", ""),
                value=stat.get("value", "0"),
                subtitle=stat.get("subtitle", ""),
                color=stat.get("color", "blue"),
                icon=stat.get("icon")
            )
            for stat in stats
        ],
        columns="4",
        spacing="4",
        width="100%"
    )

def quick_actions_card() -> rx.Component:
    """Tarjeta de acciones rápidas para el dashboard"""
    
    actions = [
        {"title": "Nueva Empresa", "icon": "building", "href": "/empresas", "color": "blue"},
        {"title": "Nueva Sede", "icon": "map-pin", "href": "/sedes", "color": "green"},
        {"title": "Nuevo Empleado", "icon": "user-plus", "href": "/empleados", "color": "purple"},
        {"title": "Procesar Nómina", "icon": "calculator", "href": "/nomina", "color": "orange"}
    ]
    
    content = rx.grid(
        *[
            rx.link(
                rx.vstack(
                    rx.icon(action["icon"], size=24, color=f"var(--{action['color']}-9)"),
                    rx.text(action["title"], size="2", weight="medium", text_align="center"),
                    align="center",
                    spacing="2",
                    padding="3",
                    _hover={"bg": f"var(--{action['color']}-3)", "cursor": "pointer"},
                    border_radius="md",
                    transition="all 0.2s ease"
                ),
                href=action["href"],
                underline="none"
            )
            for action in actions
        ],
        columns="2",
        spacing="2"
    )
    
    return base_card(
        title="Acciones Rápidas",
        content=content,
        icon=rx.icon("zap", size=20, color="var(--blue-9)"),
        hover_effect=False
    )

def recent_activity_card(activities: List[Dict]) -> rx.Component:
    """
    Tarjeta de actividad reciente
    
    Args:
        activities: Lista de actividades recientes
    """
    
    if not activities:
        activities = [
            {"title": "Nueva empresa creada", "subtitle": "PLETÓRICA", "time": "2 min ago", "icon": "building"},
            {"title": "Empleado actualizado", "subtitle": "Juan Pérez", "time": "15 min ago", "icon": "user"},
            {"title": "Nómina procesada", "subtitle": "Septiembre 2024", "time": "1 hour ago", "icon": "calculator"}
        ]
    
    content = rx.vstack(
        *[
            rx.hstack(
                rx.icon(activity["icon"], size=16, color="var(--gray-9)"),
                rx.vstack(
                    rx.text(activity["title"], size="2", weight="medium"),
                    rx.text(activity["subtitle"], size="1", color="var(--gray-9)"),
                    align="start",
                    spacing="1"
                ),
                rx.spacer(),
                rx.text(activity["time"], size="1", color="var(--gray-7)"),
                width="100%",
                align="center",
                padding="2",
                _hover={"bg": "var(--gray-2)"},
                border_radius="sm"
            )
            for activity in activities
        ],
        spacing="1",
        width="100%"
    )
    
    return base_card(
        title="Actividad Reciente",
        content=content,
        icon=rx.icon("clock", size=20, color="var(--blue-9)"),
        hover_effect=False
    )

def dashboard_summary_cards(
    total_empresas: int = 0,
    total_sedes: int = 0,
    total_empleados: int = 0,
    nomina_pendiente: int = 0
) -> rx.Component:
    """Tarjetas de resumen para el dashboard principal"""
    
    stats = [
        {
            "title": "Total Empresas",
            "value": str(total_empresas),
            "subtitle": f"{total_empresas} activas",
            "color": "blue",
            "icon": "building"
        },
        {
            "title": "Total Sedes",
            "value": str(total_sedes),
            "subtitle": "Todas las ubicaciones",
            "color": "green",
            "icon": "map-pin"
        },
        {
            "title": "Total Empleados",
            "value": str(total_empleados),
            "subtitle": "Personal activo",
            "color": "purple",
            "icon": "users"
        },
        {
            "title": "Nóminas Pendientes",
            "value": str(nomina_pendiente),
            "subtitle": "Por procesar",
            "color": "orange",
            "icon": "calculator"
        }
    ]
    
    return dashboard_stats_grid(stats)