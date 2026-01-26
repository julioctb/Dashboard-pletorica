"""Modales para el modulo de Requisiciones (detalle, confirmar, adjudicar)."""
import reflex as rx
from app.presentation.components.ui.form_input import form_select
from app.presentation.pages.requisiciones.requisiciones_state import RequisicionesState
from app.presentation.components.requisiciones.requisicion_estado_badge import estado_requisicion_badge


# =============================================================================
# MODAL DE DETALLE
# =============================================================================

def modal_detalle_requisicion() -> rx.Component:
    """Modal para mostrar detalles de una requisicion."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                RequisicionesState.requisicion_seleccionada,
                rx.vstack(
                    rx.dialog.title("Detalle de Requisicion"),

                    # Info principal
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.text("Informacion General", weight="bold", size="4"),
                                rx.spacer(),
                                rx.badge(
                                    RequisicionesState.requisicion_seleccionada["numero_requisicion"],
                                    color_scheme="blue",
                                    size="2",
                                    variant="solid",
                                ),
                                align="center",
                                width="100%",
                            ),
                            rx.grid(
                                rx.vstack(
                                    rx.text("Estado:", weight="bold", size="2"),
                                    estado_requisicion_badge(
                                        RequisicionesState.requisicion_seleccionada["estado"],
                                        show_icon=True,
                                    ),
                                    align="start",
                                ),
                                rx.vstack(
                                    rx.text("Tipo:", weight="bold", size="2"),
                                    rx.text(
                                        RequisicionesState.requisicion_seleccionada["tipo_contratacion"],
                                        size="2",
                                    ),
                                    align="start",
                                ),
                                rx.vstack(
                                    rx.text("Fecha:", weight="bold", size="2"),
                                    rx.text(
                                        RequisicionesState.requisicion_seleccionada["fecha_elaboracion"],
                                        size="2",
                                    ),
                                    align="start",
                                ),
                                rx.vstack(
                                    rx.text("Dependencia:", weight="bold", size="2"),
                                    rx.text(
                                        RequisicionesState.requisicion_seleccionada["dependencia_requirente"],
                                        size="2",
                                    ),
                                    align="start",
                                ),
                                columns="2",
                                spacing="4",
                            ),
                            spacing="3",
                        ),
                        width="100%",
                    ),

                    # Objeto de contratacion
                    rx.cond(
                        RequisicionesState.requisicion_seleccionada["objeto_contratacion"],
                        rx.card(
                            rx.vstack(
                                rx.text("Objeto de Contratacion", weight="bold", size="4"),
                                rx.text(
                                    RequisicionesState.requisicion_seleccionada["objeto_contratacion"],
                                    size="2",
                                ),
                                spacing="2",
                            ),
                            width="100%",
                        ),
                    ),

                    # Empresa adjudicada (si aplica)
                    rx.cond(
                        RequisicionesState.requisicion_seleccionada["empresa_nombre"],
                        rx.card(
                            rx.vstack(
                                rx.text("Empresa Adjudicada", weight="bold", size="4"),
                                rx.text(
                                    RequisicionesState.requisicion_seleccionada["empresa_nombre"],
                                    size="2",
                                ),
                                spacing="2",
                            ),
                            width="100%",
                        ),
                    ),

                    # Botones
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cerrar", variant="soft", size="2"),
                        ),
                        rx.cond(
                            RequisicionesState.requisicion_seleccionada["estado"] == "BORRADOR",
                            rx.button(
                                "Editar",
                                on_click=lambda: RequisicionesState.abrir_modal_editar(
                                    RequisicionesState.requisicion_seleccionada,
                                ),
                                size="2",
                            ),
                        ),
                        spacing="2",
                        justify="end",
                    ),

                    spacing="4",
                    width="100%",
                ),
            ),
            max_width="600px",
        ),
        open=RequisicionesState.mostrar_modal_detalle,
        on_open_change=RequisicionesState.set_mostrar_modal_detalle,
    )


# =============================================================================
# MODAL CONFIRMAR ELIMINAR
# =============================================================================

def modal_confirmar_eliminar_requisicion() -> rx.Component:
    """Modal de confirmacion para eliminar requisicion."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Eliminar Requisicion"),
            rx.alert_dialog.description(
                rx.cond(
                    RequisicionesState.requisicion_seleccionada,
                    rx.vstack(
                        rx.text(
                            "Esta seguro que desea eliminar la requisicion ",
                            rx.text(
                                RequisicionesState.requisicion_seleccionada["numero_requisicion"],
                                weight="bold",
                            ),
                            "?",
                        ),
                        rx.text(
                            "Esta accion no se puede deshacer.",
                            size="2",
                            color="gray",
                        ),
                        spacing="2",
                    ),
                    "Esta seguro que desea eliminar esta requisicion?",
                ),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "No, mantener",
                        variant="soft",
                        on_click=RequisicionesState.cerrar_confirmar_eliminar,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        rx.cond(
                            RequisicionesState.saving,
                            rx.hstack(rx.spinner(size="1"), "Eliminando...", spacing="2"),
                            "Si, eliminar",
                        ),
                        color_scheme="red",
                        on_click=RequisicionesState.eliminar_requisicion,
                        disabled=RequisicionesState.saving,
                    ),
                ),
                spacing="3",
                justify="end",
            ),
        ),
        open=RequisicionesState.mostrar_modal_confirmar_eliminar,
    )


