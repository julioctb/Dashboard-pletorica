"""
Page Layout - Estructura Estándar de Páginas
=============================================

Define la estructura visual consistente para todas las páginas:
- Header con título, subtítulo y acción principal
- Toolbar con búsqueda, filtros y toggle de vista
- Área de contenido

Uso:
    from app.presentation.layout import page_layout, page_header, page_toolbar
    
    def mi_pagina():
        return page_layout(
            header=page_header(
                titulo="Mi Página",
                subtitulo="Descripción",
                icono="home",
            ),
            toolbar=page_toolbar(...),
            content=mi_contenido(),
        )
"""

import reflex as rx
from app.presentation.theme import (
    Colors,
    Spacing,
    Typography,
    Transitions,
)


# =============================================================================
# PAGE HEADER
# =============================================================================

def page_header(
    titulo: str,
    subtitulo: str = "",
    icono: str = None,
    accion_principal: rx.Component = None,
) -> rx.Component:
    """
    Header estándar de página.
    
    Args:
        titulo: Título principal de la página
        subtitulo: Descripción breve (opcional)
        icono: Nombre del icono Lucide (opcional)
        accion_principal: Botón de acción principal (ej: "Nuevo")
    
    Ejemplo:
        page_header(
            titulo="Contratos",
            subtitulo="Gestione los contratos del sistema",
            icono="file-text",
            accion_principal=rx.button("+ Nuevo Contrato", ...),
        )
    """
    return rx.hstack(
        # Lado izquierdo: Icono + Títulos
        rx.hstack(
            # Icono (opcional)
            rx.cond(
                icono is not None,
                rx.center(
                    rx.icon(
                        icono,
                        size=28,
                        color=Colors.PRIMARY,
                    ),
                    width="48px",
                    height="48px",
                    background=Colors.PRIMARY_LIGHT,
                    border_radius="12px",
                ),
            ) if icono else rx.fragment(),
            # Títulos
            rx.vstack(
                rx.heading(
                    titulo,
                    size="7",
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_PRIMARY,
                    line_height=Typography.LINE_HEIGHT_TIGHT,
                ),
                rx.cond(
                    subtitulo != "",
                    rx.text(
                        subtitulo,
                        font_size=Typography.SIZE_BASE,
                        color=Colors.TEXT_SECONDARY,
                ),  
                rx.fragment(),
                    ),
                spacing="1",
                align_items="start",
            ),
            spacing="4",
            align="center",
        ),
        
        rx.spacer(),
        
        # Lado derecho: Acción principal (opcional)
        rx.cond(
        accion_principal,
        accion_principal,
          rx.fragment(),
        ),
            
        
        width="100%",
        padding_bottom=Spacing.LG,
        margin_bottom=Spacing.MD,
        border_bottom=f"1px solid {Colors.BORDER}",
        align="center",
    )


# =============================================================================
# VIEW TOGGLE (Tabla / Cards)
# =============================================================================

def view_toggle(
    current_view: str,
    on_change_table: callable,
    on_change_cards: callable,
) -> rx.Component:
    """
    Toggle para cambiar entre vista de tabla y cards.
    
    Args:
        current_view: "table" o "cards"
        on_change_table: Callback al seleccionar tabla
        on_change_cards: Callback al seleccionar cards
    """
    return rx.hstack(
        rx.tooltip(
            rx.icon_button(
                rx.icon("list", size=18),
                size="2",
                variant=rx.cond(current_view == "table", "solid", "ghost"),
                color_scheme="gray",
                on_click=on_change_table,
                cursor="pointer",
            ),
            content="Vista de tabla",
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon("layout-grid", size=18),
                size="2",
                variant=rx.cond(current_view == "cards", "solid", "ghost"),
                color_scheme="gray",
                on_click=on_change_cards,
                cursor="pointer",
            ),
            content="Vista de tarjetas",
        ),
        spacing="1",
        padding="4px",
        background=Colors.SECONDARY_LIGHT,
        border_radius="8px",
    )


# =============================================================================
# PAGE TOOLBAR
# =============================================================================

