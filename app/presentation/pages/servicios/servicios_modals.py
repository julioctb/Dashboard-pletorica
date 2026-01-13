"""
Componentes de modal para Áreas de Servicio.
"""
import reflex as rx
from app.presentation.pages.areas_servicio.areas_servicio_state import AreasServicioState


def form_input(
    placeholder: str,
    value: rx.Var,
    on_change: callable,
    on_blur: callable = None,
    error: rx.Var = None,
    max_length: int = None,
    **props
) -> rx.Component:
    """Input de formulario con manejo de errores"""
    return rx.vstack(
        rx.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            max_length=max_length,
            width="100%",
            **props
        ),
        rx.cond(
            error,
            rx.text(error, color="red", size="1"),
            rx.text("", size="1")  # Espacio reservado
        ),
        spacing="1",
        width="100%",
        align_items="stretch"
    )


def form_textarea(
    placeholder: str,
    value: rx.Var,
    on_change: callable,
    on_blur: callable = None,
    error: rx.Var = None,
    max_length: int = None,
    **props
) -> rx.Component:
    """Textarea de formulario con manejo de errores"""
    return rx.vstack(
        rx.text_area(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            max_length=max_length,
            width="100%",
            rows="3",
            **props
        ),
        rx.cond(
            error,
            rx.text(error, color="red", size="1"),
            rx.text("", size="1")
        ),
        spacing="1",
        width="100%",
        align_items="stretch"
    )


def modal_area_servicio() -> rx.Component:
    """Modal para crear o editar área de servicio"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    AreasServicioState.es_edicion,
                    "Editar Área de Servicio",
                    "Nueva Área de Servicio"
                )
            ),
            rx.dialog.description(
                rx.vstack(
                    # Campo: Clave
                    rx.vstack(
                        rx.text("Clave *", size="2", weight="medium"),
                        form_input(
                            placeholder="Ej: JAR, LIM, MTO",
                            value=AreasServicioState.form_clave,
                            on_change=AreasServicioState.set_form_clave,
                            on_blur=AreasServicioState.validar_clave_campo,
                            error=AreasServicioState.error_clave,
                            max_length=5,
                        ),
                        rx.text(
                            "2-5 letras mayúsculas",
                            size="1",
                            color="gray"
                        ),
                        spacing="1",
                        width="100%",
                        align_items="stretch"
                    ),

                    # Campo: Nombre
                    rx.vstack(
                        rx.text("Nombre *", size="2", weight="medium"),
                        form_input(
                            placeholder="Ej: JARDINERÍA",
                            value=AreasServicioState.form_nombre,
                            on_change=AreasServicioState.set_form_nombre,
                            on_blur=AreasServicioState.validar_nombre_campo,
                            error=AreasServicioState.error_nombre,
                            max_length=50,
                        ),
                        spacing="1",
                        width="100%",
                        align_items="stretch"
                    ),

                    # Campo: Descripción
                    rx.vstack(
                        rx.text("Descripción", size="2", weight="medium"),
                        form_textarea(
                            placeholder="Descripción del área de servicio (opcional)",
                            value=AreasServicioState.form_descripcion,
                            on_change=AreasServicioState.set_form_descripcion,
                            on_blur=AreasServicioState.validar_descripcion_campo,
                            error=AreasServicioState.error_descripcion,
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
                        on_click=AreasServicioState.cerrar_modal_area,
                    ),
                ),
                rx.button(
                    rx.cond(
                        AreasServicioState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Guardando..."),
                            spacing="2"
                        ),
                        rx.text("Guardar")
                    ),
                    on_click=AreasServicioState.guardar_area,
                    disabled=~AreasServicioState.puede_guardar,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="450px",
        ),
        open=AreasServicioState.mostrar_modal_area,
        on_open_change=AreasServicioState.set_mostrar_modal_area,
    )


def modal_confirmar_eliminar() -> rx.Component:
    """Modal de confirmación para eliminar área"""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Eliminar Área de Servicio"),
            rx.alert_dialog.description(
                rx.vstack(
                    rx.text(
                        "¿Estás seguro de que deseas eliminar esta área?"
                    ),
                    rx.cond(
                        AreasServicioState.area_seleccionada,
                        rx.callout(
                            rx.text(
                                rx.text(
                                    AreasServicioState.area_seleccionada["clave"],
                                    weight="bold"
                                ),
                                " - ",
                                AreasServicioState.area_seleccionada["nombre"],
                            ),
                            icon="info",
                            color_scheme="blue",
                        ),
                        rx.text("")
                    ),
                    rx.text(
                        "Esta acción desactivará el área. Podrás reactivarla después.",
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
                        on_click=AreasServicioState.cerrar_confirmar_eliminar,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        rx.cond(
                            AreasServicioState.saving,
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Eliminando..."),
                                spacing="2"
                            ),
                            rx.text("Eliminar")
                        ),
                        color_scheme="red",
                        on_click=AreasServicioState.eliminar_area,
                    ),
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),
            max_width="400px",
        ),
        open=AreasServicioState.mostrar_modal_confirmar_eliminar,
        on_open_change=AreasServicioState.set_mostrar_modal_confirmar_eliminar,
    )