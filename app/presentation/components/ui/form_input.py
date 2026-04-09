"""Componentes de formulario reutilizables con labels visibles."""
import reflex as rx
from typing import Any
from reflex.vars.base import Var, var_operation, var_operation_return

from app.presentation.theme import (
    Colors,
    FORM_ERROR_STYLE,
    FORM_LABEL_STYLE,
    Radius,
    Spacing,
    Typography,
)


PORTAL_LABEL_STYLE = {
    **FORM_LABEL_STYLE,
    "font_size": Typography.SIZE_XS,
    "font_weight": Typography.WEIGHT_MEDIUM,
    "color": Colors.TEXT_SECONDARY,
    "margin_bottom": Spacing.XS,
}
PORTAL_FOOTER_STYLE = {
    **{key: value for key, value in FORM_ERROR_STYLE.items() if key != "color"},
    "font_size": Typography.SIZE_XS,
    "margin_top": Spacing.XS,
    "min_height": Spacing.BASE,
}


def _input_props_for_variant(style_variant: str, error: Any = None) -> dict[str, Any]:
    """Props visuales reutilizables para inputs por variante."""
    if style_variant == "portal":
        return {
            "size": "3",
            "font_size": Typography.SIZE_SM,
            "font_family": Typography.FONT_FAMILY,
            "line_height": Typography.LINE_HEIGHT_NORMAL,
            "background": Colors.SURFACE,
            "color": Colors.TEXT_PRIMARY,
            "border": f"1px solid {Colors.BORDER}",
            "border_radius": Radius.MD,
            "border_color": (
                rx.cond(error != "", Colors.ERROR, Colors.BORDER)
                if error is not None
                else Colors.BORDER
            ),
            "_focus": {
                "border_color": Colors.BORDER_FOCUS,
                "outline": "none",
            },
            "_placeholder": {
                "color": Colors.TEXT_MUTED,
            },
        }
    return {}


def _select_root_props_for_variant(style_variant: str) -> dict[str, Any]:
    """Props del root de select por variante."""
    if style_variant == "portal":
        return {
            "size": "3",
            "width": "100%",
        }
    return {}


def _select_trigger_props_for_variant(style_variant: str, error: Any = None) -> dict[str, Any]:
    """Props visuales reutilizables para triggers de select por variante."""
    if style_variant == "portal":
        return {
            "width": "100%",
            "font_size": Typography.SIZE_SM,
            "font_family": Typography.FONT_FAMILY,
            "line_height": Typography.LINE_HEIGHT_NORMAL,
            "background": Colors.SURFACE,
            "color": Colors.TEXT_PRIMARY,
            "border": f"1px solid {Colors.BORDER}",
            "border_radius": Radius.MD,
            "border_color": (
                rx.cond(error != "", Colors.ERROR, Colors.BORDER)
                if error is not None
                else Colors.BORDER
            ),
            "_focus": {
                "border_color": Colors.BORDER_FOCUS,
                "outline": "none",
            },
        }
    return {}


# =============================================================================
# HELPERS INTERNOS
# =============================================================================

def _render_label(
    label: str,
    required: Any = False,
    error: Any = None,
    label_variant: str = "default",
) -> rx.Component:
    """Renderiza label encima del input. Cambia a rojo si hay error."""
    if not label:
        return rx.fragment()

    parts = [label]
    if isinstance(required, bool):
        if required:
            parts.append(rx.text.span(" *", color=Colors.ERROR))
    else:
        parts.append(
            rx.cond(
                required,
                rx.text.span(" *", color=Colors.ERROR),
                rx.fragment(),
            )
        )

    base_color = (
        Colors.TEXT_SECONDARY
        if label_variant in {"portal", "wizard"}
        else Colors.TEXT_MUTED
        if label_variant == "metadata"
        else Colors.TEXT_PRIMARY
    )
    color = base_color
    if error is not None:
        color = rx.cond(error != "", Colors.ERROR, base_color)

    label_props = {
        "color": color,
    }
    if label_variant == "portal":
        label_props.update(PORTAL_LABEL_STYLE)
    elif label_variant == "wizard":
        label_props.update(
            {
                "font_size": "11px",
                "font_weight": Typography.WEIGHT_MEDIUM,
                "text_transform": "uppercase",
                "letter_spacing": "0.04em",
            }
        )
    elif label_variant == "metadata":
        label_props.update(
            {
                "font_size": "10px",
                "font_weight": Typography.WEIGHT_MEDIUM,
                "text_transform": "uppercase",
                "letter_spacing": "0.04em",
            }
        )
    else:
        label_props.update(
            {
                "size": "2",
                "weight": "medium",
            }
        )

    return rx.text(*parts, **label_props)