def page_toolbar(
    # Búsqueda
    search_value: str = "",
    search_placeholder: str = "Buscar...",
    on_search_change: callable = None,
    on_search_clear: callable = None,
    
    # Filtros (slot para componentes de filtro)
    filters: rx.Component = None,
    
    # Toggle de vista
    show_view_toggle: bool = True,
    current_view: str = "table",
    on_view_table: callable = None,
    on_view_cards: callable = None,
    
    # Elementos adicionales a la derecha
    extra_right: rx.Component = None,
) -> rx.Component:
    """
    Barra de herramientas estándar con búsqueda, filtros y toggle de vista.
    
    Args:
        search_value: Valor actual del campo de búsqueda
        search_placeholder: Placeholder del campo de búsqueda
        on_search_change: Callback al cambiar búsqueda
        on_search_clear: Callback al limpiar búsqueda
        filters: Componente de filtros (opcional)
        show_view_toggle: Mostrar toggle tabla/cards
        current_view: Vista actual ("table" o "cards")
        on_view_table: Callback para vista tabla
        on_view_cards: Callback para vista cards
        extra_right: Componentes adicionales al final (opcional)
    
    Ejemplo:
        page_toolbar(
            search_value=State.search,
            on_search_change=State.set_search,
            show_view_toggle=True,
            current_view=State.view_mode,
            on_view_table=State.set_view_table,
            on_view_cards=State.set_view_cards,
        )
    """
    return rx.hstack(
        # Búsqueda
        rx.box(
            rx.hstack(
                rx.icon("search", size=18, color=Colors.TEXT_MUTED),
                rx.input(
                    placeholder=search_placeholder,
                    value=search_value,
                    on_change=on_search_change,
                    variant="soft",
                    size="2",
                    width="100%",
                    style={
                        "border": "none",
                        "background": "transparent",
                        "_focus": {
                            "outline": "none",
                        },
                    },
                ),
                rx.cond(
                    search_value != "",
                    rx.icon_button(
                        rx.icon("x", size=14),
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=on_search_clear,
                        cursor="pointer",
                    ),
                ),
                padding_x=Spacing.SM,
                align="center",
                width="100%",
            ),
            min_width="280px",
            max_width="400px",
            background=Colors.SECONDARY_LIGHT,
            border_radius="8px",
            border=f"1px solid {Colors.BORDER}",
            transition=Transitions.FAST,
            style={
                "_focus_within": {
                    "border_color": Colors.PRIMARY,
                    "box_shadow": f"0 0 0 3px {Colors.PRIMARY_LIGHT}",
                },
            },
        ),
        
        # Filtros (opcional)
        filters if filters else rx.fragment(),
        
        rx.spacer(),
        
        # Elementos adicionales (opcional)
        extra_right if extra_right else rx.fragment(),
        
        # Toggle de vista (opcional)
        rx.cond(
            show_view_toggle,
            view_toggle(
                current_view=current_view,
                on_change_table=on_view_table,
                on_change_cards=on_view_cards,
            ),
        ) if show_view_toggle else rx.fragment(),
        
        width="100%",
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border_radius="8px",
        border=f"1px solid {Colors.BORDER}",
        margin_bottom=Spacing.MD,
        align="center",
        gap=Spacing.MD,
    )


# =============================================================================
# PAGE LAYOUT COMPLETO
# =============================================================================

def page_content_area(content: rx.Component) -> rx.Component:
    """
    Área de contenido principal de la página.
    """
    return rx.box(
        content,
        width="100%",
        flex="1",
    )


def page_layout(
    header: rx.Component = None,
    toolbar: rx.Component = None,
    content: rx.Component = None,
) -> rx.Component:
    """
    Layout completo de página con header, toolbar y contenido.
    
    Args:
        header: Componente de header (usar page_header())
        toolbar: Componente de toolbar (usar page_toolbar())
        content: Contenido principal de la página
    
    Ejemplo:
        def contratos_page():
            return page_layout(
                header=page_header(
                    titulo="Contratos",
                    subtitulo="Gestione los contratos",
                    icono="file-text",
                    accion_principal=boton_nuevo,
                ),
                toolbar=page_toolbar(
                    search_value=ContratosState.search,
                    ...
                ),
                content=tabla_contratos(),
            )
    """
    return rx.vstack(
        # Header (opcional)
        header if header else rx.fragment(),
        
        # Toolbar (opcional)
        toolbar if toolbar else rx.fragment(),
        
        # Contenido principal
        page_content_area(content) if content else rx.fragment(),
        
        width="100%",
        min_height="100%",
        spacing="0",
        align_items="stretch",
    )


# =============================================================================
# LAYOUT PRINCIPAL CON SIDEBAR
# =============================================================================

def main_layout(content: rx.Component) -> rx.Component:
    """
    Layout principal de la aplicación con sidebar.
    Reemplaza la función index() en app.py.
    
    Uso en app.py:
        from app.presentation.layout import main_layout
        
        app.add_page(lambda: main_layout(dashboard_page()), route="/")
    """
    from app.presentation.layout.sidebar_layout import sidebar
    
    return rx.hstack(
        # Sidebar colapsable
        sidebar(),
        
        # Área de contenido
        rx.box(
            content,
            background=Colors.BG_APP,
            width="100%",
            flex="1",
            overflow_y="auto",
            padding=Spacing.LG,
            min_height="100vh",
        ),
        
        width="100%",
        spacing="0",
        align_items="stretch",
    )