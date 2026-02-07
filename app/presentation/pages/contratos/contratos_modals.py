"""
Modales para el módulo de Contratos.
"""
import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_select, form_textarea, form_date
from app.presentation.components.ui import status_badge_reactive
from app.presentation.pages.contratos.contratos_state import ContratosState
from app.presentation.theme import Colors


def _seccion_info_basica() -> rx.Component:
    """Sección de información básica (siempre visible, fuera de tabs)"""
    return rx.vstack(
        rx.text("Información Básica", weight="bold", size="3"),

        # Fila 1: Empresa y Tipo de Contrato
        rx.hstack(
            form_select(
                label="Empresa",
                required=True,
                placeholder="Seleccione empresa",
                value=ContratosState.form_empresa_id,
                on_change=ContratosState.set_form_empresa_id,
                options=ContratosState.opciones_empresa,
                error=ContratosState.error_empresa_id,
            ),
            form_select(
                label="Tipo de contrato",
                required=True,
                placeholder="Seleccione tipo",
                value=ContratosState.form_tipo_contrato,
                on_change=ContratosState.set_form_tipo_contrato,
                options=ContratosState.opciones_tipo_contrato,
                error=ContratosState.error_tipo_contrato,
            ),
            spacing="2",
            width="100%"
        ),

        # Fila 2: Modalidad y Tipo Duración
        rx.hstack(
            form_select(
                label="Modalidad de adjudicacion",
                required=True,
                placeholder="Seleccione modalidad",
                value=ContratosState.form_modalidad_adjudicacion,
                on_change=ContratosState.set_form_modalidad_adjudicacion,
                options=ContratosState.opciones_modalidad,
                error=ContratosState.error_modalidad_adjudicacion,
            ),
            # Tipo de duración (solo SERVICIOS)
            rx.cond(
                ContratosState.es_servicios,
                form_select(
                    label="Tipo de duracion",
                    required=True,
                    placeholder="Seleccione duracion",
                    value=ContratosState.form_tipo_duracion,
                    on_change=ContratosState.set_form_tipo_duracion,
                    options=ContratosState.opciones_tipo_duracion,
                    error=ContratosState.error_tipo_duracion,
                ),
            ),
            spacing="2",
            width="100%"
        ),

        form_input(
            label="Folio BUAP",
            placeholder="Ej: BUAP-2026-001",
            value=ContratosState.form_folio_buap,
            on_change=ContratosState.set_form_folio_buap,
            error=ContratosState.error_folio_buap,
        ),

        spacing="2",
        width="100%"
    )