def _render_footer(
    error: Any = None,
    hint: Any = "",
    field_variant: str = "default",
) -> rx.Component:
    """Renderiza error (prioridad) o hint debajo del input sin swap de nodos DOM."""
    has_static_hint = isinstance(hint, str) and hint != ""
    has_dynamic_hint = hint is not None and not isinstance(hint, str)
    footer_props = (
        PORTAL_FOOTER_STYLE
        if field_variant == "portal"
        else {"size": "1", "min_height": "1em"}
    )
    hint_color = Colors.TEXT_SECONDARY if field_variant == "portal" else "var(--gray-9)"

    if error is not None and (has_static_hint or has_dynamic_hint):
        return rx.text(
            rx.cond(error != "", error, hint),
            color=rx.cond(error != "", Colors.ERROR, hint_color),
            **footer_props,
        )
    elif error is not None:
        return rx.text(
            error,
            color=Colors.ERROR,
            visibility=rx.cond(error != "", "visible", "hidden"),
            **footer_props,
        )
    elif has_static_hint or has_dynamic_hint:
        return rx.text(
            hint,
            color=hint_color,
            **footer_props,
        )
    else:
        return rx.text(
            "",
            visibility="hidden",
            **footer_props,
        )


def select_items_from_options(options: Any) -> rx.Component:
    """Renderiza items de select ignorando opciones con value vacío."""
    @var_operation
    def _safe_options(value: Any) -> Var:
        return var_operation_return(
            js_expression=f"(Array.isArray({value}) ? {value} : [])",
            var_type=list[dict[str, str]],
        )

    return rx.foreach(
        _safe_options(options),
        lambda opt: rx.cond(
            opt["value"] != "",
            rx.select.item(opt["label"], value=opt["value"]),
            rx.fragment(),
        ),
    )


@var_operation
def _date_display_var(value: Any) -> Var:
    """Retorna el valor visible DD/MM/AAAA preservando capturas parciales."""
    return var_operation_return(
        js_expression=(
            f"(() => {{"
            f"const raw = ((({value}) ?? '') + '').trim();"
            f"if (!raw) return '';"
            f"if (/^\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(raw)) {{"
            f"const [year, month, day] = raw.split('-');"
            f"return `${{day}}/${{month}}/${{year}}`;"
            f"}}"
            f"return raw;"
            f"}})()"
        ),
        var_type=str,
    )


@var_operation
def _date_inline_error_var(value: Any) -> Var:
    """Expone error inline cuando el año está incompleto."""
    return var_operation_return(
        js_expression=(
            f"(() => {{"
            f"const raw = ((({value}) ?? '') + '').trim();"
            f"if (!raw) return '';"
            f"const parts = raw.split('/');"
            f"if (parts.length !== 3) return '';"
            f"const year = (parts[2] || '').trim();"
            f"if (/^\\d{{1,3}}$/.test(year)) return 'Capture el año completo en formato AAAA';"
            f"return '';"
            f"}})()"
        ),
        var_type=str,
    )


# =============================================================================
# COMPONENTES DE FORMULARIO
# =============================================================================

def form_field(
    control: Any,
    label: str = "",
    required: Any = False,
    error: Any = None,
    hint: Any = "",
    spacing: str = "1",
    label_variant: str = "default",
    field_variant: str = "default",
    **layout_props,
) -> rx.Component:
    """Wrapper base para campos con label, control y footer consistente."""
    resolved_spacing = (
        Spacing.NONE
        if field_variant == "portal" and spacing == "1"
        else spacing
    )
    props = {
        "spacing": resolved_spacing,
        "width": "100%",
        "align_items": "stretch",
        **layout_props,
    }
    return rx.vstack(
        _render_label(label, required, error, label_variant=label_variant),
        control,
        _render_footer(error, hint, field_variant=field_variant),
        **props,
    )

