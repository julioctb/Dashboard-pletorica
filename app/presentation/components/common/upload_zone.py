"""Zona reutilizable para selección y subida de archivos Reflex."""

from typing import Callable

import reflex as rx

from app.presentation.theme import Colors, Radius, Spacing, Typography


ACCEPT_CSV_EXCEL = {
    "text/csv": [".csv"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/vnd.ms-excel": [".xls"],
}

ACCEPT_IMAGES_PDF = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "application/pdf": [".pdf"],
}

ACCEPT_IMAGES_PDF_WILDCARD = {
    "image/*": [".jpg", ".jpeg", ".png"],
    "application/pdf": [".pdf"],
}

ACCEPT_PDF = {"application/pdf": [".pdf"]}

ACCEPT_XML = {
    "application/xml": [".xml"],
    "text/xml": [".xml"],
}


def _upload_zone_content(
    *,
    title: str,
    helper_text: str,
    loading,
    loading_label: str,
    icon: str,
    icon_color: str,
    icon_size: int,
    padding,
) -> rx.Component:
    """Contenido visual compartido del dropzone."""
    return rx.vstack(
        rx.cond(
            loading,
            rx.vstack(
                rx.spinner(size="3"),
                rx.text(
                    loading_label,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="2",
                align="center",
            ),
            rx.vstack(
                rx.icon(icon, size=icon_size, color=icon_color),
                rx.text(
                    title,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    text_align="center",
                ),
                rx.text(
                    helper_text,
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    text_align="center",
                ),
                spacing="2",
                align="center",
            ),
        ),
        align="center",
        justify="center",
        padding=padding,
        width="100%",
    )


def _upload_zone_locked_content(
    *,
    padding,
) -> rx.Component:
    """Contenido visual cuando el upload ya tiene un archivo seleccionado."""
    return rx.vstack(
        rx.icon("file-check", size=30, color=Colors.SUCCESS),
        rx.text(
            "Archivo seleccionado",
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_PRIMARY,
            text_align="center",
        ),
        rx.text(
            "Quite el archivo seleccionado para elegir otro.",
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
            text_align="center",
        ),
        spacing="2",
        align="center",
        justify="center",
        padding=padding,
        width="100%",
    )


def _selected_files(
    *,
    upload_id: str,
    color: str,
    show_label: bool,
) -> rx.Component:
    """Lista de archivos seleccionados por Reflex para un upload_id."""
    children = []
    if show_label:
        children.append(
            rx.text(
                "Archivos seleccionados:",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_BOLD,
            )
        )
    children.append(
        rx.foreach(
            rx.selected_files(upload_id),
            lambda file_name: rx.hstack(
                rx.icon("file", size=14, color=color),
                rx.text(
                    file_name,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="2",
                align="center",
            ),
        )
    )
    return rx.vstack(
        *children,
        spacing="2",
        width="100%",
    )


def upload_zone(
    *,
    upload_id: str,
    title: str,
    helper_text: str,
    accept: dict[str, list[str]],
    max_files: int = 1,
    loading=False,
    on_upload: Callable | None = None,
    on_drop: Callable | None = None,
    button_label: str = "Subir archivo",
    loading_label: str = "Subiendo...",
    button_icon: str = "cloud-upload",
    icon: str = "upload",
    icon_color: str = Colors.PRIMARY,
    icon_size: int = 28,
    button_color_scheme: str | None = None,
    button_variant: str | None = None,
    allow_cancel: bool = False,
    show_selected_files: bool = True,
    show_selected_label: bool = False,
    selected_files_inline: bool = False,
    auto_upload: bool = False,
    disable_when_selected: bool = False,
    border: str | None = None,
    border_radius: str = Radius.LG,
    background: str | None = None,
    hover_border_color: str | None = None,
    hover_background: str | None = None,
    padding=Spacing.LG,
    width: str = "100%",
) -> rx.Component:
    """Renderiza un upload Reflex homologado.

    Use `auto_upload=True` con `on_drop` para subir al soltar/seleccionar.
    Use `on_upload` para el modo manual con botón de acción.
    """
    upload_kwargs = {}
    if auto_upload and on_drop is not None:
        upload_kwargs["on_drop"] = on_drop(rx.upload_files(upload_id=upload_id))
    if background is not None:
        upload_kwargs["background"] = background

    resolved_icon_color = icon_color or Colors.PRIMARY
    resolved_border = border or f"2px dashed {Colors.BORDER_STRONG}"
    resolved_hover_border = hover_border_color or resolved_icon_color
    hover_style = {"border_color": resolved_hover_border}
    if hover_background is not None:
        hover_style["background"] = hover_background

    has_selected_file = rx.selected_files(upload_id).length() > 0
    is_locked = disable_when_selected & has_selected_file

    upload = rx.upload(
        rx.cond(
            is_locked,
            _upload_zone_locked_content(padding=padding),
            _upload_zone_content(
                title=title,
                helper_text=helper_text,
                loading=loading,
                loading_label=loading_label,
                icon=icon,
                icon_color=resolved_icon_color,
                icon_size=icon_size,
                padding=padding,
            ),
        ),
        id=upload_id,
        accept=accept,
        max_files=max_files,
        no_click=loading | is_locked,
        no_drag=loading | is_locked,
        border=resolved_border,
        border_radius=border_radius,
        cursor=rx.cond(loading, "wait", rx.cond(is_locked, "not-allowed", "pointer")),
        width=width,
        style={"_hover": rx.cond(is_locked, {}, hover_style)},
        **upload_kwargs,
    )

    selected_children = [
        _selected_files(
            upload_id=upload_id,
            color=resolved_icon_color,
            show_label=show_selected_label,
        )
    ]
    if not selected_files_inline:
        selected_children.append(rx.spacer())
    if allow_cancel:
        selected_children.append(
            rx.button(
                "Cancelar",
                on_click=rx.clear_selected_files(upload_id),
                variant="outline",
                size="2",
            )
        )
    if on_upload is not None and not auto_upload:
        button_kwargs = {}
        if button_color_scheme is not None:
            button_kwargs["color_scheme"] = button_color_scheme
        if button_variant is not None:
            button_kwargs["variant"] = button_variant

        selected_children.append(
            rx.button(
                rx.cond(
                    loading,
                    rx.hstack(
                        rx.spinner(size="1"),
                        rx.text(loading_label, font_size=Typography.SIZE_SM),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.icon(button_icon, size=16),
                        rx.text(button_label, font_size=Typography.SIZE_SM),
                        spacing="2",
                        align="center",
                    ),
                ),
                on_click=on_upload(rx.upload_files(upload_id=upload_id)),
                disabled=loading,
                size="2",
                **button_kwargs,
            )
        )

    selected = rx.fragment()
    if show_selected_files:
        selected = rx.cond(
            rx.selected_files(upload_id).length() > 0,
            rx.hstack(
                *selected_children,
                spacing="3",
                width="100%",
                align="center",
                justify="end",
            ),
            rx.fragment(),
        )

    return rx.vstack(upload, selected, spacing="3", width=width)
