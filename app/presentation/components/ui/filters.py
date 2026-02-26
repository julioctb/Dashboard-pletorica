"""Componentes reutilizables para filtros y búsqueda."""
import reflex as rx
from typing import Callable, Optional
from app.presentation.theme import Colors, Spacing, Radius, Transitions


def input_busqueda(
    value: rx.Var,
    on_change: Callable,
    on_clear: Callable,
    on_key_down: Callable = None,
    placeholder: str = "Buscar por clave o nombre...",
    width: str = "320px",
    toolbar_style: bool = False,
) -> rx.Component:
    """
    Input de búsqueda con icono integrado y botón limpiar.

    Args:
        value: Variable de estado con el valor del input
        on_change: Función al cambiar el valor
        on_clear: Función al limpiar el input
        on_key_down: Función al presionar tecla (opcional, para Enter)
        placeholder: Texto placeholder
        width: Ancho del input
    """
    wrapper_props = {
        "position": "relative",
        "width": width,
        "display": "inline-block",
    }
    input_props = {}

    if toolbar_style:
        wrapper_props.update(
            {
                "display": "block",
                "background": Colors.SECONDARY_LIGHT,
                "border_radius": Radius.LG,
                "border": f"1px solid {Colors.BORDER}",
                "transition": Transitions.FAST,
                "style": {
                    "_focus_within": {
                        "border_color": Colors.PRIMARY,
                        "box_shadow": f"0 0 0 3px {Colors.PRIMARY_LIGHT}",
                    },
                },
            }
        )
        input_props = {
            "variant": "soft",
            "size": "2",
            "style": {
                "border": "none",
                "background": "transparent",
                "_focus": {
                    "outline": "none",
                },
            },
        }

    return rx.box(
        rx.icon(
            "search",
            size=16,
            color=Colors.TEXT_MUTED if toolbar_style else "gray",
            position="absolute",
            left=Spacing.MD if toolbar_style else "10px",
            top="50%",
            transform="translateY(-50%)",
        ),
        rx.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            on_key_down=on_key_down,
            padding_left="36px",
            padding_right="32px",
            width="100%",
            **input_props,
        ),
        # Botón limpiar (solo visible cuando hay texto)
        rx.cond(
            value != "",
                rx.icon_button(
                    rx.icon("x", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                    position="absolute",
                    right=Spacing.XS if toolbar_style else "4px",
                    top="50%",
                    transform="translateY(-50%)",
                    on_click=on_clear,
                    cursor="pointer",
                ),
        ),
        **wrapper_props,
    )


def indicador_filtros(
    tiene_filtros: rx.Var,
    on_limpiar: Callable,
) -> rx.Component:
    """
    Badge indicador de filtros activos con botón para limpiar.

    Args:
        tiene_filtros: Variable booleana indicando si hay filtros activos
        on_limpiar: Función para limpiar todos los filtros
    """
    return rx.cond(
        tiene_filtros,
        rx.badge(
            rx.hstack(
                rx.icon("filter", size=12),
                rx.text("Filtros activos", size="1"),
                rx.icon_button(
                    rx.icon("x", size=12),
                    size="1",
                    variant="ghost",
                    on_click=on_limpiar,
                    cursor="pointer",
                ),
                spacing="1",
                align="center",
            ),
            color_scheme="blue",
            variant="soft",
            radius="full",
        ),
    )


def contador_registros(
    total: rx.Var,
    tiene_filtros: rx.Var,
    texto_entidad: str = "registro",
    texto_entidad_plural: str = "",
) -> rx.Component:
    """
    Contador de registros con contexto de filtros.

    Args:
        total: Variable con el total de registros
        tiene_filtros: Variable booleana indicando si hay filtros activos
        texto_entidad: Nombre de la entidad en singular (ej: "tipo", "categoría")
        texto_entidad_plural: Nombre en plural (si vacío, se agrega 's')
    """
    plural = texto_entidad_plural if texto_entidad_plural else f"{texto_entidad}s"

    return rx.hstack(
        rx.icon("list", size=14, color="gray"),
        rx.cond(
            tiene_filtros,
            rx.text(
                f"{total} resultado(s) encontrado(s)",
                size="2",
                color="gray",
            ),
            rx.text(
                f"{total} {plural}",
                size="2",
                color="gray",
            ),
        ),
        spacing="2",
        align="center",
    )


def switch_inactivos(
    checked: rx.Var,
    on_change: Callable,
    label: str = "Mostrar inactivas",
) -> rx.Component:
    """
    Switch para mostrar/ocultar registros inactivos.

    Args:
        checked: Variable booleana con el estado del switch
        on_change: Función al cambiar el estado
        label: Texto del label
    """
    return rx.hstack(
        rx.switch(
            checked=checked,
            on_change=on_change,
            size="2",
        ),
        rx.text(
            label,
            size="2",
            color=Colors.TEXT_SECONDARY,
            cursor="pointer",
            on_click=on_change(~checked),
        ),
        gap=Spacing.SM,
        align="center",
        padding_x=Spacing.SM,
        padding_y=Spacing.XS,
        border_radius=Radius.MD,
    )


def select_estatus_onboarding(
    opciones: rx.Var,
    value: rx.Var,
    on_change: Callable,
    on_reload: Optional[Callable] = None,
    placeholder: str = "Estatus onboarding",
) -> rx.Component:
    """
    Select de estatus de onboarding reutilizable con boton recargar opcional.

    Args:
        opciones: Var con lista de dicts [{value, label}]
        value: Var con el valor seleccionado
        on_change: Handler al cambiar seleccion
        on_reload: Handler del boton recargar (si None, no se muestra)
        placeholder: Texto placeholder del trigger
    """
    children = [
        rx.select.root(
            rx.select.trigger(placeholder=placeholder),
            rx.select.content(
                rx.foreach(
                    opciones,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=value,
            on_change=on_change,
            size="2",
        ),
    ]

    if on_reload is not None:
        children.append(
            rx.button(
                rx.icon("refresh-cw", size=14),
                "Recargar",
                on_click=on_reload,
                variant="soft",
                size="2",
            ),
        )

    return rx.hstack(
        *children,
        spacing="3",
        align="center",
    )


def barra_filtros(
    *children,
    contador: rx.Component = None,
) -> rx.Component:
    """
    Contenedor card para barra de filtros.

    Args:
        *children: Componentes de filtro (input, switch, etc.)
        contador: Componente contador opcional
    """
    contenido = [
        rx.hstack(
            *children,
            spacing="4",
            width="100%",
            align="center",
        ),
    ]

    if contador:
        contenido.append(contador)

    return rx.card(
        rx.vstack(
            *contenido,
            spacing="3",
            width="100%",
        ),
        width="100%",
        padding="4",
        variant="surface",
    )
