"""
Componentes reutilizables del módulo Cotizador.

- badge_estatus_cotizacion: Badge de color por estatus
- tabla_cotizaciones: Tabla del listado principal
- resumen_partida_card: Card con totales de partida
- tabla_matriz_costos: Matriz de conceptos × categorías
"""
import reflex as rx

from app.presentation.theme import Colors, Spacing, Typography


def badge_estatus_cotizacion(estatus: rx.Var) -> rx.Component:
    """Badge de estatus para cotizaciones."""
    return rx.cond(
        estatus == 'BORRADOR',
        rx.badge("Borrador", color_scheme='gray', variant='soft'),
        rx.cond(
            estatus == 'PREPARADA',
            rx.badge("Preparada", color_scheme='blue', variant='soft'),
            rx.cond(
                estatus == 'ENVIADA',
                rx.badge("Enviada", color_scheme='orange', variant='soft'),
                rx.cond(
                    estatus == 'APROBADA',
                    rx.badge("Aprobada", color_scheme='green', variant='soft'),
                    rx.cond(
                        estatus == 'RECHAZADA',
                        rx.badge("Rechazada", color_scheme='red', variant='soft'),
                        rx.badge(estatus, color_scheme='gray', variant='soft'),
                    ),
                ),
            ),
        ),
    )


def badge_estatus_partida(estatus: rx.Var) -> rx.Component:
    """Badge de estatus para partidas."""
    return rx.cond(
        estatus == 'PENDIENTE',
        rx.badge("Pendiente", color_scheme='gray', variant='soft'),
        rx.cond(
            estatus == 'ACEPTADA',
            rx.badge("Aceptada", color_scheme='green', variant='soft'),
            rx.cond(
                estatus == 'NO_ASIGNADA',
                rx.badge("No asignada", color_scheme='orange', variant='soft'),
                rx.cond(
                    estatus == 'CONVERTIDA',
                    rx.badge("Convertida", color_scheme='purple', variant='soft'),
                    rx.badge(estatus, color_scheme='gray', variant='soft'),
                ),
            ),
        ),
    )


def fila_cotizacion(cotizacion: dict) -> rx.Component:
    """Fila de la tabla de cotizaciones."""
    from app.presentation.pages.cotizador.cotizador_state import CotizadorState
    return rx.table.row(
        rx.table.cell(
            rx.link(
                cotizacion['codigo'],
                href=rx.Var.create(f"/cotizador/{cotizacion['id']}"),
                color=Colors.PRIMARY,
                font_weight="500",
            )
        ),
        rx.table.cell(cotizacion.get('nombre_empresa', '')),
        rx.table.cell(
            rx.text(str(cotizacion.get('fecha_inicio_periodo', '')))
        ),
        rx.table.cell(
            rx.text(str(cotizacion.get('fecha_fin_periodo', '')))
        ),
        rx.table.cell(
            rx.badge(
                str(cotizacion.get('cantidad_partidas', 0)),
                color_scheme='blue',
                variant='soft',
            )
        ),
        rx.table.cell(
            badge_estatus_cotizacion(cotizacion.get('estatus', 'BORRADOR'))
        ),
        rx.table.cell(
            rx.hstack(
                rx.link(
                    rx.button(
                        rx.icon("eye", size=14),
                        size="1",
                        variant="ghost",
                        color_scheme="blue",
                    ),
                    href=rx.Var.create(f"/cotizador/{cotizacion['id']}"),
                ),
                rx.cond(
                    cotizacion.get('estatus') == 'BORRADOR',
                    rx.button(
                        rx.icon("copy", size=14),
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=CotizadorState.crear_nueva_version(cotizacion['id']),
                        title="Nueva versión",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
            )
        ),
        _hover={"background": Colors.BG_APP},
    )


def tabla_cotizaciones(cotizaciones: rx.Var, loading: rx.Var) -> rx.Component:
    """Tabla principal del listado de cotizaciones."""
    return rx.cond(
        loading,
        rx.center(rx.spinner(size="3"), padding=Spacing.XL),
        rx.cond(
            cotizaciones.length() == 0,
            rx.center(
                rx.vstack(
                    rx.icon("file-text", size=48, color=Colors.TEXT_MUTED),
                    rx.text(
                        "No hay cotizaciones",
                        color=Colors.TEXT_SECONDARY,
                        font_size=Typography.SIZE_SM,
                    ),
                    align="center",
                    spacing="2",
                ),
                padding=Spacing.XXL,
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Código"),
                        rx.table.column_header_cell("Empresa"),
                        rx.table.column_header_cell("Inicio Período"),
                        rx.table.column_header_cell("Fin Período"),
                        rx.table.column_header_cell("Partidas"),
                        rx.table.column_header_cell("Estatus"),
                        rx.table.column_header_cell("Acciones"),
                    )
                ),
                rx.table.body(
                    rx.foreach(cotizaciones, fila_cotizacion)
                ),
                width="100%",
                variant="surface",
            ),
        ),
    )


