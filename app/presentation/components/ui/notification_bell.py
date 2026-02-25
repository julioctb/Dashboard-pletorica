"""
Notification Bell - Componente de campana de notificaciones
===========================================================

Componente para mostrar notificaciones no leidas con:
- Icono campana con badge de conteo
- Popover con lista de notificaciones recientes
- Accion de "marcar todas como leidas"

Uso:
    from app.presentation.components.ui.notification_bell import notification_bell

    # En sidebar admin
    notification_bell()

    # En sidebar portal
    notification_bell_portal()
"""

import logging
from typing import Callable, List

import reflex as rx

from app.entities.notificacion import Notificacion
from app.presentation.theme import Colors, Radius, Spacing, Typography

logger = logging.getLogger(__name__)


def _notificacion_to_dict(n: Notificacion) -> dict:
    """Convierte una Notificacion a dict para el estado."""
    return {
        "id": n.id,
        "titulo": n.titulo,
        "mensaje": n.mensaje,
        "tipo": n.tipo,
        "leida": n.leida,
        "entidad_tipo": n.entidad_tipo or "",
        "entidad_id": n.entidad_id or 0,
        "fecha_creacion": str(n.fecha_creacion) if n.fecha_creacion else "",
    }


class NotificationBellState(rx.State):
    """Estado para el componente de campana de notificaciones."""

    notificaciones: list[dict] = []
    total_no_leidas: int = 0
    cargando: bool = False
    popover_abierto: bool = False

    # =========================================================================
    # COMPUTED VARS
    # =========================================================================

    @rx.var
    def tiene_notificaciones(self) -> bool:
        return self.total_no_leidas > 0

    @rx.var
    def texto_badge(self) -> str:
        if self.total_no_leidas > 99:
            return "99+"
        return str(self.total_no_leidas)

    # =========================================================================
    # CARGA DE NOTIFICACIONES
    # =========================================================================

    def _procesar_notificaciones(self, notificaciones: List[Notificacion]) -> None:
        """Procesa y almacena las notificaciones."""
        self.notificaciones = [_notificacion_to_dict(n) for n in notificaciones]

    async def cargar_notificaciones(self):
        """Carga notificaciones admin + personales del usuario actual."""
        self.cargando = True
        try:
            from app.services import notificacion_service
            from app.presentation.components.shared.auth_state import AuthState

            # Obtener ID del usuario actual
            auth = await self.get_state(AuthState)
            usuario_id = auth.id_usuario

            if usuario_id:
                # Cargar notificaciones combinadas (admin + personales)
                self.total_no_leidas = await notificacion_service.contar_no_leidas_usuario_admin(usuario_id)
                notificaciones = await notificacion_service.obtener_para_usuario_admin(
                    usuario_id=usuario_id,
                    solo_no_leidas=False,
                    limite=10,
                )
            else:
                # Fallback: solo admin si no hay usuario
                self.total_no_leidas = await notificacion_service.contar_no_leidas_admin()
                notificaciones = await notificacion_service.obtener_admin(
                    solo_no_leidas=False,
                    limite=10,
                )

            self._procesar_notificaciones(notificaciones)
        except Exception as e:
            logger.warning("Error cargando notificaciones admin: %s", e)
            self.notificaciones = []
            self.total_no_leidas = 0
        finally:
            self.cargando = False

    async def cargar_notificaciones_portal(self):
        """Carga notificaciones de la empresa activa del portal."""
        try:
            from app.presentation.portal.state.portal_state import PortalState
            portal = await self.get_state(PortalState)
            empresa_id = portal.id_empresa_actual
            if empresa_id:
                await self._cargar_notificaciones_empresa(empresa_id)
        except Exception as e:
            logger.warning("Error cargando notificaciones portal: %s", e)
            self.notificaciones = []
            self.total_no_leidas = 0

    async def _cargar_notificaciones_empresa(self, empresa_id: int):
        """Carga notificaciones de una empresa."""
        self.cargando = True
        try:
            from app.services import notificacion_service
            self.total_no_leidas = await notificacion_service.contar_no_leidas_empresa(empresa_id)
            notificaciones = await notificacion_service.obtener_por_empresa(
                empresa_id=empresa_id,
                solo_no_leidas=False,
                limite=10,
            )
            self._procesar_notificaciones(notificaciones)
        except Exception as e:
            logger.warning("Error cargando notificaciones empresa %s: %s", empresa_id, e)
            self.notificaciones = []
            self.total_no_leidas = 0
        finally:
            self.cargando = False

    # =========================================================================
    # MARCAR COMO LEIDAS
    # =========================================================================

    def _marcar_todas_localmente(self) -> None:
        """Marca todas las notificaciones como leidas en el estado local."""
        for n in self.notificaciones:
            n["leida"] = True
        self.total_no_leidas = 0

    async def marcar_leida(self, notificacion_id: int):
        """Marca una notificacion como leida."""
        try:
            from app.services import notificacion_service
            await notificacion_service.marcar_leida(notificacion_id)
            for n in self.notificaciones:
                if n.get("id") == notificacion_id:
                    n["leida"] = True
            self.total_no_leidas = max(0, self.total_no_leidas - 1)
        except Exception as e:
            logger.warning("Error marcando notificación %s como leída: %s", notificacion_id, e)

    async def marcar_todas_leidas(self):
        """Marca todas las notificaciones como leidas (admin + personales)."""
        try:
            from app.services import notificacion_service
            from app.presentation.components.shared.auth_state import AuthState

            auth = await self.get_state(AuthState)
            usuario_id = auth.id_usuario

            if usuario_id:
                await notificacion_service.marcar_todas_leidas_usuario_admin(usuario_id)
            else:
                await notificacion_service.marcar_todas_leidas_admin()

            self._marcar_todas_localmente()
        except Exception as e:
            logger.warning("Error marcando todas las notificaciones (admin) como leídas: %s", e)

    async def marcar_todas_leidas_empresa(self):
        """Marca todas las notificaciones como leidas (portal cliente)."""
        try:
            from app.presentation.portal.state.portal_state import PortalState
            portal = await self.get_state(PortalState)
            empresa_id = portal.id_empresa_actual
            if not empresa_id:
                return
            from app.services import notificacion_service
            await notificacion_service.marcar_todas_leidas_empresa(empresa_id)
            self._marcar_todas_localmente()
        except Exception as e:
            logger.warning("Error marcando notificaciones de empresa como leídas: %s", e)

    # =========================================================================
    # NAVEGACION
    # =========================================================================

    def toggle_popover(self):
        self.popover_abierto = not self.popover_abierto

    def cerrar_popover(self):
        self.popover_abierto = False

    def navegar_a_entidad(self, entidad_tipo: str, entidad_id: int):
        """Navega a la entidad relacionada (admin routes)."""
        self.popover_abierto = False
        rutas = {
            "ENTREGABLE": f"/entregables/{entidad_id}" if entidad_id else "/entregables",
            "REQUISICION": "/wip/requisiciones",
        }
        return rx.redirect(rutas.get(entidad_tipo, "/"))

    def navegar_a_entidad_portal(self, entidad_tipo: str, entidad_id: int):
        """Navega a la entidad relacionada (portal routes)."""
        self.popover_abierto = False
        rutas = {
            "ENTREGABLE": "/portal/entregables",
            "REQUISICION": "/portal",  # Portal no tiene requisiciones
        }
        return rx.redirect(rutas.get(entidad_tipo, "/portal"))