def _contenido_detalles() -> rx.Component:
    """Contenido de detalles del contrato (vigencia, montos, descripción, configuración)"""
    return rx.vstack(
        # ============================================
        # SECCIÓN 2: VIGENCIA
        # ============================================
        rx.vstack(
            rx.text("Vigencia", weight="bold", size="3"),

            rx.hstack(
                # Fecha inicio (siempre requerida)
                form_date(
                    label="Fecha de inicio",
                    required=True,
                    value=ContratosState.form_fecha_inicio,
                    on_change=ContratosState.set_form_fecha_inicio,
                    error=ContratosState.error_fecha_inicio,
                ),
                # Fecha fin (solo para SERVICIOS + TIEMPO_DETERMINADO)
                rx.cond(
                    ContratosState.es_tiempo_determinado,
                    form_date(
                        label="Fecha de fin",
                        required=True,
                        value=ContratosState.form_fecha_fin,
                        on_change=ContratosState.set_form_fecha_fin,
                        error=ContratosState.error_fecha_fin,
                    ),
                ),
                spacing="2",
                width="100%"
            ),

            spacing="2",
            width="100%"
        ),

        # ============================================
        # SECCIÓN 3: MONTOS
        # ============================================
        rx.vstack(
            rx.text("Montos", weight="bold", size="3"),

            rx.hstack(
                # Monto mínimo (solo SERVICIOS)
                rx.cond(
                    ContratosState.es_servicios,
                    form_input(
                        label="Monto minimo",
                        placeholder="Ej: 100,000.00",
                        value=ContratosState.form_monto_minimo,
                        on_change=ContratosState.set_form_monto_minimo,
                        on_blur=ContratosState.validar_monto_minimo_campo,
                        error=ContratosState.error_monto_minimo,
                    ),
                ),
                # Monto máximo (siempre)
                form_input(
                    label="Monto maximo",
                    placeholder="Ej: 500,000.00",
                    value=ContratosState.form_monto_maximo,
                    on_change=ContratosState.set_form_monto_maximo,
                    on_blur=ContratosState.validar_monto_maximo_campo,
                    error=ContratosState.error_monto_maximo,
                ),
                spacing="2",
                width="100%"
            ),

            rx.hstack(
                rx.checkbox(
                    "Montos incluyen IVA",
                    checked=ContratosState.form_incluye_iva,
                    on_change=ContratosState.set_form_incluye_iva,
                ),
                spacing="2",
            ),

            spacing="2",
            width="100%"
        ),

        # ============================================
        # SECCIÓN 4: DESCRIPCIÓN Y DETALLES
        # ============================================
        rx.vstack(
            rx.text("Descripción", weight="bold", size="3"),

            # Descripción del objeto (obligatorio)
            form_textarea(
                label="Descripcion del objeto",
                required=True,
                placeholder="Ej: Servicio de limpieza en instalaciones...",
                value=ContratosState.form_descripcion_objeto,
                on_change=ContratosState.set_form_descripcion_objeto,
                on_blur=ContratosState.validar_descripcion_objeto_campo,
                error=ContratosState.error_descripcion_objeto,
                rows="3",
            ),

            rx.hstack(
                form_input(
                    label="Origen del recurso",
                    placeholder="Ej: Recurso propio",
                    value=ContratosState.form_origen_recurso,
                    on_change=ContratosState.set_form_origen_recurso,
                ),
                form_input(
                    label="Segmento de asignacion",
                    placeholder="Ej: Operativo",
                    value=ContratosState.form_segmento_asignacion,
                    on_change=ContratosState.set_form_segmento_asignacion,
                ),
                spacing="2",
                width="100%"
            ),

            form_input(
                label="Sede/Campus",
                placeholder="Ej: Ciudad Universitaria",
                value=ContratosState.form_sede_campus,
                on_change=ContratosState.set_form_sede_campus,
            ),

            spacing="2",
            width="100%"
        ),

        # ============================================
        # SECCIÓN 5: CONFIGURACIÓN ADICIONAL
        # ============================================
        rx.vstack(
            rx.text("Configuración", weight="bold", size="3"),

            rx.hstack(
                rx.checkbox(
                    "Requiere póliza de seguro",
                    checked=ContratosState.form_requiere_poliza,
                    on_change=ContratosState.set_form_requiere_poliza,
                ),
                # Incluye personal (solo SERVICIOS)
                rx.cond(
                    ContratosState.es_servicios,
                    rx.checkbox(
                        "Incluye personal",
                        checked=ContratosState.form_tiene_personal,
                        on_change=ContratosState.set_form_tiene_personal,
                    ),
                ),
                spacing="4",
            ),

            # Nota sobre póliza automática
            rx.cond(
                ContratosState.requiere_poliza_auto,
                rx.text(
                    "* La póliza es requerida porque el contrato tiene montos mínimo y máximo",
                    size="1",
                    color="orange"
                ),
            ),

            rx.cond(
                ContratosState.form_requiere_poliza,
                form_input(
                    label="Detalles de poliza",
                    placeholder="Ej: Poliza de responsabilidad civil",
                    value=ContratosState.form_poliza_detalle,
                    on_change=ContratosState.set_form_poliza_detalle,
                ),
            ),

            # Estatus (solo en edición)
            rx.cond(
                ContratosState.es_edicion,
                form_select(
                    label="Estatus",
                    placeholder="Seleccione estatus",
                    value=ContratosState.form_estatus,
                    on_change=ContratosState.set_form_estatus,
                    options=ContratosState.opciones_estatus,
                ),
            ),

            form_textarea(
                label="Notas",
                placeholder="Ej: Observaciones adicionales...",
                value=ContratosState.form_notas,
                on_change=ContratosState.set_form_notas,
                rows="2",
            ),

            spacing="2",
            width="100%"
        ),

        spacing="6",
        width="100%",
    )


def _tab_general() -> rx.Component:
    """Pestaña general (para mostrar en tabs cuando es SERVICIOS)"""
    return _contenido_detalles()


