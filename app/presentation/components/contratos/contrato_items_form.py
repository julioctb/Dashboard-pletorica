"""
Sub-componente para gestionar items de contrato con precios requeridos.

Se usa para contratos de ADQUISICION, donde los items se copian desde
la requisicion con cantidades ajustables y precios obligatorios.
"""
import reflex as rx
from app.presentation.pages.contratos.contratos_state import ContratosState


def _fila_contrato_item(item: dict, index: int) -> rx.Component:
    """Fila editable para un item de contrato con precio requerido."""
    return rx.table.row(
        # Incluir (checkbox)
        rx.table.cell(
            rx.checkbox(
                checked=item["incluir"],
                on_change=lambda v: ContratosState.actualizar_contrato_item_campo(index, "incluir", v),
                size="1",
            ),
        ),
        # Numero
        rx.table.cell(
            rx.text(item["numero_item"], size="2", weight="medium"),
        ),
        # Unidad de medida
        rx.table.cell(
            rx.text(item["unidad_medida"], size="2"),
        ),
        # Cantidad (editable)
        rx.table.cell(
            rx.input(
                value=item["cantidad"],
                on_change=lambda v: ContratosState.actualizar_contrato_item_campo(index, "cantidad", v),
                placeholder="1",
                size="2",
                width="80px",
            ),
        ),
        # Descripcion
        rx.table.cell(
            rx.text(item["descripcion"], size="2", trim="both"),
        ),
        # Precio unitario (requerido)
        rx.table.cell(
            rx.input(
                value=item["precio_unitario"],
                on_change=lambda v: ContratosState.actualizar_contrato_item_campo(index, "precio_unitario", v),
                placeholder="0.00",
                size="2",
                width="120px",
            ),
        ),
    )


def contrato_items_form() -> rx.Component:
    """
    Tabla editable de items para contrato de ADQUISICION.

    Los items vienen pre-llenados desde la requisicion con cantidades
    editables y precios obligatorios.
    """
    return rx.vstack(
        rx.hstack(
            rx.text("Items del contrato", weight="bold", size="3"),
            rx.spacer(),
            rx.text(
                "Los precios son obligatorios",
                size="1",
                color="orange",
            ),
            align="center",
            width="100%",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("", width="40px"),
                    rx.table.column_header_cell("#", width="40px"),
                    rx.table.column_header_cell("Unidad", width="80px"),
                    rx.table.column_header_cell("Cant.", width="80px"),
                    rx.table.column_header_cell("Descripcion"),
                    rx.table.column_header_cell("Precio Unit.", width="130px"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    ContratosState.form_contrato_items,
                    lambda item, idx: _fila_contrato_item(item, idx),
                ),
            ),
            width="100%",
            variant="surface",
            size="1",
        ),
        spacing="3",
        width="100%",
    )
