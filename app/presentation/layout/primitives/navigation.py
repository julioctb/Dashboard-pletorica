"""Primitivas reutilizables de navegación (sidebar/nav groups/items)."""

import reflex as rx

from app.presentation.theme import Colors, Spacing, Transitions, Typography


def nav_item(
    *,
    text: str,
    icon: str,
    href: str,
    icon_color=Colors.TEXT_SECONDARY,
    text_color=Colors.TEXT_PRIMARY,
    hover_bg=Colors.SIDEBAR_ITEM_HOVER,
) -> rx.Component:
    """Item de navegación estándar para sidebars/listas de links."""
    return rx.link(
        rx.hstack(
            rx.icon(
                icon,
                size=20,
                color=icon_color,
                flex_shrink="0",
            ),
            rx.text(
                text,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=text_color,
                white_space="nowrap",
            ),
            width="100%",
            padding_x=Spacing.MD,
            padding_y=Spacing.SM,
            align="center",
            gap=Spacing.SM,
            border_radius="8px",
            transition=Transitions.FAST,
            style={
                "_hover": {
                    "background": hover_bg,
                },
            },
        ),
        href=href,
        underline="none",
        width="100%",
    )


def collapsible_nav_item(
    *,
    text: str,
    icon: str,
    href: str,
    is_collapsed,
    badge: rx.Component | None = None,
    tooltip_side: str = "right",
    icon_color=Colors.TEXT_SECONDARY,
    text_color=Colors.TEXT_PRIMARY,
    hover_bg=Colors.SIDEBAR_ITEM_HOVER,
) -> rx.Component:
    """Item de navegación con soporte para sidebar colapsable + tooltip."""
    item_content = rx.hstack(
        rx.icon(icon, size=20, color=icon_color, flex_shrink="0"),
        rx.cond(
            ~is_collapsed,
            rx.hstack(
                rx.text(
                    text,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=text_color,
                    white_space="nowrap",
                ),
                rx.spacer(),
                badge if badge is not None else rx.fragment(),
                width="100%",
                align="center",
            ),
            rx.fragment(),
        ),
        width="100%",
        padding_x=Spacing.MD,
        padding_y=Spacing.SM,
        align="center",
        justify=rx.cond(is_collapsed, "center", "start"),
        gap=Spacing.SM,
        border_radius="8px",
        transition=Transitions.FAST,
        style={"_hover": {"background": hover_bg}},
    )

    return rx.link(
        rx.cond(
            is_collapsed,
            rx.tooltip(item_content, content=text, side=tooltip_side),
            item_content,
        ),
        href=href,
        underline="none",
        width="100%",
    )


def nav_group_label(label: str) -> rx.Component:
    """Etiqueta de grupo de navegación."""
    return rx.text(
        label.upper(),
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_MUTED,
        letter_spacing=Typography.LETTER_SPACING_WIDE,
        padding_x=Spacing.MD,
        padding_top=Spacing.LG,
        padding_bottom=Spacing.XS,
    )


def nav_group(*items, label: str | None = None) -> rx.Component:
    """Grupo de navegación vertical con etiqueta opcional."""
    return rx.vstack(
        rx.cond(label is not None, nav_group_label(label), rx.fragment()),
        *items,
        spacing="1" if label is not None else "0",
        width="100%",
        align_items="stretch",
    )