def _tab_config_personal() -> rx.Component:
    """Pestaña de configuración de personal (solo para contratos de SERVICIOS)"""
    return rx.vstack(
        rx.callout(
            "Configure los parámetros de personal para este contrato de servicios.",
            icon="info",
            color_scheme="blue",
            size="2",
        ),

        # Tipo de servicio para configuración de personal
        form_select(
            label="Tipo de servicio",
            required=True,
            placeholder="Seleccione tipo de servicio",
            value=ContratosState.form_tipo_servicio_id,
            on_change=ContratosState.set_form_tipo_servicio_id,
            options=ContratosState.opciones_tipo_servicio,
        ),

        # Categoría de puesto (depende del tipo de servicio seleccionado)
        rx.cond(
            ContratosState.form_tipo_servicio_id != "",
            form_select(
                label="Categoria de puesto",
                required=True,
                placeholder="Seleccione categoria",
                value=ContratosState.form_categoria_puesto_id,
                on_change=ContratosState.set_form_categoria_puesto_id,
                options=ContratosState.opciones_categoria_puesto,
            ),
        ),

        spacing="4",
        width="100%",
        min_height="300px",
    )


def _fila_config_entregable(config: dict) -> rx.Component:
    """Fila de tipo de entregable configurado"""
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(config["tipo_label"], weight="medium", size="2"),
                rx.cond(
                    config["requerido"],
                    rx.badge("Requerido", color_scheme="red", size="1"),
                    rx.badge("Opcional", color_scheme="gray", size="1"),
                ),
                spacing="2",
                align="center",
            ),
            rx.text(config["periodicidad_label"], size="1", color=Colors.TEXT_MUTED),
            rx.cond(
                config["descripcion"],
                rx.text(config["descripcion"], size="1", color=Colors.TEXT_SECONDARY),
                rx.fragment(),
            ),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.button(
            rx.icon("trash-2", size=14),
            size="1",
            variant="ghost",
            color_scheme="red",
            on_click=lambda: ContratosState.eliminar_tipo_entregable(config["tipo_entregable"]),
        ),
        width="100%",
        padding="3",
        background=Colors.SECONDARY_LIGHT,
        border_radius="6px",
        align="center",
    )


def _tab_config_entregables() -> rx.Component:
    """Pestaña de configuración de entregables"""
    return rx.vstack(
        rx.callout(
            "Configure los tipos de entregables que el proveedor debe entregar periódicamente.",
            icon="info",
            color_scheme="blue",
            size="2",
        ),

        # Lista de tipos configurados
        rx.cond(
            ContratosState.tiene_config_entregables,
            rx.vstack(
                rx.text("Tipos configurados:", weight="bold", size="2"),
                rx.foreach(
                    ContratosState.config_entregables,
                    _fila_config_entregable,
                ),
                spacing="2",
                width="100%",
            ),
            rx.center(
                rx.text("No hay tipos de entregable configurados", size="2", color=Colors.TEXT_MUTED),
                padding="4",
            ),
        ),

        rx.divider(),

        # Formulario para agregar nuevo tipo
        rx.vstack(
            rx.text("Agregar tipo de entregable", weight="bold", size="2"),
            rx.hstack(
                form_select(
                    label="Tipo",
                    required=True,
                    placeholder="Seleccione tipo",
                    value=ContratosState.form_tipo_entregable,
                    on_change=ContratosState.set_form_tipo_entregable,
                    options=ContratosState.opciones_tipo_entregable,
                ),
                form_select(
                    label="Periodicidad",
                    required=True,
                    placeholder="Seleccione periodicidad",
                    value=ContratosState.form_periodicidad_entregable,
                    on_change=ContratosState.set_form_periodicidad_entregable,
                    options=ContratosState.opciones_periodicidad_entregable,
                ),
                spacing="2",
                width="100%",
            ),
            rx.hstack(
                rx.checkbox(
                    "Requerido para aprobar período",
                    checked=ContratosState.form_entregable_requerido,
                    on_change=ContratosState.set_form_entregable_requerido,
                ),
                spacing="2",
            ),
            form_input(
                label="Descripción personalizada",
                placeholder="Ej: Fotos de limpieza de áreas comunes",
                value=ContratosState.form_entregable_descripcion,
                on_change=ContratosState.set_form_entregable_descripcion,
            ),
            form_textarea(
                label="Instrucciones para el proveedor",
                placeholder="Ej: Incluir fecha y hora visible en cada foto",
                value=ContratosState.form_entregable_instrucciones,
                on_change=ContratosState.set_form_entregable_instrucciones,
                rows="2",
            ),
            rx.button(
                rx.icon("plus", size=14),
                "Agregar tipo",
                variant="soft",
                size="2",
                on_click=ContratosState.agregar_tipo_entregable,
                disabled=~ContratosState.puede_agregar_entregable,
            ),
            spacing="3",
            width="100%",
        ),

        spacing="4",
        width="100%",
        min_height="300px",
    )


