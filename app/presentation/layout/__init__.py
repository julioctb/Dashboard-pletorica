"""
Layout - Componentes de Layout del Sistema
==========================================

Exporta todos los componentes de layout:
- Sidebar colapsable
- Page layout estándar
- Header y toolbar de página

Uso:
    from app.presentation.layout import (
        sidebar,
        main_layout,
        page_layout,
        page_header,
        page_toolbar,
        SidebarState,
    )
"""

from .sidebar_state import SidebarState

from .sidebar_layout import (
    sidebar,
    sidebar_desktop,
    sidebar_item,
    sidebar_group,
)

from .page_layout import (
    page_header,
    page_toolbar,
    page_layout,
    page_content_area,
    main_layout,
    view_toggle,
)


__all__ = [
    # Estado
    "SidebarState",
    
    # Sidebar
    "sidebar",
    "sidebar_desktop",
    "sidebar_item",
    "sidebar_group",
    
    # Page layout
    "page_header",
    "page_toolbar",
    "page_layout",
    "page_content_area",
    "main_layout",
    "view_toggle",
]