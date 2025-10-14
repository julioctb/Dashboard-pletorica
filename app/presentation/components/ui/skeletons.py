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


def skeleton_form_field() -> rx.Component:
    """
    Skeleton para campo de formulario.
    Útil para formularios que cargan datos asíncronamente.
    """
    return rx.vstack(
        # Label
        rx.skeleton(
            rx.box(height="16px", width="120px"),
            loading=True
        ),
        # Input
        rx.skeleton(
            rx.box(height="36px", width="100%", border_radius="4px"),
            loading=True
        ),
        spacing="1",
        width="100%",
        align="start"
    )


def skeleton_modal_content() -> rx.Component:
    """
    Skeleton para contenido de modal.
    Útil cuando se carga una empresa para editar.
    """
    return rx.vstack(
        rx.hstack(
            rx.spinner(size="3"),
            rx.text(
                "Cargando datos...",
                size="3",
                weight="medium"
            ),
            spacing="3",
            align="center",
            justify="center",
            width="100%"
        ),

        # Simular campos del formulario
        *[skeleton_form_field() for _ in range(8)],

        # Botones
        rx.hstack(
            rx.skeleton(
                rx.box(height="32px", width="80px", border_radius="4px"),
                loading=True
            ),
            rx.skeleton(
                rx.box(height="32px", width="100px", border_radius="4px"),
                loading=True
            ),
            spacing="2",
            justify="end",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def skeleton_list(count: int = 5) -> rx.Component:
    """
    Skeleton genérico para listas.

    Args:
        count: Número de items a mostrar

    Returns:
        Lista vertical de skeletons
    """
    return rx.vstack(
        *[
            rx.hstack(
                rx.skeleton(
                    rx.box(height="40px", width="40px", border_radius="4px"),
                    loading=True
                ),
                rx.vstack(
                    rx.skeleton(
                        rx.box(height="16px", width="200px"),
                        loading=True
                    ),
                    rx.skeleton(
                        rx.box(height="12px", width="150px"),
                        loading=True
                    ),
                    spacing="1",
                    align="start"
                ),
                spacing="3",
                width="100%",
                align="center"
            )
            for _ in range(count)
        ],
        spacing="3",
        width="100%"
    )