def modal_contrato() -> rx.Component:
    """Modal unificado para crear o editar contrato"""
    return rx.dialog.root(
        rx.dialog.content(
            # Header
            rx.dialog.title(
                rx.cond(
                    ContratosState.es_edicion,
                    "Editar Contrato",
                    "Nuevo Contrato"
                )
            ),
            rx.dialog.description(
                rx.cond(
                    ContratosState.es_edicion,
                    "Modifique la información del contrato",
                    "Complete la información del nuevo contrato"
                ),
                margin_bottom="16px"
            ),

            # Mensaje de error/info
            rx.cond(
                ContratosState.mensaje_info != "",
                rx.callout(
                    ContratosState.mensaje_info,
                    icon=rx.cond(
                        ContratosState.tipo_mensaje == "error",
                        "triangle-alert",
                        "info"
                    ),
                    color_scheme=rx.cond(
                        ContratosState.tipo_mensaje == "error",
                        "red",
                        "blue"
                    ),
                    size="2",
                    width="100%",
                    margin_bottom="4",
                )
            ),

            # Sección de información básica (siempre visible)
            _seccion_info_basica(),

            # Contenido adicional con tabs (solo si es SERVICIOS)
            rx.cond(
                ContratosState.es_servicios,
                # Con pestañas para SERVICIOS
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Detalles", value="detalles"),
                        rx.tabs.trigger("Config. Personal", value="personal"),
                        rx.tabs.trigger("Config. Entregables", value="entregables"),
                    ),
                    rx.tabs.content(
                        _contenido_detalles(),
                        value="detalles",
                        padding_top="16px",
                    ),
                    rx.tabs.content(
                        _tab_config_personal(),
                        value="personal",
                        padding_top="16px",
                    ),
                    rx.tabs.content(
                        _tab_config_entregables(),
                        value="entregables",
                        padding_top="16px",
                    ),
                    default_value="detalles",
                    width="100%",
                ),
                # Sin pestañas para otros tipos - mostrar contenido directo
                _contenido_detalles(),
            ),

            rx.box(height="20px"),

            # Botones
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    size="2",
                    on_click=ContratosState.cerrar_modal_contrato
                ),
                rx.button(
                    rx.cond(
                        ContratosState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Guardando..."),
                            spacing="2"
                        ),
                        rx.cond(
                            ContratosState.es_edicion,
                            "Guardar Cambios",
                            "Crear Contrato"
                        )
                    ),
                    on_click=ContratosState.guardar_contrato,
                    disabled=ContratosState.saving,
                    color_scheme="blue",
                    size="2"
                ),
                spacing="4",
                justify="end"
            ),

            max_width="700px",
            spacing="4"
        ),
        open=ContratosState.mostrar_modal_contrato,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def _tab_informacion_contrato() -> rx.Component:
    """Pestaña de información del contrato"""
    return rx.vstack(
        # Información principal
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.text("Información General", weight="bold", size="4"),
                    rx.spacer(),
                    rx.badge(
                        ContratosState.contrato_seleccionado["codigo"],
                        color_scheme="blue",
                        size="2",
                        variant="solid",
                    ),
                    align="center",
                    width="100%",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Empresa:", weight="bold", size="2"),
                        rx.text(
                            rx.cond(
                                ContratosState.contrato_seleccionado["nombre_empresa"],
                                ContratosState.contrato_seleccionado["nombre_empresa"],
                                "Sin empresa"
                            ),
                            size="2"
                        ),
                        align="start"
                    ),
                    rx.vstack(
                        rx.text("Tipo de Servicio:", weight="bold", size="2"),
                        rx.text(
                            rx.cond(
                                ContratosState.contrato_seleccionado["nombre_servicio"],
                                ContratosState.contrato_seleccionado["nombre_servicio"],
                                "Sin tipo"
                            ),
                            size="2"
                        ),
                        align="start"
                    ),
                    rx.vstack(
                        rx.text("Tipo de Contrato:", weight="bold", size="2"),
                        rx.text(ContratosState.contrato_seleccionado["tipo_contrato"], size="2"),
                        align="start"
                    ),
                    rx.vstack(
                        rx.text("Modalidad:", weight="bold", size="2"),
                        rx.text(ContratosState.contrato_seleccionado["modalidad_adjudicacion"], size="2"),
                        align="start"
                    ),
                    rx.vstack(
                        rx.text("Estatus:", weight="bold", size="2"),
                        rx.badge(ContratosState.contrato_seleccionado["estatus"]),
                        align="start"
                    ),
                    columns="2",
                    spacing="4"
                ),
                spacing="3"
            ),
            width="100%"
        ),

        # Vigencia
        rx.card(
            rx.vstack(
                rx.text("Vigencia", weight="bold", size="4"),
                rx.hstack(
                    rx.vstack(
                        rx.text("Fecha inicio:", weight="bold", size="2"),
                        rx.text(
                            ContratosState.contrato_seleccionado["fecha_inicio"].to(str),
                            size="2",
                        ),
                        align="start"
                    ),
                    rx.vstack(
                        rx.text("Fecha fin:", weight="bold", size="2"),
                        rx.text(
                            rx.cond(
                                ContratosState.contrato_seleccionado["fecha_fin"],
                                ContratosState.contrato_seleccionado["fecha_fin"].to(str),
                                "Indefinido"
                            ),
                            size="2"
                        ),
                        align="start"
                    ),
                    rx.vstack(
                        rx.text("Tipo duración:", weight="bold", size="2"),
                        rx.text(ContratosState.contrato_seleccionado["tipo_duracion"], size="2"),
                        align="start"
                    ),
                    spacing="6"
                ),
                spacing="3"
            ),
            width="100%"
        ),

        # Montos (si existen)
        rx.cond(
            ContratosState.contrato_seleccionado["monto_minimo"] |
            ContratosState.contrato_seleccionado["monto_maximo"],
            rx.card(
                rx.vstack(
                    rx.text("Montos", weight="bold", size="4"),
                    rx.hstack(
                        rx.cond(
                            ContratosState.contrato_seleccionado["monto_minimo"],
                            rx.vstack(
                                rx.text("Monto mínimo:", weight="bold", size="2"),
                                rx.text(
                                    f"${ContratosState.contrato_seleccionado['monto_minimo'].to(str)}",
                                    size="2"
                                ),
                                align="start"
                            ),
                        ),
                        rx.cond(
                            ContratosState.contrato_seleccionado["monto_maximo"],
                            rx.vstack(
                                rx.text("Monto máximo:", weight="bold", size="2"),
                                rx.text(
                                    f"${ContratosState.contrato_seleccionado['monto_maximo'].to(str)}",
                                    size="2"
                                ),
                                align="start"
                            ),
                        ),
                        rx.vstack(
                            rx.text("Incluye IVA:", weight="bold", size="2"),
                            rx.text(
                                rx.cond(
                                    ContratosState.contrato_seleccionado["incluye_iva"],
                                    "Sí",
                                    "No"
                                ),
                                size="2"
                            ),
                            align="start"
                        ),
                        spacing="6"
                    ),
                    spacing="3"
                ),
                width="100%"
            ),
        ),

        # Descripción (si existe)
        rx.cond(
            ContratosState.contrato_seleccionado["descripcion_objeto"],
            rx.card(
                rx.vstack(
                    rx.text("Descripción", weight="bold", size="4"),
                    rx.text(
                        ContratosState.contrato_seleccionado["descripcion_objeto"],
                        size="2"
                    ),
                    spacing="2"
                ),
                width="100%"
            ),
        ),

        # Notas (si existen)
        rx.cond(
            ContratosState.contrato_seleccionado["notas"],
            rx.card(
                rx.vstack(
                    rx.text("Notas", weight="bold", size="4"),
                    rx.text(ContratosState.contrato_seleccionado["notas"], size="2"),
                    spacing="2"
                ),
                width="100%"
            ),
        ),

        spacing="4",
        width="100%",
    )


