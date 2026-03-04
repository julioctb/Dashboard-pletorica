"""
Página de detalle de una cotización.

Muestra las partidas, la matriz de costos y permite edición.
Ruta: /cotizador/[cotizacion_id]
"""
import reflex as rx

from app.presentation.theme import Colors, Spacing, Typography
from app.presentation.components.ui import (
    page_header,
    form_input,
    form_select,
    form_row,
    botones_modal,
    boton_guardar,
    boton_cancelar,
)
from app.presentation.pages.cotizador.cotizador_detalle_state import CotizadorDetalleState
from app.presentation.pages.cotizador.cotizador_components import (
    badge_estatus_cotizacion,
    badge_estatus_partida,
    resumen_partida_card,
    fila_partida_tab,
)


def _modal_agregar_categoria() -> rx.Component:
    """Modal para agregar una categoría de personal a la partida."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Agregar Categoría"),
            rx.dialog.description(
                "Define la categoría de personal y su salario base.",
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
            rx.vstack(
                rx.box(
                    rx.text(
                        "Categoría de puesto",
                        font_size=Typography.SIZE_SM,
                        font_weight="500",
                        color=Colors.TEXT_PRIMARY,
                        margin_bottom=Spacing.XS,
                    ),
                    rx.select.root(
                        rx.select.trigger(placeholder="Seleccionar categoría"),
                        rx.select.content(
                            rx.foreach(
                                CotizadorDetalleState.categorias_puesto_catalogo,
                                lambda cat: rx.select.item(
                                    cat['nombre'],
                                    value=cat['id'].to_string(),
                                ),
                            )
                        ),
                        on_change=CotizadorDetalleState.set_form_cat_categoria_puesto_id,
                        size="2",
                        width="100%",
                    ),
                    width="100%",
                ),
                form_input(
                    label="Salario base mensual",
                    required=True,
                    placeholder="Ej: 15000.00",
                    value=CotizadorDetalleState.form_cat_salario_base,
                    on_change=CotizadorDetalleState.set_form_cat_salario_base,
                    error=CotizadorDetalleState.error_cat_salario,
                ),
                form_row(
                    form_input(
                        label="Cantidad mínima",
                        placeholder="0",
                        value=CotizadorDetalleState.form_cat_cantidad_min,
                        on_change=CotizadorDetalleState.set_form_cat_cantidad_min,
                        error=CotizadorDetalleState.error_cat_cantidad_min,
                    ),
                    form_input(
                        label="Cantidad máxima",
                        placeholder="0",
                        value=CotizadorDetalleState.form_cat_cantidad_max,
                        on_change=CotizadorDetalleState.set_form_cat_cantidad_max,
                    ),
                ),
                botones_modal(
                    on_guardar=CotizadorDetalleState.agregar_categoria,
                    on_cancelar=CotizadorDetalleState.cerrar_modal_categoria,
                    saving=CotizadorDetalleState.saving,
                    texto_guardar="Agregar",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="500px",
            padding=Spacing.LG,
        ),
        open=CotizadorDetalleState.mostrar_modal_categoria,
        on_open_change=CotizadorDetalleState.set_mostrar_modal_categoria,
    )


def _modal_agregar_concepto() -> rx.Component:
    """Modal para agregar un gasto indirecto a la partida."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Agregar Concepto"),
            rx.dialog.description(
                "Agrega un gasto indirecto a la matriz de costos.",
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
            rx.vstack(
                form_input(
                    label="Nombre del concepto",
                    required=True,
                    placeholder="Ej: Uniformes, Equipo de protección",
                    value=CotizadorDetalleState.form_concepto_nombre,
                    on_change=CotizadorDetalleState.set_form_concepto_nombre,
                    error=CotizadorDetalleState.error_concepto_nombre,
                ),
                rx.box(
                    rx.text(
                        "Tipo de valor",
                        font_size=Typography.SIZE_SM,
                        font_weight="500",
                        color=Colors.TEXT_PRIMARY,
                        margin_bottom=Spacing.XS,
                    ),
                    rx.select.root(
                        rx.select.trigger(placeholder="Tipo de valor"),
                        rx.select.content(
                            rx.select.item("Importe fijo (pesos)", value="FIJO"),
                            rx.select.item("Porcentaje (%)", value="PORCENTAJE"),
                        ),
                        value=CotizadorDetalleState.form_concepto_tipo_valor,
                        on_change=CotizadorDetalleState.set_form_concepto_tipo_valor,
                        size="2",
                        width="100%",
                    ),
                    width="100%",
                ),
                botones_modal(
                    on_guardar=CotizadorDetalleState.agregar_concepto,
                    on_cancelar=CotizadorDetalleState.cerrar_modal_concepto,
                    saving=CotizadorDetalleState.saving,
                    texto_guardar="Agregar",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="450px",
            padding=Spacing.LG,
        ),
        open=CotizadorDetalleState.mostrar_modal_concepto,
        on_open_change=CotizadorDetalleState.set_mostrar_modal_concepto,
    )


def _modal_editar_costo_patronal() -> rx.Component:
    """Modal para editar manualmente el costo patronal."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Editar Costo Patronal"),
            rx.callout.root(
                rx.callout.icon(rx.icon("triangle-alert", size=16)),
                rx.callout.text(
                    "Editar manualmente sobreescribe el cálculo automático. "
                    "Usa esta opción solo si el motor no refleja tu situación fiscal."
                ),
                color="orange",
                size="1",
            ),
            rx.vstack(
                form_input(
                    label="Costo patronal mensual (pesos)",
                    required=True,
                    placeholder="0.00",
                    value=CotizadorDetalleState.form_costo_patronal_manual,
                    on_change=CotizadorDetalleState.set_form_costo_patronal_manual,
                ),
                botones_modal(
                    on_guardar=CotizadorDetalleState.guardar_costo_patronal_manual,
                    on_cancelar=CotizadorDetalleState.cerrar_modal_costo_patronal,
                    saving=CotizadorDetalleState.saving,
                    texto_guardar="Guardar",
                ),
                spacing="3",
                width="100%",
                padding_top=Spacing.MD,
            ),
            max_width="420px",
            padding=Spacing.LG,
        ),
        open=CotizadorDetalleState.mostrar_modal_costo_patronal,
        on_open_change=CotizadorDetalleState.set_mostrar_modal_costo_patronal,
    )


def _header_detalle() -> rx.Component:
    """Header con nombre de cotización y acciones."""
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.link(
                    rx.icon("arrow-left", size=16),
                    href="/cotizador",
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.heading(
                    CotizadorDetalleState.titulo_cotizacion,
                    size="4",
                    color=Colors.TEXT_PRIMARY,
                ),
                badge_estatus_cotizacion(
                    CotizadorDetalleState.cotizacion.get('estatus', 'BORRADOR')
                ),
                spacing="2",
                align="center",
            ),
            rx.text(
                rx.Var.create(
                    f"Versión {CotizadorDetalleState.cotizacion.get('version', 1)}"
                ),
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
            ),
            spacing="1",
            align_items="start",
        ),
        rx.spacer(),
        rx.hstack(
            # TODO: Botón Enviar por correo (preparado, pendiente integración SMTP)
            rx.cond(
                CotizadorDetalleState.cotizacion.get('estatus') != 'BORRADOR',
                rx.button(
                    rx.icon("mail", size=14),
                    "Enviar por correo",
                    variant="outline",
                    color_scheme="blue",
                    size="2",
                    disabled=True,
                    title="Envío por correo — próximamente",
                ),
                rx.fragment(),
            ),
            rx.cond(
                CotizadorDetalleState.cotizacion_es_editable,
                rx.button(
                    rx.icon("plus", size=14),
                    "Nueva Partida",
                    on_click=CotizadorDetalleState.agregar_partida,
                    color_scheme="blue",
                    size="2",
                ),
                rx.fragment(),
            ),
            spacing="2",
        ),
        width="100%",
        align="center",
        padding_bottom=Spacing.MD,
    )


def _tabs_partidas() -> rx.Component:
    """Tabs de navegación entre partidas."""
    return rx.cond(
        CotizadorDetalleState.cantidad_partidas == 0,
        rx.center(
            rx.vstack(
                rx.icon("layers", size=48, color=Colors.TEXT_MUTED),
                rx.text("No hay partidas", color=Colors.TEXT_SECONDARY),
                rx.cond(
                    CotizadorDetalleState.cotizacion_es_editable,
                    rx.button(
                        rx.icon("plus", size=14),
                        "Agregar primera partida",
                        on_click=CotizadorDetalleState.agregar_partida,
                        color_scheme="blue",
                        variant="soft",
                        size="2",
                    ),
                    rx.fragment(),
                ),
                align="center",
                spacing="2",
            ),
            padding=Spacing.XXL,
        ),
        rx.vstack(
            # Tabs
            rx.hstack(
                rx.foreach(
                    CotizadorDetalleState.partidas,
                    lambda p: fila_partida_tab(
                        p, CotizadorDetalleState.partida_seleccionada_id
                    ),
                ),
                spacing="1",
                overflow_x="auto",
                padding_y=Spacing.SM,
            ),
            # Contenido de la partida seleccionada
            rx.cond(
                CotizadorDetalleState.partida_seleccionada_id > 0,
                _contenido_partida(),
                rx.center(rx.spinner(size="3")),
            ),
            spacing="3",
            width="100%",
        ),
    )


def _contenido_partida() -> rx.Component:
    """Contenido de la partida seleccionada: categorías + conceptos."""
    return rx.hstack(
        # Panel izquierdo: acciones y resumen
        rx.vstack(
            _panel_acciones_partida(),
            resumen_partida_card(CotizadorDetalleState.totales_partida),
            spacing="3",
            min_width="280px",
            max_width="320px",
        ),
        # Panel derecho: tabla de categorías y matriz
        rx.vstack(
            _tabla_categorias(),
            rx.cond(
                CotizadorDetalleState.hay_categorias,
                _seccion_conceptos(),
                rx.fragment(),
            ),
            spacing="3",
            flex="1",
        ),
        spacing="3",
        width="100%",
        align_items="start",
    )


def _panel_acciones_partida() -> rx.Component:
    """Panel con acciones de la partida seleccionada."""
    return rx.card(
        rx.vstack(
            rx.text(
                "Acciones de Partida",
                font_size=Typography.SIZE_SM,
                font_weight="600",
                color=Colors.TEXT_PRIMARY,
            ),
            rx.divider(),
            # Estatus
            rx.vstack(
                rx.text("Cambiar estatus:", font_size=Typography.SIZE_XS, color=Colors.TEXT_SECONDARY),
                rx.select.root(
                    rx.select.trigger(placeholder="Cambiar estatus"),
                    rx.select.content(
                        rx.select.item("Pendiente", value="PENDIENTE"),
                        rx.select.item("Aceptada", value="ACEPTADA"),
                        rx.select.item("No asignada", value="NO_ASIGNADA"),
                    ),
                    on_change=lambda v: CotizadorDetalleState.cambiar_estatus_partida_local(v),
                    size="2",
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            # Convertir a contrato
            rx.cond(
                CotizadorDetalleState.partida_activa.get('estatus_partida') == 'ACEPTADA',
                rx.button(
                    rx.icon("arrow-right-from-line", size=14),
                    "Convertir a Contrato",
                    on_click=CotizadorDetalleState.convertir_partida_a_contrato(
                        CotizadorDetalleState.partida_seleccionada_id
                    ),
                    color_scheme="green",
                    size="2",
                    width="100%",
                ),
                rx.fragment(),
            ),
            spacing="2",
            width="100%",
        ),
        padding=Spacing.MD,
    )


def _tabla_categorias() -> rx.Component:
    """Tabla de categorías de personal de la partida."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(
                    "Categorías de Personal",
                    font_size=Typography.SIZE_SM,
                    font_weight="600",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.cond(
                    CotizadorDetalleState.cotizacion_es_editable,
                    rx.button(
                        rx.icon("plus", size=14),
                        "Agregar",
                        size="1",
                        variant="soft",
                        color_scheme="blue",
                        on_click=CotizadorDetalleState.abrir_modal_categoria,
                    ),
                    rx.fragment(),
                ),
                width="100%",
            ),
            rx.cond(
                CotizadorDetalleState.hay_categorias,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Categoría"),
                            rx.table.column_header_cell("Salario Base"),
                            rx.table.column_header_cell("Min"),
                            rx.table.column_header_cell("Max"),
                            rx.table.column_header_cell("Costo Patronal"),
                            rx.table.column_header_cell("P. Unitario"),
                            rx.table.column_header_cell("Acciones"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            CotizadorDetalleState.categorias_partida,
                            _fila_categoria,
                        )
                    ),
                    variant="surface",
                    size="1",
                    width="100%",
                ),
                rx.center(
                    rx.text(
                        "Agrega categorías de personal para construir la matriz",
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
    )


def _fila_categoria(cat: dict) -> rx.Component:
    """Fila de la tabla de categorías."""
    return rx.table.row(
        rx.table.cell(cat['categoria_nombre']),
        rx.table.cell(cat['salario_base_mensual']),
        rx.table.cell(cat['cantidad_minima']),
        rx.table.cell(cat['cantidad_maxima']),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    cat['fue_editado_manualmente'],
                    rx.badge("Manual", color_scheme="orange", size="1"),
                    rx.fragment(),
                ),
                rx.text(
                    cat['costo_patronal_efectivo'],
                    font_size=Typography.SIZE_XS,
                ),
                spacing="1",
            )
        ),
        rx.table.cell(
            rx.text(
                cat['precio_unitario_final'],
                font_weight="600",
                color=Colors.PRIMARY,
                font_size=Typography.SIZE_XS,
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("calculator", size=13),
                    size="1",
                    variant="ghost",
                    color_scheme="blue",
                    on_click=CotizadorDetalleState.recalcular_costo_patronal(cat['id']),
                    title="Recalcular costo patronal",
                ),
                rx.cond(
                    CotizadorDetalleState.cotizacion_es_editable,
                    rx.hstack(
                        rx.button(
                            rx.icon("pencil", size=13),
                            size="1",
                            variant="ghost",
                            color_scheme="orange",
                            on_click=CotizadorDetalleState.abrir_modal_costo_patronal(
                                cat['id'],
                                cat['costo_patronal_efectivo'].to_string(),
                            ),
                            title="Editar costo patronal",
                        ),
                        rx.button(
                            rx.icon("trash-2", size=13),
                            size="1",
                            variant="ghost",
                            color_scheme="red",
                            on_click=CotizadorDetalleState.eliminar_categoria(cat['id']),
                        ),
                        spacing="1",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
            )
        ),
    )


def _seccion_conceptos() -> rx.Component:
    """Sección de conceptos (gastos indirectos) de la partida."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(
                    "Conceptos Adicionales",
                    font_size=Typography.SIZE_SM,
                    font_weight="600",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    "(Gastos indirectos)",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.spacer(),
                rx.cond(
                    CotizadorDetalleState.cotizacion_es_editable,
                    rx.button(
                        rx.icon("plus", size=14),
                        "Agregar",
                        size="1",
                        variant="soft",
                        color_scheme="blue",
                        on_click=CotizadorDetalleState.abrir_modal_concepto,
                    ),
                    rx.fragment(),
                ),
                width="100%",
            ),
            rx.cond(
                CotizadorDetalleState.conceptos_partida.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Concepto"),
                            rx.table.column_header_cell("Tipo"),
                            rx.table.column_header_cell("Autogenerado"),
                            rx.table.column_header_cell("Acciones"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            CotizadorDetalleState.conceptos_partida,
                            _fila_concepto,
                        )
                    ),
                    variant="surface",
                    size="1",
                    width="100%",
                ),
                rx.center(
                    rx.text(
                        "Sin conceptos adicionales. Los costos patronales se generan automáticamente.",
                        color=Colors.TEXT_SECONDARY,
                        font_size=Typography.SIZE_XS,
                    ),
                    padding=Spacing.MD,
                ),
            ),
            spacing="2",
            width="100%",
        ),
        padding=Spacing.MD,
        width="100%",
    )


def _fila_concepto(concepto: dict) -> rx.Component:
    """Fila de la tabla de conceptos."""
    return rx.table.row(
        rx.table.cell(concepto.get('nombre', '')),
        rx.table.cell(
            rx.cond(
                concepto.get('tipo_concepto') == 'PATRONAL',
                rx.badge("Patronal", color_scheme='blue', size="1"),
                rx.badge("Indirecto", color_scheme='gray', size="1"),
            )
        ),
        rx.table.cell(
            rx.cond(
                concepto.get('es_autogenerado', False),
                rx.icon("check", size=14, color=Colors.SUCCESS),
                rx.icon("minus", size=14, color=Colors.TEXT_MUTED),
            )
        ),
        rx.table.cell(
            rx.cond(
                concepto.get('es_autogenerado', False) | (concepto.get('tipo_concepto') == 'PATRONAL'),
                rx.fragment(),
                rx.cond(
                    CotizadorDetalleState.cotizacion_es_editable,
                    rx.button(
                        rx.icon("trash-2", size=13),
                        size="1",
                        variant="ghost",
                        color_scheme="red",
                        on_click=CotizadorDetalleState.eliminar_concepto(concepto.get('id', 0)),
                    ),
                    rx.fragment(),
                ),
            )
        ),
    )


def cotizador_detalle_page() -> rx.Component:
    """Página de detalle de una cotización."""
    return rx.box(
        rx.cond(
            CotizadorDetalleState.loading_detalle,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text("Cargando cotización...", color=Colors.TEXT_SECONDARY),
                    align="center",
                    spacing="2",
                ),
                height="60vh",
            ),
            rx.vstack(
                _header_detalle(),
                _tabs_partidas(),
                spacing="3",
                width="100%",
            ),
        ),
        _modal_agregar_categoria(),
        _modal_agregar_concepto(),
        _modal_editar_costo_patronal(),
        on_mount=lambda: CotizadorDetalleState.cargar_detalle(
            rx.State.router.page.params.get("cotizacion_id", "0")
        ),
        padding=Spacing.LG,
        width="100%",
    )
