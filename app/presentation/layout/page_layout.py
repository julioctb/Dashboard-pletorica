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
from app.presentation.components.ui.headers import page_header as ui_page_header
from app.presentation.components.ui.view_toggle import view_toggle as ui_view_toggle
from app.presentation.components.ui.filters import input_busqueda
from app.presentation.theme import (
    Colors,
    Spacing,
    Radius,
    Typography,
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
    """Adapter compatible que delega al header shared de UI."""
    return rx.box(
        ui_page_header(
            icono=icono,
            titulo=titulo,
            subtitulo=subtitulo,
            accion_principal=accion_principal,
        ),
        width="100%",
        padding_bottom=Spacing.LG,
        margin_bottom=Spacing.MD,
        border_bottom=f"1px solid {Colors.BORDER}",
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
    return ui_view_toggle(
        value=current_view,
        on_change_table=on_change_table,
        on_change_cards=on_change_cards,
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
    left_group = rx.flex(
        rx.box(
            input_busqueda(
                value=search_value,
                on_change=on_search_change,
                on_clear=on_search_clear,
                placeholder=search_placeholder,
                width="100%",
                toolbar_style=True,
            ),
            width="100%",
            min_width="260px",
            max_width="400px",
            flex="1 1 300px",
        ),
        filters if filters else rx.fragment(),
        wrap="wrap",
        align="center",
        column_gap=Spacing.MD,
        row_gap=Spacing.SM,
        flex="1 1 420px",
        width="100%",
    )

    right_group = rx.flex(
        extra_right if extra_right else rx.fragment(),
        rx.cond(
            show_view_toggle,
            view_toggle(
                current_view=current_view,
                on_change_table=on_view_table,
                on_change_cards=on_view_cards,
            ),
            rx.fragment(),
        ),
        wrap="wrap",
        align="center",
        justify="end",
        column_gap=Spacing.SM,
        row_gap=Spacing.SM,
    )

    return rx.flex(
        left_group,
        right_group,
        wrap="wrap",
        align="center",
        justify="between",
        width="100%",
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border_radius=Radius.LG,
        border=f"1px solid {Colors.BORDER}",
        margin_bottom=Spacing.MD,
        column_gap=Spacing.MD,
        row_gap=Spacing.SM,
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
