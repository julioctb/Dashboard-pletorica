"""
Página principal de Categorías de Puesto.
Muestra una tabla con las categorías y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.categorias_puesto.categorias_puesto_state import CategoriasPuestoState
from app.presentation.components.ui import (
    page_header,
    acciones_crud,
    estatus_badge,
    tabla_vacia,
    tabla,
    skeleton_tabla,
)
from app.presentation.components.categorias_puesto.categorias_puesto_modals import (
    modal_categoria_puesto,
    modal_confirmar_eliminar,
)

ENCABEZADOS_CAT = [
    { 'nombre': 'Clave', 'ancho': '80px'},
    { 'nombre': 'Nombre', 'ancho': '180px'},
    { 'nombre': 'Orden', 'ancho': '60px'},
    { 'nombre': 'Descripción' },
    { 'nombre': 'Estatus', 'ancho': '80px'},
    { 'nombre': 'Acciones', 'ancho': '80px'},
]


def fila_categoria(categoria: dict) -> rx.Component:
    """Fila de la tabla para una categoría"""
    return rx.table.row(
        
        # Clave
        rx.table.cell(
            rx.text(categoria["clave"], weight="bold"),
        ),
        # Nombre
        rx.table.cell(
            rx.text(categoria["nombre"]),
        ),
        # Orden
        rx.table.cell(
            rx.text(categoria["orden"].to(str), size="2"),
        ),
        # Descripción
        rx.table.cell(
            rx.text(
                rx.cond(
                    categoria["descripcion"],
                    categoria["descripcion"],
                    "-"
                ),
                color="gray",
                size="2",
            ),
            max_width="200px",
        ),
        # Estatus
        rx.table.cell(
            estatus_badge(categoria["estatus"]),
        ),
        # Acciones
        rx.table.cell(
            acciones_crud(
                item=categoria,
                on_editar=CategoriasPuestoState.abrir_modal_editar,
                on_eliminar=CategoriasPuestoState.abrir_confirmar_eliminar,
                on_reactivar=CategoriasPuestoState.activar_categoria,
            ),
        ),
    )









def filtro_tipo_servicio() -> rx.Component:
    """Select para filtrar por tipo de servicio"""
    return rx.hstack(
        rx.text("Tipo:", size="2", color="gray"),
        rx.select.root(
            rx.select.trigger(
                placeholder="Todos los tipos",
                width="180px",
            ),
            rx.select.content(
                rx.select.item("Todos", value="0"),
                rx.foreach(
                    CategoriasPuestoState.opciones_tipo_servicio,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=CategoriasPuestoState.filtro_tipo_servicio_id,
            on_change=CategoriasPuestoState.set_filtro_tipo_servicio_id,
        ),
        spacing="2",
        align="center",
    )


def breadcrumbs() -> rx.Component:
    """Breadcrumbs de navegación"""
    return rx.hstack(
        rx.link(
            rx.hstack(
                rx.icon("home", size=14),
                rx.text("Inicio", size="2"),
                spacing="1",
            ),
            href="/",
            color="gray",
            underline="none",
            _hover={"color": "blue"},
        ),
        rx.text("/", color="gray", size="2"),
        rx.link(
            rx.text("Tipos de Servicio", size="2"),
            href="/tipos-servicio",
            color="gray",
            underline="none",
            _hover={"color": "blue"},
        ),
        rx.cond(
            CategoriasPuestoState.filtro_tipo_servicio_id != "0",
            rx.hstack(
                rx.text("/", color="gray", size="2"),
                rx.text(
                    CategoriasPuestoState.nombre_tipo_filtrado,
                    size="2",
                    weight="medium",
                ),
                spacing="1",
            ),
            rx.hstack(
                rx.text("/", color="gray", size="2"),
                rx.text("Categorías", size="2", weight="medium"),
                spacing="1",
            ),
        ),
        spacing="1",
        align="center",
        padding_bottom="2",
    )


def contenido_principal() -> rx.Component:
    """Contenido principal de la página"""
    return rx.vstack(
        # Encabezado
        page_header(
            icono="users",
            titulo="Categorías de Puesto",
            subtitulo="Administre las categorías de puesto por tipo de servicio",
        ),
        # Breadcrumbs
        breadcrumbs(),

        # Contenido: skeleton, tabla o mensaje vacío
        rx.cond(
            CategoriasPuestoState.loading,
            skeleton_tabla(columnas=ENCABEZADOS_CAT, filas=5),
            rx.cond(
                CategoriasPuestoState.mostrar_tabla,
                tabla(
                    columnas=ENCABEZADOS_CAT,
                    lista=CategoriasPuestoState.categorias,
                    filas=fila_categoria,
                    filtro_busqueda=CategoriasPuestoState.filtro_busqueda,
                    on_change_busqueda=CategoriasPuestoState.on_change_busqueda,
                    on_clear_busqueda=CategoriasPuestoState.limpiar_busqueda,
                    boton_derecho=rx.button(
                        rx.icon("plus", size=16),
                        "Nueva Categoría",
                        on_click=CategoriasPuestoState.abrir_modal_crear,
                        color_scheme="blue",
                    ),
                ),
                tabla_vacia(onclick=CategoriasPuestoState.abrir_modal_crear),
            ),
        ),

        # Modales
        modal_categoria_puesto(),
        modal_confirmar_eliminar(),

        spacing="4",
        width="100%",
        padding="6",
    )


def categorias_puesto_page() -> rx.Component:
    """Página de Categorías de Puesto"""
    return rx.box(
        contenido_principal(),
        width="100%",
        min_height="100vh",
        on_mount=CategoriasPuestoState.cargar_datos_iniciales,
    )
