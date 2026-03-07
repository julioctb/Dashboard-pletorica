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
    
    # Reactivo (para uso con rx.Var)
    status_badge_reactive(State.estatus)
"""

import reflex as rx
from app.presentation.theme import StatusColors


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


# =============================================================================
# VERSIÓN REACTIVA (para uso con rx.cond)
# =============================================================================

def status_badge_reactive(
    status: rx.Var,
    show_icon: bool = False,
    size: str = "1",
) -> rx.Component:
    """
    Versión reactiva del badge para usar con variables de estado.
    Usa rx.match para evaluar el estado dinámicamente.
    
    Uso:
        status_badge_reactive(ContratosState.contrato_seleccionado["estatus"])
    """
    def _badge(label: str, color_scheme: str, icon_name: str) -> rx.Component:
        return rx.badge(
            rx.hstack(
                rx.icon(icon_name, size=12),
                label,
                spacing="1",
            ) if show_icon else label,
            color_scheme=color_scheme,
            variant="soft",
            size=size,
        )

    return rx.match(
        status,
        ("BORRADOR", _badge("BORRADOR", "gray", "file-pen")),
        ("ACTIVO", _badge("ACTIVO", "green", "circle-check")),
        ("SUSPENDIDO", _badge("SUSPENDIDO", "amber", "circle-pause")),
        ("VENCIDO", _badge("VENCIDO", "red", "circle-alert")),
        ("CANCELADO", _badge("CANCELADO", "red", "circle-x")),
        ("CERRADO", _badge("CERRADO", "blue", "archive")),
        ("INACTIVO", _badge("INACTIVO", "red", "circle-x")),
        ("VACANTE", _badge("VACANTE", "sky", "user-plus")),
        ("OCUPADA", _badge("OCUPADA", "green", "user-check")),
        ("SUSPENDIDA", _badge("SUSPENDIDA", "amber", "user-x")),
        ("PREFACTURA_ENVIADA", _badge("PREFACTURA ENVIADA", "sky", "file-search")),
        ("PREFACTURA_RECHAZADA", _badge("PREFACTURA RECHAZADA", "red", "file-x")),
        ("PREFACTURA_APROBADA", _badge("PREFACTURA APROBADA", "green", "file-check")),
        ("FACTURADO", _badge("FACTURADO", "amber", "receipt")),
        ("PAGADO", _badge("PAGADO", "green", "badge-check")),
        rx.badge(status, color_scheme="gray", variant="soft", size=size),
    )
