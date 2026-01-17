"""
Página principal de Categorías de Puesto.
Muestra una tabla con las categorías y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.categorias_puesto.categorias_puesto_state import CategoriasPuestoState
from app.presentation.components.ui.headers import page_header
from app.presentation.components.categorias_puesto.categorias_puesto_modals import (
    modal_categoria_puesto,
    modal_confirmar_eliminar,
)


def estatus_badge(estatus: str) -> rx.Component:
    """Badge de estatus con color"""
    return rx.badge(
        estatus,
        color_scheme=rx.cond(
            estatus == "ACTIVO",
            "green",
            "red"
        ),
        size="1",
    )


def boton_accion(
    icon: str,
    on_click: callable,
    tooltip: str,
    color_scheme: str = "gray",
    disabled: bool = False,
) -> rx.Component:
    """Botón de acción con icono y tooltip"""
    return rx.tooltip(
        rx.icon_button(
            rx.icon(icon, size=16),
            size="1",
            variant="ghost",
            color_scheme=color_scheme,
            on_click=on_click,
            disabled=disabled,
            cursor="pointer",
        ),
        content=tooltip,
    )


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
            rx.hstack(
                boton_accion(
                    icon="pencil",
                    on_click=lambda: CategoriasPuestoState.abrir_modal_editar(categoria),
                    tooltip="Editar",
                    color_scheme="blue",
                ),
                rx.cond(
                    categoria["estatus"] == "ACTIVO",
                    boton_accion(
                        icon="trash-2",
                        on_click=lambda: CategoriasPuestoState.abrir_confirmar_eliminar(categoria),
                        tooltip="Eliminar",
                        color_scheme="red",
                    ),
                    boton_accion(
                        icon="rotate-ccw",
                        on_click=lambda: CategoriasPuestoState.activar_categoria(categoria),
                        tooltip="Reactivar",
                        color_scheme="green",
                    ),
                ),
                spacing="1",
            ),
        ),
    )


def tabla_categorias() -> rx.Component:
    """Tabla de categorías de puesto"""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                
                rx.table.column_header_cell("Clave", width="80px"),
                rx.table.column_header_cell("Nombre", width="180px"),
                rx.table.column_header_cell("Orden", width="60px"),
                rx.table.column_header_cell("Descripción"),
                rx.table.column_header_cell("Estatus", width="80px"),
                rx.table.column_header_cell("Acciones", width="80px"),
            ),
        ),
        rx.table.body(
            rx.foreach(
                CategoriasPuestoState.categorias,
                fila_categoria
            ),
        ),
        width="100%",
        variant="surface",
    )


def tabla_vacia() -> rx.Component:
    """Mensaje cuando no hay categorías"""
    return rx.center(
        rx.vstack(
            rx.icon("inbox", size=48, color="gray"),
            rx.text(
                "No hay categorías de puesto registradas",
                color="gray",
                size="3"
            ),
            rx.button(
                rx.icon("plus", size=16),
                "Crear primera categoría",
                on_click=CategoriasPuestoState.abrir_modal_crear,
                color_scheme="blue",
            ),
            spacing="3",
            align="center",
            padding="8",
        ),
        width="100%",
        min_height="200px",
    )


def barra_herramientas() -> rx.Component:
    """Barra de herramientas con filtros y acciones"""
    return rx.hstack(
        # Búsqueda
        rx.hstack(
            rx.input(
                placeholder="Buscar...",
                value=CategoriasPuestoState.filtro_busqueda,
                on_change=CategoriasPuestoState.set_filtro_busqueda,
                on_key_down=CategoriasPuestoState.handle_key_down,
                width="180px",
            ),
            rx.icon_button(
                rx.icon("search", size=16),
                on_click=CategoriasPuestoState.buscar_categorias,
                variant="soft",
            ),
            spacing="2",
        ),

        # Toggle inactivas
        rx.checkbox(
            "Inactivas",
            checked=CategoriasPuestoState.incluir_inactivas,
            on_change=CategoriasPuestoState.toggle_inactivas,
            size="2",
        ),

        rx.spacer(),

        # Botón crear
        rx.button(
            rx.icon("plus", size=16),
            "Nueva Categoría",
            on_click=CategoriasPuestoState.abrir_modal_crear,
            color_scheme="blue",
        ),

        spacing="4",
        width="100%",
        padding="4",
        align="center",
    )


def contador_registros() -> rx.Component:
    """Contador de registros"""
    return rx.text(
        rx.cond(
            CategoriasPuestoState.total_categorias > 0,
            f"Mostrando {CategoriasPuestoState.total_categorias} categoría(s)",
            "No hay resultados"
        ),
        size="2",
        color="gray",
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
        # Breadcrumbs
        breadcrumbs(),

        # Encabezado
        rx.hstack(
            page_header(
                icono="users",
                titulo="Categorías de Puesto",
                subtitulo="Administre las categorías de puesto por tipo de servicio"
            ),
        ),

        # Barra de herramientas
        barra_herramientas(),

        # Contador
        #contador_registros(),

        # Contenido: tabla o mensaje vacío
        rx.cond(
            CategoriasPuestoState.loading,
            rx.center(
                rx.spinner(size="3"),
                width="100%",
                min_height="200px",
            ),
            rx.cond(
                CategoriasPuestoState.total_categorias > 0,
                tabla_categorias(),
                tabla_vacia(),
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
