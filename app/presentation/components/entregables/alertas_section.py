"""
Sección de Alertas de Entregables para el Dashboard.
Muestra resumen de entregables pendientes de revisión con acceso rápido.
"""

import reflex as rx
from typing import List

from app.presentation.theme import Colors, Spacing, Typography, Radius, Shadows


# =============================================================================
# ESTADO DE ALERTAS
# =============================================================================
class AlertasEntregablesState(rx.State):
    """Estado para las alertas de entregables en el dashboard."""

    alertas: List[dict] = []
    total_en_revision: int = 0
    cargando: bool = False

    @rx.var
    def tiene_alertas(self) -> bool:
        return self.total_en_revision > 0

    @rx.var
    def mensaje_alerta(self) -> str:
        if self.total_en_revision == 0:
            return "No hay entregables pendientes"
        elif self.total_en_revision == 1:
            return "1 entregable pendiente de revisión"
        else:
            return f"{self.total_en_revision} entregables pendientes de revisión"

    async def cargar_alertas(self):
        self.cargando = True
        try:
            from app.services import entregable_service
            alertas = await entregable_service.obtener_alertas(limite=5)
            self.total_en_revision = alertas.total_en_revision
            self.alertas = [
                {
                    "id": e.id,
                    "contrato_codigo": e.contrato_codigo,
                    "empresa_nombre": e.empresa_nombre,
                    "numero_periodo": e.numero_periodo,
                    "periodo_texto": e.periodo_texto,
                    "fecha_entrega": str(e.fecha_entrega) if e.fecha_entrega else "",
                }
                for e in alertas.entregables
            ]
        except Exception:
            self.alertas = []
            self.total_en_revision = 0
        finally:
            self.cargando = False

    def ir_a_entregable(self, entregable_id: int):
        return rx.redirect(f"/entregables/{entregable_id}")

    def ir_a_entregables(self):
        return rx.redirect("/entregables")


# =============================================================================
# COMPONENTES
# =============================================================================
def _alerta_item(alerta: dict) -> rx.Component:
    return rx.hstack(
        rx.center(
            rx.icon("search", size=16, color=Colors.INFO),
            width="32px",
            height="32px",
            background=Colors.INFO_LIGHT,
            border_radius=Radius.MD,
        ),
        rx.vstack(
            rx.hstack(
                rx.text(alerta["contrato_codigo"], size="2", weight="medium"),
                rx.text("•", color=Colors.TEXT_MUTED, size="1"),
                rx.text(f"Período {alerta['numero_periodo']}", size="2", color=Colors.TEXT_SECONDARY),
                spacing="1",
            ),
            rx.text(alerta["empresa_nombre"], size="1", color=Colors.TEXT_MUTED, no_of_lines=1),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.button(
            rx.icon("arrow-right", size=14),
            size="1",
            variant="ghost",
            on_click=lambda: AlertasEntregablesState.ir_a_entregable(alerta["id"]),
        ),
        padding=Spacing.SM,
        border_radius=Radius.MD,
        _hover={"background": Colors.SURFACE_HOVER},
        cursor="pointer",
        width="100%",
        on_click=lambda: AlertasEntregablesState.ir_a_entregable(alerta["id"]),
    )


def alertas_entregables_card() -> rx.Component:
    """
    Card de alertas de entregables para el dashboard.
    Uso: from app.presentation.components.entregables import alertas_entregables_card
    """
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.hstack(rx.icon("package-check", size=20, color=Colors.INFO), rx.text("Entregables", size="4", weight="bold"), spacing="2"),
                rx.spacer(),
                rx.cond(
                    AlertasEntregablesState.tiene_alertas,
                    rx.badge(AlertasEntregablesState.total_en_revision, color_scheme="sky", variant="solid", radius="full"),
                    rx.badge("0", color_scheme="gray", variant="soft", radius="full"),
                ),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.cond(
                    AlertasEntregablesState.tiene_alertas,
                    rx.icon("circle-alert", size=14, color=Colors.INFO),
                    rx.icon("circle-check", size=14, color=Colors.SUCCESS),
                ),
                rx.text(
                    AlertasEntregablesState.mensaje_alerta,
                    size="2",
                    color=rx.cond(AlertasEntregablesState.tiene_alertas, Colors.INFO, Colors.TEXT_MUTED),
                ),
                spacing="1",
                align="center",
            ),
            rx.divider(),
            rx.cond(
                AlertasEntregablesState.cargando,
                rx.center(rx.spinner(size="2"), padding="4"),
                rx.cond(
                    AlertasEntregablesState.tiene_alertas,
                    rx.vstack(
                        rx.foreach(AlertasEntregablesState.alertas, _alerta_item),
                        rx.cond(
                            AlertasEntregablesState.total_en_revision > 5,
                            rx.button(
                                f"Ver todos ({AlertasEntregablesState.total_en_revision})",
                                variant="ghost",
                                size="1",
                                width="100%",
                                on_click=AlertasEntregablesState.ir_a_entregables,
                            ),
                            rx.fragment(),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("inbox", size=32, color=Colors.TEXT_MUTED),
                            rx.text("Sin entregables pendientes", size="2", color=Colors.TEXT_MUTED),
                            spacing="2",
                            align="center",
                        ),
                        padding="6",
                    ),
                ),
            ),
            spacing="3",
            width="100%",
        ),
        padding="4",
    )


def alertas_entregables_badge() -> rx.Component:
    """
    Badge pequeño para mostrar en el sidebar.
    Uso: rx.hstack(rx.icon("package-check"), rx.text("Entregables"), rx.spacer(), alertas_entregables_badge())
    """
    return rx.cond(
        AlertasEntregablesState.total_en_revision > 0,
        rx.badge(AlertasEntregablesState.total_en_revision, color_scheme="sky", variant="solid", radius="full", size="1"),
        rx.fragment(),
    )


def seccion_alertas_dashboard() -> rx.Component:
    """
    Sección de alertas para el dashboard principal.
    Uso: from app.presentation.components.entregables import seccion_alertas_dashboard
    """
    return rx.vstack(
        rx.hstack(rx.icon("bell", size=20, color=Colors.PRIMARY), rx.text("Alertas y Pendientes", size="5", weight="bold"), spacing="2", align="center"),
        rx.grid(alertas_entregables_card(), columns="1", spacing="4", width="100%"),
        spacing="4",
        width="100%",
        padding_bottom=Spacing.XL,
    )
