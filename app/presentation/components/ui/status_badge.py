"""
Status Badge - Badge de Estado Unificado
=========================================

Componente para mostrar el estado de contratos y entidades
con colores y iconos consistentes según el sistema de diseño.

Estados de Contrato:
- BORRADOR (gris) - Neutral/pendiente
- ACTIVO (verde) - En operación
- SUSPENDIDO (ámbar) - Temporalmente detenido
- VENCIDO (rojo) - Requiere atención
- CANCELADO (rojo) - Terminado negativamente
- CERRADO (azul) - Completado correctamente

Estados de Entidad:
- ACTIVO (verde)
- INACTIVO (rojo)

Uso:
    from app.presentation.components.ui import status_badge
    
    # Básico
    status_badge("ACTIVO")
    
    # Con icono
    status_badge("ACTIVO", show_icon=True)
    
    # Para contratos
    status_badge_contrato("VENCIDO")
"""

import reflex as rx
from app.presentation.theme import StatusColors, Typography


def status_badge(
    status: str,
    show_icon: bool = False,
    size: str = "1",
) -> rx.Component:
    """
    Badge de estado genérico.
    
    Args:
        status: Estado en mayúsculas (ACTIVO, INACTIVO, BORRADOR, etc.)
        show_icon: Mostrar icono junto al texto
        size: Tamaño del badge ("1", "2", "3")
    
    Returns:
        Badge con color apropiado según el estado
    
    Ejemplo:
        status_badge("ACTIVO")
        status_badge("VENCIDO", show_icon=True)
    """
    # Obtener configuración del estado
    color_scheme = StatusColors.get_color_scheme(status)
    icon_name = StatusColors.get_icon(status)
    
    if show_icon:
        return rx.badge(
            rx.hstack(
                rx.icon(icon_name, size=12),
                rx.text(status),
                spacing="1",
                align="center",
            ),
            color_scheme=color_scheme,
            size=size,
            variant="soft",
        )
    else:
        return rx.badge(
            status,
            color_scheme=color_scheme,
            size=size,
            variant="soft",
        )


def status_badge_contrato(
    status: str,
    show_icon: bool = True,
    size: str = "2",
) -> rx.Component:
    """
    Badge específico para estados de contrato.
    Por defecto muestra icono para mejor identificación visual.
    
    Estados: BORRADOR, ACTIVO, SUSPENDIDO, VENCIDO, CANCELADO, CERRADO
    """
    return status_badge(status, show_icon=show_icon, size=size)


def status_badge_entidad(
    status: str,
    size: str = "1",
) -> rx.Component:
    """
    Badge específico para estados de entidad (empresas, empleados).
    Sin icono por defecto para mantener compacto.

    Estados: ACTIVO, INACTIVO
    """
    return status_badge(status, show_icon=False, size=size)


def status_badge_plaza(
    status: str,
    show_icon: bool = True,
    size: str = "2",
) -> rx.Component:
    """
    Badge específico para estados de plaza.
    Por defecto muestra icono para mejor identificación visual.

    Estados: VACANTE, OCUPADA, SUSPENDIDA, CANCELADA
    """
    return status_badge(status, show_icon=show_icon, size=size)


# =============================================================================
# VERSIÓN REACTIVA (para uso con rx.cond)
# =============================================================================

def status_badge_reactive(
    status: rx.Var,
    show_icon: bool = False,
) -> rx.Component:
    """
    Versión reactiva del badge para usar con variables de estado.
    Usa rx.match para evaluar el estado dinámicamente.
    
    Uso:
        status_badge_reactive(ContratosState.contrato_seleccionado["estatus"])
    """
    return rx.match(
        status,
        ("BORRADOR", rx.badge(
            rx.hstack(
                rx.icon("file-pen", size=12) if show_icon else rx.fragment(),
                "BORRADOR",
                spacing="1",
            ) if show_icon else "BORRADOR",
            color_scheme="gray",
            variant="soft",
        )),
        ("ACTIVO", rx.badge(
            rx.hstack(
                rx.icon("circle-check", size=12) if show_icon else rx.fragment(),
                "ACTIVO",
                spacing="1",
            ) if show_icon else "ACTIVO",
            color_scheme="green",
            variant="soft",
        )),
        ("SUSPENDIDO", rx.badge(
            rx.hstack(
                rx.icon("circle-pause", size=12) if show_icon else rx.fragment(),
                "SUSPENDIDO",
                spacing="1",
            ) if show_icon else "SUSPENDIDO",
            color_scheme="amber",
            variant="soft",
        )),
        ("VENCIDO", rx.badge(
            rx.hstack(
                rx.icon("circle-alert", size=12) if show_icon else rx.fragment(),
                "VENCIDO",
                spacing="1",
            ) if show_icon else "VENCIDO",
            color_scheme="red",
            variant="soft",
        )),
        ("CANCELADO", rx.badge(
            rx.hstack(
                rx.icon("circle-x", size=12) if show_icon else rx.fragment(),
                "CANCELADO",
                spacing="1",
            ) if show_icon else "CANCELADO",
            color_scheme="red",
            variant="soft",
        )),
        ("CERRADO", rx.badge(
            rx.hstack(
                rx.icon("archive", size=12) if show_icon else rx.fragment(),
                "CERRADO",
                spacing="1",
            ) if show_icon else "CERRADO",
            color_scheme="blue",
            variant="soft",
        )),
        ("INACTIVO", rx.badge(
            rx.hstack(
                rx.icon("circle-x", size=12) if show_icon else rx.fragment(),
                "INACTIVO",
                spacing="1",
            ) if show_icon else "INACTIVO",
            color_scheme="red",
            variant="soft",
        )),
        # Estados de Plaza
        ("VACANTE", rx.badge(
            rx.hstack(
                rx.icon("user-plus", size=12) if show_icon else rx.fragment(),
                "VACANTE",
                spacing="1",
            ) if show_icon else "VACANTE",
            color_scheme="sky",
            variant="soft",
        )),
        ("OCUPADA", rx.badge(
            rx.hstack(
                rx.icon("user-check", size=12) if show_icon else rx.fragment(),
                "OCUPADA",
                spacing="1",
            ) if show_icon else "OCUPADA",
            color_scheme="green",
            variant="soft",
        )),
        ("SUSPENDIDA", rx.badge(
            rx.hstack(
                rx.icon("user-x", size=12) if show_icon else rx.fragment(),
                "SUSPENDIDA",
                spacing="1",
            ) if show_icon else "SUSPENDIDA",
            color_scheme="amber",
            variant="soft",
        )),
        # Default
        rx.badge(status, color_scheme="gray", variant="soft"),
    )


# =============================================================================
# INDICADOR DE ESTADO (versión compacta solo color)
# =============================================================================

def status_dot(status: str, size: str = "8px") -> rx.Component:
    """
    Indicador de punto de color para estados.
    Útil en tablas donde el espacio es limitado.
    
    Ejemplo:
        rx.hstack(
            status_dot("ACTIVO"),
            rx.text("Contrato ABC"),
        )
    """
    color = StatusColors.get_color(status)
    
    return rx.tooltip(
        rx.box(
            width=size,
            height=size,
            background=color,
            border_radius="50%",
            flex_shrink="0",
        ),
        content=status.title(),
    )