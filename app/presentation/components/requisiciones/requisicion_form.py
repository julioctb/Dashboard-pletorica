"""Modal de formulario para crear/editar requisiciones."""
import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_select, form_textarea
from app.presentation.pages.requisiciones.requisiciones_state import RequisicionesState
from app.presentation.components.requisiciones.requisicion_items_form import requisicion_items_form
from app.presentation.components.requisiciones.requisicion_partidas_form import requisicion_partidas_form


# =============================================================================
# SECCIONES DEL FORMULARIO
# =============================================================================

def _tab_datos_generales() -> rx.Component:
    """Tab 1: Datos generales de la requisicion."""
    return rx.vstack(
        rx.hstack(
            form_select(
                placeholder="Tipo de contratacion *",
                value=RequisicionesState.form_tipo_contratacion,
                on_change=RequisicionesState.set_form_tipo_contratacion,
                options=RequisicionesState.opciones_tipo_form,
            ),
            rx.vstack(
                rx.text("Fecha de elaboracion *", size="2", color="gray"),
                rx.input(
                    type="date",
                    value=RequisicionesState.form_fecha_elaboracion,
                    on_change=RequisicionesState.set_form_fecha_elaboracion,
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        form_textarea(
            placeholder="Objeto de la contratacion *",
            value=RequisicionesState.form_objeto_contratacion,
            on_change=RequisicionesState.set_form_objeto_contratacion,
            rows="3",
        ),
        form_textarea(
            placeholder="Justificacion de la solicitud *",
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
                placeholder="Dependencia requirente *",
                value=RequisicionesState.form_dependencia_requirente,
                on_change=RequisicionesState.set_form_dependencia_requirente,
            ),
            form_input(
                placeholder="Domicilio",
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
                placeholder="Nombre del titular *",
                value=RequisicionesState.form_titular_nombre,
                on_change=RequisicionesState.set_form_titular_nombre,
            ),
            form_input(
                placeholder="Cargo del titular",
                value=RequisicionesState.form_titular_cargo,
                on_change=RequisicionesState.set_form_titular_cargo,
            ),
            spacing="2",
            width="100%",
        ),
        rx.hstack(
            form_input(
                placeholder="Telefono",
                value=RequisicionesState.form_titular_telefono,
                on_change=RequisicionesState.set_form_titular_telefono,
            ),
            form_input(
                placeholder="Email",
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
                placeholder="Nombre del coordinador",
                value=RequisicionesState.form_coordinador_nombre,
                on_change=RequisicionesState.set_form_coordinador_nombre,
            ),
            form_input(
                placeholder="Telefono",
                value=RequisicionesState.form_coordinador_telefono,
                on_change=RequisicionesState.set_form_coordinador_telefono,
            ),
            form_input(
                placeholder="Email",
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
                placeholder="Nombre del asesor",
                value=RequisicionesState.form_asesor_nombre,
                on_change=RequisicionesState.set_form_asesor_nombre,
            ),
            form_input(
                placeholder="Telefono",
                value=RequisicionesState.form_asesor_telefono,
                on_change=RequisicionesState.set_form_asesor_telefono,
            ),
            form_input(
                placeholder="Email",
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
        form_input(
            placeholder="Lugar de entrega *",
            value=RequisicionesState.form_lugar_entrega,
            on_change=RequisicionesState.set_form_lugar_entrega,
        ),
        rx.hstack(
            rx.vstack(
                rx.text("Fecha entrega inicio", size="2", color="gray"),
                rx.input(
                    type="date",
                    value=RequisicionesState.form_fecha_entrega_inicio,
                    on_change=RequisicionesState.set_form_fecha_entrega_inicio,
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            rx.vstack(
                rx.text("Fecha entrega fin", size="2", color="gray"),
                rx.input(
                    type="date",
                    value=RequisicionesState.form_fecha_entrega_fin,
                    on_change=RequisicionesState.set_form_fecha_entrega_fin,
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        form_textarea(
            placeholder="Condiciones de entrega",
            value=RequisicionesState.form_condiciones_entrega,
            on_change=RequisicionesState.set_form_condiciones_entrega,
            rows="2",
        ),

        # Garantia
        rx.text("Garantia", weight="bold", size="3"),
        rx.hstack(
            form_input(
                placeholder="Tipo de garantia",
                value=RequisicionesState.form_tipo_garantia,
                on_change=RequisicionesState.set_form_tipo_garantia,
            ),
            form_input(
                placeholder="Vigencia de garantia",
                value=RequisicionesState.form_garantia_vigencia,
                on_change=RequisicionesState.set_form_garantia_vigencia,
            ),
            spacing="2",
            width="100%",
        ),

        # Proveedor y pago
        rx.text("Proveedor y Pago", weight="bold", size="3"),
        form_textarea(
            placeholder="Requisitos del proveedor",
            value=RequisicionesState.form_requisitos_proveedor,
            on_change=RequisicionesState.set_form_requisitos_proveedor,
            rows="2",
        ),
        form_input(
            placeholder="Forma de pago",
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
            placeholder="Existencia en almacen",
            value=RequisicionesState.form_existencia_almacen,
            on_change=RequisicionesState.set_form_existencia_almacen,
        ),
        form_textarea(
            placeholder="Observaciones",
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
        form_input(
            placeholder="Eje del PDI",
            value=RequisicionesState.form_pdi_eje,
            on_change=RequisicionesState.set_form_pdi_eje,
        ),
        form_input(
            placeholder="Objetivo del PDI",
            value=RequisicionesState.form_pdi_objetivo,
            on_change=RequisicionesState.set_form_pdi_objetivo,
        ),
        form_input(
            placeholder="Estrategia del PDI",
            value=RequisicionesState.form_pdi_estrategia,
            on_change=RequisicionesState.set_form_pdi_estrategia,
        ),
        form_input(
            placeholder="Meta del PDI",
            value=RequisicionesState.form_pdi_meta,
            on_change=RequisicionesState.set_form_pdi_meta,
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
            placeholder="Validacion del asesor juridico",
            value=RequisicionesState.form_validacion_asesor,
            on_change=RequisicionesState.set_form_validacion_asesor,
        ),
        # Elabora
        rx.text("Elabora", weight="bold", size="3"),
        rx.hstack(
            form_input(
                placeholder="Nombre de quien elabora *",
                value=RequisicionesState.form_elabora_nombre,
                on_change=RequisicionesState.set_form_elabora_nombre,
            ),
            form_input(
                placeholder="Cargo",
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
                placeholder="Nombre de quien solicita *",
                value=RequisicionesState.form_solicita_nombre,
                on_change=RequisicionesState.set_form_solicita_nombre,
            ),
            form_input(
                placeholder="Cargo",
                value=RequisicionesState.form_solicita_cargo,
                on_change=RequisicionesState.set_form_solicita_cargo,
            ),
            spacing="2",
            width="100%",
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
                    size="1",
                ),
                rx.tabs.content(_tab_datos_generales(), value="general", padding_top="16px"),
                rx.tabs.content(_tab_area_requirente(), value="area", padding_top="16px"),
                rx.tabs.content(_tab_bien_servicio(), value="bien", padding_top="16px"),
                rx.tabs.content(_tab_items(), value="items", padding_top="16px"),
                rx.tabs.content(_tab_partidas(), value="partidas", padding_top="16px"),
                rx.tabs.content(_tab_pdi(), value="pdi", padding_top="16px"),
                rx.tabs.content(_tab_firmas(), value="firmas", padding_top="16px"),
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
                            "Crear Requisicion",
                        ),
                    ),
                    on_click=RequisicionesState.guardar_requisicion,
                    disabled=RequisicionesState.saving,
                    color_scheme="blue",
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
