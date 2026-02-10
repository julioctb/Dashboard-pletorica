"""
Componentes de modal para Tipos de Servicio.
"""
import reflex as rx
from app.presentation.pages.tipo_servicio.tipo_servicio_state import TipoServicioState
from app.presentation.components.ui.form_input import form_input, form_textarea
from app.presentation.components.ui.modals import modal_confirmar_accion
from app.presentation.components.ui.buttons import boton_guardar, boton_cancelar


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
                    form_input(
                        label="Nombre",
                        required=True,
                        placeholder="Ej: JARDINERIA",
                        value=TipoServicioState.form_nombre,
                        on_change=TipoServicioState.set_form_nombre,
                        on_blur=TipoServicioState.validar_nombre_campo,
                        error=TipoServicioState.error_nombre,
                        max_length=50,
                    ),

                    # Campo: Clave (auto-generada, editable)
                    form_input(
                        label="Clave",
                        placeholder="Ej: JARD",
                        value=TipoServicioState.form_clave,
                        on_change=TipoServicioState.set_form_clave,
                        on_blur=TipoServicioState.validar_clave_campo,
                        error=TipoServicioState.error_clave,
                        max_length=5,
                        hint="Auto-generada desde el nombre (editable)",
                    ),

                    # Campo: Descripcion
                    form_textarea(
                        label="Descripcion",
                        placeholder="Ej: Servicio de mantenimiento de areas verdes",
                        value=TipoServicioState.form_descripcion,
                        on_change=TipoServicioState.set_form_descripcion,
                        on_blur=TipoServicioState.validar_descripcion_campo,
                        error=TipoServicioState.error_descripcion,
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
                    on_click=TipoServicioState.cerrar_modal_tipo,
                ),
                boton_guardar(
                    texto="Guardar",
                    texto_guardando="Guardando...",
                    on_click=TipoServicioState.guardar_tipo,
                    saving=TipoServicioState.saving,
                    disabled=~TipoServicioState.puede_guardar,
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="450px",
        ),
        open=TipoServicioState.mostrar_modal_tipo,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_confirmar_eliminar() -> rx.Component:
    """Modal de confirmación para eliminar tipo (usa componente genérico)"""
    return modal_confirmar_accion(
        open=TipoServicioState.mostrar_modal_confirmar_eliminar,
        titulo="Eliminar Tipo de Servicio",
        mensaje="¿Estás seguro de que deseas eliminar este tipo?",
        detalle_contenido=rx.cond(
            TipoServicioState.tipo_seleccionado,
            rx.text(
                rx.text(TipoServicioState.tipo_seleccionado["clave"], weight="bold"),
                " - ",
                TipoServicioState.tipo_seleccionado["nombre"],
            ),
            rx.text(""),
        ),
        nota_adicional="Esta acción desactivará el tipo. Podrás reactivarlo después.",
        on_confirmar=TipoServicioState.eliminar_tipo,
        on_cancelar=TipoServicioState.cerrar_confirmar_eliminar,
        loading=TipoServicioState.saving,
        texto_confirmar="Eliminar",
        color_confirmar="red",
        icono_detalle="info",
        color_detalle="blue",
    )
