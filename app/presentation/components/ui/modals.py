"""
Componentes de modal genéricos reutilizables.

Proporciona modales estándar para operaciones comunes como:
- Confirmación de eliminación
- Confirmación de acciones
- Modales de formulario

Uso:
    from app.presentation.components.ui import (
        modal_confirmar_eliminar,
        modal_confirmar_accion,
    )

    # Modal de eliminación simple
    modal_confirmar_eliminar(
        open=MiState.mostrar_confirmar,
        titulo="Eliminar Registro",
        mensaje="¿Está seguro de eliminar este registro?",
        detalle_contenido=rx.text(MiState.item["nombre"]),
        on_confirmar=MiState.eliminar,
        on_cancelar=MiState.cerrar_modal,
        loading=MiState.saving,
    )
"""
import reflex as rx
from typing import Any, Optional, Union

from app.presentation.components.ui.buttons import boton_guardar, botones_modal
from app.presentation.theme import Colors, Radius, Spacing, Typography


MODAL_CONTENT_PADDING = Spacing.XL
MODAL_SECTION_GAP = Spacing.BASE


def modal_confirmar_eliminar(
    open: Union[bool, rx.Var],
    titulo: str = "Eliminar",
    mensaje: str = "¿Está seguro de eliminar este elemento?",
    detalle_contenido: Optional[rx.Component] = None,
    advertencia: str = "Esta acción no se puede deshacer.",
    on_confirmar: callable = None,
    on_cancelar: callable = None,
    loading: Union[bool, rx.Var] = False,
    texto_confirmar: str = "Eliminar",
    texto_eliminando: str = "Eliminando...",
    texto_cancelar: str = "Cancelar",
    max_width: str = "400px",
) -> rx.Component:
    """
    Modal genérico para confirmar eliminación.

    Args:
        open: Estado que controla si el modal está abierto
        titulo: Título del modal
        mensaje: Mensaje principal de confirmación
        detalle_contenido: Componente opcional con detalles del elemento a eliminar
        advertencia: Texto de advertencia (None para ocultar)
        on_confirmar: Evento al confirmar
        on_cancelar: Evento al cancelar
        loading: Estado de carga
        texto_confirmar: Texto del botón de confirmar
        texto_eliminando: Texto mostrado mientras se elimina
        texto_cancelar: Texto del botón de cancelar
        max_width: Ancho máximo del modal

    Returns:
        Componente rx.alert_dialog configurado
    """
    contenido = [rx.text(mensaje)]

    # Agregar detalle si existe
    if detalle_contenido is not None:
        contenido.append(
            rx.callout(
                detalle_contenido,
                icon="triangle-alert",
                color_scheme="red",
                size="2",
            )
        )

    # Agregar advertencia si existe
    if advertencia:
        contenido.append(
            rx.text(advertencia, size="2", color="gray")
        )

    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(titulo),
            rx.alert_dialog.description(
                rx.vstack(
                    *contenido,
                    spacing="3",
                ),
            ),
            rx.box(
                botones_modal(
                    on_guardar=on_confirmar,
                    on_cancelar=on_cancelar,
                    saving=loading,
                    texto_guardar=texto_confirmar,
                    texto_guardando=texto_eliminando,
                    texto_cancelar=texto_cancelar,
                    color_guardar="red",
                ),
                width="100%",
                margin_top=MODAL_SECTION_GAP,
            ),
            max_width=max_width,
            padding=MODAL_CONTENT_PADDING,
        ),
        open=open,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_confirmar_accion(
    open: Union[bool, rx.Var],
    titulo: str,
    mensaje: str,
    detalle_contenido: Optional[rx.Component] = None,
    nota_adicional: Optional[str] = None,
    on_confirmar: callable = None,
    on_cancelar: callable = None,
    loading: Union[bool, rx.Var] = False,
    texto_confirmar: str = "Confirmar",
    texto_confirmando: str = "Procesando...",
    texto_cancelar: str = "Cancelar",
    color_confirmar: str = "blue",
    icono_detalle: str = "info",
    color_detalle: str = "blue",
    max_width: str = "400px",
) -> rx.Component:
    """
    Modal genérico para confirmar cualquier acción.

    Más flexible que modal_confirmar_eliminar, permite personalizar
    colores e iconos.

    Args:
        open: Estado que controla si el modal está abierto
        titulo: Título del modal
        mensaje: Mensaje principal
        detalle_contenido: Componente con detalles adicionales
        nota_adicional: Texto adicional en gris
        on_confirmar: Evento al confirmar
        on_cancelar: Evento al cancelar
        loading: Estado de carga
        texto_confirmar: Texto del botón confirmar
        texto_confirmando: Texto mostrado mientras se confirma
        texto_cancelar: Texto del botón cancelar
        color_confirmar: Color del botón confirmar
        icono_detalle: Icono del callout de detalle
        color_detalle: Color del callout de detalle
        max_width: Ancho máximo del modal

    Returns:
        Componente rx.alert_dialog configurado
    """
    contenido = [rx.text(mensaje)]

    if detalle_contenido is not None:
        contenido.append(
            rx.callout(
                detalle_contenido,
                icon=icono_detalle,
                color_scheme=color_detalle,
                size="2",
            )
        )

    if nota_adicional is not None:
        if isinstance(nota_adicional, rx.Var):
            contenido.append(
                rx.cond(
                    nota_adicional != "",
                    rx.text(nota_adicional, size="2", color="gray"),
                    rx.fragment(),
                )
            )
        else:
            contenido.append(
                rx.text(nota_adicional, size="2", color="gray")
            )

    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(titulo),
            rx.alert_dialog.description(
                rx.vstack(
                    *contenido,
                    spacing="3",
                ),
            ),
            rx.box(
                botones_modal(
                    on_guardar=on_confirmar,
                    on_cancelar=on_cancelar,
                    saving=loading,
                    texto_guardar=texto_confirmar,
                    texto_guardando=texto_confirmando,
                    texto_cancelar=texto_cancelar,
                    color_guardar=color_confirmar,
                ),
                width="100%",
                margin_top=MODAL_SECTION_GAP,
            ),
            max_width=max_width,
            padding=MODAL_CONTENT_PADDING,
        ),
        open=open,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_formulario(
    open: Union[bool, rx.Var],
    titulo: Any,
    descripcion: Any = "",
    contenido: rx.Component = None,
    on_guardar: callable = None,
    on_cancelar: callable = None,
    puede_guardar: Union[bool, rx.Var] = True,
    loading: Union[bool, rx.Var] = False,
    texto_guardar: Any = "Guardar",
    texto_guardando: str = "Guardando...",
    texto_cancelar: str = "Cancelar",
    max_width: str = "500px",
    icono: Optional[str] = None,
    icono_componente: Optional[rx.Component] = None,
    color_icono: str = "teal",
    scroll_body: bool = False,
    max_body_height: str = "70vh",
    color_guardar: str = "blue",
    disable_cancelar_guardando: bool = False,
    extra_footer_left: Optional[rx.Component] = None,
) -> rx.Component:
    """Modal genérico para formularios. Todos los modales del sistema heredan de aquí.

    Args:
        open: Estado que controla si el modal está abierto
        titulo: Título del modal (str o rx.Var para títulos dinámicos)
        descripcion: Descripción debajo del título (str, rx.Var o rx.Component)
        contenido: Componente con los campos del formulario
        on_guardar: Evento al guardar
        on_cancelar: Evento al cancelar
        puede_guardar: Si el botón guardar está habilitado
        loading: Estado de carga
        texto_guardar: Texto del botón guardar (acepta rx.Var)
        texto_guardando: Texto mostrado mientras guarda
        texto_cancelar: Texto del botón cancelar
        max_width: Ancho máximo del modal
        icono: Nombre de ícono lucide para el header (ej: "building", "clock")
        icono_componente: Componente de ícono ya construido (alternativa a icono)
        color_icono: Ramp Radix para colorear el ícono ("teal", "blue", "amber", etc.)
        scroll_body: Si True, el body tiene overflow_y=auto con max_body_height
        max_body_height: Alto máximo del body scrolleable
        color_guardar: Color del botón guardar (ramp Radix)
        disable_cancelar_guardando: Si True, deshabilita Cancelar mientras loading
        extra_footer_left: Componente extra alineado a la izquierda del footer (ej: botón "Limpiar")
    """
    cancel_disabled = loading if disable_cancelar_guardando else False
    if puede_guardar is True:
        guardar_disabled: Any = False
    elif isinstance(puede_guardar, rx.Var):
        guardar_disabled = ~puede_guardar
    else:
        guardar_disabled = not puede_guardar

    # Ícono en header
    _icon_box = None
    if icono_componente is not None:
        _icon_box = icono_componente
    elif icono is not None:
        _icon_box = rx.box(
            rx.icon(icono, size=20, color=f"var(--{color_icono}-11)"),
            background=f"var(--{color_icono}-3)",
            border_radius=Radius.LG,
            padding="10px",
            flex_shrink="0",
        )

    # Bloque título + descripción (elementos accesibles de Radix Dialog)
    _desc_children = [
        rx.dialog.title(
            titulo,
            margin="0",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_PRIMARY,
            line_height=Typography.LINE_HEIGHT_TIGHT,
        ),
    ]
    if isinstance(descripcion, rx.Var):
        _desc_children.append(
            rx.cond(
                descripcion != "",
                rx.dialog.description(
                    descripcion,
                    margin="0",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                    line_height=Typography.LINE_HEIGHT_NORMAL,
                ),
                rx.fragment(),
            )
        )
    elif descripcion != "":
        _desc_children.append(
            rx.dialog.description(
                descripcion,
                margin="0",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                line_height=Typography.LINE_HEIGHT_NORMAL,
            )
        )

    _title_block = rx.vstack(
        *_desc_children,
        spacing="0",
        align="start",
        flex="1",
    )

    # Header: [icon?] [title_block] [X button]
    _header_children = []
    if _icon_box is not None:
        _header_children.append(_icon_box)
    _header_children.append(_title_block)
    _header_children.append(
        rx.button(
            rx.icon("x", size=16),
            variant="ghost",
            color_scheme="gray",
            size="2",
            on_click=on_cancelar,
            disabled=cancel_disabled,
            padding="4px",
            cursor="pointer",
            flex_shrink="0",
        )
    )

    # Body props opcionales
    _body_extra: dict = {}
    if scroll_body:
        _body_extra["overflow_y"] = "auto"
        _body_extra["max_height"] = max_body_height

    _vstack_extra: dict = {}
    if scroll_body:
        _vstack_extra["max_height"] = "min(88vh, 960px)"

    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header con ícono, título y botón X
                rx.hstack(
                    *_header_children,
                    width="100%",
                    align="center",
                    spacing="3",
                    padding_x=Spacing.XL,
                    padding_y=Spacing.BASE,
                    border_bottom=f"1px solid {Colors.BORDER}",
                ),
                # Body (scrolleable si scroll_body=True)
                rx.box(
                    contenido,
                    width="100%",
                    flex="1",
                    padding_x=Spacing.XL,
                    padding_top=Spacing.BASE,
                    padding_bottom=Spacing.XL,
                    **_body_extra,
                ),
                # Footer
                rx.hstack(
                    extra_footer_left if extra_footer_left is not None else rx.fragment(),
                    rx.spacer() if extra_footer_left is not None else rx.fragment(),
                    rx.button(
                        texto_cancelar,
                        variant="outline",
                        color_scheme="gray",
                        size="2",
                        on_click=on_cancelar,
                        disabled=cancel_disabled,
                    ),
                    boton_guardar(
                        texto=texto_guardar,
                        texto_guardando=texto_guardando,
                        on_click=on_guardar,
                        saving=loading,
                        disabled=guardar_disabled,
                        color_scheme=color_guardar,
                    ),
                    justify="end" if extra_footer_left is None else "between",
                    spacing="2",
                    width="100%",
                    align="center",
                    padding_x=Spacing.XL,
                    padding_y=Spacing.BASE,
                    border_top=f"1px solid {Colors.BORDER}",
                ),
                spacing="0",
                width="100%",
                align="stretch",
                **_vstack_extra,
            ),
            max_width=max_width,
            width=f"calc(100vw - {Spacing.XXL})",
            padding="0",
            overflow="hidden",
            background=Colors.SURFACE,
            border_radius=Radius.XL,
        ),
        open=open,
        on_open_change=rx.noop,
    )


def modal_detalle(
    open: Union[bool, rx.Var],
    titulo: str,
    contenido: rx.Component,
    on_cerrar: callable = None,
    boton_accion: Optional[rx.Component] = None,
    max_width: str = "500px",
) -> rx.Component:
    """
    Modal genérico para mostrar detalles (solo lectura).

    Args:
        open: Estado que controla si el modal está abierto
        titulo: Título del modal
        contenido: Componente con los detalles a mostrar
        on_cerrar: Evento al cerrar (opcional, el dialog.close funciona automáticamente)
        boton_accion: Botón adicional opcional (ej: "Editar")
        max_width: Ancho máximo del modal

    Returns:
        Componente rx.dialog configurado
    """
    botones = [
        rx.button(
            "Cerrar",
            variant="soft",
            color_scheme="gray",
            on_click=on_cerrar,
        ),
    ]

    if boton_accion is not None:
        botones.append(boton_accion)

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(titulo),
            contenido,
            rx.hstack(
                *botones,
                justify="end",
                spacing="3",
                margin_top=MODAL_SECTION_GAP,
            ),
            max_width=max_width,
            padding=MODAL_CONTENT_PADDING,
        ),
        open=open,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )
