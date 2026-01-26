"""
Pagina principal de Requisiciones.
Muestra tabla con requisiciones, filtros y acciones CRUD + transiciones de estado.
"""
import reflex as rx
from app.presentation.pages.requisiciones.requisiciones_state import RequisicionesState
from app.presentation.layout import (
    page_layout,
    page_header,
    page_toolbar,
)
from app.presentation.components.requisiciones import (
    requisicion_tabla,
    requisicion_form_modal,
)
from app.presentation.pages.requisiciones.requisiciones_modals import (
    modal_detalle_requisicion,
    modal_confirmar_eliminar_requisicion,
    modal_confirmar_estado,
    modal_adjudicar_requisicion,
)


# =============================================================================
# FILTROS
# =============================================================================

def _filtros_requisiciones() -> rx.Component:
    """Filtros para requisiciones: estado y tipo."""
    return rx.hstack(
        # Filtro de estado
        rx.select.root(
            rx.select.trigger(placeholder="Estado", width="160px"),
            rx.select.content(
                rx.foreach(
                    RequisicionesState.opciones_estado,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=RequisicionesState.filtro_estado,
            on_change=RequisicionesState.set_filtro_estado,
        ),
        # Filtro de tipo
        rx.select.root(
            rx.select.trigger(placeholder="Tipo", width="160px"),
            rx.select.content(
                rx.foreach(
                    RequisicionesState.opciones_tipo_contratacion,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=RequisicionesState.filtro_tipo,
            on_change=RequisicionesState.set_filtro_tipo,
        ),
        # Boton aplicar filtros
        rx.button(
            "Filtrar",
            on_click=RequisicionesState.aplicar_filtros,
            variant="soft",
            size="2",
        ),
        # Boton limpiar
        rx.button(
            rx.icon("x", size=14),
            "Limpiar",
            on_click=RequisicionesState.limpiar_filtros,
            variant="ghost",
            size="2",
        ),
        spacing="2",
        wrap="wrap",
        align="center",
    )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def requisiciones_page() -> rx.Component:
    """Pagina de Requisiciones."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Requisiciones",
                subtitulo="Gestione las requisiciones de compra",
                icono="clipboard-list",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nueva Requisicion",
                    on_click=RequisicionesState.abrir_modal_crear,
                    color_scheme="blue",
                ),
            ),
            toolbar=page_toolbar(
                search_value=RequisicionesState.filtro_busqueda,
                search_placeholder="Buscar por numero, objeto o dependencia...",
                on_search_change=RequisicionesState.set_filtro_busqueda,
                on_search_clear=lambda: RequisicionesState.set_filtro_busqueda(""),
                filters=_filtros_requisiciones(),
                show_view_toggle=False,
            ),
            content=rx.vstack(
                # Tabla de requisiciones
                requisicion_tabla(),

                # Modal de formulario (crear)
                requisicion_form_modal(
                    open_var=RequisicionesState.mostrar_modal_crear,
                    on_close=RequisicionesState.cerrar_modal_crear,
                ),

                # Modal de formulario (editar)
                requisicion_form_modal(
                    open_var=RequisicionesState.mostrar_modal_editar,
                    on_close=RequisicionesState.cerrar_modal_editar,
                ),

                # Modales de acciones
                modal_detalle_requisicion(),
                modal_confirmar_eliminar_requisicion(),
                modal_confirmar_estado(),
                modal_adjudicar_requisicion(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=RequisicionesState.on_mount,
    )
