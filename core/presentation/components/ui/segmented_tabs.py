"""Tabs segmentadas reutilizables para toolbars y selectores compactos."""

import reflex as rx

from core.presentation.theme import Colors, Radius, Spacing, Transitions, Typography


FOCUS_RESET_STYLE = {
    "outline": "none",
    "box_shadow": "none",
}

TRIGGER_INNER_RESET_STYLE = {
    "outline": "none",
    "outline_offset": "0",
    "box_shadow": "none",
}

SEGMENTED_TABS_ROOT_STYLE = {
    "outline": "none",
    "box_shadow": "none",
    "&:focus": FOCUS_RESET_STYLE,
    "&:focus-visible": FOCUS_RESET_STYLE,
    "&:focus-within": FOCUS_RESET_STYLE,
}

SEGMENTED_TABS_LIST_STYLE = {
    **SEGMENTED_TABS_ROOT_STYLE,
    "&.rt-TabsList:focus-within": FOCUS_RESET_STYLE,
    "&.rt-BaseTabList:focus-within": FOCUS_RESET_STYLE,
}

SEGMENTED_TAB_TRIGGER_STYLE = {
    "padding": f"{Spacing.SM} {Spacing.MD}",
    "border_radius": Radius.MD,
    "font_size": Typography.SIZE_SM,
    "font_weight": Typography.WEIGHT_MEDIUM,
    "color": Colors.TEXT_SECONDARY,
    "background": "transparent",
    "white_space": "nowrap",
    "transition": Transitions.FAST,
    "cursor": "pointer",
    "outline": "none",
    "box_shadow": "none",
    "&:focus": FOCUS_RESET_STYLE,
    "&:focus-visible": FOCUS_RESET_STYLE,
    "&:hover": {
        "background": Colors.SECONDARY_LIGHT,
        "color": Colors.TEXT_PRIMARY,
    },
    # Radix Themes dibuja el ring en este span interno.
    "&:focus-visible .rt-BaseTabListTriggerInner": {
        **TRIGGER_INNER_RESET_STYLE,
    },
    # La línea azul persistente viene de este pseudo-elemento activo de Radix.
    "&[data-state='active']::before": {"display": "none"},
}


def segmented_tab_trigger(
    label: str,
    value: str,
    *,
    active_background: str = Colors.PRIMARY,
    active_hover_background: str = Colors.PRIMARY_HOVER,
) -> rx.Component:
    """Trigger compacto para tabs segmentadas."""
    style = {
        **SEGMENTED_TAB_TRIGGER_STYLE,
        "&[data-state='active']": {
            "background": active_background,
            "color": Colors.TEXT_INVERSE,
        },
        "&[data-state='active']:hover": {
            "background": active_hover_background,
        },
        "&[data-state='active'] .rt-BaseTabListTriggerInner": {
            **TRIGGER_INNER_RESET_STYLE,
        },
    }
    return rx.tabs.trigger(
        label,
        value=value,
        style=style,
    )


def segmented_tabs(
    *children: rx.Component,
    value,
    on_change,
    flex_shrink: str = "0",
) -> rx.Component:
    """Shell visual compartido para tabs compactas estilo portal.

    Radix Themes agrega dos affordances visuales por defecto:
    - outline de focus sobre ``.rt-BaseTabListTriggerInner``
    - indicador activo azul en ``::before`` del trigger

    Este wrapper limpia ambos para mantener el look segmentado del portal.
    """
    return rx.tabs.root(
        rx.tabs.list(
            *children,
            gap=Spacing.XS,
            padding=Spacing.XS,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            flex_shrink=flex_shrink,
            style=SEGMENTED_TABS_LIST_STYLE,
        ),
        value=value,
        on_change=on_change,
        flex_shrink=flex_shrink,
        style=SEGMENTED_TABS_ROOT_STYLE,
    )
