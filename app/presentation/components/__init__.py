"""
Components - Componentes de Presentación
=========================================

Exporta componentes organizados por tipo:
- ui/: Componentes genéricos reutilizables
"""

from .ui import (
    # Status badges
    status_badge,
    status_badge_reactive,

    # View toggle
    view_toggle,
)


__all__ = [
    # Status badges
    "status_badge",
    "status_badge_reactive",

    # View toggle
    "view_toggle",
]