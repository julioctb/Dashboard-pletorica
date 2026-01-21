"""
Theme - Sistema de Diseño BUAP Administrativo
=============================================

Exporta todos los design tokens para uso en la aplicación.

Uso:
    from app.presentation.theme import Colors, Spacing, Typography
    
    # O importar todo
    from app.presentation.theme import *
"""

from .tokens import (
    Colors,
    StatusColors,
    Spacing,
    Radius,
    Shadows,
    Transitions,
    Typography,
    Breakpoints,
    Sidebar,
    ZIndex,
    ButtonStyles,
    CardStyles,
    InputStyles,
)

from .styles import (
    GLOBAL_STYLES,
    PAGE_CONTAINER_STYLE,
    CONTENT_AREA_STYLE,
    PAGE_HEADER_STYLE,
    TOOLBAR_STYLE,
    CARD_BASE_STYLE,
    CARD_INTERACTIVE_STYLE,
    MODAL_OVERLAY_STYLE,
    MODAL_CONTENT_STYLE,
    EMPTY_STATE_STYLE,
    TABLE_CONTAINER_STYLE,
    TABLE_HEADER_STYLE,
    TABLE_ROW_STYLE,
    TABLE_CELL_STYLE,
    FORM_GROUP_STYLE,
    FORM_LABEL_STYLE,
    FORM_INPUT_STYLE,
    FORM_ERROR_STYLE,
    FORM_HELP_STYLE,
)

__all__ = [
    # Colores
    "Colors",
    "StatusColors",
    
    # Dimensiones
    "Spacing",
    "Radius",
    "Shadows",
    
    # Animaciones
    "Transitions",
    
    # Tipografía
    "Typography",
    
    # Layout
    "Breakpoints",
    "Sidebar",
    "ZIndex",
    
    # Estilos compuestos (tokens)
    "ButtonStyles",
    "CardStyles",
    "InputStyles",
    
    # Estilos globales
    "GLOBAL_STYLES",
    "PAGE_CONTAINER_STYLE",
    "CONTENT_AREA_STYLE",
    "PAGE_HEADER_STYLE",
    "TOOLBAR_STYLE",
    "CARD_BASE_STYLE",
    "CARD_INTERACTIVE_STYLE",
    "MODAL_OVERLAY_STYLE",
    "MODAL_CONTENT_STYLE",
    "EMPTY_STATE_STYLE",
    
    # Estilos de tabla
    "TABLE_CONTAINER_STYLE",
    "TABLE_HEADER_STYLE",
    "TABLE_ROW_STYLE",
    "TABLE_CELL_STYLE",
    
    # Estilos de formulario
    "FORM_GROUP_STYLE",
    "FORM_LABEL_STYLE",
    "FORM_INPUT_STYLE",
    "FORM_ERROR_STYLE",
    "FORM_HELP_STYLE",
]