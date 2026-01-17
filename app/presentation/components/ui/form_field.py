"""
Componente de campo de formulario unificado basado en FieldConfig.

Uso:
    from app.core.validation import CAMPO_RFC
    from app.presentation.components.ui.form_field import form_field

    form_field(
        config=CAMPO_RFC,
        value=State.form_rfc,
        on_change=State.set_form_rfc,
        on_blur=State.validar_rfc,
        error=State.error_rfc
    )
"""
import reflex as rx
from typing import Any, Optional, Callable, List, Tuple

from app.core.validation import FieldConfig, InputType


def form_field(
    config: FieldConfig,
    value: Any,
    on_change: Callable,
    on_blur: Optional[Callable] = None,
    error: Any = "",
    disabled: bool = False,
    options: Optional[List[str]] = None,
    **kwargs
) -> rx.Component:
    """
    Genera un campo de formulario completo basado en FieldConfig.

    Renderiza automáticamente el tipo de input correcto (text, email, tel,
    number, select, textarea) con label, hint y manejo de errores.

    Args:
        config: Configuración del campo (FieldConfig)
        value: Valor actual del campo (state var)
        on_change: Handler para cambios
        on_blur: Handler para validación al perder foco (opcional)
        error: Mensaje de error a mostrar (state var, opcional)
        disabled: Si el campo está deshabilitado
        options: Lista de opciones para select (sobrescribe config.options)
        **kwargs: Props adicionales para el input

    Returns:
        rx.Component con label, input apropiado, hint y error
    """
    # Determinar el ancho del contenedor
    width = _get_width(config.width)

    # Construir el campo según el tipo
    if config.input_type == InputType.SELECT:
        input_component = _build_select(config, value, on_change, disabled, options, **kwargs)
    elif config.input_type == InputType.TEXTAREA:
        input_component = _build_textarea(config, value, on_change, on_blur, disabled, **kwargs)
    else:
        input_component = _build_input(config, value, on_change, on_blur, disabled, **kwargs)

    return rx.box(
        rx.vstack(
            # Label
            rx.text(
                config.label,
                size="2",
                weight="medium",
                color=rx.cond(error != "", "red", "gray"),
            ),
            # Input component
            input_component,
            # Hint o Error (error tiene prioridad)
            rx.cond(
                error != "",
                rx.text(error, color="red", size="1"),
                rx.cond(
                    config.hint is not None,
                    rx.text(config.hint, color="gray", size="1"),
                    rx.fragment(),
                ),
            ),
            spacing="1",
            width="100%",
            align="start",
        ),
        width=width,
    )


def _get_width(width_config: str) -> str:
    """Convierte width config a valor CSS."""
    widths = {
        "full": "100%",
        "half": "48%",
        "third": "32%",
    }
    return widths.get(width_config, "100%")


def _build_input(
    config: FieldConfig,
    value: Any,
    on_change: Callable,
    on_blur: Optional[Callable],
    disabled: bool,
    **kwargs
) -> rx.Component:
    """Construye un input estándar (text, email, tel, number, password)."""
    # Mapeo de InputType a type HTML
    type_map = {
        InputType.TEXT: "text",
        InputType.EMAIL: "email",
        InputType.TEL: "tel",
        InputType.NUMBER: "number",
        InputType.PASSWORD: "password",
    }
    input_type = type_map.get(config.input_type, "text")

    props = {
        "placeholder": config.placeholder,
        "value": value,
        "on_change": on_change,
        "type": input_type,
        "size": "2",
        "width": "100%",
        "disabled": disabled,
        **kwargs,
    }

    if on_blur:
        props["on_blur"] = on_blur

    if config.max_len:
        props["max_length"] = config.max_len

    return rx.input(**props)


def _build_select(
    config: FieldConfig,
    value: Any,
    on_change: Callable,
    disabled: bool,
    options: Optional[List[str]] = None,
    **kwargs
) -> rx.Component:
    """Construye un select con opciones."""
    # Usar opciones pasadas como parámetro, o las del config
    if options is not None:
        option_values = options
    elif config.options:
        # Convertir lista de tuplas a lista de strings para el select
        option_values = [opt[0] for opt in config.options]
    else:
        option_values = []

    return rx.select(
        option_values,
        placeholder=config.placeholder,
        value=value,
        on_change=on_change,
        size="2",
        width="100%",
        disabled=disabled,
        **kwargs,
    )


def _build_textarea(
    config: FieldConfig,
    value: Any,
    on_change: Callable,
    on_blur: Optional[Callable],
    disabled: bool,
    **kwargs
) -> rx.Component:
    """Construye un textarea."""
    props = {
        "placeholder": config.placeholder,
        "value": value,
        "on_change": on_change,
        "size": "2",
        "width": "100%",
        "rows": str(config.rows),
        "disabled": disabled,
        **kwargs,
    }

    if on_blur:
        props["on_blur"] = on_blur

    return rx.text_area(**props)


def form_section(
    title: str,
    children: List[rx.Component],
    columns: int = 2,
    description: Optional[str] = None,
) -> rx.Component:
    """
    Agrupa campos de formulario en una sección con título.

    Args:
        title: Título de la sección
        children: Lista de form_field components
        columns: Número de columnas (1, 2, o 3)
        description: Descripción opcional de la sección

    Returns:
        rx.Component con la sección formateada
    """
    # Calcular gap según columnas
    gap = "4" if columns > 1 else "3"

    return rx.box(
        rx.vstack(
            # Header de sección
            rx.vstack(
                rx.text(
                    title,
                    size="3",
                    weight="bold",
                    color="gray",
                ),
                rx.cond(
                    description is not None,
                    rx.text(description, size="2", color="gray"),
                    rx.fragment(),
                ) if description else rx.fragment(),
                spacing="1",
                align="start",
                width="100%",
            ),
            # Separador
            rx.divider(size="4"),
            # Grid de campos
            rx.box(
                *children,
                display="flex",
                flex_wrap="wrap",
                gap=gap,
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        width="100%",
        padding="4",
        background="var(--gray-a2)",
        border_radius="8px",
        margin_bottom="4",
    )
