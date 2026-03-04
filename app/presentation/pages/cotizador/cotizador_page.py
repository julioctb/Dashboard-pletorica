"""
Página principal del módulo Cotizador.

Lista las cotizaciones de la empresa y permite crear nuevas.
Ruta: /cotizador
"""
import reflex as rx

from app.presentation.theme import Colors, Spacing, Typography
from app.presentation.components.ui import (
    page_header,
    form_input,
    form_date,
    form_row,
    botones_modal,
)
from app.presentation.pages.cotizador.cotizador_state import CotizadorState
from app.presentation.pages.cotizador.cotizador_components import (
    tabla_cotizaciones,
)


def _modal_crear_cotizacion() -> rx.Component:
    """Modal para crear una nueva cotización."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nueva Cotización"),
            rx.dialog.description(
                "Define el período y los datos del destinatario.",
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
            rx.vstack(
                form_row(
                    form_date(
                        label="Fecha inicio período",
                        required=True,
                        value=CotizadorState.form_fecha_inicio,
                        on_change=CotizadorState.set_form_fecha_inicio,
                        on_blur=CotizadorState.validar_fecha_inicio_campo,
                        error=CotizadorState.error_fecha_inicio,
                    ),
                    form_date(
                        label="Fecha fin período",
                        required=True,
                        value=CotizadorState.form_fecha_fin,
                        on_change=CotizadorState.set_form_fecha_fin,
                        on_blur=CotizadorState.validar_fecha_fin_campo,
                        error=CotizadorState.error_fecha_fin,
                    ),
                ),
                form_row(
                    form_input(
                        label="Nombre del destinatario",
                        placeholder="Ej: Dr. Juan Pérez",
                        value=CotizadorState.form_destinatario_nombre,
                        on_change=CotizadorState.set_form_destinatario_nombre,
                    ),
                    form_input(
                        label="Cargo del destinatario",
                        placeholder="Ej: Director de Planeación",
                        value=CotizadorState.form_destinatario_cargo,
                        on_change=CotizadorState.set_form_destinatario_cargo,
                    ),
                ),
                rx.hstack(
                    rx.checkbox(
                        "Incluir desglose de conceptos en PDF",
                        checked=CotizadorState.form_mostrar_desglose,
                        on_change=CotizadorState.set_form_mostrar_desglose,
                        size="2",
                    ),
                    padding_top=Spacing.XS,
                ),
                botones_modal(
                    on_guardar=CotizadorState.crear_cotizacion,
                    on_cancelar=CotizadorState.cerrar_modal_crear,
                    saving=CotizadorState.saving_cotizacion,
                    texto_guardar="Crear Cotización",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="600px",
            padding=Spacing.LG,
        ),
        open=CotizadorState.mostrar_modal_crear,
        on_open_change=CotizadorState.set_mostrar_modal_crear,
    )


def _filtros() -> rx.Component:
    """Barra de filtros para el listado."""
    opciones_estatus = [
        {"value": "__todos__", "label": "Todos los estatus"},
        {"value": "BORRADOR", "label": "Borrador"},
        {"value": "PREPARADA", "label": "Preparada"},
        {"value": "ENVIADA", "label": "Enviada"},
        {"value": "APROBADA", "label": "Aprobada"},
        {"value": "RECHAZADA", "label": "Rechazada"},
    ]
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(placeholder="Filtrar por estatus"),
            rx.select.content(
                rx.foreach(
                    opciones_estatus,
                    lambda op: rx.select.item(
                        op["label"],
                        value=op["value"],
                    ),
                )
            ),
            value=CotizadorState.filtro_estatus,
            on_change=CotizadorState.set_filtro_estatus,
            size="2",
        ),
        rx.button(
            rx.icon("plus", size=16),
            "Nueva Cotización",
            on_click=CotizadorState.abrir_modal_crear,
            color_scheme="blue",
            size="2",
        ),
        justify="between",
        width="100%",
        padding_y=Spacing.SM,
    )


def cotizador_page() -> rx.Component:
    """Página principal del listado de cotizaciones."""
    return rx.box(
        page_header(
            "file-text",
            "Cotizador",
            subtitulo="Gestiona cotizaciones de servicios para presentar a clientes",
        ),
        _filtros(),
        rx.cond(
            CotizadorState.loading_cotizaciones,
            rx.center(rx.spinner(size="3"), padding=Spacing.XL),
            tabla_cotizaciones(
                CotizadorState.cotizaciones_filtradas,
                CotizadorState.loading_cotizaciones,
            ),
        ),
        _modal_crear_cotizacion(),
        on_mount=CotizadorState.cargar_cotizaciones,
        padding=Spacing.LG,
        width="100%",
    )
