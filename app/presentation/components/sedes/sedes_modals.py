"""
Componentes de modal para Sedes BUAP.
"""
import reflex as rx
from app.presentation.pages.sedes.sedes_state import SedesState
from app.presentation.components.ui.form_input import (
    form_input,
    form_select,
    form_textarea,
    form_row,
)
from app.presentation.components.ui.modals import modal_confirmar_accion


def modal_sede() -> rx.Component:
    """Modal para crear o editar sede"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    SedesState.es_edicion,
                    "Editar Sede",
                    "Nueva Sede"
                )
            ),
            rx.dialog.description(
                rx.vstack(
                    # Seccion: Informacion basica
                    rx.text("Informacion basica", weight="bold", size="2", color="gray"),

                    # Codigo y Tipo de sede
                    form_row(
                        form_input(
                            label="Codigo",
                            required=True,
                            placeholder="Ej: CAM-CU, FAC-MED",
                            value=SedesState.form_codigo,
                            on_change=SedesState.set_form_codigo,
                            on_blur=SedesState.validar_codigo_campo,
                            error=SedesState.error_codigo,
                            max_length=20,
                            hint="Formato: PREFIJO-CLAVE",
                        ),
                        form_select(
                            label="Tipo de sede",
                            required=True,
                            placeholder="Seleccione tipo",
                            options=SedesState.opciones_tipo_sede,
                            value=SedesState.form_tipo_sede,
                            on_change=SedesState.set_form_tipo_sede,
                            error=SedesState.error_tipo_sede,
                        ),
                    ),

                    # Nombre completo
                    form_input(
                        label="Nombre completo",
                        required=True,
                        placeholder="Ej: Ciudad Universitaria",
                        value=SedesState.form_nombre,
                        on_change=SedesState.set_form_nombre,
                        on_blur=SedesState.validar_nombre_campo,
                        error=SedesState.error_nombre,
                        max_length=150,
                    ),

                    # Nombre corto
                    form_input(
                        label="Nombre corto",
                        placeholder="Ej: CU, Torre Gestion",
                        value=SedesState.form_nombre_corto,
                        on_change=SedesState.set_form_nombre_corto,
                        on_blur=SedesState.validar_nombre_corto_campo,
                        error=SedesState.error_nombre_corto,
                        max_length=50,
                        hint="Alias o abreviatura comun",
                    ),

                    # Seccion: Jerarquia y ubicacion
                    rx.text("Jerarquia y ubicacion", weight="bold", size="2", color="gray"),

                    # Es ubicacion fisica (switch)
                    rx.hstack(
                        rx.switch(
                            checked=SedesState.form_es_ubicacion_fisica,
                            on_change=SedesState.set_form_es_ubicacion_fisica,
                        ),
                        rx.text("Tiene espacio fisico propio", size="2"),
                        spacing="2",
                        align="center",
                    ),

                    # Sede padre
                    form_select(
                        label="Sede padre (jerarquia)",
                        placeholder="Sin sede padre (raiz)",
                        options=SedesState.opciones_sedes_padre,
                        value=SedesState.form_sede_padre_id,
                        on_change=SedesState.set_form_sede_padre_id,
                        hint="Ej: Facultad dentro de Campus",
                    ),

                    # Ubicacion fisica (solo si NO es ubicacion fisica)
                    rx.cond(
                        ~SedesState.form_es_ubicacion_fisica,
                        form_select(
                            label="Ubicacion fisica",
                            placeholder="Seleccione donde se ubica",
                            options=SedesState.opciones_sedes_padre,
                            value=SedesState.form_ubicacion_fisica_id,
                            on_change=SedesState.set_form_ubicacion_fisica_id,
                            hint="Sede con espacio fisico donde opera",
                        ),
                    ),

                    # Seccion: Detalles adicionales
                    rx.text("Detalles adicionales", weight="bold", size="2", color="gray"),

                    # Direccion
                    form_textarea(
                        label="Direccion",
                        placeholder="Direccion postal de la sede",
                        value=SedesState.form_direccion,
                        on_change=SedesState.set_form_direccion,
                        rows="2",
                    ),

                    # Notas
                    form_textarea(
                        label="Notas",
                        placeholder="Observaciones adicionales...",
                        value=SedesState.form_notas,
                        on_change=SedesState.set_form_notas,
                        rows="3",
                    ),

                    spacing="4",
                    width="100%",
                    padding_y="4",
                ),
            ),

            # Botones de accion
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=SedesState.cerrar_modal_sede,
                    ),
                ),
                rx.button(
                    rx.cond(
                        SedesState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Guardando..."),
                            spacing="2"
                        ),
                        rx.text("Guardar")
                    ),
                    on_click=SedesState.guardar_sede,
                    disabled=~SedesState.puede_guardar,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="550px",
        ),
        open=SedesState.mostrar_modal_sede,
        on_open_change=SedesState.set_mostrar_modal_sede,
    )


def modal_confirmar_eliminar() -> rx.Component:
    """Modal de confirmacion para eliminar sede (usa componente generico)"""
    return modal_confirmar_accion(
        open=SedesState.mostrar_modal_confirmar_eliminar,
        titulo="Eliminar Sede",
        mensaje="Esta seguro de que desea eliminar esta sede?",
        detalle_contenido=rx.cond(
            SedesState.sede_seleccionada,
            rx.text(
                rx.text(SedesState.sede_seleccionada["codigo"], weight="bold"),
                " - ",
                SedesState.sede_seleccionada["nombre"],
            ),
            rx.text(""),
        ),
        nota_adicional="Esta accion desactivara la sede. Podra reactivarla despues.",
        on_confirmar=SedesState.eliminar_sede,
        on_cancelar=SedesState.cerrar_confirmar_eliminar,
        loading=SedesState.saving,
        texto_confirmar="Eliminar",
        color_confirmar="red",
        icono_detalle="info",
        color_detalle="blue",
    )
