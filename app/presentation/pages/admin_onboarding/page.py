"""
Pagina Admin Onboarding — pipeline de onboarding para admins BUAP.

Muestra pipeline cards con conteos + tabla filtrable de empleados
en proceso de onboarding de todas las empresas.
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Spacing

from .state import AdminOnboardingState
from .components import (
    pipeline_cards,
    filtros_onboarding_admin,
    tabla_onboarding_admin,
)


def admin_onboarding_page() -> rx.Component:
    """Pagina del pipeline de onboarding (admin)."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Onboarding",
                subtitulo="Pipeline de onboarding de empleados",
                icono="user-plus",
            ),
            toolbar=rx.fragment(),
            content=rx.vstack(
                pipeline_cards(),
                filtros_onboarding_admin(),
                tabla_onboarding_admin(),
                width="100%",
                spacing="4",
                padding_top=Spacing.SM,
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=AdminOnboardingState.on_mount_admin_onboarding,
    )
