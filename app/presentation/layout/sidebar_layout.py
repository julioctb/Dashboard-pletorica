import reflex as rx
from app.core.config import Config

def footer_sidebar() -> rx.Component:
    return rx.center(
        rx.text(
            f"v{Config.APP_VERSION} - Desarrollado para Pletorica",
            size="1",
            color="var(--gray-9)"
        ),
        padding="4",
        border_top="1px solid var(--gray-6)",
        margin_top="auto"
    )

def sidebar_item(
    text: str, icon: str, href: str
) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(icon),
            rx.text(text, size="2"),
            width="100%",
            padding_x="0.5rem",
            padding_y="0.75rem",
            align="center",
            justify="start",
            style={
                "_hover": {
                    "bg": rx.color("accent", 4),
                    "color": rx.color("accent", 11),
                },
                "border-radius": "0.5em",
            },
        ),
        href=href,
        underline="none",
        weight="medium",
        width="100%",
    )

def sidebar_items() -> rx.Component:
    return rx.vstack(
        
        # TODO arreglar o definir si es necesario tener colapsables
            
            
            sidebar_item('Dashboard','layout-dashboard', '/#' ),
            sidebar_item('Listado','building-2', '/empresas' ),
            sidebar_item('Simulador','Calculator', '/simulador' ),
            sidebar_item('Servicios', 'briefcase', '/tipos-servicio'),
            sidebar_item('Categorías Puesto', 'users', '/categorias-puesto'),
            sidebar_item('Sedes','map-pin-house', '/#' ),
            sidebar_item('Personal','users', '/#' ),
            sidebar_item('Mensajes','mail', '/#' ),
            spacing='1',
            width='100%'
    )
         

def sidebar() -> rx.Component:
    return rx.box(
        rx.desktop_only(
            rx.vstack(
                rx.hstack(
                    rx.image(
                        src="/logo_reflex.jpg",
                        width='2.25em',
                        height='auto',
                        border_radius='25%'
                    ),
                    rx.heading(
                        'Pletorica',size='7',weight='bold'
                    ),
                    align='center',
                    justify='start',
                    padding_x='0.5rem',
                    width='100%'
                ),
                sidebar_items(),
                rx.spacer(),
                footer_sidebar(),
                spacing='5',
                # position="fixed",
                # left="0px",
                # top="0px",
                # z_index="5",
                padding_x="1em",
                padding_y="1.5em",
                bg=rx.color("accent", 3),
                align="start",
                height="100vh",
                #height="650px",
                width="16em",
            )
        ),
        rx.mobile_and_tablet(
            rx.drawer.root(
                rx.drawer.trigger(
                    rx.icon("align-justify", size=30)
                ),
                rx.drawer.overlay(z_index="5"),
                rx.drawer.portal(
                    rx.drawer.content(
                        rx.vstack(
                            rx.box(
                                rx.drawer.close(
                                    rx.icon("x", size=30)
                                ),
                                width="100%",
                            ),
                            sidebar_items(),
                            rx.spacer(),
                            footer_sidebar(),
                            spacing="5",
                            width="100%",
                        ),
                        top="auto",
                        right="auto",
                        height="100%",
                        width="20em",
                        padding="1.5em",
                        bg=rx.color("accent", 2),
                    ),
                    width="100%",
                ),
                direction="left",
            ),
            padding="1em",
        ),

    )