def resumen_partida_card(partida: dict) -> rx.Component:
    """Card con los totales de una partida."""
    from app.presentation.pages.cotizador.cotizador_detalle_state import CotizadorDetalleState

    def fila_total(label: str, valor: str, bold: bool = False) -> rx.Component:
        return rx.hstack(
            rx.text(
                label,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
                font_weight="600" if bold else "400",
            ),
            rx.spacer(),
            rx.text(
                valor,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_PRIMARY,
                font_weight="600" if bold else "400",
            ),
            width="100%",
        )

    total_min = partida.get('total_minimo', 0)
    total_max = partida.get('total_maximo', 0)
    subtotal_min = partida.get('subtotal_minimo', 0)
    subtotal_max = partida.get('subtotal_maximo', 0)
    iva_min = partida.get('iva_minimo', 0)
    iva_max = partida.get('iva_maximo', 0)

    def fmt(v) -> str:
        try:
            return f"${float(v):,.2f}"
        except Exception:
            return "$0.00"

    return rx.card(
        rx.vstack(
            rx.text(
                "Resumen de Partida",
                font_size=Typography.SIZE_SM,
                font_weight="600",
                color=Colors.TEXT_PRIMARY,
            ),
            rx.divider(),
            rx.vstack(
                rx.hstack(
                    rx.text("", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY, min_width="120px"),
                    rx.text("Mínimo", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY, font_weight="600"),
                    rx.spacer(),
                    rx.text("Máximo", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY, font_weight="600"),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Subtotal:", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY, min_width="120px"),
                    rx.text(fmt(subtotal_min), font_size=Typography.SIZE_XS),
                    rx.spacer(),
                    rx.text(fmt(subtotal_max), font_size=Typography.SIZE_XS),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("IVA (16%):", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY, min_width="120px"),
                    rx.text(fmt(iva_min), font_size=Typography.SIZE_XS),
                    rx.spacer(),
                    rx.text(fmt(iva_max), font_size=Typography.SIZE_XS),
                    width="100%",
                ),
                rx.divider(),
                rx.hstack(
                    rx.text("TOTAL:", font_size=Typography.SIZE_XS, color=Colors.TEXT_PRIMARY, font_weight="700", min_width="120px"),
                    rx.text(fmt(total_min), font_size=Typography.SIZE_XS, font_weight="700", color=Colors.PRIMARY),
                    rx.spacer(),
                    rx.text(fmt(total_max), font_size=Typography.SIZE_XS, font_weight="700", color=Colors.PRIMARY),
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        padding=Spacing.MD,
        width="100%",
    )


def fila_partida_tab(partida: dict, activa: rx.Var) -> rx.Component:
    """Tab de navegación de partidas."""
    from app.presentation.pages.cotizador.cotizador_detalle_state import CotizadorDetalleState

    return rx.button(
        rx.hstack(
            rx.text(
                f"Partida {partida.get('numero_partida', '')}",
                font_size=Typography.SIZE_SM,
            ),
            badge_estatus_partida(partida.get('estatus_partida', 'PENDIENTE')),
            spacing="1",
            align="center",
        ),
        variant=rx.cond(
            activa == partida.get('id', 0),
            "solid",
            "ghost",
        ),
        color_scheme=rx.cond(
            activa == partida.get('id', 0),
            "blue",
            "gray",
        ),
        size="2",
        on_click=CotizadorDetalleState.seleccionar_partida(partida.get('id', 0)),
    )
