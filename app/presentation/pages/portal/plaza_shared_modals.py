"""Modales reutilizables para operar plazas desde portal."""

import reflex as rx

from app.presentation.components.ui import (
    feedback_callout,
    form_input,
    form_select,
)
from app.presentation.components.ui.modals import modal_formulario
from app.presentation.theme import Colors, Typography


def modal_asignacion_plaza(state_cls) -> rx.Component:
    return modal_formulario(
        open=state_cls.mostrar_modal_asignacion_plaza,
        titulo=state_cls.titulo_modal_asignacion_plaza,
        descripcion=state_cls.descripcion_modal_asignacion_plaza,
        icono="users",
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
        on_guardar=state_cls.confirmar_asignacion_plaza,
        on_cancelar=state_cls.cerrar_modal_asignacion_plaza,
        puede_guardar=state_cls.puede_confirmar_asignacion_plaza,
        loading=state_cls.saving,
        texto_guardar=state_cls.texto_guardar_asignacion_plaza,
        color_guardar=Colors.PORTAL_ACCENT_SCHEME,
        max_width="460px",
        contenido=rx.vstack(
            feedback_callout(
                "La plaza conserva su sede y categoria. Si ya tiene empleado, primero debe liberarse o reasignarse para mantener el historial.",
                "info",
            ),
            form_select(
                label="Empleado",
                required=True,
                placeholder=state_cls.placeholder_empleado_plaza,
                value=state_cls.empleado_seleccionado_plaza_id,
                on_change=state_cls.set_empleado_seleccionado_plaza_id,
                options=state_cls.opciones_empleados_disponibles_plaza,
                disabled=state_cls.cargando_empleados_plaza,
                hint=rx.cond(
                    state_cls.tiene_empleados_disponibles_plaza,
                    "",
                    "Si no hay empleados disponibles, primero capture uno nuevo.",
                ),
                label_variant="portal",
                style_variant="portal",
            ),
            rx.cond(
                state_cls.cargando_empleados_plaza,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text(
                        "Cargando empleados disponibles...",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.fragment(),
            ),
            rx.cond(
                ~state_cls.tiene_empleados_disponibles_plaza & ~state_cls.cargando_empleados_plaza,
                rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo empleado",
                    on_click=[
                        state_cls.cerrar_modal_asignacion_plaza,
                        state_cls.abrir_modal_crear,
                    ],
                    variant="outline",
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    align_self="start",
                ),
                rx.fragment(),
            ),
            spacing="4",
            width="100%",
        ),
    )


def modal_categoria_plaza(state_cls) -> rx.Component:
    return modal_formulario(
        open=state_cls.mostrar_modal_categoria_plaza,
        titulo=state_cls.titulo_modal_categoria_plaza,
        descripcion=state_cls.descripcion_modal_categoria_plaza,
        icono="tags",
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
        on_guardar=state_cls.confirmar_categoria_plaza,
        on_cancelar=state_cls.cerrar_modal_categoria_plaza,
        puede_guardar=state_cls.puede_confirmar_categoria_plaza,
        loading=state_cls.saving,
        texto_guardar=state_cls.texto_guardar_categoria_plaza,
        color_guardar=Colors.PORTAL_ACCENT_SCHEME,
        max_width="460px",
        contenido=rx.vstack(
            feedback_callout(
                "Cambiar la categoria no sustituye al empleado. Si la plaza esta vacante y la categoria tiene sueldo base configurado, ese sueldo se usa como referencia inicial.",
                "info",
            ),
            form_select(
                label="Categoria",
                required=True,
                placeholder="Seleccionar categoria...",
                value=state_cls.categoria_seleccionada_plaza_id,
                on_change=state_cls.set_categoria_seleccionada_plaza_id,
                options=state_cls.opciones_categoria_plaza,
                disabled=state_cls.cargando_categorias_plaza,
                hint=state_cls.hint_categoria_plaza,
                label_variant="portal",
                style_variant="portal",
            ),
            spacing="4",
            width="100%",
        ),
    )


