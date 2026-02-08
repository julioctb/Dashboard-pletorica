"""
Estilos Globales - Sistema de Diseño BUAP
==========================================

Estilos CSS globales que se aplican a toda la aplicación.
Incluye configuración de tipografía, scrollbars, y resets.

Uso en app.py:
    from app.presentation.theme.styles import GLOBAL_STYLES

    app = rx.App(
        theme=rx.theme(...),
        style=GLOBAL_STYLES,
    )
"""

from .tokens import Typography, Colors, Transitions


# =============================================================================
# ESTILOS DE TABLA (definidos antes de GLOBAL_STYLES para poder referenciarlos)
# =============================================================================

TABLE_CONTAINER_STYLE = {
    "width": "100%",
    "overflow_x": "auto",
    "background": Colors.SURFACE,
    "border_radius": "8px",
    "border": f"1px solid {Colors.BORDER}",
}

TABLE_HEADER_STYLE = {
    "background": Colors.SECONDARY_LIGHT,
    "font_weight": Typography.WEIGHT_SEMIBOLD,
    "font_size": Typography.SIZE_SM,
    "color": Colors.TEXT_PRIMARY,
    "text_transform": "uppercase",
    "letter_spacing": Typography.LETTER_SPACING_WIDE,
}

TABLE_ROW_STYLE = {
    "border_bottom": f"1px solid {Colors.BORDER}",
    "transition": Transitions.FAST,
    "_hover": {
        "background": Colors.SURFACE_HOVER,
    },
}

TABLE_CELL_STYLE = {
    "padding": "0.75rem 1rem",
    "font_size": Typography.SIZE_BASE,
    "color": Colors.TEXT_PRIMARY,
    "vertical_align": "middle",
}


# =============================================================================
# ESTILOS GLOBALES
# =============================================================================

GLOBAL_STYLES = {
    # Reset y base
    "*": {
        "box_sizing": "border-box",
    },

    # Tipografía base - Source Sans Pro
    "body": {
        "font_family": Typography.FONT_FAMILY,
        "font_size": Typography.SIZE_BASE,
        "line_height": Typography.LINE_HEIGHT_NORMAL,
        "color": Colors.TEXT_PRIMARY,
        "background_color": Colors.BG_APP,
        "-webkit-font-smoothing": "antialiased",
        "-moz-osx-font-smoothing": "grayscale",
    },

    # Headings
    "h1, h2, h3, h4, h5, h6": {
        "font_family": Typography.FONT_FAMILY,
        "font_weight": Typography.WEIGHT_SEMIBOLD,
        "line_height": Typography.LINE_HEIGHT_TIGHT,
        "color": Colors.TEXT_PRIMARY,
    },

    # Links
    "a": {
        "color": Colors.PRIMARY,
        "text_decoration": "none",
        "transition": Transitions.FAST,
        "_hover": {
            "color": Colors.PRIMARY_HOVER,
        },
    },

    # Scrollbar personalizado (webkit)
    "::-webkit-scrollbar": {
        "width": "8px",
        "height": "8px",
    },
    "::-webkit-scrollbar-track": {
        "background": Colors.SECONDARY_LIGHT,
        "border_radius": "4px",
    },
    "::-webkit-scrollbar-thumb": {
        "background": Colors.BORDER_STRONG,
        "border_radius": "4px",
        "_hover": {
            "background": Colors.SECONDARY,
        },
    },

    # Tablas - estilos globales centralizados
    "tr": TABLE_ROW_STYLE,
    "td": TABLE_CELL_STYLE,
    "th": {
        "vertical_align": "middle",
    },

    # Focus visible para accesibilidad
    ":focus-visible": {
        "outline": f"2px solid {Colors.PRIMARY}",
        "outline_offset": "2px",
    },

    # Selección de texto
    "::selection": {
        "background": Colors.PRIMARY_LIGHT,
        "color": Colors.PRIMARY_HOVER,
    },
}


# =============================================================================
# ESTILOS DE PÁGINA
# =============================================================================

PAGE_CONTAINER_STYLE = {
    "width": "100%",
    "min_height": "100vh",
    "background_color": Colors.BG_APP,
    "padding": "0",
}

CONTENT_AREA_STYLE = {
    "width": "100%",
    "flex": "1",
    "padding": "1.5rem",
    "background_color": Colors.BG_APP,
    "overflow_y": "auto",
    "min_height": "calc(100vh - 140px)",
}


# =============================================================================
# ESTILOS DE COMPONENTES COMUNES
# =============================================================================

# Header de página
PAGE_HEADER_STYLE = {
    "width": "100%",
    "padding_bottom": "1rem",
    "border_bottom": f"1px solid {Colors.BORDER}",
    "margin_bottom": "1.5rem",
}

# Toolbar (barra de herramientas)
TOOLBAR_STYLE = {
    "width": "100%",
    "padding": "0.75rem 1rem",
    "background": Colors.SURFACE,
    "border_radius": "8px",
    "border": f"1px solid {Colors.BORDER}",
    "margin_bottom": "1rem",
}

# Card base
CARD_BASE_STYLE = {
    "background": Colors.SURFACE,
    "border_radius": "8px",
    "border": f"1px solid {Colors.BORDER}",
    "padding": "1.25rem",
    "transition": Transitions.FAST,
}

# Card interactiva (hover)
CARD_INTERACTIVE_STYLE = {
    **CARD_BASE_STYLE,
    "cursor": "pointer",
    "_hover": {
        "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.08)",
        "border_color": Colors.PRIMARY_LIGHT,
    },
}

# Modal
MODAL_OVERLAY_STYLE = {
    "background": "rgba(0, 0, 0, 0.5)",
    "backdrop_filter": "blur(4px)",
}

MODAL_CONTENT_STYLE = {
    "background": Colors.SURFACE,
    "border_radius": "12px",
    "box_shadow": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
    "max_width": "500px",
    "width": "90%",
}

# Empty state
EMPTY_STATE_STYLE = {
    "text_align": "center",
    "padding": "3rem 1.5rem",
    "color": Colors.TEXT_SECONDARY,
}


# =============================================================================
# ESTILOS DE FORMULARIO
# =============================================================================

FORM_GROUP_STYLE = {
    "margin_bottom": "1rem",
}

FORM_LABEL_STYLE = {
    "display": "block",
    "margin_bottom": "0.5rem",
    "font_size": Typography.SIZE_SM,
    "font_weight": Typography.WEIGHT_MEDIUM,
    "color": Colors.TEXT_PRIMARY,
}

FORM_INPUT_STYLE = {
    "width": "100%",
    "padding": "0.625rem 0.75rem",
    "font_size": Typography.SIZE_BASE,
    "font_family": Typography.FONT_FAMILY,
    "border": f"1px solid {Colors.BORDER}",
    "border_radius": "6px",
    "background": Colors.SURFACE,
    "transition": Transitions.FAST,
    "_focus": {
        "border_color": Colors.PRIMARY,
        "box_shadow": f"0 0 0 3px {Colors.PRIMARY_LIGHT}",
        "outline": "none",
    },
    "_placeholder": {
        "color": Colors.TEXT_MUTED,
    },
}

FORM_ERROR_STYLE = {
    "color": Colors.ERROR,
    "font_size": Typography.SIZE_SM,
    "margin_top": "0.25rem",
}

FORM_HELP_STYLE = {
    "color": Colors.TEXT_MUTED,
    "font_size": Typography.SIZE_SM,
    "margin_top": "0.25rem",
}
