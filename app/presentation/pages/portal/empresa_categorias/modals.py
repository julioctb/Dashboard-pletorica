"""Modales del catálogo de puestos del portal."""

import reflex as rx

from app.presentation.components.ui import (
    botones_modal,
    feedback_callout,
    form_input,
    form_select,
    modal_formulario,
)
from app.presentation.theme import Colors, Spacing, Typography

from .state import EmpresaCategoriasState


def modal_categoria_catalogo() -> rx.Component:
    """Modal para crear o editar categorías del catálogo."""
    return modal_formulario(
        open=EmpresaCategoriasState.modal_categoria_abierto,
        titulo=EmpresaCategoriasState.titulo_modal_categoria,
        descripcion=EmpresaCategoriasState.descripcion_modal_categoria,
        icono="briefcase",
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
        on_guardar=EmpresaCategoriasState.guardar_categoria,
        on_cancelar=EmpresaCategoriasState.cerrar_modal_categoria,
        puede_guardar=EmpresaCategoriasState.puede_guardar_categoria,
        loading=EmpresaCategoriasState.saving,
        texto_guardar=rx.cond(
            EmpresaCategoriasState.categoria_editando,
            "Guardar categoría",
            "Crear categoría",
        ),
        color_guardar=Colors.PORTAL_ACCENT_SCHEME,
        contenido=rx.vstack(
            rx.cond(
                EmpresaCategoriasState.categoria_editando_contratos_count > 0,
                feedback_callout(
                    content=rx.text(
                        "Esta categoría está en "
                        + EmpresaCategoriasState.categoria_editando_contratos_count.to(str)
                        + " contrato(s). Los cambios de nombre se reflejan en todos.",
                        font_size=Typography.SIZE_SM,
                    ),
                    kind="warning",
                ),
                rx.fragment(),
            ),
            form_select(
                label="Tipo de servicio",
                required=True,
                placeholder="Seleccionar tipo...",
                value=EmpresaCategoriasState.form_tipo_servicio_id,
                on_change=EmpresaCategoriasState.set_form_tipo_servicio_id,
                options=EmpresaCategoriasState.tipos_servicio_select_options,
                error=EmpresaCategoriasState.error_form_tipo_servicio_id,
                label_variant="portal",
                style_variant="portal",
                disabled=EmpresaCategoriasState.categoria_editando,
            ),
            form_input(
                label="Nombre",
                required=True,
                placeholder="Ej: Jardinero C",
                value=EmpresaCategoriasState.form_nombre_categoria,
                on_change=EmpresaCategoriasState.set_form_nombre_categoria,
                error=EmpresaCategoriasState.error_form_nombre_categoria,
                label_variant="portal",
                style_variant="portal",
            ),
            rx.grid(
                form_input(
                    label="Clave",
                    placeholder="Ej: JARC",
                    value=EmpresaCategoriasState.form_clave_categoria,
                    on_change=EmpresaCategoriasState.set_form_clave_categoria,
                    error=EmpresaCategoriasState.error_form_clave_categoria,
                    hint="Se autogenera si se deja vacía",
                    label_variant="portal",
                    style_variant="portal",
                ),
                form_input(
                    label="Salario base mensual sugerido",
                    placeholder="0.00",
                    value=EmpresaCategoriasState.form_salario_base_categoria,
                    on_change=EmpresaCategoriasState.set_form_salario_base_categoria,
                    error=EmpresaCategoriasState.error_form_salario_base_categoria,
                    hint="Monto mensual default al asignar a un contrato nuevo",
                    label_variant="portal",
                    style_variant="portal",
                    input_mode="decimal",
                ),
                columns=rx.breakpoints(initial="1", sm="2"),
                spacing="3",
                width="100%",
            ),
            rx.cond(
                EmpresaCategoriasState.mostrar_warning_salario_minimo_categoria,
                feedback_callout(
                    content=rx.text(
                        EmpresaCategoriasState.mensaje_warning_salario_minimo_categoria,
                        font_size=Typography.SIZE_XS,
                    ),
                    kind="warning",
                ),
                rx.fragment(),
            ),
            rx.cond(
                EmpresaCategoriasState.categoria_editando
                & EmpresaCategoriasState.categoria_editando_puede_desactivar,
                rx.box(
                    rx.separator(margin_y=Spacing.MD),
                    rx.flex(
                        rx.box(
                            rx.text(
                                "Desactivar categoría",
                                font_size=Typography.SIZE_SM,
                                font_weight=Typography.WEIGHT_MEDIUM,
                                color=Colors.ERROR,
                            ),
                            rx.text(
                                "No estará disponible para nuevos contratos. Los existentes no se afectan.",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                        ),
                        rx.button(
                            "Desactivar",
                            on_click=EmpresaCategoriasState.desactivar_categoria_puesto,
                            color_scheme="red",
                            size="1",
                            variant="outline",
                            disabled=EmpresaCategoriasState.saving,
                        ),
                        width="100%",
                        align="center",
                        justify="between",
                        gap=Spacing.SM,
                    ),
                ),
                rx.fragment(),
            ),
            width="100%",
            spacing="4",
            align_items="stretch",
        ),
        extra_footer_left=rx.cond(
            EmpresaCategoriasState.categoria_editando
            & ~EmpresaCategoriasState.categoria_editando_puede_desactivar,
            rx.text(
                "No se puede desactivar mientras tenga plazas activas en contratos operativos.",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            rx.fragment(),
        ),
    )
