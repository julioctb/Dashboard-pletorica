"""
Modales del módulo de Historial Laboral.

Este módulo es de SOLO LECTURA - solo tiene modal de detalle.
"""
import reflex as rx
from app.presentation.pages.backoffice.historial_laboral.state import HistorialLaboralState
from app.presentation.components.ui import identifier_badge
from app.presentation.components.ui.modals import modal_detalle
from app.presentation.theme import Colors


def tipo_movimiento_badge(tipo: str) -> rx.Component:
    """Badge para tipo de movimiento"""
    return rx.match(
        tipo,
        ("Alta en sistema", rx.badge("Alta", color_scheme="blue", variant="soft", size="1")),
        ("Asignación a plaza", rx.badge("Asignación", color_scheme="green", variant="soft", size="1")),
        ("Cambio de plaza", rx.badge("Cambio", color_scheme="cyan", variant="soft", size="1")),
        ("Cambio de sueldo", rx.badge("Sueldo", color_scheme=Colors.PORTAL_ACCENT_SCHEME, variant="soft", size="1")),
        ("Suspensión", rx.badge("Suspensión", color_scheme="amber", variant="soft", size="1")),
        ("Reactivación", rx.badge("Reactivación", color_scheme=Colors.PORTAL_ACCENT_SCHEME, variant="soft", size="1")),
        ("Baja del sistema", rx.badge("Baja", color_scheme="red", variant="soft", size="1")),
        # Default: usar rx.cond en lugar de "or" para variables reactivas
        rx.cond(
            tipo,
            rx.badge(tipo, color_scheme="gray", variant="soft", size="1"),
            rx.badge("N/A", color_scheme="gray", variant="soft", size="1"),
        ),
    )


def modal_detalle_historial() -> rx.Component:
    """Modal de detalle de un registro de historial"""
    return modal_detalle(
        open=HistorialLaboralState.mostrar_modal_detalle,
        titulo="Detalle del Movimiento",
        on_cerrar=HistorialLaboralState.cerrar_modal_detalle,
        max_width="450px",
        contenido=rx.cond(
            HistorialLaboralState.registro_seleccionado,
            rx.vstack(
                # Empleado
                rx.vstack(
                    rx.text("Empleado", size="1", color="gray"),
                    rx.hstack(
                        identifier_badge(HistorialLaboralState.registro_seleccionado["empleado_clave"]),
                        rx.text(
                            HistorialLaboralState.registro_seleccionado["empleado_nombre"],
                            weight="medium",
                        ),
                        spacing="2",
                    ),
                    spacing="1",
                    align_items="start",
                    width="100%",
                ),

                rx.divider(),

                # Tipo de movimiento
                rx.vstack(
                    rx.text("Tipo de Movimiento", size="1", color="gray"),
                    tipo_movimiento_badge(
                        HistorialLaboralState.registro_seleccionado["tipo_movimiento"]
                    ),
                    spacing="1",
                    align_items="start",
                    width="100%",
                ),

                rx.divider(),

                # Plaza (puede ser None)
                rx.vstack(
                    rx.text("Plaza", size="1", color="gray"),
                    rx.cond(
                        HistorialLaboralState.registro_seleccionado["plaza_numero"],
                        rx.vstack(
                            rx.text(
                                f"#{HistorialLaboralState.registro_seleccionado['plaza_numero']}",
                                weight="medium",
                            ),
                            rx.text(
                                HistorialLaboralState.registro_seleccionado["categoria_nombre"],
                                size="2",
                                color=Colors.TEXT_SECONDARY,
                            ),
                            spacing="1",
                            align_items="start",
                        ),
                        rx.text(
                            "Sin plaza asignada",
                            size="2",
                            color="gray",
                            style={"fontStyle": "italic"},
                        ),
                    ),
                    spacing="1",
                    align_items="start",
                    width="100%",
                ),

                rx.divider(),

                # Empresa y contrato
                rx.hstack(
                    rx.vstack(
                        rx.text("Empresa", size="1", color="gray"),
                        rx.cond(
                            HistorialLaboralState.registro_seleccionado["empresa_nombre"],
                            rx.text(
                                HistorialLaboralState.registro_seleccionado["empresa_nombre"],
                                size="2",
                            ),
                            rx.text("-", size="2", color="gray"),
                        ),
                        spacing="1",
                        align_items="start",
                    ),
                    rx.cond(
                        HistorialLaboralState.registro_seleccionado["contrato_codigo"],
                        rx.vstack(
                            rx.text("Contrato", size="1", color="gray"),
                            rx.text(
                                HistorialLaboralState.registro_seleccionado["contrato_codigo"],
                                size="2",
                            ),
                            spacing="1",
                            align_items="start",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                ),

                rx.divider(),

                # Período y duración
                rx.hstack(
                    rx.vstack(
                        rx.text("Período", size="1", color="gray"),
                        rx.text(
                            HistorialLaboralState.registro_seleccionado["periodo_texto"],
                            size="2",
                        ),
                        spacing="1",
                        align_items="start",
                    ),
                    rx.vstack(
                        rx.text("Duración", size="1", color="gray"),
                        rx.text(
                            HistorialLaboralState.registro_seleccionado["duracion_texto"],
                            size="2",
                            weight="medium",
                        ),
                        spacing="1",
                        align_items="start",
                    ),
                    spacing="4",
                    width="100%",
                ),

                spacing="4",
                width="100%",
                padding_y="4",
            ),
        ),
    )
