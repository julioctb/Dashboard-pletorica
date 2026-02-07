"""
Página principal de Entregables (Admin).
Nueva vista global: muestra todos los entregables, con "En Revisión" por defecto.
Cards de estadísticas son clickeables para filtrar.
"""

import reflex as rx

from app.presentation.pages.entregables.entregables_state import EntregablesState
from app.presentation.layout import page_layout, page_header
from app.presentation.components.ui import (
    status_badge_reactive,
    tabla_vacia,
    skeleton_tabla,
)
from app.presentation.theme import Colors, Spacing, Typography, Radius, Shadows


# =============================================================================
# STAT CARDS (CLICKEABLES)
# =============================================================================
def _stat_card(
    titulo: str,
    valor: rx.Var,
    icono: str,
    color_scheme: str,
    on_click,
    is_active: rx.Var,
) -> rx.Component:
    """Card de estadística clickeable que actúa como filtro."""
    color_map = {
        "gray": (Colors.SECONDARY_LIGHT, Colors.SECONDARY),
        "sky": (Colors.INFO_LIGHT, Colors.INFO),
        "green": (Colors.SUCCESS_LIGHT, Colors.SUCCESS),
        "red": (Colors.ERROR_LIGHT, Colors.ERROR),
        "amber": (Colors.WARNING_LIGHT, Colors.WARNING),
    }
    bg, icon_color = color_map.get(color_scheme, (Colors.SECONDARY_LIGHT, Colors.SECONDARY))

    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(icono, size=20, color=icon_color),
                width="40px",
                height="40px",
                border_radius=Radius.LG,
                background=bg,
            ),
            rx.vstack(
                rx.text(titulo, size="1", color=Colors.TEXT_MUTED),
                rx.text(valor, size="5", weight="bold"),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        padding=Spacing.MD,
        background=rx.cond(is_active, Colors.PRIMARY_LIGHT, Colors.SURFACE),
        border=rx.cond(
            is_active,
            f"2px solid {Colors.PRIMARY}",
            f"1px solid {Colors.BORDER}",
        ),
        border_radius=Radius.LG,
        flex="1",
        min_width="150px",
        cursor="pointer",
        on_click=on_click,
        _hover={
            "box_shadow": Shadows.MD,
            "border_color": Colors.PRIMARY,
        },
        transition="all 0.2s ease",
    )


def _seccion_estadisticas() -> rx.Component:
    """Cards de estadísticas que actúan como filtros."""
    return rx.vstack(
        # Fila 1: Flujo de revisión
        rx.hstack(
            _stat_card(
                "Total",
                EntregablesState.stats_total,
                "calendar",
                "gray",
                EntregablesState.filtrar_todos,
                EntregablesState.filtro_activo_es_todos,
            ),
            _stat_card(
                "En Revisión",
                EntregablesState.stats_en_revision,
                "search",
                "sky",
                EntregablesState.filtrar_en_revision,
                EntregablesState.filtro_activo_es_en_revision,
            ),
            _stat_card(
                "Pendientes",
                EntregablesState.stats_pendientes,
                "clock",
                "amber",
                EntregablesState.filtrar_pendientes,
                EntregablesState.filtro_activo_es_pendiente,
            ),
            _stat_card(
                "Aprobados",
                EntregablesState.stats_aprobados,
                "circle-check",
                "green",
                EntregablesState.filtrar_aprobados,
                EntregablesState.filtro_activo_es_aprobado,
            ),
            _stat_card(
                "Rechazados",
                EntregablesState.stats_rechazados,
                "circle-x",
                "red",
                EntregablesState.filtrar_rechazados,
                EntregablesState.filtro_activo_es_rechazado,
            ),
            spacing="4",
            width="100%",
            flex_wrap="wrap",
        ),
        # Fila 2: Flujo de facturación
        rx.hstack(
            _stat_card(
                "Prefacturas",
                EntregablesState.stats_prefactura_enviada,
                "file-search",
                "sky",
                EntregablesState.filtrar_prefacturas,
                EntregablesState.filtro_activo_es_prefactura,
            ),
            _stat_card(
                "Facturados",
                EntregablesState.stats_facturados,
                "receipt",
                "amber",
                EntregablesState.filtrar_facturados,
                EntregablesState.filtro_activo_es_facturado,
            ),
            _stat_card(
                "Pagados",
                EntregablesState.stats_pagados,
                "badge-check",
                "green",
                EntregablesState.filtrar_pagados,
                EntregablesState.filtro_activo_es_pagado,
            ),
            spacing="4",
            width="100%",
            flex_wrap="wrap",
        ),
        spacing="3",
        width="100%",
    )


