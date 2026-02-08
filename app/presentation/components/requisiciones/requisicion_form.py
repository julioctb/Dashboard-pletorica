"""Modal de formulario para crear/editar requisiciones - Wizard de 8 pasos."""
import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_select, form_textarea, form_date
from app.presentation.pages.requisiciones.requisiciones_state import RequisicionesState
from app.presentation.components.requisiciones.requisicion_items_form import requisicion_items_form
from app.presentation.components.common.archivo_uploader import archivo_uploader
from app.presentation.theme import Colors, Spacing, Typography


# =============================================================================
# INDICADOR DE PASOS (WIZARD)
# =============================================================================

def _indicador_pasos() -> rx.Component:
    """Indicador visual: circulos numerados + titulo del paso actual debajo."""

    def _circulo(numero: int) -> rx.Component:
        es_activo = RequisicionesState.form_paso_actual >= numero
        return rx.center(
            rx.text(str(numero), font_size=Typography.SIZE_SM, font_weight=Typography.WEIGHT_BOLD),
            width="32px",
            height="32px",
            border_radius="50%",
            background=rx.cond(es_activo, Colors.PRIMARY, Colors.SECONDARY_LIGHT),
            color=rx.cond(es_activo, Colors.TEXT_INVERSE, Colors.TEXT_SECONDARY),
            cursor="pointer",
            flex_shrink="0",
            _hover={"opacity": "0.8"},
            on_click=RequisicionesState.set_form_paso_actual(numero),
        )

    def _conector() -> rx.Component:
        return rx.box(height="2px", flex="1", min_width="12px", background=Colors.BORDER)

    return rx.vstack(
        rx.hstack(
            _circulo(1), _conector(),
            _circulo(2), _conector(),
            _circulo(3), _conector(),
            _circulo(4), _conector(),
            _circulo(5), _conector(),
            _circulo(6), _conector(),
            _circulo(7), _conector(),
            _circulo(8),
            width="100%",
            justify="center",
            align="center",
        ),
        rx.text(
            rx.match(
                RequisicionesState.form_paso_actual,
                (1, "Area Requirente"),
                (2, "Bien / Servicio"),
                (3, "Items"),
                (4, "Condiciones"),
                (5, "PDI"),
                (6, "Disponibilidad Presupuestal"),
                (7, "Firmas"),
                (8, "Anexos"),
                "Area Requirente",
            ),
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_PRIMARY,
            text_align="center",
            width="100%",
        ),
        spacing="3",
        width="100%",
        padding_y=Spacing.SM,
    )


# =============================================================================
# CONTENIDO DE CADA PASO
# =============================================================================

