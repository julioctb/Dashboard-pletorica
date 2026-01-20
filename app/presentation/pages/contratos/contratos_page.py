"""
Página principal de Contratos.
Muestra una tabla con los contratos y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.contratos.contratos_state import ContratosState
from app.presentation.components.ui import (
    page_header,
    acciones_crud,
    estatus_badge,
    tabla_vacia,
    tabla,
    skeleton_tabla,
    form_select,
    switch_inactivos,
)

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


def badge_modalidad(modalidad: str) -> rx.Component:
    """Badge para mostrar la modalidad de adjudicación"""
    return rx.match(
        modalidad,
        ("ADJUDICACION_DIRECTA", rx.badge("Directa", color_scheme="blue", size="1")),
        ("INVITACION_3", rx.badge("Inv. 3", color_scheme="purple", size="1")),
        ("LICITACION_PUBLICA", rx.badge("Licitación", color_scheme="green", size="1")),
        rx.badge(modalidad, color_scheme="gray", size="1"),
    )


def acciones_contrato(contrato: dict) -> rx.Component:
    """Acciones específicas para contratos según su estatus"""
    return rx.hstack(
        # Ver detalle
        rx.icon_button(
            rx.icon("eye", size=14),
            size="1",
            variant="ghost",
            color_scheme="gray",
            on_click=lambda: ContratosState.abrir_modal_detalle(contrato["id"]),
            title="Ver detalle",
        ),
        # Personal/Categorías (solo si tiene_personal = true y no está cancelado)
        rx.cond(
            contrato["tiene_personal"] & (contrato["estatus"] != "CANCELADO"),
            rx.icon_button(
                rx.icon("users", size=14),
                size="1",
                variant="ghost",
                color_scheme="teal",
                on_click=lambda: ContratoCategoriaState.abrir_modal_categorias(contrato),
                title="Personal",
            ),
        ),
        # Pagos (solo si está activo, vencido o cerrado)
        rx.cond(
            (contrato["estatus"] == "ACTIVO") |
            (contrato["estatus"] == "VENCIDO") |
            (contrato["estatus"] == "CERRADO"),
            rx.icon_button(
                rx.icon("credit-card", size=14),
                size="1",
                variant="ghost",
                color_scheme="purple",
                on_click=lambda: PagosState.abrir_modal_pagos(contrato),
                title="Pagos",
            ),
        ),
        # Editar (solo si puede modificarse)
        rx.cond(
            (contrato["estatus"] == "BORRADOR") |
            (contrato["estatus"] == "ACTIVO") |
            (contrato["estatus"] == "SUSPENDIDO"),
            rx.icon_button(
                rx.icon("pencil", size=14),
                size="1",
                variant="ghost",
                color_scheme="blue",
                on_click=lambda: ContratosState.abrir_modal_editar(contrato),
                title="Editar",
            ),
        ),
        # Activar (solo si está en borrador)
        rx.cond(
            contrato["estatus"] == "BORRADOR",
            rx.icon_button(
                rx.icon("check", size=14),
                size="1",
                variant="ghost",
                color_scheme="green",
                on_click=lambda: ContratosState.activar_contrato(contrato),
                title="Activar",
            ),
        ),
        # Suspender (solo si está activo)
        rx.cond(
            contrato["estatus"] == "ACTIVO",
            rx.icon_button(
                rx.icon("pause", size=14),
                size="1",
                variant="ghost",
                color_scheme="orange",
                on_click=lambda: ContratosState.suspender_contrato(contrato),
                title="Suspender",
            ),
        ),
        # Reactivar (solo si está suspendido)
        rx.cond(
            contrato["estatus"] == "SUSPENDIDO",
            rx.icon_button(
                rx.icon("play", size=14),
                size="1",
                variant="ghost",
                color_scheme="green",
                on_click=lambda: ContratosState.reactivar_contrato(contrato),
                title="Reactivar",
            ),
        ),
        # Cancelar (si no está cancelado)
        rx.cond(
            contrato["estatus"] != "CANCELADO",
            rx.icon_button(
                rx.icon("x", size=14),
                size="1",
                variant="ghost",
                color_scheme="red",
                on_click=lambda: ContratosState.abrir_confirmar_cancelar(contrato),
                title="Cancelar",
            ),
        ),
        spacing="1",
    )


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
            rx.text(
                rx.cond(
                    contrato["nombre_empresa"],
                    contrato["nombre_empresa"],
                    "Sin empresa"
                ),
                size="2",
            ),
        ),
        
       
        # Estatus
        rx.table.cell(
            estatus_badge(contrato["estatus"]),
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
    {"nombre": "Tipo de Contrato", "ancho": "150px"},
    {"nombre": "Monto", "ancho": "100px"},
    {"nombre": "Saldo", "ancho": "100px"},
    {"nombre": "Empresa", "ancho": "100px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "140px"},
]


def filtros_avanzados() -> rx.Component:
    """Filtros avanzados para contratos"""
    return rx.hstack(
        # Filtro por empresa
        rx.select.root(
            rx.select.trigger(placeholder="Empresa", width="180px"),
            rx.select.content(
                rx.select.item("Todas", value="0"),
                rx.foreach(
                    ContratosState.opciones_empresa,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"])
                ),
            ),
            value=ContratosState.filtro_empresa_id,
            on_change=ContratosState.set_filtro_empresa_id,
        ),
        # Filtro por tipo de servicio
        rx.select.root(
            rx.select.trigger(placeholder="Tipo servicio", width="180px"),
            rx.select.content(
                rx.select.item("Todos", value="0"),
                rx.foreach(
                    ContratosState.opciones_tipo_servicio,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"])
                ),
            ),
            value=ContratosState.filtro_tipo_servicio_id,
            on_change=ContratosState.set_filtro_tipo_servicio_id,
        ),
        # Filtro por estatus
        rx.select.root(
            rx.select.trigger(placeholder="Estatus", width="140px"),
            rx.select.content(
                rx.select.item("Todos", value="TODOS"),
                rx.foreach(
                    ContratosState.opciones_estatus,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"])
                ),
            ),
            value=ContratosState.filtro_estatus,
            on_change=ContratosState.set_filtro_estatus,
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


def contenido_principal() -> rx.Component:
    """Contenido principal de la página"""
    return rx.vstack(
        # Encabezado
        page_header(
            icono="file-text",
            titulo="Contratos",
            subtitulo="Administre los contratos de servicio",
        ),

        # Filtros avanzados
        rx.card(
            filtros_avanzados(),
            width="100%",
            padding="4",
        ),

        # Contenido: skeleton, tabla o mensaje vacío
        rx.cond(
            ContratosState.loading,
            skeleton_tabla(columnas=ENCABEZADOS_CONTRATOS, filas=5),
            rx.cond(
                ContratosState.mostrar_tabla,
                tabla(
                    columnas=ENCABEZADOS_CONTRATOS,
                    lista=ContratosState.contratos,
                    filas=fila_contrato,
                    filtro_busqueda=ContratosState.filtro_busqueda,
                    on_change_busqueda=ContratosState.on_change_busqueda,
                    on_clear_busqueda=lambda: ContratosState.set_filtro_busqueda(""),
                    boton_derecho=rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo Contrato",
                        on_click=ContratosState.abrir_modal_crear,
                        color_scheme="blue",
                    ),
                ),
                tabla_vacia(
                    onclick=ContratosState.abrir_modal_crear
                ),
            ),
        ),

        # Contador de registros
        rx.cond(
            ContratosState.total_contratos > 0,
            rx.text(
                f"Mostrando {ContratosState.total_contratos} contrato(s)",
                size="2",
                color="gray",
            ),
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
        padding="6",
    )


def contratos_page() -> rx.Component:
    """Página de Contratos"""
    return rx.box(
        contenido_principal(),
        width="100%",
        min_height="100vh",
        on_mount=ContratosState.cargar_datos_iniciales,
    )
