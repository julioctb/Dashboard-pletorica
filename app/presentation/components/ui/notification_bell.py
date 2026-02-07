"""
Notification Bell - Componente de campana de notificaciones
===========================================================

Componente para mostrar notificaciones no leidas con:
- Icono campana con badge de conteo
- Popover con lista de notificaciones recientes
- Accion de "marcar todas como leidas"

Uso:
    from app.presentation.components.ui.notification_bell import notification_bell

    # En sidebar
    notification_bell()
"""

import reflex as rx
from app.presentation.theme import Colors, Spacing, Radius, Typography


class NotificationBellState(rx.State):
    """Estado para el componente de campana de notificaciones."""

    notificaciones: list[dict] = []
    total_no_leidas: int = 0
    cargando: bool = False
    popover_abierto: bool = False

    @rx.var
    def tiene_notificaciones(self) -> bool:
        return self.total_no_leidas > 0

    @rx.var
    def texto_badge(self) -> str:
        if self.total_no_leidas > 99:
            return "99+"
        return str(self.total_no_leidas)

    async def cargar_notificaciones(self):
        """Carga notificaciones admin (usuario_id=None, empresa_id=None)."""
        self.cargando = True
        try:
            from app.services import notificacion_service
            self.total_no_leidas = await notificacion_service.contar_no_leidas_admin()
            notificaciones = await notificacion_service.obtener_admin(
                solo_no_leidas=False,
                limite=10,
            )
            self.notificaciones = [
                {
                    "id": n.id,
                    "titulo": n.titulo,
                    "mensaje": n.mensaje,
                    "tipo": n.tipo,
                    "leida": n.leida,
                    "entidad_tipo": n.entidad_tipo or "",
                    "entidad_id": n.entidad_id or 0,
                    "fecha_creacion": str(n.fecha_creacion) if n.fecha_creacion else "",
                }
                for n in notificaciones
            ]
        except Exception:
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
                await self.cargar_notificaciones_empresa(empresa_id)
        except Exception:
            self.notificaciones = []
            self.total_no_leidas = 0

    async def cargar_notificaciones_empresa(self, empresa_id: int):
        """Carga notificaciones de una empresa (para portal de cliente)."""
        self.cargando = True
        try:
            from app.services import notificacion_service
            self.total_no_leidas = await notificacion_service.contar_no_leidas_empresa(empresa_id)
            notificaciones = await notificacion_service.obtener_por_empresa(
                empresa_id=empresa_id,
                solo_no_leidas=False,
                limite=10,
            )
            self.notificaciones = [
                {
                    "id": n.id,
                    "titulo": n.titulo,
                    "mensaje": n.mensaje,
                    "tipo": n.tipo,
                    "leida": n.leida,
                    "entidad_tipo": n.entidad_tipo or "",
                    "entidad_id": n.entidad_id or 0,
                    "fecha_creacion": str(n.fecha_creacion) if n.fecha_creacion else "",
                }
                for n in notificaciones
            ]
        except Exception:
            self.notificaciones = []
            self.total_no_leidas = 0
        finally:
            self.cargando = False

    async def marcar_leida(self, notificacion_id: int):
        """Marca una notificacion como leida."""
        try:
            from app.services import notificacion_service
            await notificacion_service.marcar_leida(notificacion_id)
            # Actualizar en local
            for n in self.notificaciones:
                if n.get("id") == notificacion_id:
                    n["leida"] = True
            self.total_no_leidas = max(0, self.total_no_leidas - 1)
        except Exception:
            pass

    async def marcar_todas_leidas(self):
        """Marca todas las notificaciones como leidas (admin)."""
        try:
            from app.services import notificacion_service
            await notificacion_service.marcar_todas_leidas_admin()
            for n in self.notificaciones:
                n["leida"] = True
            self.total_no_leidas = 0
        except Exception:
            pass

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
            for n in self.notificaciones:
                n["leida"] = True
            self.total_no_leidas = 0
        except Exception:
            pass

    def toggle_popover(self):
        self.popover_abierto = not self.popover_abierto

    def cerrar_popover(self):
        self.popover_abierto = False

    def navegar_a_entidad(self, entidad_tipo: str, entidad_id: int):
        """Navega a la entidad relacionada (admin routes)."""
        self.popover_abierto = False
        if entidad_tipo == "ENTREGABLE" and entidad_id:
            return rx.redirect(f"/entregables/{entidad_id}")
        return rx.redirect("/")

    def navegar_a_entidad_portal(self, entidad_tipo: str, entidad_id: int):
        """Navega a la entidad relacionada (portal routes)."""
        self.popover_abierto = False
        if entidad_tipo == "ENTREGABLE" and entidad_id:
            return rx.redirect("/portal/entregables")
        return rx.redirect("/portal")