def form_input(
    placeholder: str = "",
    value: Any = "",
    on_change: callable = None,
    on_blur: callable = None,
    error: Any = None,
    max_length: int = None,
    label: str = "",
    required: Any = False,
    hint: Any = "",
    label_variant: str = "default",
    style_variant: str = "default",
    **props
) -> rx.Component:
    """
    Input de formulario con label visible y manejo de errores.

    Args:
        placeholder: Texto placeholder dentro del input
        value: Variable de estado con el valor actual
        on_change: Callback al cambiar valor
        on_blur: Callback al perder foco (para validacion)
        error: Variable con mensaje de error (opcional)
        max_length: Longitud maxima permitida
        label: Texto del label visible encima del input
        required: Si True, muestra asterisco rojo en el label
        hint: Texto de ayuda debajo del input (error tiene prioridad)
        **props: Props adicionales para rx.input (type, disabled, step, min, etc.)
    """
    input_props = {
        "placeholder": placeholder,
        "value": value,
        "on_change": on_change,
        "on_blur": on_blur,
        "max_length": max_length,
        "width": "100%",
        **_input_props_for_variant(style_variant, error),
        **props,
    }
    return form_field(
        control=rx.input(**input_props),
        label=label,
        required=required,
        error=error,
        hint=hint,
        label_variant=label_variant,
        field_variant=style_variant,
    )


def form_textarea(
    placeholder: str = "",
    value: Any = "",
    on_change: callable = None,
    on_blur: callable = None,
    error: Any = None,
    max_length: int = None,
    rows: str = "3",
    label: str = "",
    required: Any = False,
    hint: Any = "",
    label_variant: str = "default",
    style_variant: str = "default",
    **props
) -> rx.Component:
    """
    Textarea de formulario con label visible y manejo de errores.

    Args:
        placeholder: Texto placeholder dentro del textarea
        value: Variable de estado con el valor actual
        on_change: Callback al cambiar valor
        on_blur: Callback al perder foco
        error: Variable con mensaje de error (opcional)
        max_length: Longitud maxima permitida
        rows: Numero de filas visibles
        label: Texto del label visible encima del textarea
        required: Si True, muestra asterisco rojo en el label
        hint: Texto de ayuda debajo del textarea
    """
    return form_field(
        control=rx.text_area(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            max_length=max_length,
            width="100%",
            rows=rows,
            **props
        ),
        label=label,
        required=required,
        error=error,
        hint=hint,
        label_variant=label_variant,
        field_variant=style_variant,
    )


def form_select(
    placeholder: str = "",
    value: Any = "",
    on_change: callable = None,
    options: list = None,
    error: Any = None,
    label: str = "",
    required: Any = False,
    hint: Any = "",
    label_variant: str = "default",
    style_variant: str = "default",
    trigger_props: dict[str, Any] | None = None,
    **props
) -> rx.Component:
    """
    Select de formulario con label visible y manejo de errores.

    Args:
        placeholder: Texto placeholder del select
        value: Variable de estado con el valor seleccionado
        on_change: Callback al cambiar seleccion
        options: Lista de dicts [{"label": "Texto", "value": "valor"}, ...]
        error: Variable con mensaje de error (opcional)
        label: Texto del label visible encima del select
        required: Si True, muestra asterisco rojo en el label
        hint: Texto de ayuda debajo del select
    """
    if options is None:
        options = []
    select_trigger_props = {
        "placeholder": placeholder,
        "width": "100%",
        **_select_trigger_props_for_variant(style_variant, error),
    }
    if trigger_props:
        select_trigger_props.update(trigger_props)
    select_root_props = {
        **_select_root_props_for_variant(style_variant),
        "value": value,
        "on_change": on_change,
        **props,
    }

    return form_field(
        control=rx.select.root(
            rx.select.trigger(**select_trigger_props),
            rx.select.content(select_items_from_options(options)),
            **select_root_props
        ),
        label=label,
        required=required,
        error=error,
        hint=hint,
        label_variant=label_variant,
        field_variant=style_variant,
    )