# =============================================================================
# COMPONENTES UI
# =============================================================================

def _notificacion_item(
    notificacion: dict,
    on_click_handler: Callable,
) -> rx.Component:
    """Item individual de notificacion en el popover."""
    return rx.button(
        rx.hstack(
            # Indicador de no leida
            rx.cond(
                ~notificacion["leida"],
                rx.box(
                    width="8px",
                    height="8px",
                    border_radius=Radius.FULL,
                    background=Colors.PRIMARY,
                    flex_shrink="0",
                ),
                rx.box(width="8px", height="8px", flex_shrink="0"),
            ),
            # Contenido
            rx.vstack(
                rx.text(
                    notificacion["titulo"],
                    size="2",
                    weight=rx.cond(~notificacion["leida"], "bold", "regular"),
                    no_of_lines=1,
                ),
                rx.text(
                    notificacion["mensaje"],
                    size="1",
                    color=Colors.TEXT_MUTED,
                    no_of_lines=2,
                ),
                spacing="0",
                align="start",
                flex="1",
            ),
            padding_y=Spacing.XS,
            padding_x=Spacing.SM,
            width="100%",
            align="center",
            gap=Spacing.SM,
        ),
        variant="ghost",
        size="1",
        width="100%",
        cursor="pointer",
        on_click=lambda: on_click_handler(
            notificacion["entidad_tipo"],
            notificacion["entidad_id"],
        ),
        style={
            "padding": "0",
            "height": "auto",
            "justify_content": "flex-start",
            "border_radius": Radius.MD,
            "_hover": {"background": Colors.SURFACE_HOVER},
        },
    )


