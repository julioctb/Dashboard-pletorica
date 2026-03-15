"""Tabs segmentadas reutilizables para toolbars y selectores compactos."""

import reflex as rx

from app.presentation.theme import Colors, Radius, Spacing, Transitions, Typography


SEGMENTED_TAB_TRIGGER_STYLE = {
    "padding": f"{Spacing.SM} {Spacing.MD}",
    "border_radius": Radius.MD,
    "font_size": Typography.SIZE_SM,
    "font_weight": Typography.WEIGHT_MEDIUM,
    "color": Colors.TEXT_SECONDARY,
    "background": "transparent",
    "white_space": "nowrap",
    "transition": Transitions.FAST,
    "_hover": {
        "background": Colors.SECONDARY_LIGHT,
        "color": Colors.TEXT_PRIMARY,
    },
    "&[data-state='active']": {
        "background": Colors.PRIMARY,
        "color": Colors.TEXT_INVERSE,
    },
    "&[data-state='active']:hover": {
        "background": Colors.PRIMARY_HOVER,
    },
}


def segmented_tab_trigger(label: str, value: str) -> rx.Component:
    """Trigger compacto para tabs segmentadas."""
    return rx.tabs.trigger(
        label,
        value=value,
        style=SEGMENTED_TAB_TRIGGER_STYLE,
    )


def segmented_tabs(
    *children: rx.Component,
    value,
    on_change,
    flex_shrink: str = "0",
) -> rx.Component:
    """Shell visual compartido para tabs compactas estilo portal."""
    return rx.tabs.root(
        rx.tabs.list(
            *children,
            gap=Spacing.XS,
            padding=Spacing.XS,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            flex_shrink=flex_shrink,
        ),
        value=value,
        on_change=on_change,
        flex_shrink=flex_shrink,
    )
