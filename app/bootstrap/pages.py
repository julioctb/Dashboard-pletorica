"""Shared page wrappers used while composing route registries."""

from typing import Callable

import reflex as rx

from app.presentation.components.shared.auth_state import AuthState
from app.presentation.layouts.backoffice.shell_layout import authenticated_sidebar_shell
from app.presentation.layouts.backoffice.sidebar_layout import sidebar
from app.presentation.layouts.portal.portal_layout import portal_index
from app.presentation.pages.portal.state.portal_state import PortalState

PageFactory = Callable[[], rx.Component]


def backoffice_index(content: rx.Component) -> rx.Component:
    """Layout wrapper for all backoffice pages."""
    return authenticated_sidebar_shell(
        sidebar_component=sidebar(),
        content=content,
    )


def backoffice_page(page_factory: PageFactory) -> PageFactory:
    """Wrap a page factory with the shared backoffice shell."""

    def _wrapped() -> rx.Component:
        return backoffice_index(page_factory())

    return _wrapped


def portal_page(page_factory: PageFactory) -> PageFactory:
    """Wrap a page factory with the shared portal shell."""

    def _wrapped() -> rx.Component:
        return portal_index(page_factory())

    return _wrapped


def root_dispatcher_page() -> rx.Component:
    """Root route dispatcher based on role and active context."""
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Redirigiendo...", color="gray"),
            spacing="3",
            align="center",
        ),
        height="100vh",
        on_mount=AuthState.redirigir_desde_raiz,
    )


def portal_plazas_redirect_page() -> rx.Component:
    """Legacy portal plazas entry that redirects to contracts."""
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Redirigiendo a contratos...", color="gray"),
            spacing="3",
            align="center",
        ),
        width="100%",
        min_height="40vh",
        on_mount=PortalState.redirigir_a_portal_plazas,
    )


def portal_onboarding_redirect_page() -> rx.Component:
    """Legacy onboarding route that redirects to the employee filter."""
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Redirigiendo a empleados...", color="gray"),
            spacing="3",
            align="center",
        ),
        width="100%",
        min_height="40vh",
        on_mount=rx.redirect("/portal/empleados?status=en_alta", replace=True),
    )


__all__ = [
    "PageFactory",
    "backoffice_index",
    "backoffice_page",
    "portal_page",
    "root_dispatcher_page",
    "portal_plazas_redirect_page",
    "portal_onboarding_redirect_page",
]
