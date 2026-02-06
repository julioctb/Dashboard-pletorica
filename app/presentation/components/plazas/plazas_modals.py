"""
Componentes de modal para Plazas.
"""
import reflex as rx
from app.presentation.pages.plazas.plazas_state import PlazasState
from app.presentation.components.ui.form_input import form_input, form_textarea, form_date, form_select
from app.presentation.components.ui.modals import modal_confirmar_accion
from app.presentation.components.ui import status_badge_reactive


def modal_plaza() -> rx.Component:
    """Modal para crear o editar plaza"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    PlazasState.es_edicion,
                    "Editar Plaza",
                    "Nueva Plaza"
                )
            ),
            rx.dialog.description(
                rx.vstack(
                    # Campo: Fecha de inicio
                    form_date(
                        label="Fecha de inicio",
                        required=True,
                        value=PlazasState.form_fecha_inicio,
                        on_change=PlazasState.set_form_fecha_inicio,
                        error=PlazasState.error_fecha_inicio,
                    ),

                    # Campo: Fecha de fin (opcional)
                    form_date(
                        label="Fecha de fin",
                        value=PlazasState.form_fecha_fin,
                        on_change=PlazasState.set_form_fecha_fin,
                        hint="Dejar vacio para plaza indefinida",
                    ),

                    # Campo: Salario mensual
                    form_input(
                        label="Salario mensual",
                        required=True,
                        placeholder="Ej: 15000.00",
                        value=PlazasState.form_salario_mensual,
                        on_change=PlazasState.set_form_salario_mensual,
                        error=PlazasState.error_salario_mensual,
                    ),

                    # Campo: Codigo (opcional)
                    form_input(
                        label="Codigo",
                        placeholder="Ej: PLZ-001",
                        value=PlazasState.form_codigo,
                        on_change=PlazasState.set_form_codigo,
                        error=PlazasState.error_codigo,
                        max_length=20,
                        hint="Identificador unico de la plaza",
                    ),

                    # Campo: Estatus (solo en edicion)
                    rx.cond(
                        PlazasState.es_edicion,
                        form_select(
                            label="Estatus",
                            placeholder="Seleccione estatus",
                            value=PlazasState.form_estatus,
                            on_change=PlazasState.set_form_estatus,
                            options=PlazasState.opciones_estatus_form,
                        ),
                    ),

                    # Campo: Notas
                    form_textarea(
                        label="Notas",
                        placeholder="Ej: Informacion adicional sobre la plaza",
                        value=PlazasState.form_notas,
                        on_change=PlazasState.set_form_notas,
                        max_length=500,
                    ),

                    spacing="4",
                    width="100%",
                    padding_y="4",
                ),
            ),

            # Botones de accion
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=PlazasState.cerrar_modal_plaza,
                ),
                rx.button(
                    rx.cond(
                        PlazasState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Guardando..."),
                            spacing="2"
                        ),
                        rx.text("Guardar")
                    ),
                    on_click=PlazasState.guardar_plaza,
                    disabled=~PlazasState.puede_guardar,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="450px",
        ),
        open=PlazasState.mostrar_modal_plaza,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_detalle_plaza() -> rx.Component:
    """Modal para ver detalles de una plaza"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Detalle de Plaza"),
            rx.dialog.description(
                rx.cond(
                    PlazasState.plaza_seleccionada,
                    rx.vstack(
                        # Header con numero y estatus
                        rx.hstack(
                            rx.text(
                                "Plaza #",
                                PlazasState.plaza_seleccionada["numero_plaza"],
                                weight="bold",
                                size="4"
                            ),
                            rx.spacer(),
                            status_badge_reactive(
                                PlazasState.plaza_seleccionada["estatus"],
                                show_icon=True
                            ),
                            width="100%",
                            align="center",
                        ),

                        rx.divider(),

                        # Datos
                        rx.vstack(
                            # Codigo
                            rx.cond(
                                PlazasState.plaza_seleccionada["codigo"],
                                rx.hstack(
                                    rx.text("Codigo:", size="2", color="gray", width="120px"),
                                    rx.text(PlazasState.plaza_seleccionada["codigo"], size="2"),
                                    width="100%",
                                ),
                            ),

                            # Fecha inicio
                            rx.hstack(
                                rx.text("Fecha inicio:", size="2", color="gray", width="120px"),
                                rx.text(PlazasState.plaza_seleccionada["fecha_inicio_fmt"], size="2"),
                                width="100%",
                            ),

                            # Fecha fin
                            rx.hstack(
                                rx.text("Fecha fin:", size="2", color="gray", width="120px"),
                                rx.text(PlazasState.plaza_seleccionada["fecha_fin_fmt"], size="2"),
                                width="100%",
                            ),

                            # Salario
                            rx.hstack(
                                rx.text("Salario:", size="2", color="gray", width="120px"),
                                rx.text(
                                    PlazasState.plaza_seleccionada["salario_fmt"],
                                    size="2",
                                    weight="medium"
                                ),
                                width="100%",
                            ),

                            # Empleado
                            rx.cond(
                                PlazasState.plaza_seleccionada["empleado_nombre"],
                                rx.hstack(
                                    rx.text("Empleado:", size="2", color="gray", width="120px"),
                                    rx.text(
                                        PlazasState.plaza_seleccionada["empleado_nombre"],
                                        size="2"
                                    ),
                                    width="100%",
                                ),
                            ),

                            # Notas
                            rx.cond(
                                PlazasState.plaza_seleccionada["notas"],
                                rx.vstack(
                                    rx.text("Notas:", size="2", color="gray"),
                                    rx.text(
                                        PlazasState.plaza_seleccionada["notas"],
                                        size="2"
                                    ),
                                    width="100%",
                                    align_items="start",
                                ),
                            ),

                            spacing="2",
                            width="100%",
                            align_items="stretch",
                        ),

                        spacing="4",
                        width="100%",
                        padding_y="4",
                    ),
                    rx.text("No hay plaza seleccionada"),
                ),
            ),

            # Botones
            rx.hstack(
                rx.button(
                    "Cerrar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=PlazasState.cerrar_modal_detalle,
                ),
                rx.cond(
                    PlazasState.plaza_seleccionada,
                    rx.cond(
                        PlazasState.plaza_seleccionada["estatus"] != "CANCELADA",
                        rx.button(
                            rx.icon("pencil", size=14),
                            "Editar",
                            on_click=lambda: PlazasState.abrir_modal_editar(
                                PlazasState.plaza_seleccionada
                            ),
                            color_scheme="blue",
                        ),
                    ),
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="450px",
        ),
        open=PlazasState.mostrar_modal_detalle,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_confirmar_cancelar() -> rx.Component:
    """Modal de confirmacion para cancelar plaza"""
    return modal_confirmar_accion(
        open=PlazasState.mostrar_modal_confirmar_cancelar,
        titulo="Cancelar Plaza",
        mensaje="Esta seguro de que desea cancelar esta plaza?",
        detalle_contenido=rx.cond(
            PlazasState.plaza_seleccionada,
            rx.text(
                "Plaza #",
                PlazasState.plaza_seleccionada["numero_plaza"],
                rx.cond(
                    PlazasState.plaza_seleccionada["codigo"],
                    rx.text(" (", PlazasState.plaza_seleccionada["codigo"], ")"),
                ),
                weight="bold",
            ),
            rx.text(""),
        ),
        nota_adicional="Esta accion marcara la plaza como cancelada. Si tiene un empleado asignado, sera liberado.",
        on_confirmar=PlazasState.cancelar_plaza,
        on_cancelar=PlazasState.cerrar_confirmar_cancelar,
        loading=PlazasState.saving,
        texto_confirmar="Cancelar Plaza",
        color_confirmar="red",
        icono_detalle="triangle-alert",
        color_detalle="amber",
    )


def modal_asignar_empleado() -> rx.Component:
    """Modal para asignar un empleado a una plaza vacante"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Asignar Empleado"),
            rx.dialog.description(
                rx.vstack(
                    # Info de la plaza
                    rx.cond(
                        PlazasState.plaza_seleccionada,
                        rx.callout(
                            rx.hstack(
                                rx.text("Plaza #", weight="medium"),
                                rx.text(
                                    PlazasState.plaza_seleccionada["numero_plaza"],
                                    weight="bold"
                                ),
                                rx.cond(
                                    PlazasState.plaza_seleccionada["codigo"],
                                    rx.text(
                                        " (",
                                        PlazasState.plaza_seleccionada["codigo"],
                                        ")"
                                    ),
                                ),
                                spacing="1",
                            ),
                            icon="briefcase",
                            size="1",
                            width="100%",
                        ),
                    ),

                    # Selector de empleado
                    rx.vstack(
                        rx.text("Seleccionar empleado *", size="2", weight="medium"),
                        rx.cond(
                            PlazasState.cargando_empleados,
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Cargando empleados...", size="2", color="gray"),
                                spacing="2",
                                padding="2",
                            ),
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Buscar empleado...",
                                    width="100%",
                                ),
                                rx.select.content(
                                    rx.cond(
                                        PlazasState.empleados_disponibles.length() > 0,
                                        rx.foreach(
                                            PlazasState.opciones_empleados,
                                            lambda opt: rx.select.item(
                                                opt["label"],
                                                value=opt["value"],
                                            ),
                                        ),
                                        rx.select.item(
                                            "No hay empleados disponibles",
                                            value="empty",
                                            disabled=True,
                                        ),
                                    ),
                                ),
                                value=PlazasState.empleado_seleccionado_id,
                                on_change=PlazasState.set_empleado_seleccionado_id,
                            ),
                        ),
                        spacing="1",
                        width="100%",
                        align_items="stretch",
                    ),

                    spacing="4",
                    width="100%",
                    padding_y="4",
                ),
            ),

            # Botones de acción
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=PlazasState.cerrar_modal_asignar_empleado,
                ),
                rx.button(
                    rx.cond(
                        PlazasState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Asignando..."),
                            spacing="2"
                        ),
                        rx.hstack(
                            rx.icon("user-check", size=14),
                            rx.text("Asignar"),
                            spacing="2"
                        )
                    ),
                    on_click=PlazasState.confirmar_asignar_empleado,
                    disabled=~PlazasState.puede_asignar_empleado,
                    color_scheme="green",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="450px",
        ),
        open=PlazasState.mostrar_modal_asignar_empleado,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_crear_lote() -> rx.Component:
    """Modal para crear plazas"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Creación de Plazas"),
            rx.dialog.description(
                rx.vstack(
                    # Información del contexto
                    rx.callout(
                        rx.vstack(
                            rx.hstack(
                                rx.text("Contrato:", size="2", color="gray", width="80px"),
                                rx.text(PlazasState.contrato_codigo, size="2", weight="medium"),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Categoría:", size="2", color="gray", width="80px"),
                                rx.text(PlazasState.categoria_nombre, size="2", weight="medium"),
                                width="100%",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        icon="info",
                        size="1",
                        width="100%",
                    ),

                    # Campo: Cantidad
                    rx.vstack(
                        rx.text("Cantidad de plazas *", size="2", weight="medium"),
                        rx.input(
                            type="number",
                            min="1",
                            max="100",
                            value=PlazasState.form_cantidad,
                            on_change=PlazasState.set_form_cantidad,
                            width="100%",
                        ),
                        rx.cond(
                            PlazasState.error_cantidad,
                            rx.text(
                                PlazasState.error_cantidad,
                                size="1",
                                color="red"
                            ),
                        ),
                        spacing="1",
                        width="100%",
                        align_items="stretch"
                    ),

                    # Campo: Salario trabajador
                    form_input(
                        label="Salario trabajador",
                        required=True,
                        placeholder="Ej: 15,000.00",
                        value=PlazasState.form_salario_mensual,
                        on_change=PlazasState.set_form_salario_mensual,
                        error=PlazasState.error_salario_mensual,
                    ),

                    # Campo: Código (auto-generado)
                    rx.vstack(
                        rx.text("Código", size="2", weight="medium"),
                        rx.hstack(
                            rx.input(
                                value=PlazasState.form_prefijo_codigo,
                                on_change=PlazasState.set_form_prefijo_codigo,
                                width="80px",
                                max_length=10,
                            ),
                            rx.text("-", size="3", color="gray"),
                            rx.text("001, 002, ...", size="2", color="gray"),
                            spacing="2",
                            align="center",
                        ),
                        rx.text(
                            "Se generará automáticamente: ",
                            PlazasState.form_prefijo_codigo,
                            "-001, ",
                            PlazasState.form_prefijo_codigo,
                            "-002, etc.",
                            size="1",
                            color="gray"
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

            # Botones de accion
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=PlazasState.cerrar_modal_crear_lote,
                ),
                rx.button(
                    rx.cond(
                        PlazasState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Generando..."),
                            spacing="2"
                        ),
                        rx.hstack(
                            rx.icon("plus", size=14),
                            rx.text("Generar"),
                            spacing="2"
                        )
                    ),
                    on_click=PlazasState.crear_plazas_lote,
                    disabled=PlazasState.saving,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="450px",
        ),
        open=PlazasState.mostrar_modal_crear_lote,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )
