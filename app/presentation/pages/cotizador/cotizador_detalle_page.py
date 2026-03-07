"""
Página de detalle de una cotización.

Muestra las partidas, la matriz de costos y permite edición.
Ruta: /portal/cotizador/[cotizacion_id]
"""
import reflex as rx

from app.presentation.theme import Colors, Spacing, Typography
from app.presentation.layout import page_layout
from app.presentation.components.ui import (
    form_input,
    form_textarea,
    form_date,
    form_row,
    botones_modal,
)
from app.presentation.components.ui.action_buttons import (
    tabla_action_button,
    tabla_action_buttons,
)
from app.presentation.pages.cotizador.cotizador_detalle_state import CotizadorDetalleState
from app.presentation.pages.cotizador.cotizador_components import (
    badge_estatus_cotizacion,
    badge_estatus_partida,
    tipo_cotizacion_badge,
    resumen_partida_card,
    resumen_cotizacion_card,
    fila_partida_tab,
    tabla_matriz_costos,
    _table_shell,
    _header_label,
    _money_text,
)


def _meta_bloque(icono: str, etiqueta: str, valor: rx.Var | str) -> rx.Component:
    """Bloque compacto de metadata para la cabecera."""
    return rx.card(
        rx.hstack(
            rx.center(
                rx.icon(icono, size=18, color=Colors.PRIMARY),
                width="40px",
                height="40px",
                border_radius="12px",
                background=Colors.PRIMARY_LIGHT,
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(
                    etiqueta,
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                    font_weight="600",
                ),
                rx.text(
                    valor,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                    font_weight="500",
                ),
                spacing="1",
                align_items="start",
                min_width="0",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        width="100%",
    )


def _boton_cotizador(
    texto: str,
    icono: str,
    on_click,
    *,
    color_scheme: str = "gray",
    variant: str = "soft",
    size: str = "2",
    width: str | None = None,
) -> rx.Component:
    """Botón con lenguaje visual consistente para acciones del cotizador."""
    props = {
        "on_click": on_click,
        "color_scheme": color_scheme,
        "variant": variant,
        "size": size,
        "flex_shrink": "0",
    }
    if width is not None:
        props["width"] = width

    return rx.button(
        rx.hstack(
            rx.icon(icono, size=14 if size == "2" else 13),
            rx.text(texto),
            spacing="2",
            align="center",
        ),
        **props,
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
                "Agrega un gasto indirecto a la matriz de costos. Si eliges porcentaje, se captura como % y el sistema lo convierte a pesos sobre el subtotal parcial.",
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


def _modal_editar_cotizacion() -> rx.Component:
    """Modal para editar la información general de la cotización."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Editar información de la cotización"),
            rx.dialog.description(
                "Actualiza período, destinatario y notas visibles en el PDF.",
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
            rx.vstack(
                form_row(
                    form_date(
                        label="Fecha inicio período",
                        value=CotizadorDetalleState.form_edit_fecha_inicio,
                        on_change=CotizadorDetalleState.set_form_edit_fecha_inicio,
                        on_blur=CotizadorDetalleState.validar_edit_fecha_inicio_campo,
                        error=CotizadorDetalleState.error_edit_fecha_inicio,
                    ),
                    form_date(
                        label="Fecha fin período",
                        value=CotizadorDetalleState.form_edit_fecha_fin,
                        on_change=CotizadorDetalleState.set_form_edit_fecha_fin,
                        on_blur=CotizadorDetalleState.validar_edit_fecha_fin_campo,
                        error=CotizadorDetalleState.error_edit_fecha_fin,
                        min=CotizadorDetalleState.form_edit_fecha_inicio,
                    ),
                ),
                form_row(
                    form_input(
                        label="Nombre del destinatario",
                        placeholder="Ej: Dr. Juan Pérez",
                        value=CotizadorDetalleState.form_edit_destinatario_nombre,
                        on_change=CotizadorDetalleState.set_form_edit_destinatario_nombre,
                    ),
                    form_input(
                        label="Cargo del destinatario",
                        placeholder="Ej: Director de Planeación",
                        value=CotizadorDetalleState.form_edit_destinatario_cargo,
                        on_change=CotizadorDetalleState.set_form_edit_destinatario_cargo,
                    ),
                ),
                form_textarea(
                    label="Notas de la cotización",
                    placeholder="Detalles comerciales, condiciones o alcance...",
                    value=CotizadorDetalleState.form_edit_notas,
                    on_change=CotizadorDetalleState.set_form_edit_notas,
                    min_height="96px",
                ),
                rx.hstack(
                    rx.checkbox(
                        "Incluir desglose de conceptos en PDF",
                        checked=CotizadorDetalleState.form_edit_mostrar_desglose,
                        on_change=CotizadorDetalleState.set_form_edit_mostrar_desglose,
                        size="2",
                    ),
                    padding_top=Spacing.XS,
                ),
                rx.hstack(
                    rx.checkbox(
                        "Aplicar IVA 16%",
                        checked=CotizadorDetalleState.form_edit_aplicar_iva,
                        on_change=CotizadorDetalleState.set_form_edit_aplicar_iva,
                        size="2",
                    ),
                    padding_top=Spacing.XS,
                ),
                rx.cond(
                    CotizadorDetalleState.es_tipo_personal,
                    form_input(
                        label="Cantidad de meses",
                        placeholder="1",
                        value=CotizadorDetalleState.form_edit_cantidad_meses,
                        on_change=CotizadorDetalleState.set_form_edit_cantidad_meses,
                    ),
                    rx.fragment(),
                ),
                botones_modal(
                    on_guardar=CotizadorDetalleState.guardar_info_cotizacion,
                    on_cancelar=CotizadorDetalleState.cerrar_modal_editar_cotizacion,
                    saving=CotizadorDetalleState.saving,
                    texto_guardar="Guardar cambios",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="620px",
            padding=Spacing.LG,
        ),
        open=CotizadorDetalleState.mostrar_modal_editar_cotizacion,
        on_open_change=CotizadorDetalleState.set_mostrar_modal_editar_cotizacion,
    )


def _modal_editar_partida() -> rx.Component:
    """Modal para editar la información de la partida activa."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Editar información de partida"),
            rx.dialog.description(
                "Agrega notas operativas o comerciales para esta partida.",
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
            rx.vstack(
                form_textarea(
                    label="Notas de la partida",
                    placeholder="Ej: Alcance por sede, supuestos operativos o consideraciones comerciales...",
                    value=CotizadorDetalleState.form_partida_notas,
                    on_change=CotizadorDetalleState.set_form_partida_notas,
                    min_height="120px",
                ),
                botones_modal(
                    on_guardar=CotizadorDetalleState.guardar_info_partida,
                    on_cancelar=CotizadorDetalleState.cerrar_modal_editar_partida,
                    saving=CotizadorDetalleState.saving,
                    texto_guardar="Guardar partida",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="560px",
            padding=Spacing.LG,
        ),
        open=CotizadorDetalleState.mostrar_modal_editar_partida,
        on_open_change=CotizadorDetalleState.set_mostrar_modal_editar_partida,
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
    return rx.vstack(
        rx.flex(
            rx.vstack(
                rx.hstack(
                    rx.link(
                        rx.hstack(
                            rx.icon("arrow-left", size=16),
                            rx.text(
                                "Volver al listado",
                                font_size=Typography.SIZE_SM,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        href="/portal/cotizador",
                        underline="none",
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.heading(
                        CotizadorDetalleState.titulo_cotizacion,
                        size="5",
                        color=Colors.TEXT_PRIMARY,
                    ),
                    tipo_cotizacion_badge(
                        CotizadorDetalleState.tipo_cotizacion,
                    ),
                    badge_estatus_cotizacion(
                        CotizadorDetalleState.cotizacion.get('estatus', 'BORRADOR')
                    ),
                    spacing="3",
                    align="center",
                    wrap="wrap",
                    width="100%",
                ),
                rx.hstack(
                    rx.badge(
                        CotizadorDetalleState.version_cotizacion,
                        color_scheme="gray",
                        variant="soft",
                        size="1",
                    ),
                    rx.badge(
                        CotizadorDetalleState.cantidad_partidas_texto,
                        color_scheme="blue",
                        variant="soft",
                        size="1",
                    ),
                    spacing="2",
                    wrap="wrap",
                ),
                spacing="3",
                align_items="start",
                min_width="280px",
                flex="1 1 420px",
            ),
            rx.flex(
                rx.cond(
                    CotizadorDetalleState.puede_versionar_cotizacion,
                    _boton_cotizador(
                        "Nueva versión",
                        "copy",
                        CotizadorDetalleState.crear_nueva_version_actual,
                        color_scheme="gray",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    CotizadorDetalleState.puede_editar_info_cotizacion,
                    _boton_cotizador(
                        "Editar información",
                        "pencil-line",
                        CotizadorDetalleState.abrir_modal_editar_cotizacion,
                        color_scheme="gray",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    CotizadorDetalleState.cantidad_partidas > 0,
                    _boton_cotizador(
                        "Descargar PDF",
                        "download",
                        CotizadorDetalleState.descargar_pdf,
                        color_scheme="blue",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    CotizadorDetalleState.cotizacion_es_editable,
                    _boton_cotizador(
                        "Nueva Partida",
                        "plus",
                        CotizadorDetalleState.agregar_partida,
                        color_scheme="blue",
                        variant="solid",
                    ),
                    rx.fragment(),
                ),
                gap=Spacing.SM,
                justify="end",
                wrap="wrap",
                flex="1 1 280px",
            ),
            width="100%",
            justify="between",
            align="start",
            wrap="wrap",
            gap=Spacing.MD,
        ),
        rx.flex(
            rx.cond(
                CotizadorDetalleState.tiene_periodo_definido,
                _meta_bloque("calendar-range", "Periodo", CotizadorDetalleState.periodo_cotizacion),
                rx.fragment(),
            ),
            rx.cond(
                CotizadorDetalleState.es_tipo_personal,
                _meta_bloque("calendar-clock", "Duración", CotizadorDetalleState.meses_texto),
                rx.fragment(),
            ),
            _meta_bloque("user-round", "Destinatario", CotizadorDetalleState.destinatario_cotizacion),
            _meta_bloque("receipt", "IVA", CotizadorDetalleState.iva_texto),
            _meta_bloque("file-badge", "Configuración PDF", CotizadorDetalleState.desglose_pdf_texto),
            width="100%",
            wrap="wrap",
            gap=Spacing.MD,
        ),
        rx.cond(
            CotizadorDetalleState.notas_cotizacion_resumen != "Sin notas adicionales",
            rx.card(
                rx.vstack(
                    rx.text(
                        "Notas",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                        font_weight="600",
                    ),
                    rx.text(
                        CotizadorDetalleState.notas_cotizacion_resumen,
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    spacing="1",
                    align_items="start",
                ),
                width="100%",
            ),
            rx.fragment(),
        ),
        width="100%",
        spacing="4",
    )


def _toolbar_estatus_cotizacion() -> rx.Component:
    """Franja secundaria para transiciones de estatus."""
    return rx.cond(
        CotizadorDetalleState.tiene_acciones_estatus,
        rx.flex(
            rx.hstack(
                rx.icon("workflow", size=16, color=Colors.TEXT_SECONDARY),
                rx.text(
                    "Transiciones de estatus",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                    font_weight="600",
                ),
                spacing="2",
                align="center",
            ),
            rx.flex(
                rx.cond(
                    CotizadorDetalleState.puede_preparar_cotizacion,
                    _boton_cotizador(
                        "Preparar",
                        "badge-check",
                        CotizadorDetalleState.cambiar_estatus_cotizacion("PREPARADA"),
                        color_scheme="blue",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    CotizadorDetalleState.puede_marcar_enviada,
                    _boton_cotizador(
                        "Marcar enviada",
                        "send",
                        CotizadorDetalleState.cambiar_estatus_cotizacion("ENVIADA"),
                        color_scheme="orange",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    CotizadorDetalleState.puede_aprobar_cotizacion,
                    _boton_cotizador(
                        "Aprobar",
                        "circle-check-big",
                        CotizadorDetalleState.cambiar_estatus_cotizacion("APROBADA"),
                        color_scheme="green",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    CotizadorDetalleState.puede_rechazar_cotizacion,
                    _boton_cotizador(
                        "Rechazar",
                        "circle-x",
                        CotizadorDetalleState.cambiar_estatus_cotizacion("RECHAZADA"),
                        color_scheme="red",
                    ),
                    rx.fragment(),
                ),
                justify="end",
                wrap="wrap",
                gap=Spacing.SM,
            ),
            width="100%",
            justify="between",
            align="center",
            wrap="wrap",
            gap=Spacing.MD,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius="12px",
            padding=Spacing.MD,
            margin_bottom=Spacing.MD,
        ),
        rx.fragment(),
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
                    _boton_cotizador(
                        "Agregar primera partida",
                        "plus",
                        CotizadorDetalleState.agregar_partida,
                        color_scheme="blue",
                        variant="soft",
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
            # Conceptos globales + Total de cotización (fuera de la partida)
            _tabla_items_globales(),
            rx.cond(
                CotizadorDetalleState.hay_totales_cotizacion,
                resumen_cotizacion_card(),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
        ),
    )


def _fila_item_detalle(item: dict) -> rx.Component:
    """Fila de solo lectura de un item en la tabla de items del detalle."""
    return rx.table.row(
        rx.table.cell(
            rx.text(
                item.get('numero', ''),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                text_align="center",
            )
        ),
        rx.table.cell(
            rx.text(
                item.get('cantidad_texto', '1'),
                font_size=Typography.SIZE_SM,
                text_align="right",
                width="100%",
            )
        ),
        rx.table.cell(
            rx.text(
                item.get('descripcion', ''),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
            )
        ),
        rx.table.cell(
            _money_text(item.get('precio_unitario_texto', '$0.00')),
        ),
        rx.table.cell(
            _money_text(
                item.get('importe_texto', '$0.00'),
                weight="600",
            )
        ),
        rx.table.cell(
            rx.cond(
                CotizadorDetalleState.cotizacion_es_editable,
                rx.icon_button(
                    rx.icon("x", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=CotizadorDetalleState.eliminar_item_detalle(item.get('id', 0)),
                ),
                rx.fragment(),
            )
        ),
        _hover={"background": Colors.BG_APP},
    )


def _tabla_items_partida() -> rx.Component:
    """Tabla de items para una partida de tipo PRODUCTOS_SERVICIOS."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(
                    "Conceptos de la partida",
                    font_size=Typography.SIZE_BASE,
                    font_weight="600",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.cond(
                    CotizadorDetalleState.cotizacion_es_editable,
                    _boton_cotizador(
                        "Agregar",
                        "plus",
                        CotizadorDetalleState.abrir_modal_item_partida,
                        color_scheme="blue",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                width="100%",
            ),
            rx.cond(
                CotizadorDetalleState.hay_items_partida,
                _table_shell(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(_header_label("#", align="center")),
                                rx.table.column_header_cell(_header_label("Cantidad", align="right")),
                                rx.table.column_header_cell(_header_label("Concepto")),
                                rx.table.column_header_cell(_header_label("Unitario", align="right")),
                                rx.table.column_header_cell(_header_label("Importe", align="right")),
                                rx.table.column_header_cell(_header_label("", align="center")),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                CotizadorDetalleState.items_partida,
                                _fila_item_detalle,
                            )
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
                ),
                rx.center(
                    rx.text(
                        "Agrega conceptos a esta partida.",
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


def _tabla_items_globales() -> rx.Component:
    """Tabla de items globales de la cotización."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(
                    "Conceptos globales",
                    font_size=Typography.SIZE_BASE,
                    font_weight="600",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    "(aplican a toda la cotización)",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.spacer(),
                rx.cond(
                    CotizadorDetalleState.cotizacion_es_editable,
                    _boton_cotizador(
                        "Agregar global",
                        "plus",
                        CotizadorDetalleState.abrir_modal_item_global,
                        color_scheme="blue",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                CotizadorDetalleState.hay_items_globales,
                _table_shell(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(_header_label("#", align="center")),
                                rx.table.column_header_cell(_header_label("Cantidad", align="right")),
                                rx.table.column_header_cell(_header_label("Concepto")),
                                rx.table.column_header_cell(_header_label("Unitario", align="right")),
                                rx.table.column_header_cell(_header_label("Importe", align="right")),
                                rx.table.column_header_cell(_header_label("", align="center")),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                CotizadorDetalleState.items_globales,
                                _fila_item_detalle,
                            )
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
                ),
                rx.center(
                    rx.text(
                        "Sin conceptos globales.",
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
        overflow_x="auto",
    )


def _modal_agregar_item() -> rx.Component:
    """Modal para agregar un item (partida o global)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Agregar Concepto"),
            rx.dialog.description(
                "Agrega un concepto con cantidad y precio unitario.",
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
            rx.vstack(
                form_input(
                    label="Descripción",
                    required=True,
                    placeholder="Ej: Servicio de limpieza mensual",
                    value=CotizadorDetalleState.form_item_descripcion,
                    on_change=CotizadorDetalleState.set_form_item_descripcion,
                    error=CotizadorDetalleState.error_item_descripcion,
                ),
                form_row(
                    form_input(
                        label="Cantidad",
                        required=True,
                        placeholder="1",
                        value=CotizadorDetalleState.form_item_cantidad,
                        on_change=CotizadorDetalleState.set_form_item_cantidad,
                        error=CotizadorDetalleState.error_item_cantidad,
                    ),
                    form_input(
                        label="Precio unitario",
                        required=True,
                        placeholder="0.00",
                        value=CotizadorDetalleState.form_item_precio_unitario,
                        on_change=CotizadorDetalleState.set_form_item_precio_unitario,
                        error=CotizadorDetalleState.error_item_precio,
                    ),
                ),
                botones_modal(
                    on_guardar=CotizadorDetalleState.agregar_item_detalle,
                    on_cancelar=CotizadorDetalleState.cerrar_modal_item,
                    saving=CotizadorDetalleState.saving,
                    texto_guardar="Agregar",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="500px",
            padding=Spacing.LG,
        ),
        open=CotizadorDetalleState.mostrar_modal_item,
        on_open_change=CotizadorDetalleState.set_mostrar_modal_item,
    )


def _contenido_partida() -> rx.Component:
    """Contenido de la partida seleccionada: condicional por tipo."""
    return rx.cond(
        CotizadorDetalleState.es_tipo_productos,
        # PRODUCTOS_SERVICIOS: items table
        rx.flex(
            rx.vstack(
                _panel_acciones_partida(),
                resumen_partida_card(CotizadorDetalleState.totales_partida),
                spacing="3",
                min_width="280px",
                max_width="320px",
                flex="1 1 280px",
                width="100%",
            ),
            rx.vstack(
                _tabla_items_partida(),
                spacing="3",
                flex="1",
                min_width="0",
                overflow_x="auto",
                width="100%",
            ),
            width="100%",
            align="start",
            wrap="wrap",
            gap=Spacing.MD,
        ),
        # PERSONAL: categorías + conceptos + matriz
        rx.flex(
            rx.vstack(
                _panel_acciones_partida(),
                resumen_partida_card(CotizadorDetalleState.totales_partida),
                spacing="3",
                min_width="280px",
                max_width="320px",
                flex="1 1 280px",
                width="100%",
            ),
            rx.vstack(
                _tabla_categorias(),
                _seccion_conceptos(),
                tabla_matriz_costos(
                    CotizadorDetalleState.matriz_costos,
                    CotizadorDetalleState.columnas_matriz,
                    CotizadorDetalleState.hay_categorias,
                ),
                spacing="3",
                flex="1",
                min_width="0",
                overflow_x="auto",
                width="100%",
            ),
            width="100%",
            align="start",
            wrap="wrap",
            gap=Spacing.MD,
        ),
    )


def _panel_acciones_partida() -> rx.Component:
    """Panel con acciones de la partida seleccionada."""
    return rx.card(
        rx.vstack(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        CotizadorDetalleState.partida_titulo,
                        font_size=Typography.SIZE_BASE,
                        font_weight="600",
                        color=Colors.TEXT_PRIMARY,
                    ),
                    badge_estatus_partida(
                        CotizadorDetalleState.partida_activa.get('estatus_partida', 'PENDIENTE')
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                ),
                rx.text(
                    CotizadorDetalleState.partida_categorias_texto,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.cond(
                    CotizadorDetalleState.partida_rango_personal_texto != "",
                    rx.text(
                        CotizadorDetalleState.partida_rango_personal_texto,
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.fragment(),
                ),
                rx.text(
                    CotizadorDetalleState.partida_rango_total_texto,
                    font_size=Typography.SIZE_SM,
                    color=Colors.PRIMARY,
                    font_weight="600",
                ),
                spacing="1",
                width="100%",
                align_items="start",
            ),
            rx.divider(),
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Notas de partida",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                        font_weight="600",
                    ),
                    rx.spacer(),
                    rx.cond(
                        CotizadorDetalleState.puede_editar_info_partida,
                        _boton_cotizador(
                            "Editar",
                            "pencil-line",
                            CotizadorDetalleState.abrir_modal_editar_partida,
                            color_scheme="gray",
                            size="1",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.text(
                    CotizadorDetalleState.partida_notas_resumen,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                ),
                spacing="1",
                width="100%",
                align_items="start",
            ),
            rx.divider(),
            # Estatus
            rx.vstack(
                rx.text("Cambiar estatus:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                rx.cond(
                    CotizadorDetalleState.puede_asignar_partidas,
                    rx.select.root(
                        rx.select.trigger(
                            placeholder=CotizadorDetalleState.partida_activa.get(
                                'estatus_partida',
                                'PENDIENTE',
                            )
                        ),
                        rx.select.content(
                            rx.select.item("Aceptada", value="ACEPTADA"),
                            rx.select.item("No asignada", value="NO_ASIGNADA"),
                        ),
                        on_change=lambda v: CotizadorDetalleState.cambiar_estatus_partida_local(v),
                        size="2",
                        width="100%",
                    ),
                    rx.text(
                        "La asignación de partidas se habilita cuando la cotización está APROBADA.",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ),
                spacing="1",
                width="100%",
            ),
            # Convertir a contrato
            rx.cond(
                CotizadorDetalleState.partida_activa.get('estatus_partida') == 'ACEPTADA',
                _boton_cotizador(
                    "Convertir a Contrato",
                    "arrow-right-from-line",
                    CotizadorDetalleState.convertir_partida_a_contrato(
                        CotizadorDetalleState.partida_seleccionada_id
                    ),
                    color_scheme="green",
                    variant="solid",
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
                    "Categorías de personal",
                    font_size=Typography.SIZE_BASE,
                    font_weight="600",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.cond(
                    CotizadorDetalleState.cotizacion_es_editable,
                    _boton_cotizador(
                        "Agregar",
                        "plus",
                        CotizadorDetalleState.abrir_modal_categoria,
                        color_scheme="blue",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                width="100%",
            ),
            rx.cond(
                CotizadorDetalleState.hay_categorias,
                _table_shell(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(_header_label("Categoría")),
                                rx.table.column_header_cell(_header_label("Salario base", align="right")),
                                rx.table.column_header_cell(_header_label("Mín.", align="right")),
                                rx.table.column_header_cell(_header_label("Máx.", align="right")),
                                rx.table.column_header_cell(_header_label("Costo patronal", align="right")),
                                rx.table.column_header_cell(_header_label("P. unitario", align="right")),
                                rx.table.column_header_cell(_header_label("Acciones", align="center")),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                CotizadorDetalleState.categorias_partida,
                                _fila_categoria,
                            )
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
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
        overflow_x="auto",
    )


def _fila_categoria(cat: dict) -> rx.Component:
    """Fila de la tabla de categorías."""
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(
                    cat['categoria_nombre'],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                    font_weight="600",
                ),
                rx.text(
                    f"ID {cat['categoria_puesto_id']}",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="1",
                align_items="start",
            )
        ),
        rx.table.cell(_money_text(cat['salario_base_mensual'])),
        rx.table.cell(
            rx.text(
                cat['cantidad_minima'],
                width="100%",
                text_align="right",
                font_size=Typography.SIZE_SM,
            )
        ),
        rx.table.cell(
            rx.text(
                cat['cantidad_maxima'],
                width="100%",
                text_align="right",
                font_size=Typography.SIZE_SM,
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    cat['fue_editado_manualmente'],
                    rx.badge("Manual", color_scheme="orange", size="1"),
                    rx.fragment(),
                ),
                _money_text(
                    cat['costo_patronal_efectivo'],
                ),
                spacing="1",
                width="100%",
                justify="end",
            )
        ),
        rx.table.cell(
            _money_text(
                cat['precio_unitario_final'],
                color=Colors.PRIMARY,
                weight="700",
            )
        ),
        rx.table.cell(
            tabla_action_buttons(
                [
                    tabla_action_button(
                        icon="calculator",
                        tooltip="Recalcular costo patronal",
                        on_click=CotizadorDetalleState.recalcular_costo_patronal(cat['id']),
                        color_scheme="blue",
                    ),
                    tabla_action_button(
                        icon="pencil",
                        tooltip="Editar costo patronal",
                        on_click=CotizadorDetalleState.abrir_modal_costo_patronal(
                            cat['id'],
                            cat['costo_patronal_efectivo'].to_string(),
                        ),
                        color_scheme="orange",
                        visible=CotizadorDetalleState.cotizacion_es_editable,
                    ),
                    tabla_action_button(
                        icon="trash-2",
                        tooltip="Eliminar categoría",
                        on_click=CotizadorDetalleState.eliminar_categoria(cat['id']),
                        color_scheme="red",
                        visible=CotizadorDetalleState.cotizacion_es_editable,
                    ),
                ],
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
                    "Conceptos adicionales",
                    font_size=Typography.SIZE_BASE,
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
                    _boton_cotizador(
                        "Agregar",
                        "plus",
                        CotizadorDetalleState.abrir_modal_concepto,
                        color_scheme="blue",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                width="100%",
            ),
            rx.cond(
                CotizadorDetalleState.conceptos_partida.length() > 0,
                _table_shell(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(_header_label("Concepto")),
                                rx.table.column_header_cell(_header_label("Tipo")),
                                rx.table.column_header_cell(_header_label("Origen", align="center")),
                                rx.table.column_header_cell(_header_label("Acciones", align="center")),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                CotizadorDetalleState.conceptos_partida,
                                _fila_concepto,
                            )
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
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
        overflow_x="auto",
    )


def _fila_concepto(concepto: dict) -> rx.Component:
    """Fila de la tabla de conceptos."""
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(
                    concepto.get('nombre', ''),
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                    font_weight="600",
                ),
                rx.text(
                    concepto.get('tipo_valor', 'FIJO'),
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="1",
                align_items="start",
            )
        ),
        rx.table.cell(
            rx.vstack(
                rx.cond(
                    concepto.get('tipo_concepto') == 'PATRONAL',
                    rx.badge("Patronal", color_scheme='blue', size="1"),
                    rx.badge("Indirecto", color_scheme='gray', size="1"),
                ),
                rx.text(
                    rx.cond(
                        concepto.get('tipo_valor') == 'PORCENTAJE',
                        "Porcentaje (%)",
                        "Importe fijo",
                    ),
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="1",
                align_items="start",
            )
        ),
        rx.table.cell(
            rx.flex(
                rx.cond(
                    concepto.get('es_autogenerado', False),
                    rx.badge("Motor", color_scheme="green", variant="soft", size="1"),
                    rx.badge("Manual", color_scheme="gray", variant="soft", size="1"),
                ),
                justify="center",
            )
        ),
        rx.table.cell(
            tabla_action_buttons(
                [
                    tabla_action_button(
                        icon="trash-2",
                        tooltip="Eliminar concepto",
                        on_click=CotizadorDetalleState.eliminar_concepto(concepto.get('id', 0)),
                        color_scheme="red",
                        visible=(
                            ~(concepto.get('es_autogenerado', False) | (concepto.get('tipo_concepto') == 'PATRONAL'))
                        ) & CotizadorDetalleState.cotizacion_es_editable,
                    ),
                ],
                spacing="1",
            )
        ),
    )


def cotizador_detalle_page() -> rx.Component:
    """Página de detalle de una cotización."""
    return rx.box(
        page_layout(
            header=rx.cond(
                CotizadorDetalleState.loading_detalle,
                rx.fragment(),
                _header_detalle(),
            ),
            toolbar=rx.cond(
                CotizadorDetalleState.loading_detalle,
                rx.fragment(),
                _toolbar_estatus_cotizacion(),
            ),
            content=rx.vstack(
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
                    _tabs_partidas(),
                ),
                _modal_editar_cotizacion(),
                _modal_editar_partida(),
                _modal_agregar_categoria(),
                _modal_agregar_concepto(),
                _modal_editar_costo_patronal(),
                _modal_agregar_item(),
                spacing="4",
                width="100%",
            ),
        ),
        on_mount=CotizadorDetalleState.cargar_detalle,
        width="100%",
        min_height="100vh",
    )