# =============================================================================
# MODAL CONFIRMAR CAMBIO DE ESTADO
# =============================================================================

ACCIONES_TEXTO = {
    "enviar": ("Enviar Requisicion", "La requisicion sera enviada para revision.", "blue"),
    "revisar": ("Iniciar Revision", "La requisicion pasara a estado EN REVISION.", "orange"),
    "aprobar": ("Aprobar Requisicion", "La requisicion sera aprobada.", "green"),
    "devolver": ("Devolver a Borrador", "La requisicion regresara a estado BORRADOR.", "orange"),
    "cancelar": ("Cancelar Requisicion", "La requisicion sera cancelada. Esta accion no se puede revertir.", "red"),
}


def modal_confirmar_estado() -> rx.Component:
    """Modal de confirmacion para cambio de estado."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(
                rx.match(
                    RequisicionesState.accion_estado_pendiente,
                    ("enviar", "Enviar Requisicion"),
                    ("revisar", "Iniciar Revision"),
                    ("aprobar", "Aprobar Requisicion"),
                    ("devolver", "Devolver a Borrador"),
                    ("cancelar", "Cancelar Requisicion"),
                    "Confirmar Accion",
                ),
            ),
            rx.alert_dialog.description(
                rx.vstack(
                    rx.cond(
                        RequisicionesState.requisicion_seleccionada,
                        rx.text(
                            "Requisicion: ",
                            rx.text(
                                RequisicionesState.requisicion_seleccionada["numero_requisicion"],
                                weight="bold",
                            ),
                        ),
                    ),
                    rx.text(
                        rx.match(
                            RequisicionesState.accion_estado_pendiente,
                            ("enviar", "La requisicion sera enviada para revision."),
                            ("revisar", "La requisicion pasara a estado EN REVISION."),
                            ("aprobar", "La requisicion sera aprobada."),
                            ("devolver", "La requisicion regresara a estado BORRADOR."),
                            ("cancelar", "La requisicion sera cancelada. Esta accion no se puede revertir."),
                            "Confirme la accion.",
                        ),
                        size="2",
                        color="gray",
                    ),
                    spacing="2",
                ),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        on_click=RequisicionesState.cerrar_confirmar_estado,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        rx.cond(
                            RequisicionesState.saving,
                            rx.hstack(rx.spinner(size="1"), "Procesando...", spacing="2"),
                            "Confirmar",
                        ),
                        color_scheme=rx.match(
                            RequisicionesState.accion_estado_pendiente,
                            ("enviar", "blue"),
                            ("revisar", "orange"),
                            ("aprobar", "green"),
                            ("devolver", "orange"),
                            ("cancelar", "red"),
                            "blue",
                        ),
                        on_click=RequisicionesState.confirmar_cambio_estado,
                        disabled=RequisicionesState.saving,
                    ),
                ),
                spacing="3",
                justify="end",
            ),
        ),
        open=RequisicionesState.mostrar_modal_confirmar_estado,
    )


# =============================================================================
# MODAL ADJUDICAR
# =============================================================================

def modal_adjudicar_requisicion() -> rx.Component:
    """Modal para adjudicar requisicion a una empresa."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Adjudicar Requisicion"),
            rx.dialog.description(
                rx.cond(
                    RequisicionesState.requisicion_seleccionada,
                    rx.text(
                        "Adjudicar requisicion ",
                        rx.text(
                            RequisicionesState.requisicion_seleccionada["numero_requisicion"],
                            weight="bold",
                        ),
                        " a una empresa.",
                    ),
                    "Seleccione la empresa y fecha de adjudicacion.",
                ),
                margin_bottom="16px",
            ),

            rx.vstack(
                form_select(
                    placeholder="Empresa *",
                    value=RequisicionesState.form_adjudicar_empresa_id,
                    on_change=RequisicionesState.set_form_adjudicar_empresa_id,
                    options=RequisicionesState.empresas_opciones,
                ),
                rx.vstack(
                    rx.text("Fecha de adjudicacion *", size="2", color="gray"),
                    rx.input(
                        type="date",
                        value=RequisicionesState.form_adjudicar_fecha,
                        on_change=RequisicionesState.set_form_adjudicar_fecha,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),

            rx.box(height="16px"),

            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        on_click=RequisicionesState.cerrar_modal_adjudicar,
                    ),
                ),
                rx.button(
                    rx.cond(
                        RequisicionesState.saving,
                        rx.hstack(rx.spinner(size="1"), "Adjudicando...", spacing="2"),
                        "Adjudicar",
                    ),
                    color_scheme="purple",
                    on_click=RequisicionesState.adjudicar_requisicion,
                    disabled=RequisicionesState.saving,
                ),
                spacing="3",
                justify="end",
            ),

            max_width="450px",
        ),
        open=RequisicionesState.mostrar_modal_adjudicar,
    )