# =============================================================================
# BARRA DE FILTROS
# =============================================================================
def _barra_filtros() -> rx.Component:
    """Barra con búsqueda y filtro de contrato."""
    return rx.hstack(
        # Título dinámico del filtro actual
        rx.text(
            EntregablesState.titulo_filtro_actual,
            size="4",
            weight="bold",
            color=Colors.TEXT_PRIMARY,
        ),
        rx.spacer(),
        # Búsqueda
        rx.box(
            rx.input(
                placeholder="Buscar por período, contrato, empresa...",
                value=EntregablesState.filtro_busqueda,
                on_change=EntregablesState.set_filtro_busqueda,
                width="280px",
            ),
        ),
        # Filtro por contrato (opcional)
        rx.select.root(
            rx.select.trigger(placeholder="Todos los contratos", width="220px"),
            rx.select.content(
                rx.foreach(
                    EntregablesState.opciones_contratos,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=EntregablesState.filtro_contrato_id,
            on_change=EntregablesState.set_filtro_contrato,
        ),
        spacing="3",
        width="100%",
        align="center",
        padding_bottom=Spacing.MD,
    )


# =============================================================================
# TABLA DE ENTREGABLES (NUEVA ESTRUCTURA)
# =============================================================================
def _fila_entregable(entregable: dict) -> rx.Component:
    """Fila de la tabla con la nueva estructura de columnas."""
    return rx.table.row(
        # Contrato
        rx.table.cell(
            rx.badge(
                entregable["contrato_codigo"],
                color_scheme="blue",
                size="1",
                variant="soft",
            ),
        ),
        # Empresa
        rx.table.cell(
            rx.text(
                entregable["empresa_nombre"],
                size="2",
                weight="medium",
            ),
        ),
        # Período
        rx.table.cell(
            rx.vstack(
                rx.text(f"Período {entregable['numero_periodo']}", weight="medium", size="2"),
                rx.text(entregable["periodo_texto"], size="1", color=Colors.TEXT_MUTED),
                spacing="0",
                align="start",
            ),
        ),
        # Fecha Entrega
        rx.table.cell(
            rx.cond(
                entregable["fecha_entrega"],
                rx.text(entregable["fecha_entrega"], size="2"),
                rx.text("-", size="2", color=Colors.TEXT_MUTED),
            ),
        ),
        # Estado
        rx.table.cell(status_badge_reactive(entregable["estatus"])),
        # Acción
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("eye", size=14),
                    "Ver",
                    size="1",
                    variant="ghost",
                    on_click=lambda: EntregablesState.ir_a_detalle(entregable["id"]),
                ),
                rx.cond(
                    entregable["requiere_accion"],
                    rx.badge("Acción", color_scheme="sky", size="1"),
                    rx.fragment(),
                ),
                spacing="2",
            ),
        ),
        _hover={"background": Colors.SURFACE_HOVER},
        cursor="pointer",
        on_click=lambda: EntregablesState.ir_a_detalle(entregable["id"]),
    )


ENCABEZADOS_TABLA = [
    {"nombre": "Contrato", "ancho": "120px"},
    {"nombre": "Empresa", "ancho": "180px"},
    {"nombre": "Período", "ancho": "180px"},
    {"nombre": "Fecha Entrega", "ancho": "130px"},
    {"nombre": "Estado", "ancho": "120px"},
    {"nombre": "Acción", "ancho": "120px"},
]


def _tabla_entregables() -> rx.Component:
    """Tabla de entregables con nueva estructura."""
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.foreach(
                        ENCABEZADOS_TABLA,
                        lambda col: rx.table.column_header_cell(
                            col["nombre"],
                            width=col["ancho"],
                        ),
                    ),
                ),
            ),
            rx.table.body(
                rx.foreach(EntregablesState.entregables_filtrados, _fila_entregable)
            ),
            width="100%",
        ),
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        overflow="hidden",
    )


# =============================================================================
# CONTENIDO PRINCIPAL
# =============================================================================
def _contenido_principal() -> rx.Component:
    """Contenido principal de la página."""
    return rx.vstack(
        # Cards de estadísticas (clickeables como filtros)
        _seccion_estadisticas(),
        rx.divider(margin_y="4"),
        # Barra de filtros
        _barra_filtros(),
        # Tabla o skeleton
        rx.cond(
            EntregablesState.cargando,
            skeleton_tabla(columnas=ENCABEZADOS_TABLA, filas=5),
            rx.cond(
                EntregablesState.tiene_entregables,
                rx.vstack(
                    _tabla_entregables(),
                    # Contador
                    rx.text(
                        "Mostrando ",
                        EntregablesState.total_mostrados,
                        " entregable(s)",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_MUTED,
                    ),
                    width="100%",
                    spacing="3",
                ),
                tabla_vacia(
                    mensaje="No hay entregables con este filtro",
                    submensaje="Prueba cambiando los filtros o seleccionando otro estado",
                ),
            ),
        ),
        spacing="4",
        width="100%",
    )


# =============================================================================
# PÁGINA
# =============================================================================
def entregables_page() -> rx.Component:
    """Página de entregables - Vista global."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Entregables",
                subtitulo="Gestión y revisión de entregas",
                icono="package-check",
            ),
            content=_contenido_principal(),
        ),
        on_mount=EntregablesState.on_load_entregables,
    )