def _paso_area_requirente() -> rx.Component:
    """Paso 1: Area requirente + tipo contratacion + fecha elaboracion."""
    return rx.vstack(
        # Tipo y fecha (movidos desde General)
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
        rx.separator(),
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


def _paso_bien_servicio() -> rx.Component:
    """Paso 2: Bien/Servicio - objeto, entrega, garantia."""
    return rx.vstack(
        # Objeto de contratacion (movido desde General)
        form_textarea(
            label="Objeto de la contratacion",
            required=True,
            placeholder="Ej: Adquisicion de equipo de computo para laboratorio",
            value=RequisicionesState.form_objeto_contratacion,
            on_change=RequisicionesState.set_form_objeto_contratacion,
            rows="3",
        ),
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
        rx.checkbox(
            "A partir de la firma del contrato",
            checked=RequisicionesState.form_inicio_desde_firma,
            on_change=RequisicionesState.set_form_inicio_desde_firma,
        ),
        rx.cond(
            RequisicionesState.form_inicio_desde_firma,
            # Solo fecha fin
            rx.box(
                form_date(
                    label="Fecha fin del servicio",
                    value=RequisicionesState.form_fecha_entrega_fin,
                    on_change=RequisicionesState.set_form_fecha_entrega_fin,
                ),
                width="100%",
            ),
            # Ambas fechas
            rx.hstack(
                form_date(
                    label="Fecha inicio",
                    value=RequisicionesState.form_fecha_entrega_inicio,
                    on_change=RequisicionesState.set_form_fecha_entrega_inicio,
                ),
                form_date(
                    label="Fecha fin",
                    value=RequisicionesState.form_fecha_entrega_fin,
                    on_change=RequisicionesState.set_form_fecha_entrega_fin,
                ),
                spacing="2",
                width="100%",
            ),
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
        spacing="3",
        width="100%",
    )


def _paso_items() -> rx.Component:
    """Paso 3: Items de la requisicion."""
    return requisicion_items_form()


def _paso_condiciones() -> rx.Component:
    """Paso 4: Condiciones - requisitos, justificacion, pago, flags."""
    return rx.vstack(
        form_textarea(
            label="Requisitos tecnicos",
            placeholder="Ej: Experiencia minima de 2 anos...",
            value=RequisicionesState.form_requisitos_proveedor,
            on_change=RequisicionesState.set_form_requisitos_proveedor,
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
        form_input(
            label="Condiciones de pago",
            placeholder="Ej: Una vez recibidos los bienes acorde a las especificaciones tecnicas y a entera satisfaccion de la contratante",
            value=RequisicionesState.form_forma_pago,
            on_change=RequisicionesState.set_form_forma_pago,
        ),
        # Flags
        rx.hstack(
            rx.checkbox(
                "Transferencia bancaria",
                checked=RequisicionesState.form_transferencia_bancaria,
                on_change=RequisicionesState.set_form_transferencia_bancaria,
            ),
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
        form_input(
            label="Existencia en almacen",
            placeholder="Ej: 0 unidades",
            value=RequisicionesState.form_existencia_almacen,
            on_change=RequisicionesState.set_form_existencia_almacen,
        ),
        spacing="3",
        width="100%",
    )


def _paso_pdi() -> rx.Component:
    """Paso 5: Alineacion al PDI."""
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


def _paso_disponibilidad() -> rx.Component:
    """Paso 6: Disponibilidad presupuestal - partida, origen, oficio, observaciones."""
    return rx.vstack(
        form_input(
            label="Partida presupuestaria",
            placeholder="Ej: 33901",
            value=RequisicionesState.form_partida_presupuestaria,
            on_change=RequisicionesState.set_form_partida_presupuestaria,
        ),
        form_input(
            label="Origen del recurso",
            placeholder="Ej: Recurso Federal",
            value=RequisicionesState.form_origen_recurso,
            on_change=RequisicionesState.set_form_origen_recurso,
        ),
        form_input(
            label="No. de Oficio de Suficiencia",
            placeholder="Ej: SA/DPP/0123/2025",
            value=RequisicionesState.form_oficio_suficiencia,
            on_change=RequisicionesState.set_form_oficio_suficiencia,
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


def _paso_firmas() -> rx.Component:
    """Paso 7: Firmas y validaciones."""
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


def _paso_anexos() -> rx.Component:
    """Paso 8: Archivos adjuntos de la requisicion."""
    return rx.vstack(
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
    """Modal con formulario de requisicion organizado en wizard de pasos."""
    return rx.dialog.root(
        rx.dialog.content(
            # Header
            rx.dialog.title(
                rx.cond(
                    RequisicionesState.es_edicion & ~RequisicionesState.es_auto_borrador,
                    titulo_editar,
                    titulo_crear,
                )
            ),
            rx.dialog.description(
                rx.cond(
                    RequisicionesState.es_edicion & ~RequisicionesState.es_auto_borrador,
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

            # Indicador de pasos
            _indicador_pasos(),

            # Contenido del paso actual
            rx.box(
                rx.match(
                    RequisicionesState.form_paso_actual,
                    (1, _paso_area_requirente()),
                    (2, _paso_bien_servicio()),
                    (3, _paso_items()),
                    (4, _paso_condiciones()),
                    (5, _paso_pdi()),
                    (6, _paso_disponibilidad()),
                    (7, _paso_firmas()),
                    (8, _paso_anexos()),
                    _paso_area_requirente(),  # default
                ),
                min_height="300px",
                padding_top=Spacing.BASE,
            ),

            rx.box(height="20px"),

            # Footer con navegacion + guardar
            rx.hstack(
                # Izquierda: Cancelar
                rx.button(
                    "Cancelar",
                    variant="soft",
                    size="2",
                    on_click=on_close,
                ),
                rx.spacer(),
                # Derecha: Anterior + Siguiente + Guardar
                rx.cond(
                    RequisicionesState.form_paso_actual > 1,
                    rx.button(
                        rx.icon("chevron-left", size=14),
                        "Anterior",
                        variant="outline",
                        size="2",
                        on_click=RequisicionesState.ir_paso_anterior,
                    ),
                ),
                rx.cond(
                    RequisicionesState.form_paso_actual < 8,
                    rx.button(
                        "Siguiente",
                        rx.icon("chevron-right", size=14),
                        variant="outline",
                        size="2",
                        color_scheme="blue",
                        on_click=RequisicionesState.ir_paso_siguiente,
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
                            RequisicionesState.es_edicion & ~RequisicionesState.es_auto_borrador,
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
                        RequisicionesState.es_edicion & ~RequisicionesState.es_auto_borrador,
                        "blue",
                        rx.cond(
                            RequisicionesState.formulario_completo,
                            "blue",
                            "gray",
                        ),
                    ),
                    size="2",
                ),
                spacing="2",
                width="100%",
                align="center",
            ),

            max_width="850px",
            spacing="4",
        ),
        open=open_var,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )
