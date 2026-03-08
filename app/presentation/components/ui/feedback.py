"""Compatibilidad para imports legacy de feedback UI."""

from app.presentation.theme.feedback import (
    DEFAULT_TOAST_POSITION,
    FeedbackKind,
    app_toast,
    feedback_callout,
)

__all__ = [
    "DEFAULT_TOAST_POSITION",
    "FeedbackKind",
    "app_toast",
    "feedback_callout",
]
