"""Wrapper reusable para modales de formulario de empleados."""

from typing import Any, Optional, Union

import reflex as rx

from core.presentation.components.ui.modals import modal_formulario
from core.presentation.theme import Spacing


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
    title: Any,
    description: Any,
    body: rx.Component,
    on_cancel,
    on_save,
    save_text: Any,
    saving: Union[bool, rx.Var],
    save_disabled: Union[bool, rx.Var] = False,
    save_loading_text: str = "Guardando...",
    save_color_scheme: str = "blue",
    max_width: str = "600px",
    disable_cancel_while_saving: bool = True,
    header_icon: Optional[rx.Component] = None,
) -> rx.Component:
    """Thin wrapper de modal_formulario para formularios de empleado.

    Defaults específicos:
    - scroll_body=True (formulario largo con múltiples secciones)
    - max_body_height="min(88vh, 960px)"
    - disable_cancelar_guardando configurable via disable_cancel_while_saving

    Contrato:
    - `body` debe ser un componente ya compuesto (idealmente employee_form_body(...)).
    - `on_cancel` y `on_save` son handlers del state consumidor.
    - `header_icon`: rx.Component opcional (rx.box con rx.icon) para el header.
    """
    if isinstance(save_disabled, rx.Var):
        puede_guardar: Any = ~save_disabled
    else:
        puede_guardar = not save_disabled

    return modal_formulario(
        open=open_state,
        titulo=title,
        descripcion=description,
        contenido=body,
        on_guardar=on_save,
        on_cancelar=on_cancel,
        puede_guardar=puede_guardar,
        loading=saving,
        texto_guardar=save_text,
        texto_guardando=save_loading_text,
        color_guardar=save_color_scheme,
        max_width=max_width,
        icono_componente=header_icon,
        scroll_body=True,
        max_body_height="min(88vh, 960px)",
        disable_cancelar_guardando=disable_cancel_while_saving,
    )
