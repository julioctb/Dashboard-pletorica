"""Modales del módulo de plazas."""

import reflex as rx

from app.presentation.components.ui import status_badge_reactive
from app.presentation.components.ui.buttons import boton_cancelar, boton_guardar
from app.presentation.components.ui.form_input import (
    form_date,
    form_input,
    form_select,
    form_textarea,
)
from app.presentation.components.ui.modals import modal_confirmar_accion
from app.presentation.pages.plazas.plazas_state import PlazasState


def modal_plaza() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Editar Plaza"),
            rx.dialog.description(
                rx.vstack(
                    rx.cond(
                        PlazasState.plaza_seleccionada,
                        rx.callout(
                            rx.hstack(
                                rx.text("Plaza #", size="2", color="gray"),
                                rx.text(
                                    PlazasState.plaza_seleccionada["numero_plaza"],
                                    weight="bold",
                                ),
                                rx.text("del contrato", size="2", color="gray"),
                                rx.text(PlazasState.contrato_codigo, weight="medium"),
                                spacing="2",
                                wrap="wrap",
                            ),
                            icon="briefcase",
                            color_scheme="blue",
                            size="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    form_select(
                        label="Sede",
                        required=True,
                        placeholder="Seleccione sede",
                        value=PlazasState.form_sede_id,
                        on_change=PlazasState.set_form_sede_id,
                        options=PlazasState.opciones_sedes_catalogo,
                        error=PlazasState.error_sede_id,
                        hint="La plaza debe quedar relacionada a una sede para poder ocuparse.",
                    ),
                    form_select(
                        label="Categoría",
                        placeholder="Seleccione categoría",
                        value=PlazasState.form_categoria_puesto_id,
                        on_change=PlazasState.set_form_categoria_puesto_id,
                        options=PlazasState.opciones_categorias_catalogo,
                        error=PlazasState.error_categoria_puesto_id,
                        hint="Si la deja sin categoría, la plaza no podrá ocuparse.",
                    ),
                    form_date(
                        label="Fecha de inicio",
                        required=True,
                        value=PlazasState.form_fecha_inicio,
                        on_change=PlazasState.set_form_fecha_inicio,
                        error=PlazasState.error_fecha_inicio,
                    ),
                    form_date(
                        label="Fecha de fin",
                        value=PlazasState.form_fecha_fin,
                        on_change=PlazasState.set_form_fecha_fin,
                        hint="Déjelo vacío para vigencia indefinida.",
                    ),
                    form_input(
                        label="Salario mensual",
                        required=True,
                        placeholder="Ej: 15,000.00",
                        value=PlazasState.form_salario_mensual,
                        on_change=PlazasState.set_form_salario_mensual,
                        error=PlazasState.error_salario_mensual,
                    ),
                    form_input(
                        label="Código",
                        placeholder="Ej: PZA-001",
                        value=PlazasState.form_codigo,
                        on_change=PlazasState.set_form_codigo,
                        error=PlazasState.error_codigo,
                        max_length=20,
                    ),
                    form_select(
                        label="Estatus",
                        placeholder="Seleccione estatus",
                        value=PlazasState.form_estatus,
                        on_change=PlazasState.set_form_estatus,
                        options=PlazasState.opciones_estatus_form,
                    ),
                    form_textarea(
                        label="Notas",
                        placeholder="Información adicional sobre la plaza",
                        value=PlazasState.form_notas,
                        on_change=PlazasState.set_form_notas,
                        max_length=500,
                    ),
                    spacing="4",
                    width="100%",
                    padding_y="4",
                ),
            ),
            rx.hstack(
                boton_cancelar(on_click=PlazasState.cerrar_modal_plaza),
                boton_guardar(
                    texto="Guardar",
                    texto_guardando="Guardando...",
                    on_click=PlazasState.guardar_plaza,
                    saving=PlazasState.saving,
                    disabled=~PlazasState.puede_guardar,
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),
            max_width="460px",
        ),
        open=PlazasState.mostrar_modal_plaza,
        on_open_change=rx.noop,
    )


