"""
Componentes de modal para Tipos de Servicio.
"""
import reflex as rx
from app.presentation.pages.tipo_servicio.tipo_servicio_state import TipoServicioState
from app.presentation.components.ui.form_input import form_input, form_textarea


def modal_tipo_servicio() -> rx.Component:
    """Modal para crear o editar tipo de servicio"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    TipoServicioState.es_edicion,
                    "Editar Tipo de Servicio",
                    "Nuevo Tipo de Servicio"
                )
            ),
            rx.dialog.description(
                rx.vstack(
                    # Campo: Nombre (primero para auto-generar clave)
                    rx.vstack(
                        rx.text("Nombre *", size="2", weight="medium"),
                        form_input(
                            placeholder="Ej: JARDINERÍA",
                            value=TipoServicioState.form_nombre,
                            on_change=TipoServicioState.set_form_nombre,
                            on_blur=TipoServicioState.validar_nombre_campo,
                            error=TipoServicioState.error_nombre,
                            max_length=50,
                        ),
                        spacing="1",
                        width="100%",
                        align_items="stretch"
                    ),

                    # Campo: Clave (auto-generada, editable)
                    rx.vstack(
                        rx.text("Clave", size="2", weight="medium"),
                        form_input(
                            placeholder="Se genera automáticamente",
                            value=TipoServicioState.form_clave,
                            on_change=TipoServicioState.set_form_clave,
                            on_blur=TipoServicioState.validar_clave_campo,
                            error=TipoServicioState.error_clave,
                            max_length=5,
                        ),
                        rx.text(
                            "Auto-generada desde el nombre (editable)",
                            size="1",
                            color="gray"
                        ),
                        spacing="1",
                        width="100%",
                        align_items="stretch"
                    ),

                    # Campo: Descripción
                    rx.vstack(
                        rx.text("Descripción", size="2", weight="medium"),
                        form_textarea(
                            placeholder="Descripción del tipo de servicio (opcional)",
                            value=TipoServicioState.form_descripcion,
                            on_change=TipoServicioState.set_form_descripcion,
                            on_blur=TipoServicioState.validar_descripcion_campo,
                            error=TipoServicioState.error_descripcion,
                            max_length=500,
                        ),
                        spacing="1",
                        width="100%",
                        align_items="stretch"
                    ),

                    spacing="4",
                    width="100%",
                    padding_y="4",
                ),
            ),

            # Botones de acción
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=TipoServicioState.cerrar_modal_tipo,
                    ),
                ),
                rx.button(
                    rx.cond(
                        TipoServicioState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Guardando..."),
                            spacing="2"
                        ),
                        rx.text("Guardar")
                    ),
                    on_click=TipoServicioState.guardar_tipo,
                    disabled=~TipoServicioState.puede_guardar,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="450px",
        ),
        open=TipoServicioState.mostrar_modal_tipo,
        on_open_change=TipoServicioState.set_mostrar_modal_tipo,
    )


def modal_confirmar_eliminar() -> rx.Component:
    """Modal de confirmación para eliminar tipo"""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Eliminar Tipo de Servicio"),
            rx.alert_dialog.description(
                rx.vstack(
                    rx.text(
                        "¿Estás seguro de que deseas eliminar este tipo?"
                    ),
                    rx.cond(
                        TipoServicioState.tipo_seleccionado,
                        rx.callout(
                            rx.text(
                                rx.text(
                                    TipoServicioState.tipo_seleccionado["clave"],
                                    weight="bold"
                                ),
                                " - ",
                                TipoServicioState.tipo_seleccionado["nombre"],
                            ),
                            icon="info",
                            color_scheme="blue",
                        ),
                        rx.text("")
                    ),
                    rx.text(
                        "Esta acción desactivará el tipo. Podrás reactivarlo después.",
                        size="2",
                        color="gray"
                    ),
                    spacing="3",
                    width="100%"
                ),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=TipoServicioState.cerrar_confirmar_eliminar,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        rx.cond(
                            TipoServicioState.saving,
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Eliminando..."),
                                spacing="2"
                            ),
                            rx.text("Eliminar")
                        ),
                        color_scheme="red",
                        on_click=TipoServicioState.eliminar_tipo,
                    ),
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),
            max_width="400px",
        ),
        open=TipoServicioState.mostrar_modal_confirmar_eliminar,
        on_open_change=TipoServicioState.set_mostrar_modal_confirmar_eliminar,
    )
