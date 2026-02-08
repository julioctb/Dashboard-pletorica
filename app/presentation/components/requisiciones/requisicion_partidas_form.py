"""Sub-componente para gestionar partidas presupuestales dentro del formulario."""
import reflex as rx
from app.presentation.pages.requisiciones.requisiciones_state import RequisicionesState


def _fila_partida(partida: dict, index: int) -> rx.Component:
    """Fila editable para una partida presupuestal."""
    return rx.table.row(
        # Partida presupuestaria
        rx.table.cell(
            rx.input(
                value=partida["partida_presupuestaria"],
                on_change=lambda v: RequisicionesState.actualizar_partida_campo(index, "partida_presupuestaria", v),
                placeholder="Partida",
                size="2",
                width="100%",
            ),
        ),
        # Origen recurso
        rx.table.cell(
            rx.input(
                value=partida["origen_recurso"],
                on_change=lambda v: RequisicionesState.actualizar_partida_campo(index, "origen_recurso", v),
                placeholder="Origen",
                size="2",
                width="100%",
            ),
        ),
        # Acciones
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("trash-2", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=lambda: RequisicionesState.eliminar_partida(index),
                ),
                content="Eliminar partida",
            ),
        ),
    )


def requisicion_partidas_form() -> rx.Component:
    """Tabla editable de partidas presupuestales para el formulario."""
    return rx.vstack(
        rx.hstack(
            rx.text("Partidas Presupuestales", weight="bold", size="3"),
            rx.spacer(),
            align="center",
            width="100%",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Partida"),
                    rx.table.column_header_cell("Origen Recurso"),
                    rx.table.column_header_cell("", width="50px"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    RequisicionesState.form_partidas,
                    lambda partida, idx: _fila_partida(partida, idx),
                ),
            ),
            width="100%",
            variant="surface",
            size="1",
        ),
        rx.button(
            rx.icon("plus", size=14),
            "Agregar partida",
            on_click=RequisicionesState.agregar_partida,
            variant="soft",
            size="2",
        ),
        spacing="3",
        width="100%",
    )
