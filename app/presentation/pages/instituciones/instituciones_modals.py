"""
Componentes de modal para Instituciones.
"""
import reflex as rx
from app.presentation.pages.instituciones.instituciones_state import InstitucionesState
from app.presentation.components.ui.form_input import (
    form_input,
    form_select,
    form_row,
)
from app.presentation.components.ui.modals import modal_confirmar_accion
from app.presentation.components.ui.buttons import boton_guardar, boton_cancelar
from app.presentation.theme import Colors, Spacing, Typography


def modal_institucion() -> rx.Component:
    """Modal para crear o editar institucion"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    InstitucionesState.es_edicion,
                    "Editar Institucion",
                    "Nueva Institucion",
                )
            ),
            rx.dialog.description(
                rx.vstack(
                    form_input(
                        label="Nombre",
                        required=True,
                        placeholder="Ej: Benemerita Universidad Autonoma de Puebla",
                        value=InstitucionesState.form_nombre,
                        on_change=InstitucionesState.set_form_nombre,
                        on_blur=InstitucionesState.validar_nombre_campo,
                        error=InstitucionesState.error_nombre,
                        max_length=200,
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
                    ),
                    spacing="4",
                    width="100%",
                    padding_y="4",
                ),
            ),
            # Botones
            rx.hstack(
                boton_cancelar(
                    on_click=InstitucionesState.cerrar_modal_institucion,
                ),
                boton_guardar(
                    texto="Guardar",
                    texto_guardando="Guardando...",
                    on_click=InstitucionesState.guardar_institucion,
                    saving=InstitucionesState.saving,
                    disabled=~InstitucionesState.puede_guardar,
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),
            max_width="450px",
        ),
        open=InstitucionesState.mostrar_modal_institucion,
        on_open_change=rx.noop,
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
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Gestionar Empresas"),
            rx.dialog.description(
                rx.vstack(
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
            ),
            # Boton cerrar
            rx.hstack(
                boton_cancelar(
                    on_click=InstitucionesState.cerrar_modal_empresas,
                    texto="Cerrar",
                ),
                justify="end",
                width="100%",
                padding_top="4",
            ),
            max_width="500px",
        ),
        open=InstitucionesState.mostrar_modal_empresas,
        on_open_change=rx.noop,
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
                rx.text(InstitucionesState.institucion_seleccionada["codigo"], weight="bold"),
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
