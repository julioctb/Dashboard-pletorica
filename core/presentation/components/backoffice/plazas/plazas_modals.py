"""Modales del módulo de plazas."""

import reflex as rx

from core.presentation.components.ui import (
    form_field,
    modal_detalle,
    modal_formulario,
    status_badge_reactive,
)
from core.presentation.components.ui.form_input import (
    form_date,
    form_input,
    form_select,
    form_textarea,
)
from core.presentation.components.ui.modals import modal_confirmar_accion
from core.presentation.pages.backoffice.plazas.plazas_state import PlazasState
from core.presentation.theme import Spacing


def _modal_body(*children: rx.Component) -> rx.Component:
    return rx.vstack(
        *children,
        spacing="4",
        width="100%",
    )


def _contenido_modal_plaza() -> rx.Component:
    return _modal_body(
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
        form_select(
            label="Tipo de jornada",
            required=True,
            value=PlazasState.form_tipo_jornada,
            on_change=PlazasState.set_form_tipo_jornada,
            options=[
                {"value": "COMPLETA", "label": "Jornada completa"},
                {"value": "MEDIA_JORNADA", "label": "Media jornada"},
                {"value": "POR_HORAS", "label": "Por horas"},
            ],
            hint="Completa fija factor 1.00 y media jornada fija factor 0.50.",
        ),
        form_input(
            label="Factor de jornada",
            required=True,
            placeholder="Ej: 1.00 o 0.75",
            value=PlazasState.form_factor_jornada,
            on_change=PlazasState.set_form_factor_jornada,
            error=PlazasState.error_factor_jornada,
            hint="Solo aplica libremente para plazas por horas.",
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
    )


def modal_plaza() -> rx.Component:
    return modal_formulario(
        open=PlazasState.mostrar_modal_plaza,
        titulo="Editar Plaza",
        descripcion="Actualice la sede, categoría y condiciones operativas de la plaza.",
        contenido=_contenido_modal_plaza(),
        on_guardar=PlazasState.guardar_plaza,
        on_cancelar=PlazasState.cerrar_modal_plaza,
        puede_guardar=PlazasState.puede_guardar,
        loading=PlazasState.saving,
        texto_guardar="Guardar",
        texto_guardando="Guardando...",
        max_width="460px",
    )


def _contenido_detalle_plaza() -> rx.Component:
    return rx.cond(
        PlazasState.plaza_seleccionada,
        _modal_body(
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
                rx.hstack(
                    rx.text("Jornada:", size="2", color="gray", width="120px"),
                    rx.text(
                        PlazasState.plaza_seleccionada["tipo_jornada_label"],
                        size="2",
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Factor:", size="2", color="gray", width="120px"),
                    rx.text(
                        PlazasState.plaza_seleccionada["factor_jornada"],
                        size="2",
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
        ),
        rx.text("No hay plaza seleccionada"),
    )


def modal_detalle_plaza() -> rx.Component:
    return modal_detalle(
        open=PlazasState.mostrar_modal_detalle,
        titulo="Detalle de Plaza",
        contenido=_contenido_detalle_plaza(),
        on_cerrar=PlazasState.cerrar_modal_detalle,
        boton_accion=rx.cond(
            PlazasState.plaza_seleccionada & PlazasState.puede_operar_plazas_en_contexto,
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
        max_width="460px",
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
        texto_confirmando="Cancelando...",
        color_confirmar="red",
        icono_detalle="triangle-alert",
        color_detalle="amber",
    )


def _contenido_asignar_empleado() -> rx.Component:
    return _modal_body(
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
        form_field(
            label="Seleccionar empleado",
            required=True,
            control=rx.cond(
                PlazasState.cargando_empleados,
                rx.box(
                    rx.hstack(
                        rx.spinner(size="1"),
                        rx.text("Cargando empleados...", size="2", color="gray"),
                        spacing="2",
                        align="center",
                    ),
                    width="100%",
                    padding_y=Spacing.SM,
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
        ),
    )


def modal_asignar_empleado() -> rx.Component:
    return modal_formulario(
        open=PlazasState.mostrar_modal_asignar_empleado,
        titulo="Asignar Empleado",
        descripcion="Seleccione el empleado que ocupará la plaza actual.",
        contenido=_contenido_asignar_empleado(),
        on_guardar=PlazasState.confirmar_asignar_empleado,
        on_cancelar=PlazasState.cerrar_modal_asignar_empleado,
        puede_guardar=PlazasState.puede_asignar_empleado,
        loading=PlazasState.saving,
        texto_guardar="Asignar",
        texto_guardando="Asignando...",
        max_width="460px",
    )


def _contenido_asignacion_lote() -> rx.Component:
    return _modal_body(
        rx.callout(
            rx.vstack(
                rx.hstack(
                    rx.text("Contrato:", size="2", color="gray", width="90px"),
                    rx.text(PlazasState.contrato_codigo, size="2", weight="medium"),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Modo:", size="2", color="gray", width="90px"),
                    rx.text(
                        PlazasState.titulo_modo_asignacion_lote,
                        size="2",
                        weight="medium",
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Disponibles:", size="2", color="gray", width="90px"),
                    rx.text(
                        PlazasState.disponibles_asignacion_lote,
                        size="2",
                        weight="medium",
                    ),
                    width="100%",
                ),
                rx.text(
                    PlazasState.descripcion_modo_asignacion_lote,
                    size="2",
                    color="gray",
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
            hint=PlazasState.hint_sede_asignacion_lote,
        ),
        rx.cond(
            PlazasState.es_modo_sede_categoria_lote,
            form_select(
                label="Categoría destino",
                required=True,
                placeholder="Seleccione categoría",
                value=PlazasState.form_categoria_puesto_id,
                on_change=PlazasState.set_form_categoria_puesto_id,
                options=PlazasState.opciones_categorias_catalogo,
                error=PlazasState.error_categoria_puesto_id,
            ),
            rx.fragment(),
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
        rx.cond(
            PlazasState.es_modo_sede_categoria_lote,
            form_input(
                label="Salario mensual",
                placeholder="Opcional, se aplicará al lote",
                value=PlazasState.form_salario_mensual,
                on_change=PlazasState.set_form_salario_mensual,
                error=PlazasState.error_salario_mensual,
                hint="Si lo deja vacío, se conserva el salario actual de cada plaza.",
            ),
            rx.fragment(),
        ),
        rx.cond(
            PlazasState.es_modo_sede_categoria_lote,
            form_input(
                label="Prefijo de código",
                placeholder="Ej: JAR",
                value=PlazasState.form_prefijo_codigo,
                on_change=PlazasState.set_form_prefijo_codigo,
                hint="Si se captura, generará códigos como PREFIJO-001.",
                max_length=10,
            ),
            rx.fragment(),
        ),
    )


def _contenido_modal_crear_lote() -> rx.Component:
    return rx.cond(
        PlazasState.mostrar_tabs_asignacion_lote,
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Sede + categoría", value="sede_categoria"),
                rx.tabs.trigger("Solo sede", value="solo_sede"),
            ),
            rx.tabs.content(
                _contenido_asignacion_lote(),
                value="sede_categoria",
                padding_top=Spacing.BASE,
            ),
            rx.tabs.content(
                _contenido_asignacion_lote(),
                value="solo_sede",
                padding_top=Spacing.BASE,
            ),
            value=PlazasState.modo_asignacion_lote,
            on_change=PlazasState.set_modo_asignacion_lote,
            width="100%",
        ),
        _contenido_asignacion_lote(),
    )


def modal_crear_lote() -> rx.Component:
    return modal_formulario(
        open=PlazasState.mostrar_modal_crear_lote,
        titulo="Asignar Plazas",
        descripcion="Configure el modo de asignación y aplique la operación sobre las plazas disponibles.",
        contenido=_contenido_modal_crear_lote(),
        on_guardar=PlazasState.crear_plazas_lote,
        on_cancelar=PlazasState.cerrar_modal_crear_lote,
        puede_guardar=PlazasState.puede_guardar_asignacion_lote,
        loading=PlazasState.saving,
        texto_guardar="Asignar",
        texto_guardando="Aplicando...",
        max_width="460px",
    )
