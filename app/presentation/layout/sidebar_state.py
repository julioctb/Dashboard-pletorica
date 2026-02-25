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

from app.presentation.components.shared.auth_state import AuthState


class SidebarState(AuthState):
    """
    Estado global del sidebar.

    Solo maneja colapso/expansión. La lógica de simulación de cliente
    está en AuthState para que sea compartida con PortalState.

    Attributes:
        is_collapsed: True si el sidebar está en modo icono-only
        entregables_pendientes: Contador de entregables en revisión
    """

    is_collapsed: bool = False
    entregables_pendientes: int = 0

    def toggle(self):
        """Alterna entre expandido y colapsado."""
        self.is_collapsed = not self.is_collapsed

    def expand(self):
        """Expande el sidebar."""
        self.is_collapsed = False

    def collapse(self):
        """Colapsa el sidebar."""
        self.is_collapsed = True

    async def cargar_alertas(self):
        """Carga el contador de entregables pendientes de revisión."""
        try:
            from app.services import entregable_service
            self.entregables_pendientes = await entregable_service.contar_en_revision()
        except Exception:
            self.entregables_pendientes = 0

    @rx.var
    def tiene_alertas_entregables(self) -> bool:
        """True si hay entregables pendientes de revisión."""
        return self.entregables_pendientes > 0

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

    @rx.var
    def usuario_contexto_sidebar(self) -> str:
        """
        Texto secundario del usuario en el sidebar.

        Evita mostrar "Sin empresa" para perfiles internos de plataforma.
        """
        if self.es_superadmin:
            return "Administrador"

        if self.es_institucion and self.institucion_actual:
            return str(self.institucion_actual.get("nombre", "Institución"))

        return self.nombre_empresa_actual
