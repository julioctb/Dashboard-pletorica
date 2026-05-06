"""
Componentes de modal para Instituciones.
"""

import reflex as rx

from app.presentation.components.ui.form_input import form_input, form_select
from app.presentation.components.ui.modals import (modal_confirmar_accion,
                                                   modal_detalle,
                                                   modal_formulario)
from app.presentation.pages.backoffice.instituciones.state import \
    InstitucionesState
from app.presentation.theme import Colors, Spacing, Typography


def modal_institucion() -> rx.Component:
    """Modal para crear o editar institucion"""
    return modal_formulario(
        open=InstitucionesState.mostrar_modal_institucion,
        titulo=rx.cond(
            InstitucionesState.es_edicion,
            "Editar Institucion",
            "Nueva Institucion",
        ),
        icono="building-2",
        on_guardar=InstitucionesState.guardar_institucion,
        on_cancelar=InstitucionesState.cerrar_modal_institucion,
        puede_guardar=InstitucionesState.puede_guardar,
        loading=InstitucionesState.saving,
        max_width="450px",
        contenido=rx.vstack(
            form_input(
                label="Nombre",
                required=True,
                placeholder="Ej: Benemerita Universidad Autonoma de Puebla",
                value=InstitucionesState.form_nombre,
                on_change=InstitucionesState.set_form_nombre,
                on_blur=InstitucionesState.validar_nombre_campo,
                error=InstitucionesState.error_nombre,
                max_length=200,
                uppercase=True,
            ),
            form_input(
                label="Codigo",
                required=True,
                placeholder="Ej: BUAP, GOB-PUE",
                hint="Identificador unico corto",
                value=InstitucionesState.form_codigo,
                on_change=InstitucionesState.set_form_codigo,
                on_blur=InstitucionesState.validar_codigo_campo,
                error=InstitucionesState.error_codigo,
                max_length=20,
                uppercase=True,
            ),
            spacing="4",
            width="100%",
            padding_y="4",
        ),
    )


def _fila_empresa_asignada(asignacion: dict) -> rx.Component:
    """Fila de empresa asignada en el modal de gestion."""
    return rx.hstack(
        rx.vstack(
            rx.text(
                asignacion["empresa_nombre"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.text(
                asignacion["empresa_rfc"],
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            spacing="0",
            flex="1",
        ),
        rx.icon_button(
            rx.icon("x", size=14),
            variant="ghost",
            color_scheme="red",
            size="1",
            on_click=lambda: InstitucionesState.quitar_empresa(asignacion),
        ),
        width="100%",
        align="center",
        padding_y=Spacing.XS,
    )


def modal_gestionar_empresas() -> rx.Component:
    """Modal para asignar/quitar empresas de una institucion."""
    return modal_detalle(
        open=InstitucionesState.mostrar_modal_empresas,
        titulo="Gestionar Empresas",
        on_cerrar=InstitucionesState.cerrar_modal_empresas,
        max_width="500px",
        contenido=rx.vstack(
            # Selector para agregar empresa
            rx.hstack(
                rx.box(
                    form_select(
                        label="Agregar empresa",
                        placeholder="Seleccione empresa...",
                        options=InstitucionesState.opciones_empresas,
                        value=InstitucionesState.form_empresa_id,
                        on_change=InstitucionesState.set_form_empresa_id,
                    ),
                    flex="1",
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    "Asignar",
                    on_click=InstitucionesState.asignar_empresa,
                    disabled=InstitucionesState.form_empresa_id == "",
                    color_scheme="blue",
                    size="2",
                ),
                width="100%",
                align="end",
                gap=Spacing.SM,
            ),
            rx.divider(),
            # Lista de empresas asignadas
            rx.text(
                "Empresas asignadas",
                font_weight=Typography.WEIGHT_BOLD,
                font_size=Typography.SIZE_SM,
            ),
            rx.cond(
                InstitucionesState.empresas_asignadas.length() > 0,
                rx.vstack(
                    rx.foreach(
                        InstitucionesState.empresas_asignadas,
                        _fila_empresa_asignada,
                    ),
                    spacing="1",
                    width="100%",
                    max_height="250px",
                    overflow_y="auto",
                ),
                rx.center(
                    rx.text(
                        "Sin empresas asignadas",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_MUTED,
                    ),
                    padding="4",
                ),
            ),
            spacing="4",
            width="100%",
            padding_y="4",
        ),
    )


def modal_confirmar_desactivar() -> rx.Component:
    """Modal de confirmacion para desactivar institucion."""
    return modal_confirmar_accion(
        open=InstitucionesState.mostrar_modal_confirmar_desactivar,
        titulo="Desactivar Institucion",
        mensaje="Esta seguro de que desea desactivar esta institucion?",
        detalle_contenido=rx.cond(
            InstitucionesState.institucion_seleccionada,
            rx.text(
                rx.text(
                    InstitucionesState.institucion_seleccionada["codigo"], weight="bold"
                ),
                " - ",
                InstitucionesState.institucion_seleccionada["nombre"],
            ),
            rx.text(""),
        ),
        nota_adicional="Esta accion desactivara la institucion. Podra reactivarla despues.",
        on_confirmar=InstitucionesState.desactivar_institucion,
        on_cancelar=InstitucionesState.cerrar_confirmar_desactivar,
        loading=InstitucionesState.saving,
        texto_confirmar="Desactivar",
        color_confirmar="red",
        icono_detalle="info",
        color_detalle="blue",
    )
