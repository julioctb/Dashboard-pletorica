"""
Página de detalle por empleado (vista Contabilidad).

Ruta: /nominas/empleado-detalle
Acceso: es_contabilidad | es_admin_empresa

Muestra el desglose completo de percepciones, deducciones y otros pagos
del recibo de nómina de un empleado en el período activo.
"""
import reflex as rx

from app.presentation.pages.nominas.nomina_contabilidad_state import NominaContabilidadState
from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Colors, Spacing, Radius


# =============================================================================
# BADGE ORIGEN
# =============================================================================

def _badge_origen(origen: rx.Var) -> rx.Component:
    return rx.match(
        origen,
        ('SISTEMA',      rx.badge('Sistema',      color_scheme='gray',   size='1', variant='soft')),
        ('RRHH',         rx.badge('RRHH',         color_scheme='orange', size='1', variant='soft')),
        ('CONTABILIDAD', rx.badge('Contabilidad', color_scheme='blue',   size='1', variant='soft')),
        rx.badge(origen, size='1'),
    )


# =============================================================================
# TABLA DE MOVIMIENTOS
# =============================================================================

ENCABEZADOS_DESGLOSE = [
    {"nombre": "Concepto",  "ancho": "240px"},
    {"nombre": "Monto",     "ancho": "110px"},
    {"nombre": "Gravable",  "ancho": "110px"},
    {"nombre": "Exento",    "ancho": "110px"},
    {"nombre": "Origen",    "ancho": "110px"},
]


def _fila_movimiento(mov: dict) -> rx.Component:
    """Fila de desglose de un movimiento (percepción, deducción u otro pago)."""
    return rx.table.row(
        rx.table.cell(
            rx.text(mov['concepto_nombre'], size="2", weight="medium"),
        ),
        rx.table.cell(
            rx.text("$" + mov['monto'].to(str), size="2", weight="medium"),
        ),
        rx.table.cell(
            rx.text(
                "$" + mov['monto_gravable'].to(str),
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                "$" + mov['monto_exento'].to(str),
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            _badge_origen(mov['origen']),
        ),
    )


def _tabla_movimientos(movimientos_var: rx.Var) -> rx.Component:
    """Tabla genérica de movimientos."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                *[
                    rx.table.column_header_cell(
                        rx.text(h["nombre"], size="1", color=Colors.TEXT_MUTED),
                        width=h["ancho"],
                    )
                    for h in ENCABEZADOS_DESGLOSE
                ]
            )
        ),
        rx.table.body(
            rx.foreach(movimientos_var, _fila_movimiento),
        ),
        width="100%",
        variant="surface",
        size="1",
    )


def _seccion(
    titulo: str,
    icono: str,
    color_scheme: str,
    movimientos_var: rx.Var,
    tiene_var: rx.Var,
) -> rx.Component:
    """Sección con encabezado y tabla de movimientos de un tipo."""
    return rx.cond(
        tiene_var,
        rx.vstack(
            rx.hstack(
                rx.icon(icono, size=16, color=f"var(--{color_scheme}-9)"),
                rx.text(titulo, size="3", weight="bold"),
                spacing="2",
                align="center",
            ),
            _tabla_movimientos(movimientos_var),
            width="100%",
            spacing="2",
        ),
        rx.fragment(),
    )


# =============================================================================
# PANEL TOTALES
# =============================================================================

def _resumen_totales() -> rx.Component:
    """Tarjetas con percepciones, deducciones, otros pagos y NETO del empleado."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text("Percepciones", size="1", color=Colors.TEXT_MUTED),
                rx.text(
                    "$" + NominaContabilidadState.detalle_total_percepciones.to(str),
                    size="4",
                    weight="bold",
                    color=Colors.SUCCESS,
                ),
                spacing="0",
                align="start",
            ),
            rx.separator(orientation="vertical", size="2"),
            rx.vstack(
                rx.text("Deducciones", size="1", color=Colors.TEXT_MUTED),
                rx.text(
                    "$" + NominaContabilidadState.detalle_total_deducciones.to(str),
                    size="4",
                    weight="bold",
                    color=Colors.ERROR,
                ),
                spacing="0",
                align="start",
            ),
            rx.separator(orientation="vertical", size="2"),
            rx.vstack(
                rx.text("Otros pagos", size="1", color=Colors.TEXT_MUTED),
                rx.text(
                    "$" + NominaContabilidadState.detalle_total_otros_pagos.to(str),
                    size="4",
                    weight="bold",
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="0",
                align="start",
            ),
            rx.separator(orientation="vertical", size="2"),
            rx.vstack(
                rx.text("NETO A PAGAR", size="1", color=Colors.TEXT_MUTED, weight="bold"),
                rx.text(
                    "$" + NominaContabilidadState.detalle_total_neto.to(str),
                    size="6",
                    weight="bold",
                    color=Colors.PRIMARY,
                ),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            # Recalcular (solo si período no cerrado)
            rx.cond(
                ~NominaContabilidadState.periodo_cerrado,
                rx.button(
                    rx.icon("refresh-cw", size=14),
                    "Recalcular",
                    on_click=NominaContabilidadState.recalcular_empleado,
                    loading=NominaContabilidadState.saving,
                    variant="soft",
                    color_scheme="blue",
                    size="2",
                ),
                rx.fragment(),
            ),
            spacing="6",
            align="center",
            wrap="wrap",
            width="100%",
        ),
        padding=Spacing.LG,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        width="100%",
    )


# =============================================================================
# COMPUTED VARS PARA CONDICIONAR SECCIONES
# Usamos len() Python-side en vars booleanas del state:
#   movimientos_percepciones: list[dict] - ya filtrado en state
# =============================================================================

def _tiene_percepciones() -> rx.Var:
    return NominaContabilidadState.movimientos_percepciones.length() > 0


def _tiene_deducciones() -> rx.Var:
    return NominaContabilidadState.movimientos_deducciones.length() > 0


def _tiene_otros_pagos() -> rx.Var:
    return NominaContabilidadState.movimientos_otros_pagos.length() > 0


# =============================================================================
# PÁGINA
# =============================================================================

def detalle_empleado_page() -> rx.Component:
    """Página de desglose de nómina por empleado."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo=rx.hstack(
                    rx.link(
                        "Nóminas",
                        href=NominaContabilidadState.nomina_base_path,
                        size="4",
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.icon("chevron-right", size=14, color=Colors.TEXT_MUTED),
                    rx.link(
                        NominaContabilidadState.periodo_nombre,
                        href=NominaContabilidadState.nomina_calculo_path,
                        size="4",
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.icon("chevron-right", size=14, color=Colors.TEXT_MUTED),
                    rx.text(
                        NominaContabilidadState.detalle_nombre_empleado,
                        size="4",
                        weight="bold",
                    ),
                    spacing="2",
                    align="center",
                ),
                subtitulo=rx.hstack(
                    rx.text("Clave:", size="2", color=Colors.TEXT_MUTED),
                    rx.text(
                        NominaContabilidadState.detalle_clave_empleado,
                        size="2",
                        weight="medium",
                    ),
                    spacing="1",
                ),
                icono="receipt",
            ),
            content=rx.vstack(
                _resumen_totales(),
                _seccion(
                    "Percepciones",
                    "trending-up",
                    "green",
                    NominaContabilidadState.movimientos_percepciones,
                    _tiene_percepciones(),
                ),
                _seccion(
                    "Otros Pagos",
                    "gift",
                    "blue",
                    NominaContabilidadState.movimientos_otros_pagos,
                    _tiene_otros_pagos(),
                ),
                _seccion(
                    "Deducciones",
                    "trending-down",
                    "red",
                    NominaContabilidadState.movimientos_deducciones,
                    _tiene_deducciones(),
                ),
                spacing="6",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=NominaContabilidadState.on_mount_detalle,
    )
