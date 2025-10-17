import reflex as rx
from app.entities import EmpresaResumen


def info_row(
    icon: str,
    text: str,
    color: str = "var(--gray-11)",
    icon_color: str = "var(--gray-9)",
    truncate: bool = False,
    italic: bool = False,
    width: str = "auto"
) -> rx.Component:
    """
    Helper para crear filas de información con icono y texto.

    Reduce duplicación de código en la tarjeta.
    """
    return rx.hstack(
        rx.icon(icon, size=16, color=icon_color),
        rx.text(
            text,
            size="2",
            color=color,
            truncate=truncate,
            style={"fontStyle": "italic"} if italic else {}
        ),
        spacing="2",
        align="center",
        width=width
    )


def get_estatus_border(estatus) -> rx.Component:
    """Retorna el estilo de borde según estatus (reactivo con rx.cond)"""
    return rx.cond(
        estatus == "ACTIVO",
        "4px solid var(--green-9)",
        rx.cond(
            estatus == "SUSPENDIDO",
            "4px solid var(--amber-9)",
            "4px solid var(--red-9)"
        )
    )


def get_estatus_opacity(estatus) -> rx.Component:
    """Retorna la opacidad según estatus (reactivo con rx.cond)"""
    return rx.cond(
        estatus == "ACTIVO",
        "1",
        rx.cond(
            estatus == "SUSPENDIDO",
            "0.85",
            "0.6"
        )
    )


def get_estatus_filter(estatus) -> rx.Component:
    """Retorna el filtro CSS según estatus (reactivo con rx.cond)"""
    return rx.cond(
        estatus == "INACTIVO",
        "grayscale(50%)",
        "none"
    )


def get_estatus_shadow(estatus) -> rx.Component:
    """Retorna la sombra hover según estatus (reactivo con rx.cond)"""
    return rx.cond(
        estatus == "ACTIVO",
        "0 4px 12px rgba(34, 197, 94, 0.15)",
        rx.cond(
            estatus == "SUSPENDIDO",
            "0 4px 12px rgba(251, 191, 36, 0.15)",
            "0 4px 12px rgba(239, 68, 68, 0.15)"
        )
    )


def get_estatus_color(estatus: str) -> str:
    """
    Retorna el color scheme apropiado para cada estatus.

    Args:
        estatus: String del estatus (ya convertido por use_enum_values)

    Returns:
        Color scheme string para el badge
    """
    color_map = {
        "ACTIVO": "green",
        "SUSPENDIDO": "yellow",
        "INACTIVO": "red"
    }
    return color_map.get(estatus, "gray")


def empresa_card(empresa: EmpresaResumen, on_view: callable, on_edit: callable) -> rx.Component:
    """
    Tarjeta optimizada para mostrar información de una empresa.

    Mejoras UI/UX:
    - Razón social en lugar de ID como subtítulo
    - 3 datos clave visibles (email, teléfono, fecha)
    - Borde visual según estatus
    - Información más relevante y accesible

    Optimizaciones técnicas:
    - Helpers reutilizables (info_row, get_estatus_*)
    - Sin código duplicado
    - Evaluación de estatus optimizada
    - Tooltips en botones

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

    # Contenido principal - 3 datos clave
    content = rx.vstack(
        # Email (prioritario)
        rx.cond(
            empresa.email,
            info_row("mail", empresa.email, truncate=True, width="100%"),
            info_row(
                "triangle-alert",
                "Email no registrado",
                color="var(--amber-9)",
                icon_color="var(--amber-9)",
                italic=True
            )
        ),

        # Teléfono
        rx.cond(
            empresa.contacto_principal,
            info_row("phone", empresa.contacto_principal),
            info_row(
                "phone-off",
                "Sin teléfono",
                color="var(--gray-8)",
                icon_color="var(--gray-8)",
                italic=True
            )
        ),

        # Fecha de registro de la empresa
        rx.hstack(
            rx.text(
                "Fecha de alta:",
                size="2",
                color="var(--gray-9)"
            ),
            rx.text(
                rx.moment(empresa.fecha_creacion, format='DD-MM-YYYY'),
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
            rx.tooltip(
                rx.button(
                    rx.icon("eye", size=14),
                    "Ver",
                    size="1",
                    variant="soft",
                    on_click=lambda: on_view(empresa.id)
                ),
                content="Ver detalles de la empresa"
            ),
            rx.tooltip(
                rx.button(
                    rx.icon("pencil", size=14),
                    size="1",
                    variant="soft",
                    on_click=lambda: on_edit(empresa.id)
                ),
                content="Editar empresa"
            ),
            spacing="1"
        ),
        width="100%",
        align="center"
    )

    # Tarjeta inline (sin abstracción base_card)
    return rx.card(
        rx.vstack(
            # Header de la tarjeta
            rx.hstack(
                rx.vstack(
                    rx.text(empresa.nombre_comercial, size="4", weight="bold"),
                    rx.text(empresa.razon_social, size="2", color="var(--gray-9)"),
                    align="start",
                    spacing="1"
                ),
                rx.spacer(),
                tipo_badge,
                width="100%",
                align="center"
            ),
            # Contenido principal con espaciado flexible
            rx.box(content, flex="1", overflow_y="auto"),
            # Acciones
            actions,
            spacing="3",
            align="start",
            width="100%",
            height="100%"
        ),
        width="100%",
        style={
            "height": "240px",  # Altura fija para todas las cards
            "display": "flex",
            "flexDirection": "column",
            "borderLeft": get_estatus_border(empresa.estatus),
            "opacity": get_estatus_opacity(empresa.estatus),
            "filter": get_estatus_filter(empresa.estatus),
            "transition": "all 0.2s ease",
            "&:hover": {
                "bg": "var(--gray-2)",
                "transform": "translateY(-2px)",
                "boxShadow": get_estatus_shadow(empresa.estatus)
            }
        }
    )