def modal_detalle_plaza() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Detalle de Plaza"),
            rx.dialog.description(
                rx.cond(
                    PlazasState.plaza_seleccionada,
                    rx.vstack(
                        rx.hstack(
                            rx.text(
                                "Plaza #",
                                PlazasState.plaza_seleccionada["numero_plaza"],
                                weight="bold",
                                size="4",
                            ),
                            rx.spacer(),
                            status_badge_reactive(
                                PlazasState.plaza_seleccionada["estatus"],
                                show_icon=True,
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.divider(),
                        rx.vstack(
                            rx.hstack(
                                rx.text("Contrato:", size="2", color="gray", width="120px"),
                                rx.text(PlazasState.contrato_codigo, size="2"),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Sede:", size="2", color="gray", width="120px"),
                                rx.text(
                                    PlazasState.plaza_seleccionada["sede_nombre"],
                                    size="2",
                                ),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Categoría:", size="2", color="gray", width="120px"),
                                rx.text(
                                    PlazasState.plaza_seleccionada["categoria_nombre"],
                                    size="2",
                                ),
                                width="100%",
                            ),
                            rx.cond(
                                PlazasState.plaza_seleccionada["codigo"],
                                rx.hstack(
                                    rx.text("Código:", size="2", color="gray", width="120px"),
                                    rx.text(PlazasState.plaza_seleccionada["codigo"], size="2"),
                                    width="100%",
                                ),
                                rx.fragment(),
                            ),
                            rx.hstack(
                                rx.text("Fecha inicio:", size="2", color="gray", width="120px"),
                                rx.text(
                                    PlazasState.plaza_seleccionada["fecha_inicio_fmt"],
                                    size="2",
                                ),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Fecha fin:", size="2", color="gray", width="120px"),
                                rx.text(
                                    PlazasState.plaza_seleccionada["fecha_fin_fmt"],
                                    size="2",
                                ),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Salario:", size="2", color="gray", width="120px"),
                                rx.text(
                                    PlazasState.plaza_seleccionada["salario_fmt"],
                                    size="2",
                                    weight="medium",
                                ),
                                width="100%",
                            ),
                            rx.cond(
                                PlazasState.plaza_seleccionada["empleado_nombre"],
                                rx.hstack(
                                    rx.text("Empleado:", size="2", color="gray", width="120px"),
                                    rx.text(
                                        PlazasState.plaza_seleccionada["empleado_nombre"],
                                        size="2",
                                    ),
                                    width="100%",
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                PlazasState.plaza_seleccionada["notas"],
                                rx.vstack(
                                    rx.text("Notas:", size="2", color="gray"),
                                    rx.text(
                                        PlazasState.plaza_seleccionada["notas"],
                                        size="2",
                                    ),
                                    width="100%",
                                    align_items="start",
                                ),
                                rx.fragment(),
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
                        PlazasState.puede_operar_plazas_en_contexto,
                        rx.button(
                            rx.icon("pencil", size=14),
                            "Editar",
                            on_click=lambda: PlazasState.abrir_modal_editar(
                                PlazasState.plaza_seleccionada
                            ),
                            color_scheme="blue",
                        ),
                        rx.fragment(),
                    ),
                    rx.fragment(),
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),
            max_width="460px",
        ),
        open=PlazasState.mostrar_modal_detalle,
        on_open_change=rx.noop,
    )


def modal_confirmar_cancelar() -> rx.Component:
    return modal_confirmar_accion(
        open=PlazasState.mostrar_modal_confirmar_cancelar,
        titulo="Cancelar Plaza",
        mensaje="Esta acción cancelará permanentemente la plaza seleccionada.",
        detalle_contenido=rx.cond(
            PlazasState.plaza_seleccionada,
            rx.text(
                "Plaza #",
                PlazasState.plaza_seleccionada["numero_plaza"],
                rx.cond(
                    PlazasState.plaza_seleccionada["codigo"],
                    rx.text(" (", PlazasState.plaza_seleccionada["codigo"], ")"),
                    rx.fragment(),
                ),
                weight="bold",
            ),
            rx.text(""),
        ),
        nota_adicional="Si la plaza tiene un empleado asignado, también será liberado.",
        on_confirmar=PlazasState.cancelar_plaza,
        on_cancelar=PlazasState.cerrar_confirmar_cancelar,
        loading=PlazasState.saving,
        texto_confirmar="Cancelar Plaza",
        color_confirmar="red",
        icono_detalle="triangle-alert",
        color_detalle="amber",
    )


def modal_asignar_empleado() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Asignar Empleado"),
            rx.dialog.description(
                rx.vstack(
                    rx.cond(
                        PlazasState.plaza_seleccionada,
                        rx.callout(
                            rx.vstack(
                                rx.hstack(
                                    rx.text("Plaza:", size="2", color="gray", width="80px"),
                                    rx.text(
                                        f"#{PlazasState.plaza_seleccionada['numero_plaza']}",
                                        weight="bold",
                                    ),
                                    width="100%",
                                ),
                                rx.hstack(
                                    rx.text("Categoría:", size="2", color="gray", width="80px"),
                                    rx.text(
                                        PlazasState.plaza_seleccionada["categoria_nombre"],
                                        weight="medium",
                                    ),
                                    width="100%",
                                ),
                                rx.hstack(
                                    rx.text("Sede:", size="2", color="gray", width="80px"),
                                    rx.text(
                                        PlazasState.plaza_seleccionada["sede_nombre"],
                                        weight="medium",
                                    ),
                                    width="100%",
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            icon="briefcase",
                            color_scheme="blue",
                            size="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
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
            rx.hstack(
                boton_cancelar(on_click=PlazasState.cerrar_modal_asignar_empleado),
                boton_guardar(
                    texto="Asignar",
                    texto_guardando="Asignando...",
                    on_click=PlazasState.confirmar_asignar_empleado,
                    saving=PlazasState.saving,
                    disabled=~PlazasState.puede_asignar_empleado,
                    color_scheme="green",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),
            max_width="460px",
        ),
        open=PlazasState.mostrar_modal_asignar_empleado,
        on_open_change=rx.noop,
    )


def modal_crear_lote() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Asignar Plazas"),
            rx.dialog.description(
                rx.vstack(
                    rx.callout(
                        rx.vstack(
                            rx.hstack(
                                rx.text("Contrato:", size="2", color="gray", width="80px"),
                                rx.text(PlazasState.contrato_codigo, size="2", weight="medium"),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Disponibles:", size="2", color="gray", width="80px"),
                                rx.text(
                                    PlazasState.vacantes_sin_categoria_disponibles,
                                    size="2",
                                    weight="medium",
                                ),
                                width="100%",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        icon="tags",
                        color_scheme="blue",
                        size="1",
                        width="100%",
                    ),
                    form_select(
                        label="Sede destino",
                        required=True,
                        placeholder="Seleccione sede",
                        value=PlazasState.form_sede_id,
                        on_change=PlazasState.set_form_sede_id,
                        options=PlazasState.opciones_sedes_catalogo,
                        error=PlazasState.error_sede_id,
                        hint="La sede se asignará a todas las plazas del lote.",
                    ),
                    form_select(
                        label="Categoría destino",
                        required=True,
                        placeholder="Seleccione categoría",
                        value=PlazasState.form_categoria_puesto_id,
                        on_change=PlazasState.set_form_categoria_puesto_id,
                        options=PlazasState.opciones_categorias_catalogo,
                        error=PlazasState.error_categoria_puesto_id,
                    ),
                    form_input(
                        label="Cantidad de plazas",
                        required=True,
                        type="number",
                        min="1",
                        value=PlazasState.form_cantidad,
                        on_change=PlazasState.set_form_cantidad,
                        error=PlazasState.error_cantidad,
                    ),
                    form_input(
                        label="Salario mensual",
                        placeholder="Opcional, se aplicará al lote",
                        value=PlazasState.form_salario_mensual,
                        on_change=PlazasState.set_form_salario_mensual,
                        error=PlazasState.error_salario_mensual,
                        hint="Si lo deja vacío, se conserva el salario actual de cada plaza.",
                    ),
                    form_input(
                        label="Prefijo de código",
                        placeholder="Ej: JAR",
                        value=PlazasState.form_prefijo_codigo,
                        on_change=PlazasState.set_form_prefijo_codigo,
                        hint="Si se captura, generará códigos como PREFIJO-001.",
                        max_length=10,
                    ),
                    spacing="4",
                    width="100%",
                    padding_y="4",
                ),
            ),
            rx.hstack(
                boton_cancelar(on_click=PlazasState.cerrar_modal_crear_lote),
                boton_guardar(
                    texto="Asignar",
                    texto_guardando="Aplicando...",
                    on_click=PlazasState.crear_plazas_lote,
                    saving=PlazasState.saving,
                    disabled=~PlazasState.puede_guardar_categorizacion_lote,
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),
            max_width="460px",
        ),
        open=PlazasState.mostrar_modal_crear_lote,
        on_open_change=rx.noop,
    )
