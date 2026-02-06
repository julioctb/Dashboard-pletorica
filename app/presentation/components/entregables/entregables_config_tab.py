"""
Componente de Configuración de Entregables para Contratos.
Se usa como una pestaña/tab dentro del modal de creación/edición de contrato.
"""

import reflex as rx

from app.presentation.pages.contratos.entregables_config_state import EntregablesConfigState
from app.presentation.components.ui import form_select, form_input, form_textarea
from app.presentation.theme import Colors, Spacing, Radius


# =============================================================================
# LISTA DE TIPOS CONFIGURADOS
# =============================================================================
def _card_tipo_configurado(tipo: dict) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(tipo["tipo_label"], size="2", weight="medium"),
                rx.cond(
                    tipo["requerido"],
                    rx.badge("Requerido", color_scheme="red", size="1"),
                    rx.badge("Opcional", color_scheme="gray", size="1"),
                ),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.icon("repeat", size=12, color=Colors.TEXT_MUTED),
                rx.text(tipo["periodicidad_label"], size="1", color=Colors.TEXT_MUTED),
                spacing="1",
            ),
            rx.cond(
                tipo["descripcion"],
                rx.text(tipo["descripcion"], size="1", color=Colors.TEXT_SECONDARY, no_of_lines=1),
                rx.fragment(),
            ),
            spacing="1",
            align="start",
            flex="1",
        ),
        rx.hstack(
            rx.button(
                rx.icon("pencil", size=14),
                size="1",
                variant="ghost",
                on_click=lambda: EntregablesConfigState.abrir_modal_editar(tipo["id"]),
            ),
            rx.button(
                rx.icon("trash-2", size=14),
                size="1",
                variant="ghost",
                color_scheme="red",
                on_click=lambda: EntregablesConfigState.eliminar_tipo(tipo["id"]),
            ),
            spacing="1",
        ),
        padding=Spacing.SM,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.MD,
        width="100%",
        align="center",
    )


def _lista_tipos_configurados() -> rx.Component:
    return rx.cond(
        EntregablesConfigState.tiene_tipos,
        rx.vstack(
            rx.foreach(EntregablesConfigState.tipos_configurados, _card_tipo_configurado),
            spacing="2",
            width="100%",
        ),
        rx.center(
            rx.vstack(
                rx.icon("package", size=32, color=Colors.TEXT_MUTED),
                rx.text("No hay tipos de entregable configurados", size="2", color=Colors.TEXT_MUTED),
                rx.text("Agregue los tipos de entregable que la empresa debe entregar", size="1", color=Colors.TEXT_MUTED),
                spacing="2",
                align="center",
            ),
            padding="6",
        ),
    )


# =============================================================================
# MODAL DE AGREGAR/EDITAR TIPO
# =============================================================================
def _modal_tipo_entregable() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(EntregablesConfigState.titulo_modal),
            rx.dialog.description(
                rx.vstack(
                    form_select(
                        label="Tipo de entregable",
                        required=True,
                        placeholder="Seleccione tipo",
                        value=EntregablesConfigState.form_tipo_entregable,
                        on_change=EntregablesConfigState.set_form_tipo_entregable,
                        options=rx.cond(
                            EntregablesConfigState.es_edicion_tipo,
                            EntregablesConfigState.opciones_tipo_entregable,
                            EntregablesConfigState.tipos_disponibles_para_agregar,
                        ),
                        error=EntregablesConfigState.error_tipo,
                        disabled=EntregablesConfigState.es_edicion_tipo,
                    ),
                    form_select(
                        label="Periodicidad",
                        required=True,
                        value=EntregablesConfigState.form_periodicidad,
                        on_change=EntregablesConfigState.set_form_periodicidad,
                        options=EntregablesConfigState.opciones_periodicidad,
                    ),
                    rx.hstack(
                        rx.switch(checked=EntregablesConfigState.form_requerido, on_change=EntregablesConfigState.set_form_requerido),
                        rx.text("Es requerido para aprobar el período", size="2"),
                        spacing="2",
                        align="center",
                    ),
                    form_input(
                        label="Descripción personalizada",
                        placeholder="Ej: Fotos del área de limpieza",
                        value=EntregablesConfigState.form_descripcion,
                        on_change=EntregablesConfigState.set_form_descripcion,
                        hint="Nombre personalizado para este tipo (opcional)",
                    ),
                    form_textarea(
                        label="Instrucciones para el cliente",
                        placeholder="Ej: Subir al menos 5 fotos de diferentes áreas...",
                        value=EntregablesConfigState.form_instrucciones,
                        on_change=EntregablesConfigState.set_form_instrucciones,
                        hint="Indicaciones de qué debe incluir el entregable (opcional)",
                    ),
                    spacing="4",
                    width="100%",
                    padding_y="3",
                ),
            ),
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EntregablesConfigState.cerrar_modal_tipo,
                ),
                rx.button(
                    "Guardar",
                    on_click=EntregablesConfigState.guardar_tipo,
                    loading=EntregablesConfigState.guardando,
                    disabled=~EntregablesConfigState.puede_guardar_tipo,
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
            max_width="500px",
        ),
        open=EntregablesConfigState.mostrar_modal_tipo,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


# =============================================================================
# TAB/SECCIÓN PRINCIPAL
# =============================================================================
def tab_entregables_config() -> rx.Component:
    """
    Pestaña de configuración de entregables para el modal de contrato.
    Uso: rx.tabs.content(tab_entregables_config(), value="entregables")
    """
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Tipos de Entregable", size="3", weight="bold"),
                rx.text("Configure qué debe entregar la empresa proveedora", size="2", color=Colors.TEXT_SECONDARY),
                spacing="0",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Agregar tipo",
                size="2",
                on_click=EntregablesConfigState.abrir_modal_agregar,
                disabled=~EntregablesConfigState.puede_agregar_tipo,
            ),
            width="100%",
            align="end",
        ),
        rx.divider(),
        rx.cond(EntregablesConfigState.cargando, rx.center(rx.spinner(size="2"), padding="6"), _lista_tipos_configurados()),
        _modal_tipo_entregable(),
        spacing="4",
        width="100%",
    )


def seccion_entregables_contrato() -> rx.Component:
    """
    Sección de entregables para mostrar dentro del modal de contrato. Versión compacta sin tabs.
    """
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("package-check", size=18, color=Colors.PRIMARY),
                rx.text("Entregables Requeridos", size="3", weight="bold"),
                rx.spacer(),
                rx.cond(
                    EntregablesConfigState.puede_agregar_tipo,
                    rx.button(rx.icon("plus", size=12), "Agregar", size="1", variant="soft", on_click=EntregablesConfigState.abrir_modal_agregar),
                    rx.fragment(),
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                EntregablesConfigState.cargando,
                rx.center(rx.spinner(size="2"), padding="4"),
                rx.cond(
                    EntregablesConfigState.tiene_tipos,
                    rx.vstack(rx.foreach(EntregablesConfigState.tipos_configurados, _card_tipo_configurado), spacing="2", width="100%"),
                    rx.center(rx.text("Sin tipos configurados", size="2", color=Colors.TEXT_MUTED), padding="4"),
                ),
            ),
            spacing="3",
            width="100%",
        ),
        _modal_tipo_entregable(),
        padding="4",
    )
