"""
Componentes UI para la pagina Bajas de Personal del portal.
"""
import reflex as rx

from app.presentation.constants import FILTRO_TODAS
from app.presentation.components.ui import (
    table_shell,
    tabla_action_button,
    empty_state_card,
    boton_cancelar,
    boton_guardar,
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
    estatus = baja.get("estatus", "")
    return rx.match(
        estatus,
        (
            "INICIADA",
            rx.button(
                "Comunicar BUAP",
                size="2",
                variant="soft",
                color_scheme="blue",
                on_click=BajasState.comunicar_baja(baja),
                white_space="nowrap",
            ),
        ),
        (
            "COMUNICADA",
            rx.button(
                "Registrar liquidacion",
                size="2",
                variant="soft",
                color_scheme="green",
                on_click=BajasState.registrar_liquidacion(baja),
                white_space="nowrap",
            ),
        ),
        (
            "LIQUIDADA",
            rx.button(
                "Cerrar",
                size="2",
                variant="soft",
                color_scheme="gray",
                on_click=BajasState.cerrar_baja(baja),
                white_space="nowrap",
            ),
        ),
        rx.fragment(),
    )


def fila_baja(baja: dict) -> rx.Component:
    """Fila de tabla de bajas."""
    estatus = baja.get("estatus", "")

    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(
                    baja.get("empleado_nombre", "-"),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    baja.get("empleado_clave", "-"),
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="0",
                align="start",
            ),
        ),
        _celda_centrada(_motivo_text(baja.get("motivo", ""))),
        rx.table.cell(
            rx.text(
                baja.get("fecha_efectiva_fmt", baja.get("fecha_efectiva", "-")),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        _celda_centrada(_badge_estatus_baja(estatus)),
        _celda_centrada(
            _badge_liquidacion(baja.get("badge_liquidacion", "pendiente")),
        ),
        _celda_centrada(_sustitucion_badge(baja)),
        _celda_centrada(
            rx.hstack(
                _accion_primaria_baja(baja),
                tabla_action_button(
                    icon="x",
                    tooltip="Cancelar baja",
                    on_click=BajasState.abrir_cancelacion(baja),
                    color_scheme="red",
                    visible=(estatus == "INICIADA") | (estatus == "COMUNICADA"),
                ),
                spacing="1",
            ),
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
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(placeholder="Filtro", width="180px"),
            rx.select.content(
                rx.select.item("Activas", value="ACTIVAS"),
                rx.select.item("Cerradas", value="CERRADAS"),
                rx.select.item("Todas", value=FILTRO_TODAS),
            ),
            value=BajasState.filtro_estatus,
            on_change=BajasState.cambiar_filtro,
            size="2",
        ),
        rx.button(
            rx.icon("refresh-cw", size=14),
            "Recargar",
            on_click=BajasState.recargar_bajas,
            variant="soft",
            size="2",
        ),
        spacing="3",
        align="center",
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
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Cancelar baja"),
            rx.dialog.description(
                "Esta accion cancelara el proceso de baja y reactivara al empleado."
            ),
            rx.vstack(
                rx.text(
                    "Motivo de cancelacion *",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.text_area(
                    value=BajasState.form_notas_cancelacion,
                    on_change=BajasState.set_form_notas_cancelacion,
                    placeholder="Explique por que se cancela la baja (min. 5 caracteres)...",
                    width="100%",
                    rows="4",
                ),
                rx.callout(
                    rx.text(
                        "Al cancelar, el empleado se reactivara y la baja quedara marcada como cancelada.",
                        font_size=Typography.SIZE_BASE,
                    ),
                    icon="info",
                    color_scheme="blue",
                    size="1",
                    width="100%",
                ),
                spacing="3",
                width="100%",
                padding_y=Spacing.BASE,
            ),
            rx.hstack(
                boton_cancelar(on_click=BajasState.cerrar_modal_accion),
                boton_guardar(
                    texto="Cancelar baja",
                    texto_guardando="Cancelando...",
                    on_click=BajasState.cancelar_baja,
                    saving=BajasState.saving,
                    color_scheme="red",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),
            max_width="500px",
        ),
        open=BajasState.mostrar_modal_accion,
        on_open_change=rx.noop,
    )
