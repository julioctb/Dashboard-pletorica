"""Wrappers de modales de plazas para la pagina por contrato."""

import reflex as rx

from app.presentation.components.ui import (
    feedback_callout,
    form_input,
    form_select,
)
from app.presentation.pages.portal.plaza_shared_modals import (
    modal_asignacion_plaza as shared_modal_asignacion_plaza,
    modal_asignacion_sede_plaza as shared_modal_asignacion_sede_plaza,
    modal_categoria_plaza as shared_modal_categoria_plaza,
    modal_reasignacion_plaza as shared_modal_reasignacion_plaza,
    modal_salario_plaza as shared_modal_salario_plaza,
)
from app.presentation.components.ui.modals import modal_formulario
from app.presentation.theme import Colors, Radius, Shadows, Spacing, Typography

from .state import ContratoPlazasState


def _combobox_nombre_categoria() -> rx.Component:
    """Combobox con autocompletado de nombres de categoria previos de la empresa."""
    return rx.box(
        rx.text(
            "Nombre",
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_SECONDARY,
            margin_bottom=Spacing.XS,
        ),
        rx.box(
            rx.input(
                placeholder="Ej: Jardinero A",
                value=ContratoPlazasState.form_nombre_categoria,
                on_change=ContratoPlazasState.set_form_nombre_categoria,
                on_focus=ContratoPlazasState.abrir_combobox_nombre_categoria,
                on_blur=ContratoPlazasState.cerrar_combobox_nombre_categoria,
                width="100%",
            ),
            rx.cond(
                ContratoPlazasState.mostrar_sugerencias_nombre_categoria,
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            ContratoPlazasState.nombres_categoria_sugerencias_filtradas,
                            lambda sugerencia: rx.box(
                                rx.text(
                                    sugerencia,
                                    font_size=Typography.SIZE_SM,
                                    color=Colors.TEXT_PRIMARY,
                                ),
                                on_mouse_down=ContratoPlazasState.seleccionar_sugerencia_nombre_categoria(
                                    sugerencia,
                                ),
                                padding=f"{Spacing.XS} {Spacing.SM}",
                                cursor="pointer",
                                width="100%",
                                _hover={"background": Colors.PORTAL_PRIMARY_LIGHT},
                            ),
                        ),
                        spacing="0",
                        width="100%",
                        align_items="stretch",
                    ),
                    position="absolute",
                    top="100%",
                    left="0",
                    right="0",
                    margin_top=Spacing.XS,
                    background=Colors.SURFACE,
                    border=f"1px solid {Colors.BORDER}",
                    border_radius=Radius.MD,
                    box_shadow=Shadows.MD,
                    max_height="220px",
                    overflow_y="auto",
                    z_index="10",
                ),
                rx.fragment(),
            ),
            position="relative",
            width="100%",
        ),
        rx.cond(
            ContratoPlazasState.error_form_nombre_categoria != "",
            rx.text(
                ContratoPlazasState.error_form_nombre_categoria,
                font_size=Typography.SIZE_XS,
                color=Colors.ERROR,
                margin_top=Spacing.XS,
            ),
            rx.fragment(),
        ),
        width="100%",
    )


def modal_asignacion_plaza():
    return shared_modal_asignacion_plaza(ContratoPlazasState)


def modal_categoria_plaza():
    return shared_modal_categoria_plaza(ContratoPlazasState)


def modal_salario_plaza():
    return shared_modal_salario_plaza(ContratoPlazasState)


def modal_asignacion_sede_plaza():
    return shared_modal_asignacion_sede_plaza(ContratoPlazasState)


def modal_reasignacion_plaza():
    return shared_modal_reasignacion_plaza(ContratoPlazasState)


def modal_categoria_contrato():
    return modal_formulario(
        open=ContratoPlazasState.modal_categoria_abierto,
        titulo=ContratoPlazasState.titulo_modal_categoria,
        descripcion=ContratoPlazasState.descripcion_modal_categoria,
        icono="tags",
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
        on_guardar=ContratoPlazasState.guardar_categoria,
        on_cancelar=ContratoPlazasState.cerrar_modal_categoria,
        puede_guardar=ContratoPlazasState.puede_guardar_categoria,
        loading=ContratoPlazasState.saving,
        texto_guardar=rx.cond(
            ContratoPlazasState.categoria_editando,
            "Guardar categoría",
            "Agregar categoría",
        ),
        color_guardar=Colors.PORTAL_ACCENT_SCHEME,
        max_width="520px",
        contenido=rx.vstack(
            _combobox_nombre_categoria(),
            form_select(
                label="Tipo de sueldo",
                required=True,
                placeholder="Seleccionar...",
                value=ContratoPlazasState.form_tipo_sueldo,
                on_change=ContratoPlazasState.set_form_tipo_sueldo,
                options=[
                    {"label": "Sueldo bruto", "value": "BRUTO"},
                    {"label": "Sueldo neto", "value": "NETO"},
                ],
                label_variant="portal",
                style_variant="portal",
            ),
            rx.box(
                rx.text(
                    rx.cond(
                        ContratoPlazasState.form_tipo_sueldo == "BRUTO",
                        "Sueldo bruto mensual",
                        "Sueldo neto mensual",
                    ),
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_SECONDARY,
                    margin_bottom=Spacing.XS,
                ),
                form_input(
                    label="",
                    required=True,
                    type="number",
                    step="0.01",
                    min="0",
                    placeholder="0.00",
                    value=ContratoPlazasState.form_sueldo_base,
                    on_change=ContratoPlazasState.set_form_sueldo_base,
                    error=ContratoPlazasState.error_form_sueldo_base,
                    hint=ContratoPlazasState.form_preview_sueldo_hint,
                    label_variant="portal",
                    style_variant="portal",
                ),
                width="100%",
            ),
            rx.cond(
                ContratoPlazasState.form_es_menor_salario_minimo,
                feedback_callout(
                    content=rx.text(
                        "Este sueldo es menor al salario mínimo para jornada completa. "
                        "Solo es válido para jornada parcial o por horas.",
                        font_size=Typography.SIZE_XS,
                    ),
                    kind="warning",
                ),
                rx.fragment(),
            ),
            form_input(
                label="Costo contractual mensual",
                type="number",
                step="0.01",
                min="0",
                placeholder="0.00",
                value=ContratoPlazasState.form_costo_contractual,
                on_change=ContratoPlazasState.set_form_costo_contractual,
                error=ContratoPlazasState.error_form_costo_contractual,
                hint="Lo que la empresa cobra al cliente por persona/mes. Se usa para calcular el margen.",
                label_variant="portal",
                style_variant="portal",
            ),
            rx.flex(
                form_input(
                    label="Plazas mínimas",
                    required=True,
                    type="number",
                    min="0",
                    placeholder="0",
                    value=ContratoPlazasState.form_min_plazas,
                    on_change=ContratoPlazasState.set_form_min_plazas,
                    error=ContratoPlazasState.error_form_min_plazas,
                    label_variant="portal",
                    style_variant="portal",
                ),
                form_input(
                    label="Plazas máximas",
                    type="number",
                    min="0",
                    placeholder="Dejar vacío si es contrato abierto",
                    value=ContratoPlazasState.form_max_plazas,
                    on_change=ContratoPlazasState.set_form_max_plazas,
                    error=ContratoPlazasState.error_form_max_plazas,
                    hint="Opcional. Vacío = sin tope (contrato abierto).",
                    label_variant="portal",
                    style_variant="portal",
                ),
                gap=Spacing.MD,
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
    )
