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
from typing import Optional, Union

from app.presentation.components.ui.buttons import botones_modal
from app.presentation.theme import Spacing


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

    if nota_adicional:
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
    titulo: str,
    descripcion: str,
    contenido: rx.Component,
    on_guardar: callable,
    on_cancelar: callable,
    puede_guardar: Union[bool, rx.Var] = True,
    loading: Union[bool, rx.Var] = False,
    texto_guardar: str = "Guardar",
    texto_guardando: str = "Guardando...",
    texto_cancelar: str = "Cancelar",
    max_width: str = "500px",
) -> rx.Component:
    """
    Modal genérico para formularios.

    Args:
        open: Estado que controla si el modal está abierto
        titulo: Título del modal
        descripcion: Descripción debajo del título
        contenido: Componente con los campos del formulario
        on_guardar: Evento al guardar
        on_cancelar: Evento al cancelar
        puede_guardar: Si el botón guardar está habilitado
        loading: Estado de carga
        texto_guardar: Texto del botón guardar
        texto_guardando: Texto mostrado mientras guarda
        texto_cancelar: Texto del botón cancelar
        max_width: Ancho máximo del modal

    Returns:
        Componente rx.dialog configurado
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(titulo),
            rx.dialog.description(
                descripcion,
                margin_bottom=MODAL_SECTION_GAP,
            ),
            contenido,
            rx.box(
                botones_modal(
                    on_guardar=on_guardar,
                    on_cancelar=on_cancelar,
                    saving=loading,
                    disabled=(
                        ~puede_guardar if isinstance(puede_guardar, rx.Var) else not puede_guardar
                    ),
                    texto_guardar=texto_guardar,
                    texto_guardando=texto_guardando,
                    texto_cancelar=texto_cancelar,
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
