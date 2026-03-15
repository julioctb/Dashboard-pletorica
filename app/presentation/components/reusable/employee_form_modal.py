"""Wrapper reusable para modales de formulario de empleados."""

import reflex as rx

from app.presentation.components.ui import boton_guardar
from app.presentation.theme import Colors, Radius, Spacing, Typography


def employee_form_body(*children, spacing: str = "4", padding_y=Spacing.BASE) -> rx.Component:
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
        align="stretch",
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
    save_disabled=False,
    save_loading_text: str = "Guardando...",
    save_color_scheme: str = "blue",
    max_width: str = "600px",
    disable_cancel_while_saving=True,
) -> rx.Component:
    """Modal shell reusable para formularios de empleado.

    Contrato:
    - `body` debe ser un componente ya compuesto (idealmente `employee_form_body(...)`).
    - `on_cancel` y `on_save` son handlers del state consumidor.
    - Solo encapsula shell visual y footer de acciones.
    - Deshabilita `Cancelar` mientras `saving` por defecto para evitar doble submit/cierre.
    """
    cancel_disabled = saving if disable_cancel_while_saving else False

    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.vstack(
                    rx.dialog.title(
                        title,
                        margin="0",
                        font_size=Typography.SIZE_LG,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_PRIMARY,
                        line_height=Typography.LINE_HEIGHT_TIGHT,
                    ),
                    rx.dialog.description(
                        description,
                        margin="0",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                        line_height=Typography.LINE_HEIGHT_NORMAL,
                    ),
                    width="100%",
                    spacing="1",
                    align="start",
                    padding_x=Spacing.XL,
                    padding_top=Spacing.XL,
                    padding_bottom=Spacing.BASE,
                ),
                rx.box(
                    body,
                    width="100%",
                    flex="1",
                    overflow_y="auto",
                    padding_x=Spacing.XL,
                    padding_bottom=Spacing.XL,
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                        on_click=on_cancel,
                        disabled=cancel_disabled,
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.spacer(),
                    boton_guardar(
                        texto=save_text,
                        texto_guardando=save_loading_text,
                        on_click=on_save,
                        saving=saving,
                        disabled=save_disabled,
                        color_scheme=save_color_scheme,
                    ),
                    width="100%",
                    align="center",
                    padding_x=Spacing.XL,
                    padding_y=Spacing.BASE,
                    border_top=f"1px solid {Colors.BORDER}",
                ),
                width="100%",
                spacing="0",
                align="stretch",
                max_height="min(88vh, 960px)",
            ),
            max_width=max_width,
            width=f"calc(100vw - {Spacing.XXL})",
            padding="0",
            overflow="hidden",
            background=Colors.SURFACE,
            border_radius=Radius.XL,
        ),
        open=open_state,
        on_open_change=rx.noop,
    )
