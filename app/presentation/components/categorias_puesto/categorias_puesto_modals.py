"""
Componentes de modal para Categorías de Puesto.
"""
import reflex as rx
from app.presentation.pages.categorias_puesto.categorias_puesto_state import CategoriasPuestoState


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
            rx.text("", size="1")
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


def form_select(
    placeholder: str,
    value: rx.Var,
    on_change: callable,
    options: list,
    error: rx.Var = None,
    **props
) -> rx.Component:
    """Select de formulario con manejo de errores"""
    return rx.vstack(
        rx.select.root(
            rx.select.trigger(placeholder=placeholder, width="100%"),
            rx.select.content(
                rx.foreach(
                    options,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"])
                ),
            ),
            value=value,  # Ya es string, no necesita conversión
            on_change=on_change,
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


def modal_categoria_puesto() -> rx.Component:
    """Modal para crear o editar categoría de puesto"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    CategoriasPuestoState.es_edicion,
                    "Editar Categoría de Puesto",
                    "Nueva Categoría de Puesto"
                )
            ),
            rx.dialog.description(
                rx.vstack(
                    # Campo: Tipo de Servicio
                    rx.vstack(
                        rx.text("Tipo de Servicio *", size="2", weight="medium"),
                        form_select(
                            placeholder="Seleccione un tipo de servicio",
                            value=CategoriasPuestoState.form_tipo_servicio_id,
                            on_change=CategoriasPuestoState.set_form_tipo_servicio_id,
                            options=CategoriasPuestoState.opciones_tipo_servicio,
                            error=CategoriasPuestoState.error_tipo_servicio_id,
                        ),
                        spacing="1",
                        width="100%",
                        align_items="stretch"
                    ),

                    # Fila: Clave y Orden
                    rx.hstack(
                        # Campo: Clave
                        rx.vstack(
                            rx.text("Clave *", size="2", weight="medium"),
                            form_input(
                                placeholder="Ej: OPE, SUP, GER",
                                value=CategoriasPuestoState.form_clave,
                                on_change=CategoriasPuestoState.set_form_clave,
                                on_blur=CategoriasPuestoState.validar_clave_campo,
                                error=CategoriasPuestoState.error_clave,
                                max_length=5,
                            ),
                            rx.text(
                                "2-5 letras mayúsculas",
                                size="1",
                                color="gray"
                            ),
                            spacing="1",
                            width="60%",
                            align_items="stretch"
                        ),

                        # Campo: Orden
                        rx.vstack(
                            rx.text("Orden", size="2", weight="medium"),
                            form_input(
                                placeholder="0",
                                value=CategoriasPuestoState.form_orden,
                                on_change=CategoriasPuestoState.set_form_orden,
                                on_blur=CategoriasPuestoState.validar_orden_campo,
                                error=CategoriasPuestoState.error_orden,
                                type="number",
                            ),
                            rx.text(
                                "Orden de visualización",
                                size="1",
                                color="gray"
                            ),
                            spacing="1",
                            width="40%",
                            align_items="stretch"
                        ),
                        spacing="4",
                        width="100%",
                    ),

                    # Campo: Nombre
                    rx.vstack(
                        rx.text("Nombre *", size="2", weight="medium"),
                        form_input(
                            placeholder="Ej: OPERATIVO, SUPERVISOR",
                            value=CategoriasPuestoState.form_nombre,
                            on_change=CategoriasPuestoState.set_form_nombre,
                            on_blur=CategoriasPuestoState.validar_nombre_campo,
                            error=CategoriasPuestoState.error_nombre,
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
                            placeholder="Descripción de la categoría (opcional)",
                            value=CategoriasPuestoState.form_descripcion,
                            on_change=CategoriasPuestoState.set_form_descripcion,
                            on_blur=CategoriasPuestoState.validar_descripcion_campo,
                            error=CategoriasPuestoState.error_descripcion,
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
                        on_click=CategoriasPuestoState.cerrar_modal_categoria,
                    ),
                ),
                rx.button(
                    rx.cond(
                        CategoriasPuestoState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Guardando..."),
                            spacing="2"
                        ),
                        rx.text("Guardar")
                    ),
                    on_click=CategoriasPuestoState.guardar_categoria,
                    disabled=~CategoriasPuestoState.puede_guardar,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="500px",
        ),
        open=CategoriasPuestoState.mostrar_modal_categoria,
        on_open_change=CategoriasPuestoState.set_mostrar_modal_categoria,
    )


def modal_confirmar_eliminar() -> rx.Component:
    """Modal de confirmación para eliminar categoría"""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Eliminar Categoría de Puesto"),
            rx.alert_dialog.description(
                rx.vstack(
                    rx.text(
                        "¿Estás seguro de que deseas eliminar esta categoría?"
                    ),
                    rx.cond(
                        CategoriasPuestoState.categoria_seleccionada,
                        rx.callout(
                            rx.text(
                                rx.text(
                                    CategoriasPuestoState.categoria_seleccionada["clave"],
                                    weight="bold"
                                ),
                                " - ",
                                CategoriasPuestoState.categoria_seleccionada["nombre"],
                            ),
                            icon="info",
                            color_scheme="blue",
                        ),
                        rx.text("")
                    ),
                    rx.text(
                        "Esta acción desactivará la categoría. Podrás reactivarla después.",
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
                        on_click=CategoriasPuestoState.cerrar_confirmar_eliminar,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        rx.cond(
                            CategoriasPuestoState.saving,
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Eliminando..."),
                                spacing="2"
                            ),
                            rx.text("Eliminar")
                        ),
                        color_scheme="red",
                        on_click=CategoriasPuestoState.eliminar_categoria,
                    ),
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),
            max_width="400px",
        ),
        open=CategoriasPuestoState.mostrar_modal_confirmar_eliminar,
        on_open_change=CategoriasPuestoState.set_mostrar_modal_confirmar_eliminar,
    )
