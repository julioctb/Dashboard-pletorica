"""
Componentes de modal para Tipos de Servicio.
"""
import reflex as rx
from app.presentation.pages.tipo_servicio.tipo_servicio_state import TipoServicioState
from app.presentation.components.ui.form_input import form_input, form_textarea
from app.presentation.components.ui.modals import modal_confirmar_accion, modal_formulario


def modal_tipo_servicio() -> rx.Component:
    """Modal para crear o editar tipo de servicio"""
    return modal_formulario(
        open=TipoServicioState.mostrar_modal_tipo,
        titulo=rx.cond(
            TipoServicioState.es_edicion,
            "Editar Tipo de Servicio",
            "Nuevo Tipo de Servicio",
        ),
        icono="layers",
        on_guardar=TipoServicioState.guardar_tipo,
        on_cancelar=TipoServicioState.cerrar_modal_tipo,
        puede_guardar=TipoServicioState.puede_guardar,
        loading=TipoServicioState.saving,
        max_width="450px",
        contenido=rx.vstack(
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
