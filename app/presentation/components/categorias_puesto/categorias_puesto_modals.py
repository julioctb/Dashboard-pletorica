"""
Componentes de modal para Categorías de Puesto.
"""
import reflex as rx
from app.presentation.pages.categorias_puesto.categorias_puesto_state import CategoriasPuestoState
from app.presentation.components.ui.form_input import form_input, form_textarea, form_select


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
                    # Campo: Tipo de Servicio (primero para verificar duplicados)
                    form_select(
                        label="Tipo de servicio",
                        required=True,
                        placeholder="Seleccione un tipo de servicio",
                        value=CategoriasPuestoState.form_tipo_servicio_id,
                        on_change=CategoriasPuestoState.set_form_tipo_servicio_id,
                        options=CategoriasPuestoState.opciones_tipo_servicio,
                        error=CategoriasPuestoState.error_tipo_servicio_id,
                        disabled=True,
                    ),

                    # Campo: Nombre (genera clave automáticamente)
                    form_input(
                        label="Nombre",
                        required=True,
                        placeholder="Ej: OPERATIVO, SUPERVISOR",
                        value=CategoriasPuestoState.form_nombre,
                        on_change=CategoriasPuestoState.set_form_nombre,
                        on_blur=CategoriasPuestoState.validar_nombre_campo,
                        error=CategoriasPuestoState.error_nombre,
                        max_length=50,
                    ),

                    # Fila: Clave y Orden
                    rx.hstack(
                        # Campo: Clave (auto-generada)
                        rx.box(
                            form_input(
                                label="Clave",
                                placeholder="Ej: OPER",
                                value=CategoriasPuestoState.form_clave,
                                on_change=CategoriasPuestoState.set_form_clave,
                                on_blur=CategoriasPuestoState.validar_clave_campo,
                                error=CategoriasPuestoState.error_clave,
                                max_length=5,
                                hint="Auto-generada (editable)",
                            ),
                            width="60%",
                        ),

                        # Campo: Orden
                        rx.box(
                            form_input(
                                label="Orden",
                                placeholder="Ej: 1",
                                value=CategoriasPuestoState.form_orden,
                                on_change=CategoriasPuestoState.set_form_orden,
                                on_blur=CategoriasPuestoState.validar_orden_campo,
                                error=CategoriasPuestoState.error_orden,
                                type="number",
                                hint="Orden de visualizacion",
                            ),
                            width="40%",
                        ),
                        spacing="4",
                        width="100%",
                    ),

                    # Campo: Descripción
                    form_textarea(
                        label="Descripcion",
                        placeholder="Ej: Personal operativo de campo",
                        value=CategoriasPuestoState.form_descripcion,
                        on_change=CategoriasPuestoState.set_form_descripcion,
                        on_blur=CategoriasPuestoState.validar_descripcion_campo,
                        error=CategoriasPuestoState.error_descripcion,
                        max_length=500,
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
