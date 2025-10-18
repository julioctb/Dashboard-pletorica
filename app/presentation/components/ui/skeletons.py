"""
Componentes de skeleton para estados de carga.

Los skeletons mejoran la percepción de performance al mostrar placeholders
durante la carga de datos, en lugar de spinners genéricos.
"""
import reflex as rx


def skeleton_empresa_card() -> rx.Component:
    """
    Skeleton para tarjeta de empresa.
    Simula la estructura de empresa_card mientras carga.
    """
    return rx.card(
        rx.vstack(
            # Header (nombre + badge)
            rx.hstack(
                rx.skeleton(
                    rx.box(height="24px", width="200px"),
                    loading=True
                ),
                rx.spacer(),
                rx.skeleton(
                    rx.box(height="20px", width="80px", border_radius="12px"),
                    loading=True
                ),
                width="100%",
                align="center"
            ),

            # Subtitle (tipo de empresa)
            rx.skeleton(
                rx.box(height="16px", width="100px"),
                loading=True
            ),

            # Contacto
            rx.hstack(
                rx.skeleton(
                    rx.box(height="16px", width="16px", border_radius="50%"),
                    loading=True
                ),
                rx.skeleton(
                    rx.box(height="16px", width="180px"),
                    loading=True
                ),
                spacing="2",
                align="center"
            ),

            # Acciones (footer)
            rx.hstack(
                rx.skeleton(
                    rx.box(height="20px", width="70px"),
                    loading=True
                ),
                rx.spacer(),
                rx.hstack(
                    rx.skeleton(
                        rx.box(height="28px", width="28px", border_radius="4px"),
                        loading=True
                    ),
                    rx.skeleton(
                        rx.box(height="28px", width="64px", border_radius="4px"),
                        loading=True
                    ),
                    spacing="2"
                ),
                width="100%",
                align="center"
            ),

            spacing="3",
            width="100%"
        ),
        width="100%",
        max_width="400px"
    )


def skeleton_empresa_grid(count: int = 6) -> rx.Component:
    """
    Grid de skeletons para empresas.

    Args:
        count: Número de skeletons a mostrar (default 6)

    Returns:
        Grid con skeletons que simula empresa_grid
    """
    return rx.vstack(
        # Texto de carga
        rx.hstack(
            rx.spinner(size="2"),
            rx.text(
                "Cargando empresas...",
                size="2",
                color="var(--gray-9)"
            ),
            spacing="2",
            align="center"
        ),

        # Grid de skeletons
        rx.grid(
            *[skeleton_empresa_card() for _ in range(count)],
            columns="3",
            spacing="4",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


