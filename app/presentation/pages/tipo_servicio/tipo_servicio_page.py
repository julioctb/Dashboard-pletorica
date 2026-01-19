"""
Página principal de Tipos de Servicio.
Muestra una tabla con los tipos y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.tipo_servicio.tipo_servicio_state import TipoServicioState
from app.presentation.components.ui import (
    page_header,
    acciones_crud,
    estatus_badge,
    tabla_vacia,
    tabla,
    skeleton_tabla,
)


from app.presentation.components.tipo_servicio.tipo_servicio_modals import (
    modal_tipo_servicio,
    modal_confirmar_eliminar,
)



def fila_tipo(tipo: dict) -> rx.Component:
    """Fila de la tabla para un tipo"""
    return rx.table.row(
        # Clave
        rx.table.cell(
            rx.text(tipo["clave"], weight="bold"),
        ),
        # Nombre (click navega a categorías de puesto)
        rx.table.cell(
            rx.link(
                rx.text(
                    tipo["nombre"],
                    _hover={"text_decoration": "underline"},
                ),
                href="/categorias-puesto?tipo=" + tipo["id"].to(str),
                color="inherit",
                underline="none",
            ),
        ),
        # Descripción
        rx.table.cell(
            rx.text(
                rx.cond(
                    tipo["descripcion"],
                    tipo["descripcion"],
                    "-"
                ),
                color="gray",
                size="2",
            ),
            max_width="300px",
        ),
        # Estatus
        rx.table.cell(
            estatus_badge(tipo["estatus"]),
        ),
        # Acciones
        rx.table.cell(
            acciones_crud(
                item=tipo,
                on_editar=TipoServicioState.abrir_modal_editar,
                on_eliminar=TipoServicioState.abrir_confirmar_eliminar,
                on_reactivar=TipoServicioState.activar_tipo,
            ),
        ),
    )

ENCABEZADOS_TIP = [
    { 'nombre': 'Clave', 'ancho': '100px'},
    { 'nombre': 'Nombre', 'ancho': '200px'},
    { 'nombre': 'Descripción' },
    { 'nombre': 'Estatus', 'ancho': '100px'},
    { 'nombre': 'Acciones', 'ancho': '100px'},
]

def tabla_tipos() -> rx.Component:
    """Tabla de tipos de servicio"""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Clave", width="100px"),
                rx.table.column_header_cell("Nombre", width="200px"),
                rx.table.column_header_cell("Descripción"),
                rx.table.column_header_cell("Estatus", width="100px"),
                rx.table.column_header_cell("Acciones", width="100px"),
            ),
        ),
        rx.table.body(
            rx.foreach(
                TipoServicioState.tipos,
                fila_tipo
            ),
        ),
        width="100%",
        variant="surface",
    )



def contenido_principal() -> rx.Component:
    """Contenido principal de la página"""
    return rx.vstack(
        # Encabezado
        page_header(
            icono="briefcase",
            titulo="Servicios",
            subtitulo="Administre los tipos de servicio del sistema",
        ),

        # Contenido: skeleton, tabla o mensaje vacío
        rx.cond(
            TipoServicioState.loading,
            skeleton_tabla(columnas=ENCABEZADOS_TIP, filas=5),
            rx.cond(
                TipoServicioState.mostrar_tabla,
                tabla(
                    columnas=ENCABEZADOS_TIP,
                    lista=TipoServicioState.tipos,
                    filas=fila_tipo,
                    filtro_busqueda=TipoServicioState.filtro_busqueda,
                    on_change_busqueda=TipoServicioState.on_change_busqueda,
                    on_clear_busqueda=TipoServicioState.limpiar_busqueda,
                    boton_derecho=rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo Servicio",
                        on_click=TipoServicioState.abrir_modal_crear,
                        color_scheme="blue",
                    ),
                ),
                tabla_vacia(onclick=TipoServicioState.abrir_modal_crear),
            ),
        ),

        # Modales
        modal_tipo_servicio(),
        modal_confirmar_eliminar(),

        spacing="4",
        width="100%",
        padding="6",
    )


def tipo_servicio_page() -> rx.Component:
    """Página de Tipos de Servicio"""
    return rx.box(
        contenido_principal(),
        width="100%",
        min_height="100vh",
        on_mount=TipoServicioState.cargar_tipos,
    )