def _notificacion_item(notificacion: dict) -> rx.Component:
    """Item individual de notificacion en el popover."""
    return rx.hstack(
        rx.cond(
            ~notificacion["leida"],
            rx.box(
                width="8px",
                height="8px",
                border_radius="50%",
                background=Colors.PRIMARY,
                flex_shrink="0",
            ),
            rx.box(width="8px", height="8px", flex_shrink="0"),
        ),
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
        cursor="pointer",
        border_radius=Radius.MD,
        _hover={"background": Colors.SURFACE_HOVER},
        on_click=lambda: NotificationBellState.navegar_a_entidad(
            notificacion["entidad_tipo"],
            notificacion["entidad_id"],
        ),
    )


def _notificacion_item_portal(notificacion: dict) -> rx.Component:
    """Item individual de notificacion para portal de cliente."""
    return rx.hstack(
        rx.cond(
            ~notificacion["leida"],
            rx.box(
                width="8px",
                height="8px",
                border_radius="50%",
                background=Colors.PRIMARY,
                flex_shrink="0",
            ),
            rx.box(width="8px", height="8px", flex_shrink="0"),
        ),
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
        cursor="pointer",
        border_radius=Radius.MD,
        _hover={"background": Colors.SURFACE_HOVER},
        on_click=lambda: NotificationBellState.navegar_a_entidad_portal(
            notificacion["entidad_tipo"],
            notificacion["entidad_id"],
        ),
    )


def notification_bell() -> rx.Component:
    """
    Componente de campana de notificaciones (admin).
    Muestra badge con conteo y popover con lista.
    """
    return rx.popover.root(
        rx.popover.trigger(
            rx.box(
                rx.icon_button(
                    rx.icon("bell", size=18),
                    variant="ghost",
                    color_scheme="gray",
                    size="2",
                    cursor="pointer",
                ),
                # Badge de conteo
                rx.cond(
                    NotificationBellState.tiene_notificaciones,
                    rx.box(
                        rx.text(
                            NotificationBellState.texto_badge,
                            font_size="10px",
                            font_weight="bold",
                            color="white",
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
                        padding_x="4px",
                    ),
                    rx.fragment(),
                ),
                position="relative",
            ),
        ),
        rx.popover.content(
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
                            on_click=NotificationBellState.marcar_todas_leidas,
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
                                _notificacion_item,
                            ),
                            spacing="0",
                            width="100%",
                            max_height="300px",
                            overflow_y="auto",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("bell-off", size=24, color=Colors.TEXT_MUTED),
                                rx.text("Sin notificaciones", size="2", color=Colors.TEXT_MUTED),
                                spacing="2",
                                align="center",
                            ),
                            padding="6",
                        ),
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            width="320px",
            side="right",
        ),
        on_open_change=lambda _: NotificationBellState.cargar_notificaciones(),
    )


def notification_bell_portal() -> rx.Component:
    """
    Version del bell para el portal de cliente.
    Carga notificaciones por empresa_id al abrir.
    """
    return rx.popover.root(
        rx.popover.trigger(
            rx.box(
                rx.icon_button(
                    rx.icon("bell", size=18),
                    variant="ghost",
                    color_scheme="gray",
                    size="2",
                    cursor="pointer",
                ),
                rx.cond(
                    NotificationBellState.tiene_notificaciones,
                    rx.box(
                        rx.text(
                            NotificationBellState.texto_badge,
                            font_size="10px",
                            font_weight="bold",
                            color="white",
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
                        padding_x="4px",
                    ),
                    rx.fragment(),
                ),
                position="relative",
            ),
        ),
        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Notificaciones", size="3", weight="bold"),
                    rx.spacer(),
                    rx.cond(
                        NotificationBellState.tiene_notificaciones,
                        rx.button(
                            "Marcar todas",
                            size="1",
                            variant="ghost",
                            on_click=NotificationBellState.marcar_todas_leidas_empresa,
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.divider(),
                rx.cond(
                    NotificationBellState.cargando,
                    rx.center(rx.spinner(size="2"), padding="4"),
                    rx.cond(
                        NotificationBellState.notificaciones.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                NotificationBellState.notificaciones,
                                _notificacion_item_portal,
                            ),
                            spacing="0",
                            width="100%",
                            max_height="300px",
                            overflow_y="auto",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("bell-off", size=24, color=Colors.TEXT_MUTED),
                                rx.text("Sin notificaciones", size="2", color=Colors.TEXT_MUTED),
                                spacing="2",
                                align="center",
                            ),
                            padding="6",
                        ),
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            width="320px",
            side="right",
        ),
        on_open_change=lambda _: NotificationBellState.cargar_notificaciones_portal(),
    )