def _fila_entregable(entregable: dict) -> rx.Component:
    """Fila de entregable en la tabla"""
    return rx.table.row(
        rx.table.cell(rx.text(f"Período {entregable['numero_periodo']}", weight="medium")),
        rx.table.cell(rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY)),
        rx.table.cell(status_badge_reactive(entregable["estatus"])),
        rx.table.cell(
            rx.cond(
                entregable["monto_aprobado"],
                rx.text(f"${entregable['monto_aprobado']}", size="2", weight="medium"),
                rx.text("-", size="2", color=Colors.TEXT_MUTED),
            ),
        ),
        rx.table.cell(
            rx.button(
                rx.icon("eye", size=14),
                size="1",
                variant="ghost",
                on_click=rx.redirect(f"/entregables/{entregable['id']}"),
            ),
        ),
    )


def _tab_entregables_contrato() -> rx.Component:
    """Pestaña de entregables del contrato"""
    return rx.vstack(
        rx.cond(
            ContratosState.cargando_entregables,
            rx.center(rx.spinner(size="3"), padding="8"),
            rx.cond(
                ContratosState.tiene_entregables_contrato,
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Período"),
                                rx.table.column_header_cell("Fechas"),
                                rx.table.column_header_cell("Estado"),
                                rx.table.column_header_cell("Monto"),
                                rx.table.column_header_cell(""),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(ContratosState.entregables_contrato, _fila_entregable),
                        ),
                        width="100%",
                    ),
                    overflow_x="auto",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("package", size=40, color=Colors.TEXT_MUTED),
                        rx.text("No hay entregables para este contrato", color=Colors.TEXT_MUTED),
                        rx.text("Los entregables se generan automáticamente según la configuración", size="1", color=Colors.TEXT_MUTED),
                        spacing="2",
                        align="center",
                    ),
                    padding="8",
                ),
            ),
        ),
        spacing="4",
        width="100%",
        min_height="200px",
    )


