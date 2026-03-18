"""
Componentes UI para la pagina Bajas de Personal del portal.
"""
import reflex as rx

from app.core.ui_helpers import FILTRO_TODOS
from app.presentation.components.ui import (
    feedback_callout,
    filtros_inline,
    form_textarea,
    modal_formulario,
    table_shell,
    empty_state_card,
    tabla_cta_button,
    table_cell_actions,
    table_cell_badge,
    table_cell_text_sm,
    table_text_sm,
)
from app.presentation.theme import Colors, Typography, Spacing

from .state import BajasState


def _badge_estatus_baja(estatus: str) -> rx.Component:
    return rx.match(
        estatus,
        ("INICIADA", rx.badge("Iniciada", color_scheme="orange", variant="soft", size="1")),
        ("COMUNICADA", rx.badge("Comunicada", color_scheme="blue", variant="soft", size="1")),
        ("LIQUIDADA", rx.badge("Liquidada", color_scheme="green", variant="soft", size="1")),
        ("CERRADA", rx.badge("Cerrada", color_scheme="gray", variant="soft", size="1")),
        ("CANCELADA", rx.badge("Cancelada", color_scheme="red", variant="soft", size="1")),
        rx.badge(estatus, color_scheme="gray", variant="soft", size="1"),
    )


def _badge_liquidacion(badge: str) -> rx.Component:
    return rx.match(
        badge,
        ("entregada", rx.badge("Entregada", color_scheme="green", variant="soft", size="1")),
        ("vencida", rx.badge("Vencida", color_scheme="red", variant="solid", size="1")),
        ("proxima", rx.badge("Proxima", color_scheme="yellow", variant="soft", size="1")),
        rx.badge("Pendiente", color_scheme="gray", variant="outline", size="1"),
    )


def _motivo_text(motivo: str) -> rx.Component:
    return rx.match(
        motivo,
        ("RENUNCIA", rx.text("Renuncia", font_size=Typography.SIZE_SM)),
        ("DESPIDO", rx.text("Despido", font_size=Typography.SIZE_SM)),
        ("FIN_CONTRATO", rx.text("Fin contrato", font_size=Typography.SIZE_SM)),
        ("JUBILACION", rx.text("Jubilacion", font_size=Typography.SIZE_SM)),
        ("FALLECIMIENTO", rx.text("Fallecimiento", font_size=Typography.SIZE_SM)),
        ("OTRO", rx.text("Otro", font_size=Typography.SIZE_SM)),
        rx.text(motivo, font_size=Typography.SIZE_SM),
    )


def _sustitucion_badge(baja: dict) -> rx.Component:
    valor = baja.get("requiere_sustitucion")
    return rx.cond(
        valor == True,
        rx.badge("Requiere", color_scheme="blue", variant="soft", size="1"),
        rx.cond(
            valor == False,
            rx.badge("No requiere", color_scheme="gray", variant="soft", size="1"),
            rx.badge("Sin definir", color_scheme="gray", variant="outline", size="1"),
        ),
    )


def _celda_centrada(component: rx.Component) -> rx.Component:
    """Centra contenido dentro de una celda de tabla."""
    return rx.table.cell(
        rx.center(
            component,
            width="100%",
        ),
    )


def _accion_primaria_baja(baja: dict) -> rx.Component:
    return rx.match(
        baja.get("estatus", ""),
        (
            "INICIADA",
            tabla_cta_button(
                "Comunicar al cliente",
                BajasState.comunicar_baja(baja),
                color_scheme="orange",
            ),
        ),
        (
            "COMUNICADA",
            tabla_cta_button(
                "Procesar liquidacion",
                BajasState.registrar_liquidacion(baja),
                color_scheme="blue",
            ),
        ),
        (
            "LIQUIDADA",
            tabla_cta_button(
                "Cerrar baja",
                BajasState.cerrar_baja(baja),
                color_scheme="green",
            ),
        ),
        tabla_cta_button(
            "Consultar",
            BajasState.consultar_baja(baja),
            color_scheme="gray",
        ),
    )


