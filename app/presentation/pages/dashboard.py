import reflex as rx



def dashboard_page() -> rx.Component:
    return rx.heading(
        'Dashboard',
        as_='h1'
    )