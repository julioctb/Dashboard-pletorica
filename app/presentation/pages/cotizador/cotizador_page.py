"""
Página principal del módulo Cotizador.

Lista las cotizaciones de la empresa y permite crear nuevas.
Soporta dos tipos: PRODUCTOS_SERVICIOS y PERSONAL.
Ruta: /portal/cotizador
"""
import reflex as rx

from app.presentation.theme import Colors, Spacing, Typography, Radius
from app.presentation.theme import CARD_INTERACTIVE_STYLE
from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.components.ui import form_input, form_textarea, form_row, botones_modal
from app.presentation.pages.cotizador.cotizador_state import CotizadorState
from app.presentation.pages.cotizador.cotizador_components import (
    tabla_cotizaciones,
    tipo_cotizacion_badge,
)


def _fila_categoria(cat: dict, partida_idx: rx.Var) -> rx.Component:
    """Fila de una categoría dentro de la mini-tabla de una partida."""
    return rx.table.row(
        rx.table.cell(
            rx.text(cat["nombre"], font_size=Typography.SIZE_SM),
        ),
        rx.table.cell(
            rx.text(
                rx.cond(cat["salario"] != "", "$" + cat["salario"], "-"),
                font_size=Typography.SIZE_SM,
            ),
        ),
        rx.table.cell(
            rx.text(cat["min"], font_size=Typography.SIZE_SM),
        ),
        rx.table.cell(
            rx.text(cat["max"], font_size=Typography.SIZE_SM),
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("x", size=14),
                variant="ghost",
                color_scheme="red",
                size="1",
                on_click=CotizadorState.eliminar_categoria_form(
                    partida_idx,
                    cat["cat_idx"],
                ),
            ),
        ),
    )


def _fila_agregar_categoria(partida_idx: rx.Var) -> rx.Component:
    """Formulario inline para agregar categoría a una partida."""
    return rx.cond(
        CotizadorState.partida_editando_idx == partida_idx,
        rx.vstack(
            rx.hstack(
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Categoría de puesto",
                    ),
                    rx.select.content(
                        rx.foreach(
                            CotizadorState.categorias_puesto_opciones,
                            lambda op: rx.select.item(
                                op["nombre"],
                                value=op["id"].to(str),
                            ),
                        ),
                    ),
                    value=CotizadorState.form_temp_cat_puesto_id,
                    on_change=CotizadorState.set_form_temp_cat_puesto_id,
                    size="2",
                    width="40%",
                ),
                rx.input(
                    placeholder="Salario",
                    value=CotizadorState.form_temp_cat_salario,
                    on_change=CotizadorState.set_form_temp_cat_salario,
                    size="2",
                    width="25%",
                    type="number",
                ),
                rx.input(
                    placeholder="Mín",
                    value=CotizadorState.form_temp_cat_min,
                    on_change=CotizadorState.set_form_temp_cat_min,
                    size="2",
                    width="15%",
                    type="number",
                ),
                rx.input(
                    placeholder="Máx",
                    value=CotizadorState.form_temp_cat_max,
                    on_change=CotizadorState.set_form_temp_cat_max,
                    size="2",
                    width="15%",
                    type="number",
                ),
                width="100%",
                spacing="2",
            ),
            rx.cond(
                CotizadorState.error_temp_cat_salario != "",
                rx.text(
                    CotizadorState.error_temp_cat_salario,
                    color=Colors.ERROR,
                    font_size=Typography.SIZE_XS,
                ),
            ),
            rx.hstack(
                rx.button(
                    "Agregar",
                    on_click=CotizadorState.confirmar_agregar_categoria,
                    size="1",
                    color_scheme="blue",
                    variant="soft",
                ),
                rx.button(
                    "Cancelar",
                    on_click=CotizadorState.cancelar_agregar_categoria,
                    size="1",
                    variant="ghost",
                ),
                spacing="2",
            ),
            spacing="2",
            width="100%",
            padding_top=Spacing.XS,
        ),
        # Botón para iniciar agregar
        rx.button(
            rx.icon("plus", size=14),
            "Categoría",
            on_click=CotizadorState.iniciar_agregar_categoria(partida_idx),
            size="1",
            variant="ghost",
            color_scheme="blue",
        ),
    )