def fila_baja(baja: dict) -> rx.Component:
    """Fila de tabla de bajas."""
    return rx.table.row(
        table_cell_text_sm(
            baja.get("empleado_nombre_ui", ""),
            weight=Typography.WEIGHT_MEDIUM,
            fallback="-",
        ),
        _celda_centrada(_motivo_text(baja.get("motivo", ""))),
        table_cell_text_sm(
            baja.get("fecha_efectiva_fmt", baja.get("fecha_efectiva", "-")),
            tone="secondary",
        ),
        table_cell_badge(_badge_estatus_baja(baja.get("estatus", ""))),
        _celda_centrada(
            _badge_liquidacion(baja.get("badge_liquidacion", "pendiente")),
        ),
        _celda_centrada(_sustitucion_badge(baja)),
        table_cell_actions(
            _accion_primaria_baja(baja),
        ),
    )


ENCABEZADOS_BAJAS = [
    {"nombre": "Empleado", "ancho": "220px"},
    {"nombre": "Motivo", "ancho": "140px", "header_align": "center"},
    {"nombre": "Fec. Efectiva", "ancho": "120px"},
    {"nombre": "Estatus", "ancho": "120px", "header_align": "center"},
    {"nombre": "Liquidacion", "ancho": "120px", "header_align": "center"},
    {"nombre": "Sustitucion", "ancho": "130px", "header_align": "center"},
    {"nombre": "Acciones", "ancho": "240px", "header_align": "center"},
]


def alertas_liquidacion() -> rx.Component:
    """Panel de alertas de liquidacion."""
    return rx.cond(
        BajasState.tiene_alertas,
        rx.card(
            rx.vstack(
                rx.text(
                    "Alertas de liquidacion",
                    font_size=Typography.SIZE_LG,
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                rx.foreach(
                    BajasState.alertas,
                    lambda alerta: rx.callout(
                        rx.text(alerta["mensaje"], font_size=Typography.SIZE_SM),
                        icon=rx.cond(
                            alerta["nivel"] == "critico",
                            "triangle-alert",
                            "info",
                        ),
                        color_scheme=rx.cond(
                            alerta["nivel"] == "critico",
                            "red",
                            "yellow",
                        ),
                        size="1",
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.fragment(),
    )


def filtros_bajas() -> rx.Component:
    """Filtro de bajas por estatus."""
    return filtros_inline(
        rx.select.root(
            rx.select.trigger(placeholder="Filtro", width="180px"),
            rx.select.content(
                rx.select.item("Activas", value="ACTIVAS"),
                rx.select.item("Cerradas", value="CERRADAS"),
                rx.select.item("Todas", value=FILTRO_TODOS),
            ),
            value=BajasState.filtro_estatus,
            on_change=BajasState.cambiar_filtro,
            size="2",
        ),
    )


def tabla_bajas() -> rx.Component:
    """Tabla principal de bajas."""
    return table_shell(
        loading=BajasState.loading,
        headers=ENCABEZADOS_BAJAS,
        rows=BajasState.bajas_filtradas,
        row_renderer=fila_baja,
        has_rows=BajasState.bajas_filtradas.length() > 0,
        empty_component=empty_state_card(
            title="No hay bajas registradas",
            description="Las bajas activas apareceran aqui junto con sus alertas de liquidacion.",
            icon="user-minus",
        ),
        total_caption="Mostrando " + BajasState.bajas_filtradas.length().to(str) + " baja(s)",
        loading_rows=5,
    )


def modal_cancelacion() -> rx.Component:
    """Modal para cancelar una baja."""
    return modal_formulario(
        open=BajasState.mostrar_modal_accion,
        titulo="Cancelar baja",
        descripcion="Esta acción cancelará el proceso de baja y reactivará al empleado.",
        icono="user-x",
        color_icono="red",
        color_guardar="red",
        texto_guardar="Cancelar baja",
        texto_guardando="Cancelando...",
        on_guardar=BajasState.cancelar_baja,
        on_cancelar=BajasState.cerrar_modal_accion,
        loading=BajasState.saving,
        max_width="500px",
        contenido=rx.vstack(
            form_textarea(
                label="Motivo de cancelación",
                required=True,
                value=BajasState.form_notas_cancelacion,
                on_change=BajasState.set_form_notas_cancelacion,
                placeholder="Explique por qué se cancela la baja (mín. 5 caracteres)...",
                label_variant="portal",
                style_variant="portal",
                rows="4",
            ),
            feedback_callout(
                "Al cancelar, el empleado se reactivará y la baja quedará marcada como cancelada.",
                "info",
            ),
            spacing="4",
            width="100%",
        ),
    )
