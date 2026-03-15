"""
Modales para el módulo de Contratos.
"""
import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_select, form_textarea, form_date
from app.presentation.components.ui import (
    status_badge_reactive,
    boton_guardar,
    boton_cancelar,
    boton_eliminar,
    empty_state_card,
    feedback_callout,
    metric_card,
    table_shell,
)
from app.presentation.pages.contratos.contratos_state import ContratosState
from app.presentation.pages.contratos.contrato_detail_sections import contrato_detail_info_sections
from app.presentation.theme import Colors, Radius, Spacing, Typography


def _tarjeta_paso(
    titulo: str,
    descripcion: str,
    contenido: rx.Component,
) -> rx.Component:
    """Contenedor visual consistente para cada paso del wizard."""
    return rx.card(
        rx.vstack(
            rx.vstack(
                rx.text(titulo, size="4", weight="bold", color=Colors.TEXT_PRIMARY),
                rx.text(descripcion, size="2", color=Colors.TEXT_SECONDARY),
                spacing="1",
                width="100%",
                align="start",
            ),
            contenido,
            spacing="4",
            width="100%",
            align="stretch",
        ),
        width="100%",
        variant="surface",
    )


def _indicador_pasos() -> rx.Component:
    """Indicador compacto del wizard de contratos."""

    def _paso(numero: int) -> rx.Component:
        es_actual = ContratosState.form_paso_actual == numero
        es_completado = ContratosState.form_paso_actual > numero
        es_navegable = rx.match(
            numero,
            (1, True),
            (2, ContratosState.puede_navegar_a_paso_2_wizard),
            (3, ContratosState.puede_navegar_a_paso_3_wizard),
            False,
        )
        on_click_paso = ContratosState.set_form_paso_actual(numero)

        return rx.center(
            rx.text(
                str(numero),
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_SEMIBOLD,
            ),
            width="28px",
            height="28px",
            border_radius="999px",
            background=rx.cond(
                es_actual,
                Colors.PRIMARY,
                rx.cond(es_completado, Colors.PRIMARY_LIGHTER, Colors.SURFACE),
            ),
            color=rx.cond(
                es_actual,
                Colors.TEXT_INVERSE,
                rx.cond(es_completado, Colors.PRIMARY, Colors.TEXT_SECONDARY),
            ),
            border=rx.cond(
                es_actual,
                f"1px solid {Colors.PRIMARY}",
                rx.cond(
                    es_completado,
                    f"1px solid {Colors.PRIMARY_LIGHT}",
                    f"1px solid {Colors.BORDER}",
                ),
            ),
            cursor=rx.cond(es_navegable, "pointer", "not-allowed"),
            flex_shrink="0",
            opacity=rx.cond(es_navegable, "1", "0.55"),
            pointer_events=rx.cond(es_navegable, "auto", "none"),
            transition="all 180ms ease",
            on_click=on_click_paso,
        )

    def _conector(activo: rx.Var | bool = False) -> rx.Component:
        return rx.box(
            width="32px",
            height="1px",
            background=rx.cond(activo, Colors.PRIMARY_LIGHT, Colors.BORDER),
            flex_shrink="0",
        )

    pasos_uno = rx.hstack(_paso(1), spacing="0", align="center")

    pasos_dos = rx.hstack(
        _paso(1),
        _conector(ContratosState.form_paso_actual >= 2),
        _paso(2),
        align="center",
        spacing="2",
    )

    pasos_dos_sin_plazas = rx.hstack(
        _paso(1),
        _conector(ContratosState.form_paso_actual >= 2),
        _paso(2),
        align="center",
        spacing="2",
    )

    pasos_tres = rx.hstack(
        _paso(1),
        _conector(ContratosState.form_paso_actual >= 2),
        _paso(2),
        _conector(ContratosState.form_paso_actual >= 3),
        _paso(3),
        align="center",
        spacing="2",
    )

    return rx.box(
        rx.cond(
            ContratosState.mostrar_paso_plazas,
            rx.cond(ContratosState.mostrar_paso_entregables, pasos_tres, pasos_dos),
            rx.cond(ContratosState.mostrar_paso_entregables, pasos_dos_sin_plazas, pasos_uno),
        ),
        width="auto",
        flex_shrink="0",
    )


