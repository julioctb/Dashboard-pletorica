"""
Components - Componentes de Presentación
=========================================

Exporta componentes organizados por tipo:
- ui/: Componentes genéricos reutilizables
"""

from .ui import (
    # Status badges
    status_badge,
    status_badge_contrato,
    status_badge_entidad,
    status_badge_reactive,
    status_dot,
    
    # View toggle
    view_toggle,
    view_toggle_with_label,
    view_toggle_segmented,
   
)


__all__ = [
    # Status badges
    "status_badge",
    "status_badge_contrato",
    "status_badge_entidad",
    "status_badge_reactive",
    "status_dot",
    
    # View toggle
    "view_toggle",
    "view_toggle_with_label",
    "view_toggle_segmented",
    
]