def _partida_form_row(partida: dict) -> rx.Component:
    """Renderiza una partida con sus categorías inline."""
    p_idx = partida["idx"]
    categorias = partida["categorias"]

    return rx.box(
        rx.vstack(
            # Encabezado
            rx.hstack(
                rx.text(
                    "Partida ",
                    partida["num"],
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    font_size=Typography.SIZE_SM,
                ),
                rx.spacer(),
                rx.cond(
                    CotizadorState.form_partidas.length() > 1,
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        variant="ghost",
                        color_scheme="red",
                        size="1",
                        on_click=CotizadorState.eliminar_partida_form(p_idx),
                    ),
                ),
                width="100%",
                align="center",
            ),
            # Tabla de categorías
            rx.cond(
                categorias.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                "Puesto",
                                font_size=Typography.SIZE_XS,
                            ),
                            rx.table.column_header_cell(
                                "Salario",
                                font_size=Typography.SIZE_XS,
                            ),
                            rx.table.column_header_cell(
                                "Mín",
                                font_size=Typography.SIZE_XS,
                            ),
                            rx.table.column_header_cell(
                                "Máx",
                                font_size=Typography.SIZE_XS,
                            ),
                            rx.table.column_header_cell(
                                "",
                                width="40px",
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            categorias,
                            lambda cat: _fila_categoria(cat, p_idx),
                        ),
                    ),
                    size="1",
                    width="100%",
                ),
            ),
            # Fila agregar categoría
            _fila_agregar_categoria(p_idx),
            spacing="2",
            width="100%",
        ),
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        padding=Spacing.SM,
        width="100%",
    )


# =============================================================================
# WIZARD DE CREACIÓN — Indicador de pasos
# =============================================================================

def _indicador_pasos() -> rx.Component:
    """Indicador visual: 3 círculos numerados + conectores + título del paso."""

    def _circulo(numero: int) -> rx.Component:
        es_activo = CotizadorState.form_paso_actual >= numero
        return rx.center(
            rx.text(
                str(numero),
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_BOLD,
            ),
            width="32px",
            height="32px",
            border_radius="50%",
            background=rx.cond(es_activo, Colors.PRIMARY, Colors.SECONDARY_LIGHT),
            color=rx.cond(es_activo, Colors.TEXT_INVERSE, Colors.TEXT_SECONDARY),
            cursor="pointer",
            flex_shrink="0",
            _hover={"opacity": "0.8"},
            on_click=CotizadorState.set_form_paso_actual(numero),
        )

    def _conector() -> rx.Component:
        return rx.box(
            height="2px", flex="1", min_width="12px", background=Colors.BORDER,
        )

    return rx.vstack(
        rx.hstack(
            _circulo(1), _conector(),
            _circulo(2), _conector(),
            _circulo(3),
            width="100%",
            justify="center",
            align="center",
        ),
        rx.text(
            rx.match(
                CotizadorState.form_paso_actual,
                (1, "Datos generales"),
                (2, "Partidas"),
                (3, "Resumen"),
                "Datos generales",
            ),
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_PRIMARY,
            text_align="center",
            width="100%",
        ),
        spacing="3",
        width="100%",
        padding_y=Spacing.SM,
    )


# =============================================================================
# MODAL SELECTOR DE TIPO
# =============================================================================

def _modal_selector_tipo() -> rx.Component:
    """Modal para elegir tipo de cotización antes del wizard."""
    def _card_tipo(icon_name: str, titulo: str, descripcion: str, tipo: str) -> rx.Component:
        return rx.card(
            rx.vstack(
                rx.icon(icon_name, size=32, color=Colors.PRIMARY),
                rx.text(
                    titulo,
                    font_size=Typography.SIZE_LG,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    descripcion,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                    text_align="center",
                ),
                align="center",
                spacing="2",
                padding=Spacing.MD,
            ),
            cursor="pointer",
            style=CARD_INTERACTIVE_STYLE,
            on_click=CotizadorState.seleccionar_tipo_cotizacion(tipo),
            width="100%",
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nueva Cotización"),
            rx.dialog.description(
                "Selecciona el tipo de cotización que deseas crear.",
                margin_bottom="16px",
            ),
            rx.grid(
                _card_tipo(
                    "package",
                    "Productos / Servicios",
                    "Cotiza bienes y servicios generales con tabla de conceptos",
                    "PRODUCTOS_SERVICIOS",
                ),
                _card_tipo(
                    "users",
                    "Personal",
                    "Cotiza personal con cálculo patronal por perfil",
                    "PERSONAL",
                ),
                columns="2",
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    size="2",
                    on_click=CotizadorState.cerrar_selector_tipo,
                ),
                spacing="2",
                width="100%",
                padding_top=Spacing.SM,
            ),
            max_width="550px",
        ),
        open=CotizadorState.mostrar_selector_tipo,
        on_open_change=rx.noop,
    )


# =============================================================================
# WIZARD DE CREACIÓN — Contenido de cada paso
# =============================================================================

def _paso_datos_generales() -> rx.Component:
    """Paso 1: Destinatario, notas (sin fechas de período)."""
    return rx.vstack(
        form_row(
            form_input(
                label="Nombre del destinatario",
                placeholder="Ej: Dr. Juan Pérez",
                value=CotizadorState.form_destinatario_nombre,
                on_change=CotizadorState.set_form_destinatario_nombre,
            ),
            form_input(
                label="Cargo del destinatario",
                placeholder="Ej: Director de Planeación",
                value=CotizadorState.form_destinatario_cargo,
                on_change=CotizadorState.set_form_destinatario_cargo,
            ),
        ),
        form_textarea(
            label="Notas de la cotización",
            placeholder="Detalles comerciales, condiciones o alcance del servicio...",
            value=CotizadorState.form_notas,
            on_change=CotizadorState.set_form_notas,
            min_height="80px",
        ),
        rx.hstack(
            rx.checkbox(
                "Incluir desglose de conceptos en PDF",
                checked=CotizadorState.form_mostrar_desglose,
                on_change=CotizadorState.set_form_mostrar_desglose,
                size="2",
            ),
            padding_top=Spacing.XS,
        ),
        spacing="3",
        width="100%",
    )


def _item_fila(item: dict, partida_idx: rx.Var) -> rx.Component:
    """Fila de un item dentro de una partida (PRODUCTOS_SERVICIOS)."""
    return rx.table.row(
        rx.table.cell(
            rx.text(
                item["numero"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.input(
                value=item["cantidad"],
                on_change=lambda v: CotizadorState.actualizar_item_campo(
                    partida_idx, item["idx"], "cantidad", v
                ),
                type="number",
                size="2",
                width="80px",
                min="1",
            ),
        ),
        rx.table.cell(
            rx.input(
                value=item["descripcion"],
                on_change=lambda v: CotizadorState.actualizar_item_campo(
                    partida_idx, item["idx"], "descripcion", v
                ),
                placeholder="Descripción del concepto...",
                size="2",
                width="100%",
            ),
        ),
        rx.table.cell(
            rx.input(
                value=item["precio_unitario"],
                on_change=lambda v: CotizadorState.actualizar_item_campo(
                    partida_idx, item["idx"], "precio_unitario", v
                ),
                type="number",
                size="2",
                width="110px",
                step="0.01",
                min="0",
            ),
        ),
        rx.table.cell(
            rx.text(
                "$",
                item["importe"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                white_space="nowrap",
            ),
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("x", size=14),
                variant="ghost",
                color_scheme="red",
                size="1",
                on_click=CotizadorState.eliminar_item_partida(
                    partida_idx, item["idx"],
                ),
            ),
        ),
    )


def _partida_items_form(partida: dict) -> rx.Component:
    """Partida con tabla de items para PRODUCTOS_SERVICIOS."""
    p_idx = partida["idx"]
    items = partida["items"]

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    "Partida ", partida["num"],
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    font_size=Typography.SIZE_SM,
                ),
                rx.spacer(),
                rx.cond(
                    CotizadorState.form_partidas.length() > 1,
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        variant="ghost",
                        color_scheme="red",
                        size="1",
                        on_click=CotizadorState.eliminar_partida_form(p_idx),
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                items.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("#", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("Cantidad", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("Concepto", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("Unitario", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("Importe", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("", width="40px"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            items,
                            lambda item: _item_fila(item, p_idx),
                        ),
                    ),
                    size="1",
                    width="100%",
                ),
            ),
            rx.button(
                rx.icon("plus", size=14),
                "Agregar concepto",
                on_click=CotizadorState.agregar_item_partida(p_idx),
                size="1",
                variant="ghost",
                color_scheme="blue",
            ),
            spacing="2",
            width="100%",
        ),
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        padding=Spacing.SM,
        width="100%",
    )


def _paso_partidas() -> rx.Component:
    """Paso 2: Partidas con categorías o items según tipo."""
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Partidas",
                font_weight=Typography.WEIGHT_SEMIBOLD,
                font_size=Typography.SIZE_BASE,
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Agregar partida",
                on_click=CotizadorState.agregar_partida_form,
                size="1",
                variant="ghost",
                color_scheme="blue",
            ),
            width="100%",
            align="center",
        ),
        rx.vstack(
            rx.cond(
                CotizadorState.es_tipo_personal,
                rx.foreach(
                    CotizadorState.form_partidas,
                    _partida_form_row,
                ),
                rx.foreach(
                    CotizadorState.form_partidas,
                    _partida_items_form,
                ),
            ),
            spacing="3",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def _item_global_fila(item: dict) -> rx.Component:
    """Fila de un item global en paso 3."""
    return rx.table.row(
        rx.table.cell(
            rx.text(item["numero"], font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
        ),
        rx.table.cell(
            rx.input(
                value=item["cantidad"],
                on_change=lambda v: CotizadorState.actualizar_item_global_campo(
                    item["idx"], "cantidad", v
                ),
                type="number",
                size="2",
                width="80px",
                min="1",
            ),
        ),
        rx.table.cell(
            rx.input(
                value=item["descripcion"],
                on_change=lambda v: CotizadorState.actualizar_item_global_campo(
                    item["idx"], "descripcion", v
                ),
                placeholder="Concepto global...",
                size="2",
                width="100%",
            ),
        ),
        rx.table.cell(
            rx.input(
                value=item["precio_unitario"],
                on_change=lambda v: CotizadorState.actualizar_item_global_campo(
                    item["idx"], "precio_unitario", v
                ),
                type="number",
                size="2",
                width="110px",
                step="0.01",
            ),
        ),
        rx.table.cell(
            rx.text("$", item["importe"], font_size=Typography.SIZE_SM, font_weight=Typography.WEIGHT_SEMIBOLD),
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("x", size=14),
                variant="ghost",
                color_scheme="red",
                size="1",
                on_click=CotizadorState.eliminar_item_global(item["idx"]),
            ),
        ),
    )


def _paso_resumen() -> rx.Component:
    """Paso 3: Resumen con IVA interactivo, meses (personal), conceptos globales."""

    def _card_resumen(titulo: str, *children) -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.text(
                    titulo,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                *children,
                spacing="1",
                width="100%",
            ),
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            padding=Spacing.SM,
            width="100%",
        )

    return rx.vstack(
        # Destinatario
        rx.cond(
            (CotizadorState.form_destinatario_nombre != "")
            | (CotizadorState.form_destinatario_cargo != ""),
            _card_resumen(
                "Destinatario",
                rx.cond(
                    CotizadorState.form_destinatario_nombre != "",
                    rx.text(
                        CotizadorState.form_destinatario_nombre,
                        font_size=Typography.SIZE_SM,
                    ),
                ),
                rx.cond(
                    CotizadorState.form_destinatario_cargo != "",
                    rx.text(
                        CotizadorState.form_destinatario_cargo,
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ),
            ),
        ),
        # Partidas resumen
        _card_resumen(
            "Partidas",
            rx.text(
                CotizadorState.form_partidas.length().to(str),
                " partida(s) configuradas",
                font_size=Typography.SIZE_SM,
            ),
            rx.foreach(
                CotizadorState.form_partidas,
                lambda p: rx.text(
                    "Partida ", p["num"], ": ",
                    rx.cond(
                        CotizadorState.es_tipo_personal,
                        p["categorias"].length().to(str) + " categoría(s)",
                        p["items"].length().to(str) + " concepto(s)",
                    ),
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
            ),
        ),
        # Cantidad de meses (solo PERSONAL)
        rx.cond(
            CotizadorState.es_tipo_personal,
            _card_resumen(
                "Cantidad de meses",
                rx.hstack(
                    rx.input(
                        value=CotizadorState.form_cantidad_meses,
                        on_change=CotizadorState.set_form_cantidad_meses,
                        type="number",
                        min="1",
                        size="2",
                        width="100px",
                    ),
                    rx.text("meses", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    CotizadorState.error_cantidad_meses != "",
                    rx.text(
                        CotizadorState.error_cantidad_meses,
                        color=Colors.ERROR,
                        font_size=Typography.SIZE_XS,
                    ),
                ),
            ),
        ),
        # Conceptos globales
        _card_resumen(
            "Conceptos globales (aplican a toda la cotización)",
            rx.cond(
                CotizadorState.form_items_globales.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("#", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("Cantidad", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("Concepto", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("Unitario", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("Importe", font_size=Typography.SIZE_XS),
                            rx.table.column_header_cell("", width="40px"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            CotizadorState.form_items_globales,
                            _item_global_fila,
                        ),
                    ),
                    size="1",
                    width="100%",
                ),
            ),
            rx.button(
                rx.icon("plus", size=14),
                "Agregar concepto global",
                on_click=CotizadorState.agregar_item_global,
                size="1",
                variant="ghost",
                color_scheme="blue",
            ),
        ),
        # Notas
        rx.cond(
            CotizadorState.form_notas != "",
            _card_resumen(
                "Notas",
                rx.text(CotizadorState.form_notas, font_size=Typography.SIZE_SM),
            ),
        ),
        # IVA y totales
        rx.separator(),
        rx.hstack(
            rx.checkbox(
                "Aplicar IVA 16%",
                checked=CotizadorState.form_aplicar_iva,
                on_change=CotizadorState.set_form_aplicar_iva,
                size="2",
            ),
            width="100%",
        ),
        # Totales footer (solo visible para PRODUCTOS_SERVICIOS en wizard)
        rx.cond(
            CotizadorState.es_tipo_productos,
            rx.vstack(
                rx.hstack(
                    rx.text("Subtotal:", font_size=Typography.SIZE_BASE, font_weight=Typography.WEIGHT_SEMIBOLD),
                    rx.spacer(),
                    rx.text(CotizadorState.resumen_subtotal, font_size=Typography.SIZE_BASE, font_weight=Typography.WEIGHT_SEMIBOLD),
                    width="100%",
                ),
                rx.cond(
                    CotizadorState.form_aplicar_iva,
                    rx.hstack(
                        rx.text("IVA 16%:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                        rx.spacer(),
                        rx.text(CotizadorState.resumen_iva, font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                        width="100%",
                    ),
                ),
                rx.hstack(
                    rx.text("Total:", font_size=Typography.SIZE_LG, font_weight=Typography.WEIGHT_BOLD),
                    rx.spacer(),
                    rx.text(CotizadorState.resumen_total, font_size=Typography.SIZE_LG, font_weight=Typography.WEIGHT_BOLD, color=Colors.PRIMARY),
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        # Callout informativo
        rx.callout(
            "Después de crear la cotización podrás editar conceptos y valores en el detalle.",
            icon="info",
            color_scheme="blue",
            size="2",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


# =============================================================================
# MODAL WIZARD
# =============================================================================

def _modal_crear_cotizacion() -> rx.Component:
    """Modal wizard de 3 pasos para crear una nueva cotización."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    "Nueva Cotización",
                    rx.cond(
                        CotizadorState.es_tipo_personal,
                        rx.badge("Personal", color_scheme="blue", variant="soft", size="1"),
                        rx.badge("Productos/Servicios", color_scheme="green", variant="soft", size="1"),
                    ),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.dialog.description(
                rx.cond(
                    CotizadorState.es_tipo_personal,
                    "Define destinatario, partidas con perfiles de personal y configura conceptos.",
                    "Define destinatario, partidas y sus conceptos con cantidades y precios.",
                ),
                margin_bottom="16px",
            ),
            # Indicador de pasos
            _indicador_pasos(),
            # Contenido del paso actual
            rx.box(
                rx.match(
                    CotizadorState.form_paso_actual,
                    (1, _paso_datos_generales()),
                    (2, _paso_partidas()),
                    (3, _paso_resumen()),
                    _paso_datos_generales(),
                ),
                min_height="300px",
                padding_top=Spacing.BASE,
            ),
            rx.box(height="20px"),
            # Footer
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    size="2",
                    on_click=CotizadorState.cerrar_modal_crear,
                ),
                rx.spacer(),
                rx.cond(
                    CotizadorState.form_paso_actual > 1,
                    rx.button(
                        rx.icon("chevron-left", size=14),
                        "Anterior",
                        variant="outline",
                        size="2",
                        on_click=CotizadorState.ir_paso_anterior,
                    ),
                ),
                rx.cond(
                    CotizadorState.form_paso_actual < 3,
                    rx.button(
                        "Siguiente",
                        rx.icon("chevron-right", size=14),
                        variant="outline",
                        size="2",
                        color_scheme="blue",
                        on_click=CotizadorState.ir_paso_siguiente,
                    ),
                ),
                rx.button(
                    rx.cond(
                        CotizadorState.saving_cotizacion,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Creando..."),
                            spacing="2",
                        ),
                        "Crear Cotización",
                    ),
                    on_click=CotizadorState.crear_cotizacion,
                    disabled=CotizadorState.saving_cotizacion,
                    color_scheme="blue",
                    size="2",
                ),
                spacing="2",
                width="100%",
                align="center",
            ),
            max_width="850px",
            spacing="4",
        ),
        open=CotizadorState.mostrar_modal_crear,
        on_open_change=rx.noop,
    )


def _filtros() -> rx.Component:
    """Barra de filtros para el listado."""
    opciones_estatus = [
        {"value": "__todos__", "label": "Todos los estatus"},
        {"value": "BORRADOR", "label": "Borrador"},
        {"value": "PREPARADA", "label": "Preparada"},
        {"value": "ENVIADA", "label": "Enviada"},
        {"value": "APROBADA", "label": "Aprobada"},
        {"value": "RECHAZADA", "label": "Rechazada"},
    ]
    return rx.flex(
        rx.hstack(
            rx.icon("list-filter", size=16, color=Colors.TEXT_SECONDARY),
            rx.text(
                CotizadorState.total_cotizaciones,
                " cotizaciones",
                color=Colors.TEXT_SECONDARY,
                font_size=Typography.SIZE_SM,
            ),
            spacing="2",
            align="center",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Filtrar por estatus"),
            rx.select.content(
                rx.foreach(
                    opciones_estatus,
                    lambda op: rx.select.item(
                        op["label"],
                        value=op["value"],
                    ),
                )
            ),
            value=CotizadorState.filtro_estatus,
            on_change=CotizadorState.set_filtro_estatus,
            size="2",
        ),
        wrap="wrap",
        align="center",
        gap=Spacing.MD,
        width="100%",
    )


def cotizador_page() -> rx.Component:
    """Página principal del listado de cotizaciones."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Cotizador",
                subtitulo="Gestiona cotizaciones de servicios para presentar a clientes",
                icono="file-text",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nueva Cotización",
                    on_click=CotizadorState.abrir_modal_crear,
                    color_scheme="blue",
                    size="2",
                ),
            ),
            toolbar=page_toolbar(
                show_search=False,
                show_view_toggle=False,
                filters=_filtros(),
            ),
            content=rx.vstack(
                rx.cond(
                    CotizadorState.loading_cotizaciones,
                    rx.center(rx.spinner(size="3"), padding=Spacing.XL),
                    tabla_cotizaciones(
                        CotizadorState.cotizaciones_filtradas,
                        CotizadorState.loading_cotizaciones,
                    ),
                ),
                _modal_selector_tipo(),
                _modal_crear_cotizacion(),
                spacing="4",
                width="100%",
            ),
        ),
        on_mount=CotizadorState.on_mount_cotizador,
        width="100%",
        min_height="100vh",
    )
