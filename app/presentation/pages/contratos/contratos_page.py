"""
Página principal de Contratos.
Muestra una tabla o cards con los contratos y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.contratos.contratos_state import ContratosState
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.layout import (
    page_layout,
    page_header,
    page_toolbar,
)
from app.presentation.components.ui import (
    status_badge_reactive,
    tabla_vacia,
    skeleton_tabla,
    switch_inactivos,
    tabla_action_button,
    tabla_action_buttons,
)
from app.presentation.theme import Colors, Spacing, Shadows

from app.presentation.pages.contratos.contratos_modals import (
    modal_contrato,
    modal_detalle_contrato,
    modal_confirmar_cancelar,
)
from app.presentation.pages.contratos.pagos_state import PagosState
from app.presentation.pages.contratos.pagos_modals import (
    modal_pagos,
    modal_pago_form,
    modal_confirmar_eliminar_pago,
)
from app.presentation.pages.contratos.contrato_categorias_state import ContratoCategoriaState
from app.presentation.pages.contratos.contrato_categorias_modals import (
    modal_categorias,
    modal_categoria_form,
    modal_confirmar_eliminar_categoria,
)


# =============================================================================
# BADGES Y HELPERS
# =============================================================================

def badge_modalidad(modalidad: str) -> rx.Component:
    """Badge para mostrar la modalidad de adjudicación"""
    return rx.match(
        modalidad,
        ("ADJUDICACION_DIRECTA", rx.badge("Directa", color_scheme="blue", size="1")),
        ("INVITACION_3", rx.badge("Inv. 3", color_scheme="purple", size="1")),
        ("LICITACION_PUBLICA", rx.badge("Licitación", color_scheme="green", size="1")),
        rx.badge(modalidad, color_scheme="gray", size="1"),
    )


# =============================================================================
# ACCIONES DE CONTRATO
# =============================================================================

def acciones_contrato(contrato: dict) -> rx.Component:
    """Acciones específicas para contratos según su estatus"""
    es_borrador = contrato["estatus"] == "BORRADOR"
    es_activo = contrato["estatus"] == "ACTIVO"
    es_suspendido = contrato["estatus"] == "SUSPENDIDO"
    es_cancelado = contrato["estatus"] == "CANCELADO"
    puede_ver_pagos = es_activo | (contrato["estatus"] == "VENCIDO") | (contrato["estatus"] == "CERRADO")

    return tabla_action_buttons([
        # Ver detalle
        tabla_action_button(
            icon="eye",
            tooltip="Ver detalle",
            on_click=lambda: ContratosState.abrir_modal_detalle(contrato["id"]),
        ),
        # Personal/Categorías
        tabla_action_button(
            icon="users",
            tooltip="Personal",
            on_click=lambda: ContratoCategoriaState.abrir_modal_categorias(contrato),
            color_scheme="teal",
            visible=contrato["tiene_personal"] & ~es_cancelado,
        ),
        # Pagos
        tabla_action_button(
            icon="credit-card",
            tooltip="Pagos",
            on_click=lambda: PagosState.abrir_modal_pagos(contrato),
            color_scheme="purple",
            visible=puede_ver_pagos,
        ),
        # Editar
        tabla_action_button(
            icon="pencil",
            tooltip="Editar",
            on_click=lambda: ContratosState.abrir_modal_editar(contrato),
            color_scheme="blue",
            visible=(es_borrador | es_suspendido) & AuthState.puede_operar_contratos,
        ),
        # Activar
        tabla_action_button(
            icon="check",
            tooltip="Activar",
            on_click=lambda: ContratosState.activar_contrato(contrato),
            color_scheme="green",
            visible=es_borrador & AuthState.puede_operar_contratos,
        ),
        # Suspender
        tabla_action_button(
            icon="pause",
            tooltip="Suspender",
            on_click=lambda: ContratosState.suspender_contrato(contrato),
            color_scheme="orange",
            visible=es_activo & AuthState.puede_operar_contratos,
        ),
        # Reactivar
        tabla_action_button(
            icon="play",
            tooltip="Reactivar",
            on_click=lambda: ContratosState.reactivar_contrato(contrato),
            color_scheme="green",
            visible=es_suspendido & AuthState.puede_operar_contratos,
        ),
        # Cancelar
        tabla_action_button(
            icon="x",
            tooltip="Cancelar",
            on_click=lambda: ContratosState.abrir_confirmar_cancelar(contrato),
            color_scheme="red",
            visible=~es_cancelado & AuthState.puede_operar_contratos,
        ),
    ])


# =============================================================================
# TABLA DE CONTRATOS
# =============================================================================

def fila_contrato(contrato: dict) -> rx.Component:
    """Fila de la tabla para un contrato"""
    return rx.table.row(
        # Fecha Inicio
        rx.table.cell(
            rx.text(contrato["fecha_inicio_fmt"], size="2"),
        ),
        # Código
        rx.table.cell(
            rx.text(contrato["codigo"], weight="bold", size="2"),
        ),
        # Concepto
        rx.table.cell(
            rx.text(contrato["descripcion_objeto"], size="2"),
        ),
        # Tipo de Contrato
        rx.table.cell(
            rx.text(contrato["tipo_contrato"], size="2"),
        ),
        # Monto / Monto Maximo
        rx.table.cell(
            rx.text(contrato["monto_maximo_fmt"], size="2"),
        ),
        # Saldo Pendiente
        rx.table.cell(
            rx.text(contrato["saldo_pendiente_fmt"], size="2", color="orange"),
        ),
        # Empresa
        rx.table.cell(
            rx.cond(
                contrato["nombre_empresa"],
                rx.text(contrato["nombre_empresa"], size="2"),
                rx.text("Sin empresa", size="2", color=Colors.TEXT_MUTED),
            ),
        ),
        # Estatus
        rx.table.cell(
            status_badge_reactive(contrato["estatus"], show_icon=True),
        ),
        # Acciones
        rx.table.cell(
            acciones_contrato(contrato),
        ),
    )


ENCABEZADOS_CONTRATOS = [
    {"nombre": "Fecha", "ancho": "100px"},
    {"nombre": "Código", "ancho": "130px"},
    {"nombre": "Concepto", "ancho": "180px"},
    {"nombre": "Tipo", "ancho": "100px"},
    {"nombre": "Monto", "ancho": "100px"},
    {"nombre": "Saldo", "ancho": "100px"},
    {"nombre": "Empresa", "ancho": "100px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "140px"},
]


def tabla_contratos() -> rx.Component:
    """Vista de tabla de contratos"""
    return rx.cond(
        ContratosState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_CONTRATOS, filas=5),
        rx.cond(
            ContratosState.total_contratos > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_CONTRATOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            ContratosState.contratos,
                            fila_contrato,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                # Contador
                rx.text(
                    "Mostrando ", ContratosState.total_contratos, " contrato(s)",
                    size="2",
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=ContratosState.abrir_modal_crear),
        ),
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_contrato(contrato: dict) -> rx.Component:
    """Card individual para un contrato"""
    return rx.card(
        rx.vstack(
            # Header con código y estatus
            rx.hstack(
                rx.hstack(
                    rx.text(contrato["codigo"], weight="bold", size="3"),
                    badge_modalidad(contrato["modalidad_adjudicacion"]),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                status_badge_reactive(contrato["estatus"], show_icon=True),
                width="100%",
                align="center",
            ),

            rx.divider(),

            # Datos del contrato
            rx.vstack(
                rx.hstack(
                    rx.icon("calendar", size=14, color=Colors.TEXT_MUTED),
                    rx.text("Inicio:", size="2", color=Colors.TEXT_SECONDARY),
                    rx.text(contrato["fecha_inicio_fmt"], size="2"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.icon("dollar-sign", size=14, color=Colors.TEXT_MUTED),
                    rx.text("Monto:", size="2", color=Colors.TEXT_SECONDARY),
                    rx.text(contrato["monto_maximo_fmt"], size="2", weight="medium"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.icon("wallet", size=14, color=Colors.TEXT_MUTED),
                    rx.text("Saldo:", size="2", color=Colors.TEXT_SECONDARY),
                    rx.text(contrato["saldo_pendiente_fmt"], size="2", color="orange"),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    contrato["nombre_empresa"],
                    rx.hstack(
                        rx.icon("building-2", size=14, color=Colors.TEXT_MUTED),
                        rx.text("Empresa:", size="2", color=Colors.TEXT_SECONDARY),
                        rx.text(contrato["nombre_empresa"], size="2"),
                        spacing="2",
                        align="center",
                    ),
                ),
                rx.cond(
                    contrato["descripcion_objeto"],
                    rx.text(
                        contrato["descripcion_objeto"],
                        size="2",
                        color=Colors.TEXT_SECONDARY,
                        style={"max_width": "100%", "overflow": "hidden", "text_overflow": "ellipsis"},
                    ),
                ),
                spacing="2",
                align_items="start",
                width="100%",
            ),

            # Acciones
            rx.hstack(
                acciones_contrato(contrato),
                width="100%",
                justify="end",
            ),

            spacing="3",
            width="100%",
        ),
        width="100%",
        style={
            "transition": "all 0.2s ease",
            "_hover": {
                "box_shadow": Shadows.MD,
                "border_color": Colors.BORDER_STRONG,
            },
        },
    )


def grid_contratos() -> rx.Component:
    """Vista de cards de contratos"""
    return rx.cond(
        ContratosState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            ContratosState.total_contratos > 0,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        ContratosState.contratos,
                        card_contrato,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(350px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", ContratosState.total_contratos, " contrato(s)",
                    size="2",
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=ContratosState.abrir_modal_crear),
        ),
    )


# =============================================================================
# FILTROS AVANZADOS
# =============================================================================

def filtros_contratos() -> rx.Component:
    """Filtros para contratos"""
    return rx.hstack(
        # Filtro de fecha inicio (rango)
        rx.hstack(
            rx.vstack(
                rx.text("Desde", size="1", color=Colors.TEXT_MUTED),
                rx.input(
                    type="date",
                    value=ContratosState.filtro_fecha_desde,
                    on_change=ContratosState.set_filtro_fecha_desde,
                    width="140px",
                    size="2",
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Hasta", size="1", color=Colors.TEXT_MUTED),
                rx.input(
                    type="date",
                    value=ContratosState.filtro_fecha_hasta,
                    on_change=ContratosState.set_filtro_fecha_hasta,
                    width="140px",
                    size="2",
                ),
                spacing="1",
            ),
            spacing="2",
            align="end",
        ),
        # Switch inactivos
        switch_inactivos(
            checked=ContratosState.incluir_inactivos,
            on_change=ContratosState.set_incluir_inactivos,
            label="Mostrar inactivos",
        ),
        # Botón limpiar filtros
        rx.cond(
            ContratosState.tiene_filtros_activos,
            rx.button(
                rx.icon("x", size=14),
                "Limpiar",
                on_click=ContratosState.limpiar_filtros,
                variant="ghost",
                size="2",
            ),
        ),
        spacing="3",
        wrap="wrap",
        align="center",
    )


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

def contratos_page() -> rx.Component:
    """Página de Contratos usando el nuevo layout"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Contratos",
                subtitulo="Administre los contratos de servicio",
                icono="file-text",
                accion_principal=rx.cond(
                    AuthState.puede_operar_contratos,
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo Contrato",
                        on_click=ContratosState.abrir_modal_crear,
                        color_scheme="blue",
                    ),
                    rx.fragment(),
                ),
            ),
            toolbar=page_toolbar(
                search_value=ContratosState.filtro_busqueda,
                search_placeholder="Buscar por folio, empresa o concepto...",
                on_search_change=ContratosState.on_change_busqueda,
                on_search_clear=lambda: ContratosState.set_filtro_busqueda(""),
                filters=filtros_contratos(),
                show_view_toggle=True,
                current_view=ContratosState.view_mode,
                on_view_table=ContratosState.set_view_table,
                on_view_cards=ContratosState.set_view_cards,
            ),
            content=rx.vstack(
                # Contenido según vista
                rx.cond(
                    ContratosState.is_table_view,
                    tabla_contratos(),
                    grid_contratos(),
                ),

                # Modales de contratos
                modal_contrato(),
                modal_detalle_contrato(),
                modal_confirmar_cancelar(),

                # Modales de pagos
                modal_pagos(),
                modal_pago_form(),
                modal_confirmar_eliminar_pago(),

                # Modales de categorías de personal
                modal_categorias(),
                modal_categoria_form(),
                modal_confirmar_eliminar_categoria(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=ContratosState.cargar_datos_iniciales,
    )