def _paso_contrato() -> rx.Component:
    """Paso 1: datos principales del contrato."""
    empresa_field = rx.cond(
        ContratosState.empresa_fijada_en_contexto,
        form_input(
            label="Empresa",
            required=True,
            label_variant="wizard",
            value=ContratosState.nombre_empresa_formulario,
            error=ContratosState.error_empresa_id,
            hint="Se usa la empresa precargada para este contrato.",
            disabled=True,
        ),
        form_select(
            label="Empresa",
            required=True,
            label_variant="wizard",
            placeholder="Seleccione empresa",
            value=ContratosState.form_empresa_id,
            on_change=ContratosState.set_form_empresa_id,
            options=ContratosState.opciones_empresa,
            error=ContratosState.error_empresa_id,
            hint="Se precarga desde el contexto activo cuando está disponible.",
        ),
    )
    def _campo_folio() -> rx.Component:
        return form_input(
            label="Folio institución",
            label_variant="wizard",
            placeholder="Ej: INST-2026-001",
            value=ContratosState.form_folio_buap,
            on_change=ContratosState.set_form_folio_buap,
            on_blur=ContratosState.validar_folio_buap_campo,
            error=ContratosState.error_folio_buap,
        )

    def _bloque_incluye_personal() -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.checkbox(
                        "Incluye personal",
                        checked=ContratosState.form_tiene_personal,
                        on_change=ContratosState.set_form_tiene_personal,
                        disabled=ContratosState.es_adquisicion,
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.text(
                    "Active esta opción si el contrato debe materializar plazas.",
                    size="1",
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            padding=Spacing.SM,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.MD,
            background=Colors.SECONDARY_LIGHT,
            width="100%",
            flex="1",
            min_width="280px",
        )

    return _tarjeta_paso(
        "Datos del contrato",
        "Capture la información base y la vigencia del contrato.",
        rx.vstack(
            rx.hstack(
                empresa_field,
                form_select(
                    label="Tipo de contrato",
                    required=True,
                    label_variant="wizard",
                    placeholder="Seleccione tipo",
                    value=ContratosState.form_tipo_contrato,
                    on_change=ContratosState.set_form_tipo_contrato,
                    options=ContratosState.opciones_tipo_contrato,
                    error=ContratosState.error_tipo_contrato,
                ),
                spacing="3",
                width="100%",
                align="start",
            ),
            rx.cond(
                ContratosState.es_edicion,
                _campo_folio(),
                rx.fragment(),
            ),
            rx.cond(
                ContratosState.es_servicios,
                rx.hstack(
                    rx.box(
                        form_select(
                            label="Tipo de servicio",
                            required=True,
                            label_variant="wizard",
                            placeholder="Seleccione tipo de servicio",
                            value=ContratosState.form_tipo_servicio_id,
                            on_change=ContratosState.set_form_tipo_servicio_id,
                            options=ContratosState.opciones_tipo_servicio,
                            error=ContratosState.error_tipo_servicio_id,
                        ),
                        width="100%",
                        flex="1",
                        min_width="280px",
                    ),
                    _bloque_incluye_personal(),
                    spacing="3",
                    width="100%",
                    align="start",
                    wrap="wrap",
                ),
                rx.fragment(),
            ),
            form_textarea(
                label="Objeto del contrato",
                label_variant="wizard",
                placeholder="Ej: Servicio integral de limpieza en instalaciones administrativas.",
                value=ContratosState.form_descripcion_objeto,
                on_change=ContratosState.set_form_descripcion_objeto,
                on_blur=ContratosState.sync_form_descripcion_objeto_blur,
                error=ContratosState.error_descripcion_objeto,
                hint=rx.cond(
                    ContratosState.es_edicion,
                    "Opcional. Capture o actualice este dato cuando la institución asigne el folio.",
                    "Opcional. Puede completarlo después, cuando la institución genere el folio.",
                ),
                rows="4",
            ),
            rx.hstack(
                form_date(
                    label="Fecha de inicio",
                    required=True,
                    label_variant="wizard",
                    value=ContratosState.form_fecha_inicio,
                    on_change=ContratosState.set_form_fecha_inicio,
                    on_blur=ContratosState.validar_fecha_inicio_campo,
                    error=ContratosState.error_fecha_inicio,
                ),
                form_date(
                    label="Fecha fin",
                    label_variant="wizard",
                    value=ContratosState.form_fecha_fin,
                    on_change=ContratosState.set_form_fecha_fin,
                    on_blur=ContratosState.validar_fecha_fin_campo,
                    error=ContratosState.error_fecha_fin,
                    hint="Si la deja vacía, el contrato se tomará como indefinido.",
                ),
                spacing="3",
                width="100%",
                align="start",
            ),
            spacing="4",
            width="100%",
        ),
    )


def _paso_plazas() -> rx.Component:
    """Paso 2: configuración de plazas."""
    plazas_habilitadas = ContratosState.es_servicios & ContratosState.form_tiene_personal
    totales_bloqueados = ContratosState.usa_desglose_categorias_plazas
    puede_configurar_desglose = plazas_habilitadas & (ContratosState.form_tipo_servicio_id != "")

    def _label_campo(texto: str, *, required: bool = False) -> rx.Component:
        return rx.hstack(
            rx.text(
                texto,
                font_size="11px",
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_SECONDARY,
                text_transform="uppercase",
                letter_spacing="0.04em",
            ),
            rx.cond(
                required,
                rx.text("*", font_size="11px", color="var(--red-9)", weight="medium"),
                rx.fragment(),
            ),
            spacing="1",
            align="center",
            width="100%",
        )

    def _campo_shell(
        titulo: str,
        control: rx.Component,
        *,
        required: bool = False,
        width: str = "100%",
    ) -> rx.Component:
        return rx.vstack(
            _label_campo(titulo, required=required),
            control,
            spacing="1",
            align="stretch",
            width=width,
        )

    def _seccion_shell(
        titulo: str,
        descripcion: str,
        contenido: rx.Component,
        *,
        action: rx.Component | None = None,
    ) -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            titulo,
                            size="3",
                            weight="medium",
                            color=Colors.TEXT_PRIMARY,
                            letter_spacing=Typography.LETTER_SPACING_TIGHT,
                        ),
                        rx.text(
                            descripcion,
                            font_size=Typography.SIZE_XS,
                            color=Colors.TEXT_MUTED,
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.spacer(),
                    action if action is not None else rx.fragment(),
                    width="100%",
                    align="center",
                ),
                contenido,
                spacing="3",
                width="100%",
                align="stretch",
            ),
            width="100%",
            padding=Spacing.BASE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
        )

    def _dato_resumen(titulo: str, valor: rx.Var | str) -> rx.Component:
        return rx.vstack(
            rx.text(
                titulo,
                font_size="10px",
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing="0.04em",
            ),
            rx.text(
                valor,
                font_size=Typography.SIZE_XL,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                color=Colors.TEXT_PRIMARY,
                letter_spacing=Typography.LETTER_SPACING_TIGHT,
                style={"fontVariantNumeric": "tabular-nums"},
            ),
            spacing="0",
            align="start",
            width="100%",
            min_width="0",
        )

    resumen_compacto = rx.box(
        rx.vstack(
            rx.text(
                "Resumen",
                size="2",
                weight="medium",
                color=Colors.TEXT_PRIMARY,
                letter_spacing=Typography.LETTER_SPACING_TIGHT,
            ),
            rx.hstack(
                rx.box(
                    _dato_resumen(
                        "Plazas mínimas",
                        rx.cond(
                            ContratosState.form_cantidad_plazas_minima != "",
                            ContratosState.form_cantidad_plazas_minima,
                            "0",
                        ),
                    ),
                    flex="1",
                    min_width="0",
                ),
                rx.box(width="1px", height="32px", background=Colors.BORDER, flex_shrink="0"),
                rx.box(
                    _dato_resumen(
                        "Plazas máximas",
                        rx.cond(
                            ContratosState.form_cantidad_plazas_maxima != "",
                            ContratosState.form_cantidad_plazas_maxima,
                            "0",
                        ),
                    ),
                    flex="1",
                    min_width="0",
                ),
                rx.box(width="1px", height="32px", background=Colors.BORDER, flex_shrink="0"),
                rx.box(
                    _dato_resumen(
                        "Monto mínimo",
                        rx.cond(
                            ContratosState.form_monto_minimo != "",
                            ContratosState.form_monto_minimo,
                            "$ 0",
                        ),
                    ),
                    flex="1",
                    min_width="0",
                ),
                rx.box(width="1px", height="32px", background=Colors.BORDER, flex_shrink="0"),
                rx.box(
                    _dato_resumen(
                        "Monto máximo",
                        rx.cond(
                            ContratosState.form_monto_maximo != "",
                            ContratosState.form_monto_maximo,
                            "$ 0",
                        ),
                    ),
                    flex="1",
                    min_width="0",
                ),
                spacing="3",
                width="100%",
                align="start",
                wrap="nowrap",
            ),
            rx.text(
                rx.cond(
                    totales_bloqueados,
                    "Calculado a partir del desglose por categorías",
                    "Basado en el rango global capturado",
                ),
                font_size="11px",
                color=Colors.TEXT_MUTED,
                text_align="center",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        width="100%",
        padding=Spacing.BASE,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.LG,
    )

    def _fila_categoria_configurada(item: dict) -> rx.Component:
        return rx.box(
            rx.hstack(
                rx.box(
                    rx.vstack(
                        rx.text(
                            item["categoria_nombre"],
                            size="2",
                            weight="medium",
                            color=Colors.TEXT_PRIMARY,
                        ),
                        rx.cond(
                            item["categoria_clave"] != "",
                            rx.text(
                                item["categoria_clave"],
                                font_size="11px",
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.fragment(),
                        ),
                        spacing="0",
                        align="start",
                        width="100%",
                    ),
                    flex="2",
                    min_width="0",
                ),
                rx.box(
                    rx.text(
                        rx.cond(item["costo_unitario"], item["costo_unitario"], "-"),
                        size="2",
                        color=Colors.TEXT_PRIMARY,
                        style={"fontVariantNumeric": "tabular-nums"},
                    ),
                    flex="1",
                    text_align="right",
                ),
                rx.box(
                    rx.text(
                        item["cantidad_minima"],
                        size="2",
                        color=Colors.TEXT_PRIMARY,
                        style={"fontVariantNumeric": "tabular-nums"},
                    ),
                    flex="1",
                    text_align="right",
                ),
                rx.box(
                    rx.text(
                        item["cantidad_maxima"],
                        size="2",
                        color=Colors.TEXT_PRIMARY,
                        style={"fontVariantNumeric": "tabular-nums"},
                    ),
                    flex="1",
                    text_align="right",
                ),
                rx.box(
                    rx.icon_button(
                        rx.icon("x", size=14),
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=lambda: ContratosState.quitar_categoria_contrato(item["uid"]),
                        opacity="0.72",
                    ),
                    width="28px",
                    flex_shrink="0",
                    display="flex",
                    justify_content="flex-end",
                ),
                spacing="3",
                width="100%",
                align="center",
            ),
            width="100%",
            padding_y=Spacing.MD,
            border_top=f"1px solid {Colors.BORDER}",
        )

    lista_categorias = rx.cond(
        ContratosState.tiene_categorias_contrato_configuradas,
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.text(
                        "Categoría",
                        font_size="11px",
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing="0.04em",
                    ),
                    flex="2",
                    min_width="0",
                ),
                rx.box(
                    rx.text(
                        "Costo",
                        font_size="11px",
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing="0.04em",
                        text_align="right",
                    ),
                    flex="1",
                ),
                rx.box(
                    rx.text(
                        "Mín.",
                        font_size="11px",
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing="0.04em",
                        text_align="right",
                    ),
                    flex="1",
                ),
                rx.box(
                    rx.text(
                        "Máx.",
                        font_size="11px",
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing="0.04em",
                        text_align="right",
                    ),
                    flex="1",
                ),
                rx.box(width="28px", flex_shrink="0"),
                spacing="3",
                width="100%",
            ),
            rx.foreach(ContratosState.form_categorias_contrato, _fila_categoria_configurada),
            spacing="0",
            width="100%",
        ),
        rx.box(
            rx.vstack(
                rx.icon("layout-grid", size=36, color=Colors.TEXT_MUTED),
                rx.text(
                    "Sin categorías configuradas",
                    size="2",
                    weight="medium",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    "Se usará el rango global de abajo",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    text_align="center",
                ),
                spacing="2",
                width="100%",
                align="center",
                justify="center",
            ),
            width="100%",
            min_height="140px",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )

    formulario_catalogo = rx.box(
        rx.vstack(
            rx.grid(
                _campo_shell(
                    "Categoría",
                    form_select(
                        label="",
                        placeholder="Seleccione categoría",
                        value=ContratosState.form_categoria_puesto_id,
                        on_change=ContratosState.set_form_categoria_puesto_id,
                        options=ContratosState.opciones_categoria_puesto_para_contrato,
                        error=ContratosState.error_categoria_contrato_id,
                    ),
                    required=True,
                ),
                _campo_shell(
                    "Costo",
                    form_input(
                        label="",
                        placeholder="0.00",
                        value=ContratosState.form_categoria_contrato_costo,
                        on_change=ContratosState.set_form_categoria_contrato_costo,
                        error=ContratosState.error_categoria_contrato_costo,
                    ),
                    required=True,
                ),
                grid_template_columns="minmax(0, 1.8fr) minmax(180px, 1fr)",
                column_gap=Spacing.MD,
                row_gap=Spacing.MD,
                width="100%",
                align_items="start",
            ),
            rx.grid(
                _campo_shell(
                    "Plazas mínimas",
                    form_input(
                        label="",
                        placeholder="0",
                        value=ContratosState.form_categoria_contrato_minima,
                        on_change=ContratosState.set_form_categoria_contrato_minima,
                        error=ContratosState.error_categoria_contrato_minima,
                        type="number",
                        min="0",
                    ),
                    required=True,
                ),
                _campo_shell(
                    "Plazas máximas",
                    form_input(
                        label="",
                        placeholder="0",
                        value=ContratosState.form_categoria_contrato_maxima,
                        on_change=ContratosState.set_form_categoria_contrato_maxima,
                        error=ContratosState.error_categoria_contrato_maxima,
                        type="number",
                        min="0",
                    ),
                    required=True,
                ),
                rx.box(
                    rx.button(
                        "Agregar",
                        on_click=ContratosState.agregar_categoria_contrato,
                        disabled=~ContratosState.puede_agregar_categoria_contrato,
                        color_scheme="blue",
                        size="2",
                        width="100%",
                    ),
                    width="100%",
                    padding_top="19px",
                ),
                grid_template_columns="minmax(0, 1fr) minmax(0, 1fr) 160px",
                column_gap=Spacing.MD,
                row_gap=Spacing.MD,
                width="100%",
                align_items="start",
            ),
            rx.text(
                "Costo contractual por persona/mes. No se copia al salario de la plaza.",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        width="100%",
        padding=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.MD,
    )

    formulario_nueva_categoria = rx.box(
        rx.vstack(
            rx.text(
                "La nueva categoría quedará disponible en el catálogo del tipo de servicio seleccionado.",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            rx.grid(
                _campo_shell(
                    "Nombre de categoría",
                    form_input(
                        label="",
                        placeholder="Nombre de categoría",
                        value=ContratosState.form_nueva_categoria_nombre,
                        on_change=ContratosState.set_form_nueva_categoria_nombre,
                        error=ContratosState.error_nueva_categoria_nombre,
                    ),
                    required=True,
                ),
                _campo_shell(
                    "Clave",
                    form_input(
                        label="",
                        placeholder="Clave",
                        value=ContratosState.form_nueva_categoria_clave,
                        on_change=ContratosState.set_form_nueva_categoria_clave,
                        error=ContratosState.error_nueva_categoria_clave,
                        max_length=5,
                    ),
                    required=True,
                ),
                grid_template_columns="minmax(0, 2fr) minmax(140px, 1fr)",
                column_gap=Spacing.MD,
                row_gap=Spacing.MD,
                width="100%",
                align_items="start",
            ),
            rx.grid(
                _campo_shell(
                    "Costo",
                    form_input(
                        label="",
                        placeholder="0.00",
                        value=ContratosState.form_categoria_contrato_costo,
                        on_change=ContratosState.set_form_categoria_contrato_costo,
                        error=ContratosState.error_categoria_contrato_costo,
                    ),
                    required=True,
                ),
                _campo_shell(
                    "Plazas mínimas",
                    form_input(
                        label="",
                        placeholder="0",
                        value=ContratosState.form_categoria_contrato_minima,
                        on_change=ContratosState.set_form_categoria_contrato_minima,
                        error=ContratosState.error_categoria_contrato_minima,
                        type="number",
                        min="0",
                    ),
                    required=True,
                ),
                _campo_shell(
                    "Plazas máximas",
                    form_input(
                        label="",
                        placeholder="0",
                        value=ContratosState.form_categoria_contrato_maxima,
                        on_change=ContratosState.set_form_categoria_contrato_maxima,
                        error=ContratosState.error_categoria_contrato_maxima,
                        type="number",
                        min="0",
                    ),
                    required=True,
                ),
                grid_template_columns="repeat(3, minmax(0, 1fr))",
                column_gap=Spacing.MD,
                row_gap=Spacing.MD,
                width="100%",
                align_items="start",
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    "Cancelar",
                    variant="ghost",
                    color_scheme="gray",
                    size="2",
                    on_click=ContratosState.ocultar_form_crear_categoria_contrato,
                    color=Colors.TEXT_SECONDARY,
                ),
                boton_guardar(
                    texto="Agregar categoría",
                    texto_guardando="Agregando...",
                    on_click=ContratosState.agregar_categoria_contrato,
                    saving=ContratosState.guardando_categoria_contrato,
                    disabled=~ContratosState.puede_agregar_categoria_contrato,
                    size="2",
                ),
                spacing="2",
                width="100%",
                align="center",
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        width="100%",
        padding=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.MD,
    )

    bloque_categorias = _seccion_shell(
        "Categorías",
        "Desglose las plazas por categoría o use el rango global.",
        rx.vstack(
            rx.cond(
                plazas_habilitadas,
                rx.cond(
                    puede_configurar_desglose,
                    rx.vstack(
                        rx.cond(
                            ContratosState.mostrar_form_nueva_categoria,
                            formulario_nueva_categoria,
                            formulario_catalogo,
                        ),
                        lista_categorias,
                        spacing="3",
                        width="100%",
                    ),
                    rx.box(
                        rx.text(
                            "Seleccione el tipo de servicio en el paso Datos para habilitar el catálogo de categorías.",
                            font_size=Typography.SIZE_XS,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        width="100%",
                        padding=Spacing.MD,
                        background=Colors.SECONDARY_LIGHT,
                        border_radius=Radius.MD,
                    ),
                ),
                rx.box(
                    rx.text(
                        "El desglose por categoría solo aplica cuando el contrato de servicios incluye personal.",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    width="100%",
                    padding=Spacing.MD,
                    background=Colors.SECONDARY_LIGHT,
                    border_radius=Radius.MD,
                ),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        action=rx.cond(
            puede_configurar_desglose,
            rx.cond(
                ContratosState.mostrar_form_nueva_categoria,
                rx.button(
                    "Usar catálogo",
                    variant="ghost",
                    size="1",
                    color_scheme="gray",
                    on_click=ContratosState.ocultar_form_crear_categoria_contrato,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.button(
                    rx.icon("plus", size=13),
                    "Agregar",
                    variant="outline",
                    size="1",
                    color_scheme="gray",
                    on_click=ContratosState.mostrar_form_crear_categoria_contrato,
                ),
            ),
            rx.fragment(),
        ),
    )

    bloque_rango_global = _seccion_shell(
        "Rango global",
        "Capture el total de plazas si no necesita desglosarlas por categoría.",
        rx.cond(
            totales_bloqueados,
            rx.box(
                rx.text(
                    "Este rango se calcula automáticamente a partir de las categorías capturadas.",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                width="100%",
                padding=Spacing.MD,
                background=Colors.SECONDARY_LIGHT,
                border_radius=Radius.MD,
                opacity="0.88",
            ),
            rx.grid(
                _campo_shell(
                    "Plazas mínimas",
                    form_input(
                        label="",
                        required=plazas_habilitadas,
                        placeholder="0",
                        value=ContratosState.form_cantidad_plazas_minima,
                        on_change=ContratosState.set_form_cantidad_plazas_minima,
                        on_blur=ContratosState.validar_cantidad_plazas_minima_campo,
                        error=ContratosState.error_cantidad_plazas_minima,
                        type="number",
                        min="0",
                        disabled=~plazas_habilitadas,
                    ),
                    required=True,
                ),
                _campo_shell(
                    "Plazas máximas",
                    form_input(
                        label="",
                        required=plazas_habilitadas,
                        placeholder="0",
                        value=ContratosState.form_cantidad_plazas_maxima,
                        on_change=ContratosState.set_form_cantidad_plazas_maxima,
                        on_blur=ContratosState.validar_cantidad_plazas_maxima_campo,
                        error=ContratosState.error_cantidad_plazas_maxima,
                        type="number",
                        min="0",
                        disabled=~plazas_habilitadas,
                    ),
                    required=True,
                ),
                grid_template_columns="repeat(2, minmax(0, 1fr))",
                column_gap=Spacing.MD,
                row_gap=Spacing.MD,
                width="100%",
                align_items="start",
            ),
        ),
    )

    return _tarjeta_paso(
        "Plazas",
        "Configure el rango global o desglose las plazas por categoría cuando necesite mayor detalle.",
        rx.vstack(
            bloque_categorias,
            bloque_rango_global,
            resumen_compacto,
            spacing="4",
            width="100%",
        ),
    )


def _fila_config_entregable(config: dict) -> rx.Component:
    """Fila de tipo de entregable configurado"""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        config["tipo_label"],
                        font_size="13px",
                        weight="medium",
                        color=Colors.TEXT_PRIMARY,
                    ),
                    rx.badge(
                        config["periodicidad_label"],
                        color_scheme="gray",
                        variant="soft",
                        size="1",
                    ),
                    rx.cond(
                        config["requerido"],
                        rx.badge("Requerido", color_scheme="amber", variant="soft", size="1"),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.cond(
                    config["descripcion"],
                    rx.text(
                        config["descripcion"],
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.spacer(),
            rx.icon_button(
                rx.icon("x", size=14),
                size="1",
                variant="ghost",
                color_scheme="gray",
                opacity="0.72",
                on_click=lambda: ContratosState.eliminar_tipo_entregable(config["tipo_entregable"]),
            ),
            spacing="3",
            width="100%",
            align="center",
        ),
        width="100%",
        padding_y=Spacing.MD,
        border_bottom=f"1px solid {Colors.BORDER}",
    )


def _paso_entregables() -> rx.Component:
    """Paso 3: configuración inicial de entregables."""
    def _label_campo(texto: str, *, required: bool = False) -> rx.Component:
        return rx.hstack(
            rx.text(
                texto,
                font_size="11px",
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_SECONDARY,
                text_transform="uppercase",
                letter_spacing="0.04em",
            ),
            rx.cond(
                required,
                rx.text("*", font_size="11px", color="var(--red-9)", weight="medium"),
                rx.fragment(),
            ),
            spacing="1",
            align="center",
            width="100%",
        )

    def _campo_shell(
        titulo: str,
        control: rx.Component,
        *,
        required: bool = False,
    ) -> rx.Component:
        return rx.vstack(
            _label_campo(titulo, required=required),
            control,
            spacing="1",
            width="100%",
            align="stretch",
        )

    def _seccion_shell(
        titulo: str,
        descripcion: str,
        contenido: rx.Component,
        *,
        action: rx.Component | None = None,
    ) -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            titulo,
                            size="3",
                            weight="medium",
                            color=Colors.TEXT_PRIMARY,
                            letter_spacing=Typography.LETTER_SPACING_TIGHT,
                        ),
                        rx.text(
                            descripcion,
                            font_size=Typography.SIZE_XS,
                            color=Colors.TEXT_MUTED,
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.spacer(),
                    action if action is not None else rx.fragment(),
                    width="100%",
                    align="center",
                ),
                contenido,
                spacing="3",
                width="100%",
                align="stretch",
            ),
            width="100%",
            padding=Spacing.BASE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
        )

    formulario_entregable = rx.box(
        rx.vstack(
            rx.grid(
                _campo_shell(
                    "Tipo",
                    form_select(
                        label="",
                        required=True,
                        placeholder="Seleccione tipo",
                        value=ContratosState.form_tipo_entregable,
                        on_change=ContratosState.set_form_tipo_entregable,
                        options=ContratosState.opciones_tipo_entregable,
                    ),
                    required=True,
                ),
                _campo_shell(
                    "Periodicidad",
                    form_select(
                        label="",
                        required=True,
                        placeholder="Seleccione periodicidad",
                        value=ContratosState.form_periodicidad_entregable,
                        on_change=ContratosState.set_form_periodicidad_entregable,
                        options=ContratosState.opciones_periodicidad_entregable,
                    ),
                    required=True,
                ),
                grid_template_columns="repeat(2, minmax(0, 1fr))",
                column_gap=Spacing.MD,
                row_gap=Spacing.MD,
                width="100%",
                align_items="start",
            ),
            _campo_shell(
                "Descripción personalizada",
                form_input(
                    label="",
                    placeholder="Ej: Fotografías mensuales del servicio",
                    value=ContratosState.form_entregable_descripcion,
                    on_change=ContratosState.set_form_entregable_descripcion,
                ),
            ),
            _campo_shell(
                "Instrucciones para el proveedor",
                form_textarea(
                    label="",
                    placeholder="Ej: Subir evidencia fechada y con nombre del área atendida.",
                    value=ContratosState.form_entregable_instrucciones,
                    on_change=ContratosState.set_form_entregable_instrucciones,
                    rows="3",
                    style={"resize": "vertical"},
                ),
            ),
            rx.hstack(
                rx.checkbox(
                    "Requerido para aprobar el periodo",
                    checked=ContratosState.form_entregable_requerido,
                    on_change=ContratosState.set_form_entregable_requerido,
                ),
                rx.spacer(),
                rx.button(
                    "Cancelar",
                    variant="ghost",
                    color_scheme="gray",
                    size="2",
                    on_click=ContratosState.ocultar_form_entregable,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.button(
                    "Agregar",
                    color_scheme="blue",
                    size="2",
                    on_click=ContratosState.agregar_tipo_entregable,
                    disabled=~ContratosState.puede_agregar_entregable,
                ),
                spacing="2",
                width="100%",
                align="center",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        width="100%",
        padding=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.MD,
    )

    lista_entregables = rx.cond(
        ContratosState.tiene_config_entregables,
        rx.vstack(
            rx.foreach(
                ContratosState.config_entregables,
                _fila_config_entregable,
            ),
            spacing="0",
            width="100%",
        ),
        rx.box(
            rx.vstack(
                rx.icon("file-text", size=36, color=Colors.TEXT_MUTED),
                rx.text(
                    "Sin entregables configurados",
                    size="2",
                    weight="medium",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    "Este paso es opcional; puede configurarlos después.",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    text_align="center",
                ),
                spacing="2",
                width="100%",
                align="center",
            ),
            width="100%",
            min_height="140px",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )

    return _tarjeta_paso(
        "Entregables",
        "Configure los tipos de entregable que el proveedor deberá presentar.",
        rx.vstack(
            _seccion_shell(
                "Entregables",
                "Tipos de entregable que el proveedor deberá presentar.",
                rx.vstack(
                    rx.cond(
                        ContratosState.mostrar_form_agregar_entregable,
                        formulario_entregable,
                        rx.fragment(),
                    ),
                    lista_entregables,
                    spacing="3",
                    width="100%",
                    align="stretch",
                ),
                action=rx.cond(
                    ContratosState.mostrar_form_agregar_entregable,
                    rx.fragment(),
                    rx.button(
                        rx.icon("plus", size=13),
                        "Agregar tipo",
                        variant="outline",
                        size="1",
                        color_scheme="gray",
                        on_click=ContratosState.mostrar_form_entregable,
                    ),
                ),
            ),
            rx.box(
                rx.hstack(
                    rx.icon("info", size=16, color=Colors.INFO),
                    rx.text(
                        "Puede dejar este paso vacío si el contrato no requiere entregables configurables desde el alta.",
                        font_size="12.5px",
                        color=Colors.INFO,
                    ),
                    spacing="2",
                    width="100%",
                    align="center",
                ),
                width="100%",
                padding=Spacing.MD,
                background=Colors.INFO_LIGHT,
                border_radius=Radius.MD,
            ),
            spacing="4",
            width="100%",
        ),
    )


def modal_contrato() -> rx.Component:
    """Modal wizard para crear o editar contratos."""
    contenido_paso = rx.match(
        ContratosState.paso_actual_wizard,
        ("datos", _paso_contrato()),
        ("plazas", _paso_plazas()),
        ("entregables", _paso_entregables()),
        _paso_contrato(),
    )

    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.dialog.title(
                                rx.cond(
                                    ContratosState.es_edicion,
                                    "Editar Contrato",
                                    "Nuevo Contrato",
                                )
                            ),
                            rx.text(
                                rx.match(
                                    ContratosState.paso_actual_wizard,
                                    ("datos", "Información base del contrato"),
                                    ("plazas", "Configuración de plazas"),
                                    ("entregables", "Configuración de entregables"),
                                    "Configuración del contrato",
                                ),
                                font_size=Typography.SIZE_SM,
                                color=Colors.TEXT_MUTED,
                            ),
                            spacing="1",
                            width="100%",
                            align="start",
                        ),
                        rx.spacer(),
                        _indicador_pasos(),
                        width="100%",
                        align="center",
                    ),
                    rx.box(width="100%", height="1px", background=Colors.BORDER),
                    rx.cond(
                        ContratosState.mensaje_info != "",
                        feedback_callout(
                            ContratosState.mensaje_info,
                            ContratosState.tipo_mensaje,
                        ),
                        rx.fragment(),
                    ),
                    spacing="3",
                    width="100%",
                    align="start",
                ),
                rx.box(
                    contenido_paso,
                    width="100%",
                    max_height="60vh",
                    overflow_y="auto",
                    padding_right=Spacing.XS,
                ),
                rx.box(width="100%", height="1px", background=Colors.BORDER),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=ContratosState.cerrar_modal_contrato,
                        variant="ghost",
                        color_scheme="gray",
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.spacer(),
                    rx.cond(
                        ~ContratosState.es_primer_paso_wizard,
                        rx.button(
                            "Anterior",
                            on_click=ContratosState.ir_paso_anterior,
                            variant="outline",
                            color_scheme="gray",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        ~ContratosState.es_edicion,
                        rx.cond(
                            ContratosState.paso_actual_wizard == "entregables",
                            boton_guardar(
                                texto="Guardar borrador",
                                texto_guardando="Guardando...",
                                on_click=ContratosState.guardar_borrador_contrato,
                                saving=ContratosState.saving,
                                disabled=~ContratosState.puede_guardar_borrador_contrato,
                                color_scheme="gray",
                                variant="outline",
                            ),
                            boton_guardar(
                                texto="Guardar borrador",
                                texto_guardando="Guardando...",
                                on_click=ContratosState.guardar_borrador_contrato,
                                saving=ContratosState.saving,
                                disabled=~ContratosState.puede_guardar_borrador_contrato,
                                color_scheme="gray",
                                variant="soft",
                            ),
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        ContratosState.es_ultimo_paso_wizard,
                        boton_guardar(
                            texto=rx.cond(
                                ContratosState.es_edicion,
                                "Guardar cambios",
                                "Crear Contrato",
                            ),
                            texto_guardando="Guardando...",
                            on_click=ContratosState.guardar_contrato,
                            saving=ContratosState.saving,
                            disabled=~ContratosState.puede_guardar,
                        ),
                        boton_guardar(
                            texto="Siguiente",
                            texto_guardando="Siguiente",
                            on_click=ContratosState.ir_paso_siguiente,
                            saving=False,
                            disabled=~ContratosState.puede_avanzar_paso_actual_wizard,
                        ),
                    ),
                    spacing="2",
                    width="100%",
                    align="center",
                ),
                spacing="4",
                width="100%",
                align="stretch",
            ),
            max_width="820px",
            width="95vw",
            padding=Spacing.LG,
        ),
        open=ContratosState.mostrar_modal_contrato,
        on_open_change=rx.noop,
    )
def _tab_informacion_contrato() -> rx.Component:
    """Pestaña de información del contrato."""
    return contrato_detail_info_sections(
        ContratosState.contrato_seleccionado,
        ContratosState.categorias_detalle_contrato,
        total_categorias=ContratosState.total_categorias_detalle_contrato,
        tiene_categorias=ContratosState.tiene_categorias_detalle_contrato,
    )


def _fila_entregable(entregable: dict) -> rx.Component:
    """Fila de entregable en la tabla"""
    return rx.table.row(
        rx.table.cell(rx.text(f"Período {entregable['numero_periodo']}", weight="medium")),
        rx.table.cell(rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY)),
        rx.table.cell(status_badge_reactive(entregable["estatus"])),
        rx.table.cell(
            rx.cond(
                entregable["monto_aprobado"],
                rx.text(entregable["monto_aprobado_fmt"], size="2", weight="medium"),
                rx.text("-", size="2", color=Colors.TEXT_MUTED),
            ),
        ),
        rx.table.cell(
            rx.button(
                rx.icon("eye", size=14),
                size="1",
                variant="ghost",
                on_click=rx.redirect(f"/entregables/{entregable['id']}"),
            ),
        ),
    )


def _tab_entregables_contrato() -> rx.Component:
    """Pestaña de entregables del contrato"""
    return rx.vstack(
        rx.cond(
            ContratosState.cargando_entregables,
            rx.center(rx.spinner(size="3"), padding="8"),
            rx.cond(
                ContratosState.tiene_entregables_contrato,
                rx.box(
                    table_shell(
                        loading=False,
                        has_rows=True,
                        empty_component=rx.fragment(),
                        header_cells=[
                            rx.table.column_header_cell("Período"),
                            rx.table.column_header_cell("Fechas"),
                            rx.table.column_header_cell("Estado"),
                            rx.table.column_header_cell("Monto"),
                            rx.table.column_header_cell(""),
                        ],
                        body_component=rx.foreach(ContratosState.entregables_contrato, _fila_entregable),
                    ),
                    overflow_x="auto",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("package", size=40, color=Colors.TEXT_MUTED),
                        rx.text("No hay entregables para este contrato", color=Colors.TEXT_MUTED),
                        rx.text("Los entregables se generan automáticamente según la configuración", size="1", color=Colors.TEXT_MUTED),
                        spacing="2",
                        align="center",
                    ),
                    padding="8",
                ),
            ),
        ),
        spacing="4",
        width="100%",
        min_height="200px",
    )


def modal_detalle_contrato() -> rx.Component:
    """Modal para mostrar detalles del contrato con pestañas"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                ContratosState.contrato_seleccionado,
                rx.vstack(
                    rx.dialog.title("Detalle del Contrato"),

                    # Tabs de contenido
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Información", value="info"),
                            rx.tabs.trigger(
                                rx.hstack(
                                    rx.text("Entregables"),
                                    rx.cond(
                                        ContratosState.tiene_entregables_contrato,
                                        rx.badge(
                                            ContratosState.entregables_contrato.length(),
                                            color_scheme="blue",
                                            size="1",
                                        ),
                                        rx.fragment(),
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                value="entregables",
                            ),
                        ),
                        rx.tabs.content(
                            _tab_informacion_contrato(),
                            value="info",
                            padding_top="16px",
                        ),
                        rx.tabs.content(
                            _tab_entregables_contrato(),
                            value="entregables",
                            padding_top="16px",
                        ),
                        default_value="info",
                        width="100%",
                    ),

                    # Botones
                    rx.hstack(
                        rx.button(
                            "Cerrar",
                            variant="soft",
                            size="2",
                            on_click=ContratosState.cerrar_modal_detalle,
                        ),
                        # Editar solo si está en BORRADOR o SUSPENDIDO
                        rx.cond(
                            (ContratosState.contrato_seleccionado["estatus"] == "BORRADOR") |
                            (ContratosState.contrato_seleccionado["estatus"] == "SUSPENDIDO"),
                            rx.button(
                                "Editar",
                                on_click=lambda: ContratosState.abrir_modal_editar(
                                    ContratosState.contrato_seleccionado
                                ),
                                size="2"
                            ),
                        ),
                        spacing="2",
                        justify="end",
                        margin_top="16px",
                    ),

                    spacing="4",
                    width="100%"
                ),
            ),
            max_width="700px"
        ),
        open=ContratosState.mostrar_modal_detalle,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_confirmar_cancelar() -> rx.Component:
    """Modal de confirmación para cancelar contrato"""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Cancelar Contrato"),
            rx.alert_dialog.description(
                rx.cond(
                    ContratosState.contrato_seleccionado,
                    rx.text(
                        "¿Está seguro que desea cancelar el contrato ",
                        rx.text(
                            ContratosState.contrato_seleccionado["codigo"],
                            weight="bold"
                        ),
                        "? Esta acción no se puede deshacer."
                    ),
                    "¿Está seguro que desea cancelar este contrato?"
                )
            ),
            rx.hstack(
                boton_cancelar(
                    texto="No, mantener",
                    on_click=ContratosState.cerrar_confirmar_cancelar,
                ),
                boton_eliminar(
                    texto="Sí, cancelar",
                    texto_eliminando="Cancelando...",
                    on_click=ContratosState.cancelar_contrato,
                    saving=ContratosState.saving,
                ),
                spacing="3",
                justify="end",
            ),
        ),
        open=ContratosState.mostrar_modal_confirmar_cancelar,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )
