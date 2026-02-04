"""
Sidebar State - Estado del Sidebar Colapsable
==============================================

Maneja el estado de expansión/colapso del sidebar.
Hereda de AuthState para acceder a información del usuario logueado
(nombre, empresa actual, rol) y métodos de sesión (cerrar_sesion).

Uso:
    from app.presentation.layout import SidebarState

    # En componentes:
    rx.cond(SidebarState.is_collapsed, ..., ...)
    SidebarState.nombre_usuario  # nombre del usuario logueado
    SidebarState.es_admin  # True si es administrador

    # Toggle:
    on_click=SidebarState.toggle
"""

import reflex as rx
from typing import List

from app.presentation.components.shared.auth_state import AuthState


class SidebarState(AuthState):
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

    # =========================================================================
    # DEV VIEW SWITCHER (solo DEBUG)
    # =========================================================================

    @rx.var
    def dev_modo_cliente_activo(self) -> bool:
        """True si el dev switcher está en modo cliente (empresas cargadas o simulando)."""
        return len(self._empresas_simulacion) > 0 or self._simulando_cliente

    @rx.var
    def opciones_empresas_simulacion(self) -> List[dict]:
        """Opciones de empresas para el select de simulación."""
        return [
            {"label": e["nombre"], "value": str(e["id"])}
            for e in self._empresas_simulacion
        ]

    @rx.var
    def valor_empresa_simulada(self) -> str:
        """Valor actual del select de empresa simulada."""
        if self._simulando_cliente and self.empresa_actual:
            return str(self.empresa_actual.get("empresa_id", ""))
        return ""

    async def on_dev_view_change(self, vista: str):
        """Handler para toggle Admin/Cliente en dev switcher."""
        if vista == "cliente":
            await self.cargar_empresas_simulacion()
        else:
            return self.desactivar_simulacion_cliente()