def modal_detalle_contrato() -> rx.Component:
    """Modal para mostrar detalles del contrato con pestañas"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                ContratosState.contrato_seleccionado,
                rx.vstack(
                    rx.dialog.title("Detalle del Contrato"),

                    # Tabs de contenido
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Información", value="info"),
                            rx.tabs.trigger(
                                rx.hstack(
                                    rx.text("Entregables"),
                                    rx.cond(
                                        ContratosState.tiene_entregables_contrato,
                                        rx.badge(
                                            ContratosState.entregables_contrato.length(),
                                            color_scheme="blue",
                                            size="1",
                                        ),
                                        rx.fragment(),
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                value="entregables",
                            ),
                        ),
                        rx.tabs.content(
                            _tab_informacion_contrato(),
                            value="info",
                            padding_top="16px",
                        ),
                        rx.tabs.content(
                            _tab_entregables_contrato(),
                            value="entregables",
                            padding_top="16px",
                        ),
                        default_value="info",
                        width="100%",
                    ),

                    # Botones
                    rx.hstack(
                        rx.button(
                            "Cerrar",
                            variant="soft",
                            size="2",
                            on_click=ContratosState.cerrar_modal_detalle,
                        ),
                        # Editar solo si está en BORRADOR o SUSPENDIDO
                        rx.cond(
                            (ContratosState.contrato_seleccionado["estatus"] == "BORRADOR") |
                            (ContratosState.contrato_seleccionado["estatus"] == "SUSPENDIDO"),
                            rx.button(
                                "Editar",
                                on_click=lambda: ContratosState.abrir_modal_editar(
                                    ContratosState.contrato_seleccionado
                                ),
                                size="2"
                            ),
                        ),
                        spacing="2",
                        justify="end",
                        margin_top="16px",
                    ),

                    spacing="4",
                    width="100%"
                ),
            ),
            max_width="700px"
        ),
        open=ContratosState.mostrar_modal_detalle,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_confirmar_cancelar() -> rx.Component:
    """Modal de confirmación para cancelar contrato"""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Cancelar Contrato"),
            rx.alert_dialog.description(
                rx.cond(
                    ContratosState.contrato_seleccionado,
                    rx.text(
                        "¿Está seguro que desea cancelar el contrato ",
                        rx.text(
                            ContratosState.contrato_seleccionado["codigo"],
                            weight="bold"
                        ),
                        "? Esta acción no se puede deshacer."
                    ),
                    "¿Está seguro que desea cancelar este contrato?"
                )
            ),
            rx.hstack(
                rx.button(
                    "No, mantener",
                    variant="soft",
                    on_click=ContratosState.cerrar_confirmar_cancelar
                ),
                rx.button(
                    rx.cond(
                        ContratosState.saving,
                        rx.hstack(rx.spinner(size="1"), "Cancelando...", spacing="2"),
                        "Sí, cancelar"
                    ),
                    color_scheme="red",
                    on_click=ContratosState.cancelar_contrato,
                    disabled=ContratosState.saving,
                ),
                spacing="3",
                justify="end"
            ),
        ),
        open=ContratosState.mostrar_modal_confirmar_cancelar,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )
