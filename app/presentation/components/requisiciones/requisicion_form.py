"""Modal de formulario para crear/editar requisiciones."""
import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_select, form_textarea, form_date
from app.presentation.pages.requisiciones.requisiciones_state import RequisicionesState
from app.presentation.components.requisiciones.requisicion_items_form import requisicion_items_form
from app.presentation.components.requisiciones.requisicion_partidas_form import requisicion_partidas_form
from app.presentation.components.common.archivo_uploader import archivo_uploader


# =============================================================================
# SECCIONES DEL FORMULARIO
# =============================================================================

def _tab_datos_generales() -> rx.Component:
    """Tab 1: Datos generales de la requisicion."""
    return rx.vstack(
        rx.hstack(
            form_select(
                label="Tipo de contratacion",
                required=True,
                placeholder="Seleccione tipo",
                value=RequisicionesState.form_tipo_contratacion,
                on_change=RequisicionesState.set_form_tipo_contratacion,
                options=RequisicionesState.opciones_tipo_form,
            ),
            form_date(
                label="Fecha de elaboracion",
                required=True,
                value=RequisicionesState.form_fecha_elaboracion,
                on_change=RequisicionesState.set_form_fecha_elaboracion,
            ),
            spacing="2",
            width="100%",
        ),
        form_textarea(
            label="Objeto de la contratacion",
            required=True,
            placeholder="Ej: Adquisicion de equipo de computo para laboratorio",
            value=RequisicionesState.form_objeto_contratacion,
            on_change=RequisicionesState.set_form_objeto_contratacion,
            rows="3",
        ),
        form_textarea(
            label="Justificacion",
            required=True,
            placeholder="Ej: Se requiere para dar continuidad al programa...",
            value=RequisicionesState.form_justificacion,
            on_change=RequisicionesState.set_form_justificacion,
            rows="3",
        ),
        spacing="3",
        width="100%",
    )


def _tab_area_requirente() -> rx.Component:
    """Tab 2: Datos del area requirente."""
    return rx.vstack(
        rx.callout(
            "Estos campos se pre-llenan desde la configuracion.",
            icon="info",
            color_scheme="blue",
            size="1",
        ),
        # Dependencia
        rx.text("Dependencia Requirente", weight="bold", size="3"),
        rx.hstack(
            form_input(
                label="Dependencia requirente",
                required=True,
                placeholder="Ej: Facultad de Ingenieria",
                value=RequisicionesState.form_dependencia_requirente,
                on_change=RequisicionesState.set_form_dependencia_requirente,
            ),
            form_input(
                label="Domicilio",
                placeholder="Ej: Av. San Claudio s/n, CU",
                value=RequisicionesState.form_domicilio,
                on_change=RequisicionesState.set_form_domicilio,
            ),
            spacing="2",
            width="100%",
        ),
        # Titular
        rx.text("Titular", weight="bold", size="3"),
        rx.hstack(
            form_input(
                label="Nombre",
                required=True,
                placeholder="Ej: Juan Perez Lopez",
                value=RequisicionesState.form_titular_nombre,
                on_change=RequisicionesState.set_form_titular_nombre,
            ),
            form_input(
                label="Cargo",
                placeholder="Ej: Director de Facultad",
                value=RequisicionesState.form_titular_cargo,
                on_change=RequisicionesState.set_form_titular_cargo,
            ),
            spacing="2",
            width="100%",
        ),
        rx.hstack(
            form_input(
                label="Telefono",
                placeholder="Ej: 2221234567",
                value=RequisicionesState.form_titular_telefono,
                on_change=RequisicionesState.set_form_titular_telefono,
            ),
            form_input(
                label="Email",
                placeholder="Ej: titular@correo.buap.mx",
                value=RequisicionesState.form_titular_email,
                on_change=RequisicionesState.set_form_titular_email,
            ),
            spacing="2",
            width="100%",
        ),
        # Coordinador
        rx.text("Coordinador", weight="bold", size="3"),
        rx.hstack(
            form_input(
                label="Nombre",
                placeholder="Ej: Maria Garcia",
                value=RequisicionesState.form_coordinador_nombre,
                on_change=RequisicionesState.set_form_coordinador_nombre,
            ),
            form_input(
                label="Telefono",
                placeholder="Ej: 2229876543",
                value=RequisicionesState.form_coordinador_telefono,
                on_change=RequisicionesState.set_form_coordinador_telefono,
            ),
            form_input(
                label="Email",
                placeholder="Ej: coordinador@correo.buap.mx",
                value=RequisicionesState.form_coordinador_email,
                on_change=RequisicionesState.set_form_coordinador_email,
            ),
            spacing="2",
            width="100%",
        ),
        # Asesor
        rx.text("Asesor", weight="bold", size="3"),
        rx.hstack(
            form_input(
                label="Nombre",
                placeholder="Ej: Carlos Martinez",
                value=RequisicionesState.form_asesor_nombre,
                on_change=RequisicionesState.set_form_asesor_nombre,
            ),
            form_input(
                label="Telefono",
                placeholder="Ej: 2225551234",
                value=RequisicionesState.form_asesor_telefono,
                on_change=RequisicionesState.set_form_asesor_telefono,
            ),
            form_input(
                label="Email",
                placeholder="Ej: asesor@correo.buap.mx",
                value=RequisicionesState.form_asesor_email,
                on_change=RequisicionesState.set_form_asesor_email,
            ),
            spacing="2",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def _tab_bien_servicio() -> rx.Component:
    """Tab 3: Datos del bien o servicio."""
    return rx.vstack(
        # Lugar y fechas de entrega
        rx.text("Entrega", weight="bold", size="3"),
        form_select(
            label="Lugar de entrega",
            required=True,
            placeholder="Seleccione lugar",
            value=RequisicionesState.form_lugar_entrega,
            on_change=RequisicionesState.set_form_lugar_entrega,
            options=RequisicionesState.lugares_entrega_opciones,
        ),
        rx.hstack(
            form_date(
                label="Fecha entrega inicio",
                value=RequisicionesState.form_fecha_entrega_inicio,
                on_change=RequisicionesState.set_form_fecha_entrega_inicio,
            ),
            form_date(
                label="Fecha entrega fin",
                value=RequisicionesState.form_fecha_entrega_fin,
                on_change=RequisicionesState.set_form_fecha_entrega_fin,
            ),
            spacing="2",
            width="100%",
        ),
        form_textarea(
            label="Condiciones de entrega",
            placeholder="Ej: Entrega en horario de 9:00 a 14:00",
            value=RequisicionesState.form_condiciones_entrega,
            on_change=RequisicionesState.set_form_condiciones_entrega,
            rows="2",
        ),

        # Garantia
        rx.text("Garantia", weight="bold", size="3"),
        rx.hstack(
            form_input(
                label="Tipo de garantia",
                placeholder="Ej: Fianza, Carta compromiso",
                value=RequisicionesState.form_tipo_garantia,
                on_change=RequisicionesState.set_form_tipo_garantia,
            ),
            form_input(
                label="Vigencia",
                placeholder="Ej: 12 meses",
                value=RequisicionesState.form_garantia_vigencia,
                on_change=RequisicionesState.set_form_garantia_vigencia,
            ),
            spacing="2",
            width="100%",
        ),

        # Proveedor y pago
        rx.text("Proveedor y Pago", weight="bold", size="3"),
        form_textarea(
            label="Requisitos del proveedor",
            placeholder="Ej: Experiencia minima de 2 anos...",
            value=RequisicionesState.form_requisitos_proveedor,
            on_change=RequisicionesState.set_form_requisitos_proveedor,
            rows="2",
        ),
        form_input(
            label="Forma de pago",
            placeholder="Ej: Transferencia bancaria",
            value=RequisicionesState.form_forma_pago,
            on_change=RequisicionesState.set_form_forma_pago,
        ),

        # Flags
        rx.hstack(
            rx.checkbox(
                "Requiere anticipo",
                checked=RequisicionesState.form_requiere_anticipo,
                on_change=RequisicionesState.set_form_requiere_anticipo,
            ),
            rx.checkbox(
                "Requiere muestras",
                checked=RequisicionesState.form_requiere_muestras,
                on_change=RequisicionesState.set_form_requiere_muestras,
            ),
            rx.checkbox(
                "Requiere visita",
                checked=RequisicionesState.form_requiere_visita,
                on_change=RequisicionesState.set_form_requiere_visita,
            ),
            spacing="4",
        ),

        # Otros
        rx.text("Otros", weight="bold", size="3"),
        form_input(
            label="Existencia en almacen",
            placeholder="Ej: 0 unidades",
            value=RequisicionesState.form_existencia_almacen,
            on_change=RequisicionesState.set_form_existencia_almacen,
        ),
        form_textarea(
            label="Observaciones",
            placeholder="Ej: Notas adicionales sobre la requisicion",
            value=RequisicionesState.form_observaciones,
            on_change=RequisicionesState.set_form_observaciones,
            rows="2",
        ),

        spacing="3",
        width="100%",
    )


def _tab_items() -> rx.Component:
    """Tab 4: Items de la requisicion."""
    return requisicion_items_form()


def _tab_partidas() -> rx.Component:
    """Tab 5: Partidas presupuestales."""
    return requisicion_partidas_form()


def _tab_pdi() -> rx.Component:
    """Tab 6: Alineacion al PDI."""
    return rx.vstack(
        rx.callout(
            "Indique la alineacion con el Plan de Desarrollo Institucional.",
            icon="info",
            color_scheme="blue",
            size="1",
        ),
        form_textarea(
            label="Eje del PDI",
            placeholder="Ej: Eje 1 - Formacion integral",
            value=RequisicionesState.form_pdi_eje,
            on_change=RequisicionesState.set_form_pdi_eje,
            rows="2",
        ),
        form_textarea(
            label="Objetivo del PDI",
            placeholder="Ej: Objetivo 1.1",
            value=RequisicionesState.form_pdi_objetivo,
            on_change=RequisicionesState.set_form_pdi_objetivo,
            rows="2",
        ),
        form_textarea(
            label="Estrategia del PDI",
            placeholder="Ej: Estrategia 1.1.1",
            value=RequisicionesState.form_pdi_estrategia,
            on_change=RequisicionesState.set_form_pdi_estrategia,
            rows="2",
        ),
        form_textarea(
            label="Meta del PDI",
            placeholder="Ej: Meta 1.1.1.1",
            value=RequisicionesState.form_pdi_meta,
            on_change=RequisicionesState.set_form_pdi_meta,
            rows="2",
        ),
        spacing="3",
        width="100%",
    )


def _tab_firmas() -> rx.Component:
    """Tab 7: Firmas y validaciones."""
    return rx.vstack(
        rx.callout(
            "Estos campos se pre-llenan desde la configuracion.",
            icon="info",
            color_scheme="blue",
            size="1",
        ),
        # Validacion
        rx.text("Validacion", weight="bold", size="3"),
        form_input(
            label="Validacion del asesor tecnico",
            placeholder="Ej: Nombre del asesor",
            value=RequisicionesState.form_validacion_asesor,
            on_change=RequisicionesState.set_form_validacion_asesor,
        ),
        # Elabora
        rx.text("Elabora", weight="bold", size="3"),
        rx.hstack(
            form_input(
                label="Nombre",
                required=True,
                placeholder="Ej: Juan Perez",
                value=RequisicionesState.form_elabora_nombre,
                on_change=RequisicionesState.set_form_elabora_nombre,
            ),
            form_input(
                label="Cargo",
                placeholder="Ej: Jefe de Departamento",
                value=RequisicionesState.form_elabora_cargo,
                on_change=RequisicionesState.set_form_elabora_cargo,
            ),
            spacing="2",
            width="100%",
        ),
        # Solicita
        rx.text("Solicita", weight="bold", size="3"),
        rx.hstack(
            form_input(
                label="Nombre",
                required=True,
                placeholder="Ej: Maria Lopez",
                value=RequisicionesState.form_solicita_nombre,
                on_change=RequisicionesState.set_form_solicita_nombre,
            ),
            form_input(
                label="Cargo",
                placeholder="Ej: Director",
                value=RequisicionesState.form_solicita_cargo,
                on_change=RequisicionesState.set_form_solicita_cargo,
            ),
            spacing="2",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def _tab_archivos() -> rx.Component:
    """Tab 8: Archivos adjuntos de la requisicion."""
    return rx.vstack(
        rx.cond(
            RequisicionesState.es_edicion,
            rx.vstack(
                rx.callout(
                    "Suba imagenes (JPG, PNG) o documentos PDF. Las imagenes se comprimen automaticamente.",
                    icon="info",
                    color_scheme="blue",
                    size="1",
                ),
                archivo_uploader(
                    upload_id="archivos_requisicion",
                    archivos=RequisicionesState.archivos_entidad,
                    on_upload=RequisicionesState.handle_upload_archivo,
                    on_delete=RequisicionesState.eliminar_archivo_entidad,
                    subiendo=RequisicionesState.subiendo_archivo,
                ),
                spacing="3",
                width="100%",
            ),
            rx.callout(
                "Guarde la requisicion primero para poder adjuntar archivos.",
                icon="info",
                color_scheme="gray",
                size="1",
            ),
        ),
        spacing="3",
        width="100%",
    )


# =============================================================================
# MODAL PRINCIPAL
# =============================================================================

def requisicion_form_modal(
    open_var,
    on_close: callable,
    titulo_crear: str = "Nueva Requisicion",
    titulo_editar: str = "Editar Requisicion",
) -> rx.Component:
    """Modal con formulario de requisicion organizado en tabs."""
    return rx.dialog.root(
        rx.dialog.content(
            # Header
            rx.dialog.title(
                rx.cond(
                    RequisicionesState.es_edicion,
                    titulo_editar,
                    titulo_crear,
                )
            ),
            rx.dialog.description(
                rx.cond(
                    RequisicionesState.es_edicion,
                    "Modifique la informacion de la requisicion",
                    "Complete la informacion de la nueva requisicion",
                ),
                margin_bottom="16px",
            ),

            # Mensaje de error/info
            rx.cond(
                RequisicionesState.mensaje_info != "",
                rx.callout(
                    RequisicionesState.mensaje_info,
                    icon=rx.cond(
                        RequisicionesState.tipo_mensaje == "error",
                        "triangle-alert",
                        "info",
                    ),
                    color_scheme=rx.cond(
                        RequisicionesState.tipo_mensaje == "error",
                        "red",
                        "blue",
                    ),
                    size="2",
                    width="100%",
                    margin_bottom="4",
                ),
            ),

            # Tabs
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("General", value="general"),
                    rx.tabs.trigger("Area Req.", value="area"),
                    rx.tabs.trigger("Bien/Servicio", value="bien"),
                    rx.tabs.trigger("Items", value="items"),
                    rx.tabs.trigger("Partidas", value="partidas"),
                    rx.tabs.trigger("PDI", value="pdi"),
                    rx.tabs.trigger("Firmas", value="firmas"),
                    rx.tabs.trigger("Archivos", value="archivos"),
                    size="1",
                ),
                rx.tabs.content(_tab_datos_generales(), value="general", padding_top="16px"),
                rx.tabs.content(_tab_area_requirente(), value="area", padding_top="16px"),
                rx.tabs.content(_tab_bien_servicio(), value="bien", padding_top="16px"),
                rx.tabs.content(_tab_items(), value="items", padding_top="16px"),
                rx.tabs.content(_tab_partidas(), value="partidas", padding_top="16px"),
                rx.tabs.content(_tab_pdi(), value="pdi", padding_top="16px"),
                rx.tabs.content(_tab_firmas(), value="firmas", padding_top="16px"),
                rx.tabs.content(_tab_archivos(), value="archivos", padding_top="16px"),
                default_value="general",
                width="100%",
            ),

            rx.box(height="20px"),

            # Botones
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        size="2",
                        on_click=on_close,
                    ),
                ),
                rx.button(
                    rx.cond(
                        RequisicionesState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Guardando..."),
                            spacing="2",
                        ),
                        rx.cond(
                            RequisicionesState.es_edicion,
                            "Guardar Cambios",
                            rx.cond(
                                RequisicionesState.formulario_completo,
                                "Crear Requisicion",
                                "Guardar Borrador",
                            ),
                        ),
                    ),
                    on_click=RequisicionesState.guardar_requisicion,
                    disabled=RequisicionesState.saving,
                    color_scheme=rx.cond(
                        RequisicionesState.es_edicion,
                        "blue",
                        rx.cond(
                            RequisicionesState.formulario_completo,
                            "blue",
                            "gray",
                        ),
                    ),
                    size="2",
                ),
                spacing="4",
                justify="end",
            ),

            max_width="850px",
            spacing="4",
        ),
        open=open_var,
    )
