"""
Componentes reutilizables del módulo Cotizador.

- badge_estatus_cotizacion: Badge de color por estatus
- tabla_cotizaciones: Tabla del listado principal
- resumen_partida_card: Card con totales de partida
- tabla_matriz_costos: Matriz de conceptos × categorías
"""
import reflex as rx

from app.presentation.components.ui.action_buttons import (
    tabla_action_button,
    tabla_action_buttons,
)
from app.presentation.theme import (
    Colors,
    Spacing,
    Typography,
    TABLE_CONTAINER_STYLE,
    TABLE_HEADER_STYLE,
)


def _table_shell(content: rx.Component, min_width: str = "100%") -> rx.Component:
    """Contenedor visual consistente para tablas del cotizador."""
    return rx.box(
        content,
        width="100%",
        min_width=min_width,
        overflow_x="auto",
        style=TABLE_CONTAINER_STYLE,
    )


def _header_label(texto: str, align: str = "left") -> rx.Component:
    """Label de encabezado consistente con el sistema visual."""
    return rx.text(
        texto,
        font_size=TABLE_HEADER_STYLE["font_size"],
        font_weight=TABLE_HEADER_STYLE["font_weight"],
        color=TABLE_HEADER_STYLE["color"],
        text_transform="none",
        letter_spacing=Typography.LETTER_SPACING_NORMAL,
        text_align=align,
        width="100%",
        white_space="nowrap",
    )


def _money_text(
    valor: rx.Var | str,
    *,
    color: str = Colors.TEXT_PRIMARY,
    weight: str = "500",
    size: str = Typography.SIZE_SM,
) -> rx.Component:
    """Texto monetario con alineación consistente."""
    return rx.text(
        valor,
        font_size=size,
        font_weight=weight,
        color=color,
        width="100%",
        text_align="right",
        white_space="nowrap",
    )


def tipo_cotizacion_badge(tipo: rx.Var) -> rx.Component:
    """Badge de tipo de cotización."""
    return rx.cond(
        tipo == 'PERSONAL',
        rx.badge(
            rx.icon("users", size=12),
            "Personal",
            color_scheme='blue',
            variant='soft',
        ),
        rx.badge(
            rx.icon("package", size=12),
            "Productos",
            color_scheme='green',
            variant='soft',
        ),
    )


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
                    rx.badge("Convertida", color_scheme='blue', variant='soft'),
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
                rx.text(
                    cotizacion['codigo'],
                    color=Colors.PRIMARY,
                    font_weight="600",
                    font_size=Typography.SIZE_SM,
                    white_space="nowrap",
                ),
                href="/portal/cotizador/" + cotizacion["codigo"].to(str),
            )
        ),
        rx.table.cell(
            tipo_cotizacion_badge(cotizacion.get('tipo', 'PERSONAL'))
        ),
        rx.table.cell(
            rx.text(
                cotizacion.get('nombre_empresa', ''),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
            )
        ),
        rx.table.cell(
            rx.flex(
                rx.badge(
                    cotizacion.get('cantidad_partidas_texto', '0'),
                    color_scheme='blue',
                    variant='soft',
                ),
                justify="center",
            )
        ),
        rx.table.cell(
            badge_estatus_cotizacion(cotizacion.get('estatus', 'BORRADOR'))
        ),
        rx.table.cell(
            tabla_action_buttons(
                [
                    rx.tooltip(
                        rx.link(
                            rx.icon_button(
                                rx.icon("eye", size=16),
                                size="2",
                                variant="soft",
                                color_scheme="blue",
                            ),
                            href="/portal/cotizador/" + cotizacion["codigo"].to(str),
                        ),
                        content="Ver detalle",
                    ),
                    tabla_action_button(
                        icon="copy",
                        tooltip="Crear nueva versión",
                        on_click=CotizadorState.crear_nueva_version(cotizacion['id']),
                        color_scheme="gray",
                        visible=cotizacion.get('estatus') != 'APROBADA',
                    ),
                ],
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
            _table_shell(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(_header_label("Código")),
                            rx.table.column_header_cell(_header_label("Tipo")),
                            rx.table.column_header_cell(_header_label("Empresa")),
                            rx.table.column_header_cell(_header_label("Partidas", align="center")),
                            rx.table.column_header_cell(_header_label("Estatus")),
                            rx.table.column_header_cell(_header_label("Acciones", align="center")),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(cotizaciones, fila_cotizacion)
                    ),
                    width="100%",
                    variant="surface",
                    size="2",
                ),
                min_width="860px",
            ),
        ),
    )


