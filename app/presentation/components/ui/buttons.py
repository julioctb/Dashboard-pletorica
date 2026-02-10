"""
Componentes de botones reutilizables.

Proporciona botones estándar con estados de carga consistentes:
- boton_guardar: Botón para guardar con spinner y texto "Guardando..."
- boton_accion: Botón genérico con estado de carga

Uso:
    from app.presentation.components.ui import boton_guardar

    boton_guardar(
        texto="Crear Empresa",
        texto_guardando="Creando...",
        on_click=MiState.crear,
        saving=MiState.saving,
        disabled=MiState.tiene_errores,
    )
"""
import reflex as rx
from typing import Union, Optional


def boton_guardar(
    texto: str = "Guardar",
    texto_guardando: str = "Guardando...",
    on_click: callable = None,
    saving: Union[bool, rx.Var] = False,
    disabled: Union[bool, rx.Var] = False,
    color_scheme: str = "blue",
    size: str = "2",
    variant: str = "solid",
    width: Optional[str] = None,
    **kwargs,
) -> rx.Component:
    """
    Botón de guardar con estado de carga estandarizado.

    Cuando saving=True:
    - Muestra spinner + texto_guardando
    - Se deshabilita automáticamente
    - Previene múltiples clicks

    Args:
        texto: Texto del botón en estado normal
        texto_guardando: Texto mostrado mientras guarda (con spinner)
        on_click: Evento al hacer click
        saving: Estado de guardado (rx.Var recomendado)
        disabled: Deshabilitar botón (adicional a saving)
        color_scheme: Color del botón (blue, green, red, etc.)
        size: Tamaño del botón (1, 2, 3)
        variant: Variante del botón (solid, soft, outline, ghost)
        width: Ancho opcional del botón
        **kwargs: Props adicionales para rx.button

    Returns:
        Componente rx.button con estado de carga

    Example:
        boton_guardar(
            texto="Crear Usuario",
            texto_guardando="Creando...",
            on_click=UsuariosState.crear,
            saving=UsuariosState.saving,
            disabled=UsuariosState.tiene_errores,
        )
    """
    # Construir props del botón
    button_props = {
        "color_scheme": color_scheme,
        "size": size,
        "variant": variant,
        **kwargs,
    }

    if width is not None:
        button_props["width"] = width

    if on_click is not None:
        button_props["on_click"] = on_click

    # disabled: combinar saving con disabled adicional
    if isinstance(saving, rx.Var) and isinstance(disabled, rx.Var):
        button_props["disabled"] = saving | disabled
    elif isinstance(saving, rx.Var):
        button_props["disabled"] = saving if not disabled else saving | True
    elif isinstance(disabled, rx.Var):
        button_props["disabled"] = disabled if not saving else disabled | True
    else:
        button_props["disabled"] = saving or disabled

    return rx.button(
        rx.cond(
            saving,
            rx.hstack(
                rx.spinner(size="1"),
                texto_guardando,
                spacing="2",
                align="center",
            ),
            texto,
        ),
        **button_props,
    )


def boton_cancelar(
    texto: str = "Cancelar",
    on_click: callable = None,
    disabled: Union[bool, rx.Var] = False,
    size: str = "2",
    **kwargs,
) -> rx.Component:
    """
    Botón de cancelar estándar.

    Args:
        texto: Texto del botón
        on_click: Evento al hacer click
        disabled: Deshabilitar botón
        size: Tamaño del botón
        **kwargs: Props adicionales

    Returns:
        Componente rx.button estilizado para cancelar
    """
    return rx.button(
        texto,
        variant="soft",
        color_scheme="gray",
        size=size,
        on_click=on_click,
        disabled=disabled,
        **kwargs,
    )


def boton_eliminar(
    texto: str = "Eliminar",
    texto_eliminando: str = "Eliminando...",
    on_click: callable = None,
    saving: Union[bool, rx.Var] = False,
    disabled: Union[bool, rx.Var] = False,
    size: str = "2",
    **kwargs,
) -> rx.Component:
    """
    Botón de eliminar con estado de carga.

    Args:
        texto: Texto del botón en estado normal
        texto_eliminando: Texto mostrado mientras elimina
        on_click: Evento al hacer click
        saving: Estado de guardado
        disabled: Deshabilitar botón
        size: Tamaño del botón
        **kwargs: Props adicionales

    Returns:
        Componente rx.button rojo con estado de carga
    """
    return boton_guardar(
        texto=texto,
        texto_guardando=texto_eliminando,
        on_click=on_click,
        saving=saving,
        disabled=disabled,
        color_scheme="red",
        size=size,
        **kwargs,
    )


def botones_modal(
    on_guardar: callable = None,
    on_cancelar: callable = None,
    saving: Union[bool, rx.Var] = False,
    disabled: Union[bool, rx.Var] = False,
    texto_guardar: str = "Guardar",
    texto_guardando: str = "Guardando...",
    texto_cancelar: str = "Cancelar",
    color_guardar: str = "blue",
    size: str = "2",
) -> rx.Component:
    """
    Par de botones estándar para modales (Cancelar + Guardar).

    Uso común en footers de modales de formulario.

    Args:
        on_guardar: Evento del botón guardar
        on_cancelar: Evento del botón cancelar
        saving: Estado de guardado
        disabled: Deshabilitar botón guardar
        texto_guardar: Texto del botón guardar
        texto_guardando: Texto mientras guarda
        texto_cancelar: Texto del botón cancelar
        color_guardar: Color del botón guardar
        size: Tamaño de los botones

    Returns:
        rx.hstack con botones Cancelar y Guardar
    """
    return rx.hstack(
        boton_cancelar(
            texto=texto_cancelar,
            on_click=on_cancelar,
            size=size,
        ),
        boton_guardar(
            texto=texto_guardar,
            texto_guardando=texto_guardando,
            on_click=on_guardar,
            saving=saving,
            disabled=disabled,
            color_scheme=color_guardar,
            size=size,
        ),
        spacing="3",
        justify="end",
    )
