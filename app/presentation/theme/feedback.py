"""Contrato visual compartido para feedback inline y toast."""

from __future__ import annotations

from typing import Literal

import reflex as rx

FeedbackKind = Literal["error", "success", "warning", "info"]

DEFAULT_TOAST_POSITION = "top-center"

_STATIC_FEEDBACK_CONFIG = {
    "error": {"icon": "triangle-alert", "color_scheme": "red"},
    "success": {"icon": "circle-check", "color_scheme": "green"},
    "warning": {"icon": "triangle-alert", "color_scheme": "amber"},
    "info": {"icon": "info", "color_scheme": "blue"},
}


def _feedback_icon(kind: FeedbackKind | rx.Var) -> str | rx.Var:
    """Resuelve el icono para feedback estático o reactivo."""
    if isinstance(kind, str):
        return _STATIC_FEEDBACK_CONFIG.get(kind, _STATIC_FEEDBACK_CONFIG["info"])["icon"]

    return rx.match(
        kind,
        ("error", "triangle-alert"),
        ("success", "circle-check"),
        ("warning", "triangle-alert"),
        "info",
    )


def _feedback_color_scheme(kind: FeedbackKind | rx.Var) -> str | rx.Var:
    """Resuelve el color para feedback estático o reactivo."""
    if isinstance(kind, str):
        return _STATIC_FEEDBACK_CONFIG.get(kind, _STATIC_FEEDBACK_CONFIG["info"])["color_scheme"]

    return rx.match(
        kind,
        ("error", "red"),
        ("success", "green"),
        ("warning", "amber"),
        "blue",
    )


def feedback_callout(
    content,
    kind: FeedbackKind | rx.Var,
    *,
    size: str = "2",
    width: str = "100%",
    margin_bottom: str | None = None,
    role: str = "alert",
    aria_live: str = "assertive",
) -> rx.Component:
    """Callout consistente para mensajes inline del sistema."""
    props = {
        "icon": _feedback_icon(kind),
        "color_scheme": _feedback_color_scheme(kind),
        "size": size,
        "width": width,
        "role": role,
        "aria_live": aria_live,
    }

    if margin_bottom is not None:
        props["margin_bottom"] = margin_bottom

    return rx.callout(content, **props)


def app_toast(
    kind: FeedbackKind,
    message: str | rx.Var,
    *,
    position: str = DEFAULT_TOAST_POSITION,
    duration: int | None = None,
    **props,
) -> rx.Component:
    """Wrapper para toasts con contrato visual único."""
    toast_props = dict(props)
    toast_props["position"] = position
    if duration is not None:
        toast_props["duration"] = duration

    if kind == "success":
        return rx.toast.success(message, **toast_props)
    if kind == "warning":
        return rx.toast.warning(message, **toast_props)
    if kind == "info":
        return rx.toast.info(message, **toast_props)
    return rx.toast.error(message, **toast_props)
