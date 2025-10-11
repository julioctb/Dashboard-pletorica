import reflex as rx
from app.presentation.components.ui.headers import page_header



def dashboard_page() -> rx.Component:
    return page_header(
        icono="layout-dashboard",
        titulo="Panel de Control",
        subtitulo="Visión general de las empresas"
    )