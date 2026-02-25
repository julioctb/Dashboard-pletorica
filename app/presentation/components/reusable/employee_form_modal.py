"""Wrapper reusable para modales de formulario de empleados."""

import reflex as rx

from app.presentation.components.ui import boton_cancelar, boton_guardar


def employee_form_body(*children, spacing: str = "4", padding_y="4") -> rx.Component:
    """Contenedor reusable para cuerpos de formulario de empleado.

    Contrato:
    - Recibe componentes (`children`) ya construidos por el modulo consumidor.
    - Estandariza `spacing`, `width` y `padding_y`.
    - No contiene logica de negocio ni handlers de estado.
    """
    return rx.vstack(
        *children,
        spacing=spacing,
        width="100%",
        padding_y=padding_y,
    )


def employee_form_modal(
    *,
    open_state,
    title,
    description,
    body: rx.Component,
    on_cancel,
    on_save,
    save_text,
    saving,
    save_loading_text: str = "Guardando...",
    save_color_scheme: str = "blue",
    max_width: str = "600px",
) -> rx.Component:
    """Modal shell reusable para formularios de empleado.

    Contrato:
    - `body` debe ser un componente ya compuesto (idealmente `employee_form_body(...)`).
    - `on_cancel` y `on_save` son handlers del state consumidor.
    - Solo encapsula shell visual y footer de acciones.
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(title),
            rx.dialog.description(description),
            body,
            rx.hstack(
                boton_cancelar(on_click=on_cancel),
                boton_guardar(
                    texto=save_text,
                    texto_guardando=save_loading_text,
                    on_click=on_save,
                    saving=saving,
                    color_scheme=save_color_scheme,
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),
            max_width=max_width,
        ),
        open=open_state,
        on_open_change=rx.noop,
    )