def _badge_conteo() -> rx.Component:
    """Badge con el conteo de notificaciones."""
    return rx.cond(
        NotificationBellState.tiene_notificaciones,
        rx.box(
            rx.text(
                NotificationBellState.texto_badge,
                font_size=Typography.SIZE_XS,
                font_weight="bold",
                color=Colors.TEXT_INVERSE,
                line_height="1",
            ),
            position="absolute",
            top="-2px",
            right="-2px",
            background=Colors.ERROR,
            border_radius="50%",
            min_width="18px",
            height="18px",
            display="flex",
            align_items="center",
            justify_content="center",
            padding_x=Spacing.XS,
        ),
        rx.fragment(),
    )


def _trigger_button() -> rx.Component:
    """Botón trigger de la campana con badge."""
    return rx.box(
        rx.icon_button(
            rx.icon("bell", size=18),
            variant="ghost",
            color_scheme="gray",
            size="2",
            cursor="pointer",
        ),
        _badge_conteo(),
        position="relative",
    )


def _empty_state() -> rx.Component:
    """Estado vacío cuando no hay notificaciones."""
    return rx.center(
        rx.vstack(
            rx.icon("bell-off", size=24, color=Colors.TEXT_MUTED),
            rx.text("Sin notificaciones", size="2", color=Colors.TEXT_MUTED),
            spacing="2",
            align="center",
        ),
        padding="6",
    )


def _popover_content(
    on_marcar_todas: Callable,
    item_renderer: Callable[[dict], rx.Component],
) -> rx.Component:
    """Contenido del popover de notificaciones."""
    return rx.popover.content(
        rx.vstack(
            # Header
            rx.hstack(
                rx.text("Notificaciones", size="3", weight="bold"),
                rx.spacer(),
                rx.cond(
                    NotificationBellState.tiene_notificaciones,
                    rx.button(
                        "Marcar todas",
                        size="1",
                        variant="ghost",
                        on_click=on_marcar_todas,
                    ),
                    rx.fragment(),
                ),
                width="100%",
                align="center",
            ),
            rx.divider(),
            # Lista de notificaciones
            rx.cond(
                NotificationBellState.cargando,
                rx.center(rx.spinner(size="2"), padding="4"),
                rx.cond(
                    NotificationBellState.notificaciones.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            NotificationBellState.notificaciones,
                            item_renderer,
                        ),
                        spacing="0",
                        width="100%",
                        max_height="300px",
                        overflow_y="auto",
                    ),
                    _empty_state(),
                ),
            ),
            spacing="2",
            width="100%",
        ),
        width="320px",
        side="right",
    )


# =============================================================================
# COMPONENTES PÚBLICOS
# =============================================================================

def notification_bell() -> rx.Component:
    """
    Componente de campana de notificaciones (admin).
    Muestra badge con conteo y popover con lista.
    """
    return rx.popover.root(
        rx.popover.trigger(_trigger_button()),
        _popover_content(
            on_marcar_todas=NotificationBellState.marcar_todas_leidas,
            item_renderer=lambda n: _notificacion_item(
                n, NotificationBellState.navegar_a_entidad
            ),
        ),
        on_open_change=lambda _: NotificationBellState.cargar_notificaciones(),
    )


def notification_bell_portal() -> rx.Component:
    """
    Version del bell para el portal de cliente.
    Carga notificaciones por empresa_id al abrir.
    """
    return rx.popover.root(
        rx.popover.trigger(_trigger_button()),
        _popover_content(
            on_marcar_todas=NotificationBellState.marcar_todas_leidas_empresa,
            item_renderer=lambda n: _notificacion_item(
                n, NotificationBellState.navegar_a_entidad_portal
            ),
        ),
        on_open_change=lambda _: NotificationBellState.cargar_notificaciones_portal(),
    )