def resumen_partida_card(partida: dict) -> rx.Component:
    """Card con los totales de una partida (usa computed vars reactivas)."""
    from app.presentation.pages.cotizador.cotizador_detalle_state import CotizadorDetalleState

    resumen_personal = rx.vstack(
        rx.hstack(
            rx.text("", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="120px"),
            rx.text("Mínimo", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, font_weight=Typography.WEIGHT_SEMIBOLD),
            rx.spacer(),
            rx.text("Máximo", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, font_weight=Typography.WEIGHT_SEMIBOLD),
            width="100%",
        ),
        rx.hstack(
            rx.text("Subtotal:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="120px"),
            rx.text(CotizadorDetalleState.resumen_subtotal_min, font_size=Typography.SIZE_SM),
            rx.spacer(),
            rx.text(CotizadorDetalleState.resumen_subtotal_max, font_size=Typography.SIZE_SM),
            width="100%",
        ),
        rx.cond(
            CotizadorDetalleState.aplicar_iva,
            rx.hstack(
                rx.text("IVA (16%):", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="120px"),
                rx.text(CotizadorDetalleState.resumen_iva_min, font_size=Typography.SIZE_SM),
                rx.spacer(),
                rx.text(CotizadorDetalleState.resumen_iva_max, font_size=Typography.SIZE_SM),
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.divider(),
        rx.hstack(
            rx.text("TOTAL:", font_size=Typography.SIZE_BASE, color=Colors.TEXT_PRIMARY, font_weight="700", min_width="120px"),
            rx.text(CotizadorDetalleState.resumen_total_min, font_size=Typography.SIZE_BASE, font_weight="700", color=Colors.PRIMARY),
            rx.spacer(),
            rx.text(CotizadorDetalleState.resumen_total_max, font_size=Typography.SIZE_BASE, font_weight="700", color=Colors.PRIMARY),
            width="100%",
            background=Colors.PRIMARY_LIGHTER,
            padding=Spacing.SM,
            border_radius="10px",
        ),
        spacing="2",
        width="100%",
    )

    resumen_productos = rx.vstack(
        rx.hstack(
            rx.text("Subtotal:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="120px"),
            rx.spacer(),
            rx.text(CotizadorDetalleState.resumen_subtotal_min, font_size=Typography.SIZE_SM),
            width="100%",
        ),
        rx.cond(
            CotizadorDetalleState.aplicar_iva,
            rx.hstack(
                rx.text("IVA (16%):", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="120px"),
                rx.spacer(),
                rx.text(CotizadorDetalleState.resumen_iva_min, font_size=Typography.SIZE_SM),
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.divider(),
        rx.hstack(
            rx.text("TOTAL:", font_size=Typography.SIZE_BASE, color=Colors.TEXT_PRIMARY, font_weight="700", min_width="120px"),
            rx.spacer(),
            rx.text(CotizadorDetalleState.resumen_total_min, font_size=Typography.SIZE_BASE, font_weight="700", color=Colors.PRIMARY),
            width="100%",
            background=Colors.PRIMARY_LIGHTER,
            padding=Spacing.SM,
            border_radius="10px",
        ),
        spacing="2",
        width="100%",
    )

    return rx.card(
        rx.vstack(
            rx.text(
                "Totales de Partida",
                font_size=Typography.SIZE_BASE,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.divider(),
            rx.cond(
                CotizadorDetalleState.es_tipo_personal,
                resumen_personal,
                resumen_productos,
            ),
            spacing="3",
            width="100%",
        ),
        padding=Spacing.LG,
        width="100%",
    )


def fila_partida_tab(partida: dict, activa: rx.Var) -> rx.Component:
    """Tab de navegación de partidas."""
    from app.presentation.pages.cotizador.cotizador_detalle_state import CotizadorDetalleState

    es_activa = activa == partida.get('id', 0)

    return rx.button(
        rx.vstack(
            rx.hstack(
                rx.text(
                    "Partida ",
                    partida.get('numero_partida', ''),
                    font_size=Typography.SIZE_SM,
                    font_weight="600",
                    color=rx.cond(es_activa, Colors.TEXT_PRIMARY, Colors.TEXT_PRIMARY),
                ),
                badge_estatus_partida(partida.get('estatus_partida', 'PENDIENTE')),
                spacing="2",
                align="center",
                width="100%",
                justify="between",
            ),
            rx.text(
                partida.get('categorias_texto', '0 categorías'),
                font_size=Typography.SIZE_XS,
                color=rx.cond(es_activa, Colors.TEXT_PRIMARY, Colors.TEXT_SECONDARY),
                width="100%",
                text_align="left",
            ),
            rx.cond(
                partida.get('personal_rango_texto', '') != '',
                rx.text(
                    partida.get('personal_rango_texto', ''),
                    font_size=Typography.SIZE_XS,
                    color=rx.cond(es_activa, Colors.TEXT_PRIMARY, Colors.TEXT_SECONDARY),
                    width="100%",
                    text_align="left",
                ),
                rx.fragment(),
            ),
            rx.cond(
                partida.get('total_minimo_texto', '$0.00') == partida.get('total_maximo_texto', '$0.00'),
                rx.text(
                    partida.get('total_minimo_texto', '$0.00'),
                    font_size=Typography.SIZE_SM,
                    color=rx.cond(es_activa, Colors.PRIMARY_HOVER, Colors.PRIMARY),
                    font_weight="600",
                    width="100%",
                    text_align="left",
                ),
                rx.text(
                    partida.get('total_minimo_texto', '$0.00'),
                    " a ",
                    partida.get('total_maximo_texto', '$0.00'),
                    font_size=Typography.SIZE_SM,
                    color=rx.cond(es_activa, Colors.PRIMARY_HOVER, Colors.PRIMARY),
                    font_weight="600",
                    width="100%",
                    text_align="left",
                ),
            ),
            spacing="1",
            align_items="start",
            width="100%",
        ),
        variant=rx.cond(
            es_activa,
            "surface",
            "ghost",
        ),
        color_scheme=rx.cond(
            es_activa,
            "blue",
            "gray",
        ),
        background=rx.cond(
            es_activa,
            Colors.PRIMARY_LIGHTER,
            Colors.SURFACE,
        ),
        border=rx.cond(
            es_activa,
            f"1px solid {Colors.PRIMARY_LIGHT}",
            f"1px solid {Colors.BORDER}",
        ),
        size="2",
        on_click=CotizadorDetalleState.seleccionar_partida(partida.get('id', 0)),
        min_width="220px",
        height="auto",
        align_items="start",
        padding=Spacing.MD,
        box_shadow=rx.cond(
            es_activa,
            "0 4px 12px rgba(30, 64, 175, 0.08)",
            "none",
        ),
    )


def _celda_matriz(concepto: dict, celda: dict) -> rx.Component:
    """Renderiza una celda de la matriz respetando si es editable o calculada."""
    from app.presentation.pages.cotizador.cotizador_detalle_state import CotizadorDetalleState

    return rx.table.cell(
        rx.cond(
            celda.get('editable', False),
            rx.vstack(
                rx.input(
                    default_value=celda.get('valor_input', '0.00'),
                    on_blur=lambda value: CotizadorDetalleState.actualizar_valor_celda(
                        concepto.get('id', 0),
                        celda.get('partida_categoria_id', 0),
                        value,
                    ),
                    type="number",
                    step="0.01",
                    min="0",
                    width="100%",
                    min_width="132px",
                    text_align="right",
                    background=Colors.SURFACE,
                ),
                rx.cond(
                    concepto.get('tipo_valor') == 'PORCENTAJE',
                    rx.text(
                        "Equivale a ",
                        celda.get('valor_calculado_texto', '$0.00'),
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                        width="100%",
                        text_align="right",
                    ),
                    rx.text(
                        celda.get('valor_mostrado_texto', '$0.00'),
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                        width="100%",
                        text_align="right",
                    ),
                ),
                spacing="1",
                align_items="start",
                min_width="132px",
                width="100%",
            ),
            rx.vstack(
                _money_text(
                    celda.get('valor_mostrado_texto', '$0.00'),
                ),
                rx.cond(
                    concepto.get('tipo_valor') == 'PORCENTAJE',
                    rx.text(
                        celda.get('valor_input', '0.00'),
                        "% capturado",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                        width="100%",
                        text_align="right",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align_items="end",
                min_width="132px",
                width="100%",
            ),
        ),
        vertical_align="top",
    )


def _fila_matriz(concepto: dict) -> rx.Component:
    """Fila completa de concepto dentro de la matriz de costos."""
    return rx.table.row(
        rx.table.row_header_cell(
            rx.vstack(
                rx.text(
                    concepto.get('nombre', ''),
                    font_size=Typography.SIZE_SM,
                    font_weight="600",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.cond(
                    concepto.get('es_autogenerado', False),
                    rx.text(
                        "Generado por el motor patronal",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align_items="start",
                min_width="220px",
                width="100%",
            ),
            background=Colors.SURFACE,
            position="sticky",
            left="0",
            z_index="1",
        ),
        rx.table.cell(
            rx.vstack(
                rx.cond(
                    concepto.get('tipo_concepto') == 'PATRONAL',
                    rx.badge("Patronal", color_scheme="blue", variant="soft"),
                    rx.badge("Indirecto", color_scheme="gray", variant="soft"),
                ),
                rx.text(
                    concepto.get('tipo_valor_texto', ''),
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="1",
                align_items="start",
                min_width="160px",
                width="100%",
            ),
            background=Colors.SURFACE,
            position="sticky",
            left="220px",
            z_index="1",
        ),
        rx.foreach(
            concepto['celdas'],
            lambda celda: _celda_matriz(concepto, celda),
        ),
    )


def tabla_matriz_costos(
    matriz_costos: rx.Var,
    columnas_matriz: rx.Var,
    hay_categorias: rx.Var,
) -> rx.Component:
    """Matriz editable de conceptos × categorías con precio unitario final."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Matriz de costos",
                        font_size=Typography.SIZE_BASE,
                        font_weight="600",
                        color=Colors.TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Los conceptos por porcentaje se capturan como % y se convierten a pesos sobre el subtotal parcial.",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="1",
                    align_items="start",
                ),
                width="100%",
                justify="between",
                align="start",
            ),
            rx.cond(
                hay_categorias,
                _table_shell(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(_header_label("Concepto")),
                                rx.table.column_header_cell(_header_label("Tipo")),
                                rx.foreach(
                                    columnas_matriz,
                                    lambda columna: rx.table.column_header_cell(
                                        rx.vstack(
                                            rx.text(
                                                columna.get('categoria_nombre', ''),
                                                font_size=Typography.SIZE_SM,
                                                font_weight="600",
                                                color=Colors.TEXT_PRIMARY,
                                            ),
                                            rx.text(
                                                columna.get('cantidad_rango_texto', ''),
                                                font_size=Typography.SIZE_XS,
                                                color=Colors.TEXT_SECONDARY,
                                            ),
                                            spacing="1",
                                            align_items="start",
                                            min_width="150px",
                                            width="100%",
                                        )
                                    ),
                                ),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(matriz_costos, _fila_matriz),
                            rx.table.row(
                                rx.table.row_header_cell(
                                    rx.text(
                                        "Precio unitario final",
                                        font_size=Typography.SIZE_SM,
                                        font_weight="700",
                                        color=Colors.TEXT_PRIMARY,
                                    ),
                                    background=Colors.PRIMARY_LIGHTER,
                                    position="sticky",
                                    left="0",
                                    z_index="1",
                                ),
                                rx.table.cell(
                                    rx.text(
                                        "Consolidado por categoría",
                                        font_size=Typography.SIZE_XS,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                    background=Colors.PRIMARY_LIGHTER,
                                    position="sticky",
                                    left="220px",
                                    z_index="1",
                                ),
                                rx.foreach(
                                    columnas_matriz,
                                    lambda columna: rx.table.cell(
                                        _money_text(
                                            columna.get('precio_unitario_texto', '$0.00'),
                                            color=Colors.PRIMARY,
                                            weight="700",
                                        )
                                    ),
                                ),
                            ),
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
                ),
                rx.center(
                    rx.text(
                        "Agrega categorías para construir la matriz de costos.",
                        color=Colors.TEXT_SECONDARY,
                        font_size=Typography.SIZE_XS,
                    ),
                    padding=Spacing.LG,
                ),
            ),
            spacing="2",
            width="100%",
        ),
        padding=Spacing.MD,
        width="100%",
        overflow_x="auto",
    )


def resumen_cotizacion_card() -> rx.Component:
    """Card con totales de toda la cotización (partidas + items globales + IVA)."""
    from app.presentation.pages.cotizador.cotizador_detalle_state import CotizadorDetalleState

    totales_personal = rx.vstack(
        rx.hstack(
            rx.text("", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="140px"),
            rx.text("Mínimo", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, font_weight=Typography.WEIGHT_SEMIBOLD),
            rx.spacer(),
            rx.text("Máximo", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, font_weight=Typography.WEIGHT_SEMIBOLD),
            width="100%",
        ),
        rx.hstack(
            rx.text("Subtotal:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="140px"),
            rx.text(CotizadorDetalleState.cot_subtotal_min, font_size=Typography.SIZE_SM),
            rx.spacer(),
            rx.text(CotizadorDetalleState.cot_subtotal_max, font_size=Typography.SIZE_SM),
            width="100%",
        ),
        rx.cond(
            CotizadorDetalleState.aplicar_iva,
            rx.hstack(
                rx.text("IVA (16%):", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="140px"),
                rx.text(CotizadorDetalleState.cot_iva_min, font_size=Typography.SIZE_SM),
                rx.spacer(),
                rx.text(CotizadorDetalleState.cot_iva_max, font_size=Typography.SIZE_SM),
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.divider(),
        rx.hstack(
            rx.text("TOTAL:", font_size=Typography.SIZE_LG, color=Colors.TEXT_PRIMARY, font_weight="700", min_width="140px"),
            rx.text(CotizadorDetalleState.cot_total_min, font_size=Typography.SIZE_LG, font_weight="700", color=Colors.PRIMARY),
            rx.spacer(),
            rx.text(CotizadorDetalleState.cot_total_max, font_size=Typography.SIZE_LG, font_weight="700", color=Colors.PRIMARY),
            width="100%",
            background=Colors.PRIMARY_LIGHTER,
            padding=Spacing.SM,
            border_radius="10px",
        ),
        spacing="2",
        width="100%",
    )

    totales_productos = rx.vstack(
        rx.hstack(
            rx.text("Subtotal:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="140px"),
            rx.spacer(),
            rx.text(CotizadorDetalleState.cot_subtotal_min, font_size=Typography.SIZE_SM),
            width="100%",
        ),
        rx.cond(
            CotizadorDetalleState.aplicar_iva,
            rx.hstack(
                rx.text("IVA (16%):", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY, min_width="140px"),
                rx.spacer(),
                rx.text(CotizadorDetalleState.cot_iva_min, font_size=Typography.SIZE_SM),
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.divider(),
        rx.hstack(
            rx.text("TOTAL:", font_size=Typography.SIZE_LG, color=Colors.TEXT_PRIMARY, font_weight="700", min_width="140px"),
            rx.spacer(),
            rx.text(CotizadorDetalleState.cot_total_min, font_size=Typography.SIZE_LG, font_weight="700", color=Colors.PRIMARY),
            width="100%",
            background=Colors.PRIMARY_LIGHTER,
            padding=Spacing.SM,
            border_radius="10px",
        ),
        spacing="2",
        width="100%",
    )

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("calculator", size=18, color=Colors.PRIMARY),
                rx.text(
                    "Total de la Cotización",
                    font_size=Typography.SIZE_BASE,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                spacing="2",
                align="center",
            ),
            rx.divider(),
            rx.cond(
                CotizadorDetalleState.es_tipo_personal,
                totales_personal,
                totales_productos,
            ),
            # IVA toggle
            rx.cond(
                CotizadorDetalleState.cotizacion_es_editable,
                rx.hstack(
                    rx.checkbox(
                        "Aplicar IVA 16%",
                        checked=CotizadorDetalleState.aplicar_iva,
                        on_change=CotizadorDetalleState.toggle_aplicar_iva,
                        size="2",
                    ),
                    padding_top=Spacing.XS,
                ),
                rx.fragment(),
            ),
            # Meses (solo personal)
            rx.cond(
                CotizadorDetalleState.es_tipo_personal & CotizadorDetalleState.cotizacion_es_editable,
                rx.hstack(
                    rx.text("Meses:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    rx.input(
                        default_value=CotizadorDetalleState.cantidad_meses,
                        on_blur=CotizadorDetalleState.actualizar_cantidad_meses,
                        type="number",
                        min="1",
                        width="80px",
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                    padding_top=Spacing.XS,
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
        ),
        padding=Spacing.LG,
        width="100%",
        border=f"2px solid {Colors.PRIMARY_LIGHT}",
    )
