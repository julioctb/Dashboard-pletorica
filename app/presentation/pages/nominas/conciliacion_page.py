"""
Página de conciliación nómina ↔ CONTPAQi.

Ruta: /nominas/conciliacion
Acceso: es_rrhh | es_contabilidad | es_admin_empresa

Permite capturar los totales de CONTPAQi por empleado,
visualiza diferencias y un semáforo verde/amarillo/rojo,
y exporta el resumen en Excel.
"""
import reflex as rx

from app.presentation.pages.nominas.conciliacion_state import NominaConciliacionState
from app.presentation.components.ui import (
    tabla_vacia,
    table_shell,
    table_cell_text_sm,
    skeleton_tabla,
    page_header,
)
from app.presentation.layout import page_layout
from app.presentation.theme import Colors, Spacing, Radius


# =============================================================================
# SELECTOR DE PERÍODO
# =============================================================================

def _opcion_periodo_conc(periodo: dict) -> rx.Component:
    return rx.select.item(periodo['nombre'], value=periodo['id'])


def _selector_periodo_conciliacion() -> rx.Component:
    return rx.hstack(
        rx.text("Período:", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
        rx.select.root(
            rx.select.trigger(placeholder="Selecciona un período…", width="260px"),
            rx.select.content(
                rx.foreach(
                    NominaConciliacionState.periodos_disponibles,
                    _opcion_periodo_conc,
                ),
            ),
            value=NominaConciliacionState.periodo_id,
            on_change=NominaConciliacionState.seleccionar_periodo_conciliacion,
            size="2",
        ),
        spacing="2",
        align="center",
    )


# =============================================================================
# SEMÁFORO — BADGE
# =============================================================================

def _badge_semaforo(semaforo: rx.Var) -> rx.Component:
    return rx.match(
        semaforo,
        ('verde',    rx.badge("✓ Verde",    color_scheme="green",  size="1")),
        ('amarillo', rx.badge("! Amarillo", color_scheme="amber",  size="1")),
        ('rojo',     rx.badge("✗ Rojo",     color_scheme="red",    size="1")),
        rx.badge("— Sin datos", color_scheme="gray", size="1"),
    )


# =============================================================================
# TABLA DE CONCILIACIÓN
# =============================================================================

_COLS_CONC = [
    {"nombre": "Clave",                 "ancho": "70px"},
    {"nombre": "Nombre",                "ancho": "180px"},
    {"nombre": "Sistema Percep.",       "ancho": "110px"},
    {"nombre": "Sistema Neto",          "ancho": "100px"},
    {"nombre": "CONTPAQi Percep.",      "ancho": "115px"},
    {"nombre": "CONTPAQi Neto",         "ancho": "105px"},
    {"nombre": "Diferencia",            "ancho": "90px"},
    {"nombre": "Semáforo",              "ancho": "100px"},
    {"nombre": "Acción",                "ancho": "70px"},
]


def _fila_conciliacion(emp: dict) -> rx.Component:
    return rx.table.row(
        table_cell_text_sm(emp['clave_empleado'], tone="muted"),
        rx.table.cell(
            rx.text(
                emp['nombre_empleado'],
                size="2",
                max_width="180px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            )
        ),
        # Sistema
        rx.table.cell(
            rx.text(
                "$" + emp['total_percepciones'].to(str),
                size="2",
                color=Colors.TEXT_PRIMARY,
            )
        ),
        rx.table.cell(
            rx.text(
                "$" + emp['total_neto'].to(str),
                size="2",
                weight="medium",
                color=Colors.PRIMARY,
            )
        ),
        # CONTPAQi
        rx.table.cell(
            rx.cond(
                emp['cp_percepciones'].to(float) > 0,
                rx.text(
                    "$" + emp['cp_percepciones'].to(str),
                    size="2",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text("—", size="2", color=Colors.TEXT_MUTED),
            )
        ),
        rx.table.cell(
            rx.cond(
                emp['cp_neto'].to(float) > 0,
                rx.text(
                    "$" + emp['cp_neto'].to(str),
                    size="2",
                    weight="medium",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text("—", size="2", color=Colors.TEXT_MUTED),
            )
        ),
        # Diferencia
        rx.table.cell(
            rx.cond(
                emp['diff_neto'].to(float) >= 0,
                rx.text(
                    "$" + emp['diff_neto'].to(str),
                    size="2",
                    weight="bold",
                    color=rx.cond(
                        emp['diff_neto'].to(float) < 1,
                        Colors.SUCCESS,
                        rx.cond(
                            emp['diff_neto'].to(float) < 10,
                            Colors.WARNING,
                            Colors.ERROR,
                        ),
                    ),
                ),
                rx.text("—", size="2", color=Colors.TEXT_MUTED),
            )
        ),
        # Semáforo
        rx.table.cell(_badge_semaforo(emp['semaforo'])),
        # Acción
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    size="2",
                    variant="soft",
                    color_scheme="indigo",
                    on_click=NominaConciliacionState.abrir_modal_contpaqi(emp),
                ),
                content="Capturar datos CONTPAQi",
            )
        ),
    )


def _tabla_conciliacion() -> rx.Component:
    return table_shell(
        loading=NominaConciliacionState.loading,
        headers=_COLS_CONC,
        rows=NominaConciliacionState.empleados_conciliacion,
        row_renderer=_fila_conciliacion,
        has_rows=NominaConciliacionState.tiene_empleados,
        empty_component=tabla_vacia(
            mensaje="Selecciona un período para cargar la conciliación"
        ),
        total_caption=(
            NominaConciliacionState.empleados_conciliacion.length().to(str)
            + " empleado(s)"
        ),
        loading_rows=5,
    )


# =============================================================================
# RESUMEN SEMÁFOROS
# =============================================================================

def _chip_semaforo(
    icono: str,
    label: str,
    valor: rx.Var,
    color: str,
    scheme: str,
) -> rx.Component:
    return rx.hstack(
        rx.icon(icono, size=14, color=color),
        rx.text(label, size="2", color=Colors.TEXT_SECONDARY),
        rx.badge(valor.to(str), color_scheme=scheme, size="2"),
        spacing="1",
        align="center",
    )


def _panel_resumen_semaforos() -> rx.Component:
    return rx.cond(
        NominaConciliacionState.tiene_empleados,
        rx.box(
            rx.hstack(
                _chip_semaforo(
                    "circle-check", "Verde (<$1)",
                    NominaConciliacionState.semaforo_verdes, Colors.SUCCESS, "green"
                ),
                rx.separator(orientation="vertical", size="2"),
                _chip_semaforo(
                    "triangle-alert", "Amarillo (<$10)",
                    NominaConciliacionState.semaforo_amarillos, Colors.WARNING, "amber"
                ),
                rx.separator(orientation="vertical", size="2"),
                _chip_semaforo(
                    "circle-x", "Rojo (≥$10)",
                    NominaConciliacionState.semaforo_rojos, Colors.ERROR, "red"
                ),
                rx.separator(orientation="vertical", size="2"),
                _chip_semaforo(
                    "circle-minus", "Sin datos",
                    NominaConciliacionState.semaforo_grises,
                    Colors.TEXT_MUTED, "gray"
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text(
                        "% que cuadra:",
                        size="2",
                        color=Colors.TEXT_SECONDARY,
                        weight="medium",
                    ),
                    rx.badge(
                        NominaConciliacionState.pct_cuadra.to(str) + "%",
                        color_scheme="green",
                        size="2",
                        variant="solid",
                    ),
                    spacing="1",
                    align="center",
                ),
                spacing="3",
                align="center",
                wrap="wrap",
                width="100%",
            ),
            padding=Spacing.MD,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            width="100%",
        ),
        rx.fragment(),
    )


# =============================================================================
# MODAL — Captura CONTPAQi
# =============================================================================

def _modal_contpaqi() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("book-open", size=18, color=Colors.PRIMARY),
                    rx.text("Capturar datos CONTPAQi"),
                    spacing="2",
                    align="center",
                )
            ),
            rx.dialog.description(
                NominaConciliacionState.emp_editando_nombre,
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
            rx.vstack(
                # Valores del sistema (solo lectura)
                rx.box(
                    rx.text("Valores del sistema", size="1", weight="bold",
                            color=Colors.TEXT_MUTED),
                    rx.hstack(
                        rx.vstack(
                            rx.text("Percepciones", size="1", color=Colors.TEXT_MUTED),
                            rx.text(
                                "$" + NominaConciliacionState.modal_sistema_percepciones.to(str),
                                size="3", weight="bold",
                            ),
                            spacing="0",
                        ),
                        rx.vstack(
                            rx.text("Deducciones", size="1", color=Colors.TEXT_MUTED),
                            rx.text(
                                "$" + NominaConciliacionState.modal_sistema_deducciones.to(str),
                                size="3", weight="bold",
                            ),
                            spacing="0",
                        ),
                        rx.vstack(
                            rx.text("Neto", size="1", color=Colors.TEXT_MUTED),
                            rx.text(
                                "$" + NominaConciliacionState.modal_sistema_neto.to(str),
                                size="3", weight="bold", color=Colors.PRIMARY,
                            ),
                            spacing="0",
                        ),
                        spacing="6",
                    ),
                    padding=Spacing.MD,
                    background=Colors.PRIMARY_LIGHTER,
                    border_radius=Radius.MD,
                ),
                rx.separator(size="4"),
                # Inputs CONTPAQi
                rx.text(
                    "Totales en CONTPAQi",
                    size="2",
                    weight="bold",
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Percepciones", size="1", weight="medium"),
                        rx.input(
                            placeholder="0.00",
                            value=NominaConciliacionState.form_contpaqi_percepciones,
                            on_change=NominaConciliacionState.set_form_contpaqi_percepciones,
                            size="2",
                            type="number",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Deducciones", size="1", weight="medium"),
                        rx.input(
                            placeholder="0.00",
                            value=NominaConciliacionState.form_contpaqi_deducciones,
                            on_change=NominaConciliacionState.set_form_contpaqi_deducciones,
                            size="2",
                            type="number",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Neto *", size="1", weight="medium"),
                        rx.input(
                            placeholder="0.00",
                            value=NominaConciliacionState.form_contpaqi_neto,
                            on_change=NominaConciliacionState.set_form_contpaqi_neto,
                            size="2",
                            type="number",
                        ),
                        spacing="1",
                    ),
                    columns="3",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Error
                rx.cond(
                    NominaConciliacionState.error_form != "",
                    rx.callout(
                        NominaConciliacionState.error_form,
                        icon="circle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                spacing="3",
                width="100%",
                margin_top=Spacing.MD,
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=NominaConciliacionState.cerrar_modal_contpaqi,
                    )
                ),
                rx.button(
                    rx.icon("check", size=15),
                    "Guardar",
                    on_click=NominaConciliacionState.capturar_contpaqi,
                    color_scheme="indigo",
                ),
                justify="end",
                gap=Spacing.SM,
                margin_top=Spacing.LG,
            ),
            max_width="520px",
        ),
        open=NominaConciliacionState.mostrar_modal_contpaqi,
        on_open_change=NominaConciliacionState.set_mostrar_modal_contpaqi,
    )


# =============================================================================
# TOOLBAR
# =============================================================================

def _toolbar_conciliacion() -> rx.Component:
    return rx.hstack(
        _selector_periodo_conciliacion(),
        rx.spacer(),
        rx.cond(
            NominaConciliacionState.tiene_empleados,
            rx.button(
                rx.cond(
                    NominaConciliacionState.exportando,
                    rx.spinner(size="1"),
                    rx.icon("file-spreadsheet", size=15),
                ),
                rx.cond(
                    NominaConciliacionState.exportando,
                    "Exportando…",
                    "Exportar Excel",
                ),
                on_click=NominaConciliacionState.exportar_excel,
                color_scheme="green",
                size="2",
                variant="soft",
                disabled=NominaConciliacionState.exportando,
            ),
            rx.fragment(),
        ),
        spacing="3",
        align="center",
        width="100%",
    )


# =============================================================================
# PÁGINA
# =============================================================================

def conciliacion_nomina_page() -> rx.Component:
    """Página de conciliación nómina ↔ CONTPAQi."""
    return rx.box(
        page_layout(
            header=page_header(
                "git-compare",
                "Conciliación Nómina",
                subtitulo="Valida los totales del sistema contra CONTPAQi",
            ),
            content=rx.vstack(
                _toolbar_conciliacion(),
                _panel_resumen_semaforos(),
                _tabla_conciliacion(),
                # Modal
                _modal_contpaqi(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=NominaConciliacionState.on_mount_conciliacion,
    )