def _date_control(
    *,
    placeholder: str = "DD/MM/AAAA",
    value: Any = "",
    on_change: callable = None,
    on_blur: callable = None,
    width: str = "100%",
    size: str = "2",
    error: Any = None,
    **props,
) -> rx.Component:
    """Control base de fecha reutilizable para formularios y filtros inline."""
    input_style = props.pop("style", {}) or {}
    display_value = _date_display_var(value)
    input_color = props.pop(
        "color",
        rx.cond(display_value != "", Colors.TEXT_PRIMARY, Colors.TEXT_MUTED),
    )
    return rx.input(
        type="text",
        value=display_value,
        placeholder=placeholder,
        on_change=on_change,
        on_blur=on_blur,
        width=width,
        size=size,
        color=input_color,
        input_mode="numeric",
        max_length=10,
        background=Colors.SURFACE,
        border_color=(
            rx.cond(error != "", "var(--red-8)", Colors.BORDER)
            if error is not None
            else Colors.BORDER
        ),
        style=input_style,
        **props,
    )


def form_date(
    label: str = "",
    placeholder: str = "DD/MM/AAAA",
    value: Any = "",
    on_change: callable = None,
    on_blur: callable = None,
    error: Any = None,
    required: Any = False,
    hint: Any = "",
    label_variant: str = "default",
    **props
) -> rx.Component:
    """
    Input de fecha con label visible y manejo de errores.

    Args:
        label: Texto del label visible encima del input
        placeholder: Texto guía mientras la fecha está vacía
        value: Variable de estado con la fecha (formato YYYY-MM-DD)
        on_change: Callback al cambiar fecha
        error: Variable con mensaje de error (opcional)
        required: Si True, muestra asterisco rojo en el label
        hint: Texto de ayuda debajo del input
    """
    inline_error = _date_inline_error_var(value)
    effective_error = (
        rx.cond(inline_error != "", inline_error, error)
        if error is not None
        else inline_error
    )
    return form_field(
        control=_date_control(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            error=effective_error,
            **props,
        ),
        label=label,
        required=required,
        error=effective_error,
        hint=hint,
        label_variant=label_variant,
    )


def filter_date_input(
    label: str,
    value: Any = "",
    on_change: callable = None,
    placeholder: str = "DD/MM/AAAA",
    width: str = "140px",
    **props,
) -> rx.Component:
    """Campo de fecha compacto para filtros inline."""
    inline_error = _date_inline_error_var(value)
    return rx.vstack(
        rx.text(label, size="1", color=Colors.TEXT_MUTED),
        _date_control(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            error=inline_error,
            width=width,
            **props,
        ),
        rx.text(
            inline_error,
            size="1",
            color="var(--red-9)",
            min_height="1em",
            visibility=rx.cond(inline_error != "", "visible", "hidden"),
        ),
        spacing="1",
    )


def compact_date_input(
    value: Any = "",
    on_change: callable = None,
    placeholder: str = "DD/MM/AAAA",
    width: str = "140px",
    error: Any = None,
    **props,
) -> rx.Component:
    """Campo de fecha compacto sin label para toolbars y filtros densos."""
    inline_error = _date_inline_error_var(value)
    effective_error = (
        rx.cond(inline_error != "", inline_error, error)
        if error is not None
        else inline_error
    )
    return _date_control(
        placeholder=placeholder,
        value=value,
        on_change=on_change,
        error=effective_error,
        width=width,
        **props,
    )


def form_row(*children) -> rx.Component:
    """
    Pone campos de formulario en fila (columnas lado a lado).

    Uso:
        form_row(
            form_input(label="Nombre", ...),
            form_input(label="RFC", ...),
        )
    """
    return rx.hstack(
        *children,
        spacing="2",
        width="100%",
    )
