"""Sub-componente para gestionar items dentro del formulario de requisiciones."""
import reflex as rx
from app.presentation.pages.requisiciones.requisiciones_state import RequisicionesState


def _fila_item(item: dict, index: int) -> rx.Component:
    """Fila editable para un item de requisicion."""
    return rx.table.row(
        # Numero
        rx.table.cell(
            rx.text(item["numero_item"], size="2", weight="medium"),
        ),
        # Unidad de medida
        rx.table.cell(
            rx.input(
                value=item["unidad_medida"],
                on_change=lambda v: RequisicionesState.actualizar_item_campo(index, "unidad_medida", v),
                placeholder="Pieza",
                size="2",
                width="100%",
            ),
        ),
        # Cantidad
        rx.table.cell(
            rx.input(
                value=item["cantidad"],
                on_change=lambda v: RequisicionesState.actualizar_item_campo(index, "cantidad", v),
                placeholder="1",
                size="2",
                width="80px",
            ),
        ),
        # Descripcion
        rx.table.cell(
            rx.input(
                value=item["descripcion"],
                on_change=lambda v: RequisicionesState.actualizar_item_campo(index, "descripcion", v),
                placeholder="Descripcion del bien/servicio",
                size="2",
                width="100%",
            ),
        ),
        # Precio unitario
        rx.table.cell(
            rx.input(
                value=item["precio_unitario_estimado"],
                on_change=lambda v: RequisicionesState.actualizar_item_campo(index, "precio_unitario_estimado", v),
                placeholder="0.00",
                size="2",
                width="100px",
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
                    on_click=lambda: RequisicionesState.eliminar_item(index),
                ),
                content="Eliminar item",
            ),
        ),
    )


def requisicion_items_form() -> rx.Component:
    """Tabla editable de items para el formulario de requisicion."""
    return rx.vstack(
        rx.hstack(
            rx.text("Items", weight="bold", size="3"),
            rx.spacer(),
            rx.text("Total estimado: ", size="2", color="gray"),
            rx.text(RequisicionesState.total_estimado_items, size="2", weight="bold"),
            align="center",
            width="100%",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("#", width="50px"),
                    rx.table.column_header_cell("Unidad", width="100px"),
                    rx.table.column_header_cell("Cant.", width="80px"),
                    rx.table.column_header_cell("Descripcion"),
                    rx.table.column_header_cell("Precio Unit.", width="110px"),
                    rx.table.column_header_cell("", width="50px"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    RequisicionesState.form_items,
                    lambda item, idx: _fila_item(item, idx),
                ),
            ),
            width="100%",
            variant="surface",
            size="1",
        ),
        rx.button(
            rx.icon("plus", size=14),
            "Agregar item",
            on_click=RequisicionesState.agregar_item,
            variant="soft",
            size="2",
        ),
        spacing="3",
        width="100%",
    )
