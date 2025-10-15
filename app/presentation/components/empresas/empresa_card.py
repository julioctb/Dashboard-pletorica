import reflex as rx
from datetime import datetime
from app.presentation.components.ui.cards import base_card
from app.entities import EmpresaResumen

def empresa_card(empresa: EmpresaResumen, on_view: callable, on_edit: callable) -> rx.Component:
    """
    Tarjeta mejorada para mostrar información de una empresa

    Mejoras UI/UX:
    - Razón social en lugar de ID como subtítulo
    - 3 datos clave visibles (email, teléfono, fecha)
    - Borde visual según estatus
    - Información más relevante y accesible

    Args:
        empresa: Objeto EmpresaResumen con datos de la empresa
        on_view: Función para ver detalles de la empresa
        on_edit: Función para editar la empresa
    """

    # Badge para tipo de empresa con colores específicos
    tipo_badge = rx.badge(
        empresa.tipo_empresa,
        color_scheme=rx.cond(
            empresa.tipo_empresa == "NOMINA",
            "blue",
            "green"
        ),
        size="2"
    )

    # Contenido principal mejorado - 3 datos clave
    content = rx.vstack(
        # Email (prioritario)
        rx.cond(
            empresa.email,
            rx.hstack(
                rx.icon("mail", size=16, color="var(--gray-9)"),
                rx.text(
                    empresa.email,
                    size="2",
                    color="var(--gray-11)",
                    truncate=True
                ),
                spacing="2",
                align="center",
                width="100%"
            ),
            rx.hstack(
                rx.icon("triangle-alert", size=16, color="var(--amber-9)"),
                rx.text(
                    "Email no registrado",
                    size="2",
                    color="var(--amber-9)",
                    style={"fontStyle": "italic"}
                ),
                spacing="2",
                align="center"
            )
        ),

        # Teléfono
        rx.cond(
            empresa.contacto_principal,
            rx.hstack(
                rx.icon("phone", size=16, color="var(--gray-9)"),
                rx.text(
                    empresa.contacto_principal,
                    size="2",
                    color="var(--gray-11)"
                ),
                spacing="2",
                align="center"
            ),
            rx.hstack(
                rx.icon("phone-off", size=16, color="var(--gray-8)"),
                rx.text(
                    "Sin teléfono",
                    size="2",
                    color="var(--gray-8)",
                    style={"fontStyle": "italic"}
                ),
                spacing="2",
                align="center"
            )
        ),

        # Fecha de creación (contexto temporal)
        rx.hstack(
            rx.icon("calendar", size=16, color="var(--gray-9)"),
            rx.text(
                rx.cond(
                    empresa.fecha_creacion,
                    empresa.fecha_creacion.to_string("%d/%m/%Y"),
                    "Fecha desconocida"
                ),
                size="2",
                color="var(--gray-9)"
            ),
            spacing="2",
            align="center"
        ),

        spacing="2",
        align="start",
        width="100%"
    )

    # Acciones de la tarjeta
    actions = rx.hstack(
        rx.badge(
            empresa.estatus,
            color_scheme=get_estatus_color(empresa.estatus),
            size="2"
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.icon("eye", size=14),
                "Ver",
                size="1",
                variant="soft",
                on_click=lambda: on_view(empresa.id)
            ),
            rx.button(
                rx.icon("pencil", size=14),
                size="1",
                variant="soft",
                on_click=lambda: on_edit(empresa.id)
            ),
            spacing="1"
        ),
        width="100%",
        align="center"
    )

    # Determinar color del borde según estatus
    border_color = rx.cond(
        empresa.estatus == "ACTIVO",
        "var(--green-9)",
        rx.cond(
            empresa.estatus == "SUSPENDIDO",
            "var(--amber-9)",
            "var(--red-9)"
        )
    )

    # Determinar opacidad según estatus
    card_opacity = rx.cond(
        empresa.estatus == "ACTIVO",
        "1",
        rx.cond(
            empresa.estatus == "SUSPENDIDO",
            "0.85",
            "0.6"
        )
    )

    # Aplicar filtro grayscale si está inactiva
    card_filter = rx.cond(
        empresa.estatus == "INACTIVO",
        "grayscale(50%)",
        "none"
    )

    # Box wrapper con estilos dinámicos y altura fija
    return rx.box(
        base_card(
            title=empresa.nombre_comercial,
            subtitle=empresa.razon_social,  # Cambio clave: razón social en lugar de ID
            badge=tipo_badge,
            content=content,
            actions=actions,
            hover_effect=True
        ),
        style={
            "minHeight": "240px",  # Altura mínima fija para uniformidad
            "height": "240px",      # Altura fija
            "display": "flex",
            "flexDirection": "column",
            "borderLeft": rx.cond(
                empresa.estatus == "ACTIVO",
                "4px solid var(--green-9)",
                rx.cond(
                    empresa.estatus == "SUSPENDIDO",
                    "4px solid var(--amber-9)",
                    "4px solid var(--red-9)"
                )
            ),
            "opacity": card_opacity,
            "filter": card_filter,
            "transition": "all 0.2s ease",
            "&:hover": {
                "transform": "translateY(-2px)",
                "boxShadow": rx.cond(
                    empresa.estatus == "ACTIVO",
                    "0 4px 12px rgba(34, 197, 94, 0.15)",
                    rx.cond(
                        empresa.estatus == "SUSPENDIDO",
                        "0 4px 12px rgba(251, 191, 36, 0.15)",
                        "0 4px 12px rgba(239, 68, 68, 0.15)"
                    )
                )
            }
        },
        width="100%"
    )

def get_estatus_color(estatus: str) -> str:
    """
    Retorna el color scheme apropiado para cada estatus

    Args:
        estatus: String del estatus (ya convertido por use_enum_values)

    Returns:
        Color scheme string para el badge
    """
    # Como EmpresaResumen tiene use_enum_values=True, estatus es string
    color_map = {
        "ACTIVO": "green",
        "SUSPENDIDO": "yellow",
        "INACTIVO": "red"
    }
    return color_map.get(estatus, "gray")