def modal_salario_plaza(state_cls) -> rx.Component:
    return modal_formulario(
        open=state_cls.mostrar_modal_salario_plaza,
        titulo=state_cls.titulo_modal_salario_plaza,
        descripcion=state_cls.descripcion_modal_salario_plaza,
        icono="badge-dollar-sign",
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
        on_guardar=state_cls.confirmar_salario_plaza,
        on_cancelar=state_cls.cerrar_modal_salario_plaza,
        puede_guardar=state_cls.puede_confirmar_salario_plaza,
        loading=state_cls.saving,
        texto_guardar=state_cls.texto_guardar_salario_plaza,
        color_guardar=Colors.PORTAL_ACCENT_SCHEME,
        max_width="460px",
        contenido=rx.vstack(
            feedback_callout(
                "Este sueldo se guarda en la plaza y no modifica el sueldo base de la categoria ni el costo contractual del contrato.",
                "info",
            ),
            form_input(
                label="Salario mensual",
                required=True,
                placeholder="Ej: $ 15,000.00",
                value=state_cls.form_salario_plaza,
                on_change=state_cls.set_form_salario_plaza,
                on_blur=state_cls.validar_salario_plaza_campo,
                error=state_cls.error_salario_plaza,
                hint=state_cls.hint_salario_plaza,
                label_variant="portal",
                style_variant="portal",
            ),
            spacing="4",
            width="100%",
        ),
    )


def modal_asignacion_sede_plaza(state_cls) -> rx.Component:
    return modal_formulario(
        open=state_cls.mostrar_modal_sede_plaza,
        titulo=state_cls.titulo_modal_sede_plaza,
        descripcion=state_cls.descripcion_modal_sede_plaza,
        icono="map-pin",
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
        on_guardar=state_cls.confirmar_sede_plaza,
        on_cancelar=state_cls.cerrar_modal_sede_plaza,
        puede_guardar=state_cls.puede_confirmar_sede_plaza,
        loading=state_cls.saving,
        texto_guardar=state_cls.texto_guardar_sede_plaza,
        color_guardar=Colors.PORTAL_ACCENT_SCHEME,
        max_width="420px",
        contenido=rx.vstack(
            feedback_callout(
                "Actualizar la sede no modifica la categoria ni la asignacion del empleado.",
                "info",
            ),
            form_select(
                label="Sede",
                required=True,
                placeholder="Seleccionar sede...",
                value=state_cls.sede_seleccionada_plaza_id,
                on_change=state_cls.set_sede_seleccionada_plaza_id,
                options=state_cls.opciones_sedes_plaza,
                label_variant="portal",
                style_variant="portal",
            ),
            spacing="4",
            width="100%",
        ),
    )


def modal_reasignacion_plaza(state_cls) -> rx.Component:
    return modal_formulario(
        open=state_cls.mostrar_modal_reasignacion_plaza,
        titulo=state_cls.titulo_modal_reasignacion_plaza,
        descripcion=state_cls.descripcion_modal_reasignacion_plaza,
        icono="shuffle",
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
        on_guardar=state_cls.confirmar_reasignacion_plaza,
        on_cancelar=state_cls.cerrar_modal_reasignacion_plaza,
        puede_guardar=state_cls.puede_confirmar_reasignacion_plaza,
        loading=state_cls.saving,
        texto_guardar="Reasignar plaza",
        color_guardar=Colors.PORTAL_ACCENT_SCHEME,
        max_width="500px",
        contenido=rx.vstack(
            feedback_callout(
                "La plaza origen se libera y el movimiento queda registrado en historial laboral.",
                "info",
            ),
            form_select(
                label="Plaza destino",
                required=True,
                placeholder="Seleccionar plaza vacante...",
                value=state_cls.plaza_destino_reasignacion_id,
                on_change=state_cls.set_plaza_destino_reasignacion_id,
                options=state_cls.opciones_reasignacion_plaza,
                hint=state_cls.hint_reasignacion_plaza,
                label_variant="portal",
                style_variant="portal",
            ),
            spacing="4",
            width="100%",
        ),
    )
