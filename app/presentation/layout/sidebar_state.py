"""
Sidebar State - Estado del Sidebar Colapsable
==============================================

Maneja el estado de expansión/colapso del sidebar.
No persiste entre sesiones (se reinicia al recargar).

Uso:
    from app.presentation.layout import SidebarState
    
    # En componentes:
    rx.cond(SidebarState.is_collapsed, ..., ...)
    
    # Toggle:
    on_click=SidebarState.toggle
"""

import reflex as rx


class SidebarState(rx.State):
    """
    Estado global del sidebar.
    
    Attributes:
        is_collapsed: True si el sidebar está en modo icono-only
    """
    
    is_collapsed: bool = False
    
    def toggle(self):
        """Alterna entre expandido y colapsado."""
        self.is_collapsed = not self.is_collapsed
    
    def expand(self):
        """Expande el sidebar."""
        self.is_collapsed = False
    
    def collapse(self):
        """Colapsa el sidebar."""
        self.is_collapsed = True
    
    @rx.var
    def sidebar_width(self) -> str:
        """Retorna el ancho actual del sidebar."""
        return "72px" if self.is_collapsed else "240px"
    
    @rx.var
    def toggle_icon(self) -> str:
        """Retorna el icono del botón toggle."""
        return "chevron-right" if self.is_collapsed else "chevron-left"
    
    @rx.var
    def toggle_tooltip(self) -> str:
        """Retorna el tooltip del botón toggle."""
        return "Expandir menú" if self.is_collapsed else "Colapsar menú"