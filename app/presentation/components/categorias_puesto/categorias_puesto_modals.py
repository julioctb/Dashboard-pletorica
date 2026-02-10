"""
Componentes de modal para Categorías de Puesto.
"""
import reflex as rx
from app.presentation.pages.categorias_puesto.categorias_puesto_state import CategoriasPuestoState
from app.presentation.components.ui.form_input import form_input, form_textarea, form_select
from app.presentation.components.ui.modals import modal_confirmar_accion
from app.presentation.components.ui.buttons import boton_guardar, boton_cancelar


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
                boton_cancelar(
                    on_click=CategoriasPuestoState.cerrar_modal_categoria,
                ),
                boton_guardar(
                    texto="Guardar",
                    texto_guardando="Guardando...",
                    on_click=CategoriasPuestoState.guardar_categoria,
                    saving=CategoriasPuestoState.saving,
                    disabled=~CategoriasPuestoState.puede_guardar,
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="500px",
        ),
        open=CategoriasPuestoState.mostrar_modal_categoria,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_confirmar_eliminar() -> rx.Component:
    """Modal de confirmación para eliminar categoría (usa componente genérico)"""
    return modal_confirmar_accion(
        open=CategoriasPuestoState.mostrar_modal_confirmar_eliminar,
        titulo="Eliminar Categoría de Puesto",
        mensaje="¿Estás seguro de que deseas eliminar esta categoría?",
        detalle_contenido=rx.cond(
            CategoriasPuestoState.categoria_seleccionada,
            rx.text(
                rx.text(
                    CategoriasPuestoState.categoria_seleccionada["clave"],
                    weight="bold"
                ),
                " - ",
                CategoriasPuestoState.categoria_seleccionada["nombre"],
            ),
            rx.text(""),
        ),
        nota_adicional="Esta acción desactivará la categoría. Podrás reactivarla después.",
        on_confirmar=CategoriasPuestoState.eliminar_categoria,
        on_cancelar=CategoriasPuestoState.cerrar_confirmar_eliminar,
        loading=CategoriasPuestoState.saving,
        texto_confirmar="Eliminar",
        color_confirmar="red",
        icono_detalle="info",
        color_detalle="blue",
    )
