"""
Página principal de Tipos de Servicio.
Muestra una tabla con los tipos y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.tipo_servicio.tipo_servicio_state import TipoServicioState
from app.presentation.components.ui.headers import page_header
from app.presentation.components.tipo_servicio.tipo_servicio_modals import (
    modal_tipo_servicio,
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


def fila_tipo(tipo: dict) -> rx.Component:
    """Fila de la tabla para un tipo"""
    return rx.table.row(
        # Clave
        rx.table.cell(
            rx.text(tipo["clave"], weight="bold"),
        ),
        # Nombre
        rx.table.cell(
            rx.text(tipo["nombre"]),
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
            rx.hstack(
                boton_accion(
                    icon="pencil",
                    on_click=lambda: TipoServicioState.abrir_modal_editar(tipo),
                    tooltip="Editar",
                    color_scheme="blue",
                ),
                rx.cond(
                    tipo["estatus"] == "ACTIVO",
                    boton_accion(
                        icon="trash-2",
                        on_click=lambda: TipoServicioState.abrir_confirmar_eliminar(tipo),
                        tooltip="Eliminar",
                        color_scheme="red",
                    ),
                    boton_accion(
                        icon="rotate-ccw",
                        on_click=lambda: TipoServicioState.activar_tipo(tipo),
                        tooltip="Reactivar",
                        color_scheme="green",
                    ),
                ),
                spacing="1",
            ),
        ),
    )


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


def tabla_vacia() -> rx.Component:
    """Mensaje cuando no hay tipos"""
    return rx.center(
        rx.vstack(
            rx.icon("inbox", size=48, color="gray"),
            rx.text(
                "No hay tipos de servicio registrados",
                color="gray",
                size="3"
            ),
            rx.button(
                rx.icon("plus", size=16),
                "Crear primer tipo",
                on_click=TipoServicioState.abrir_modal_crear,
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
        # Botón crear
        rx.button(
            rx.icon("plus", size=16),
            "Nuevo Tipo",
            on_click=TipoServicioState.abrir_modal_crear,
            color_scheme="blue",
        ),

        rx.spacer(),

        # Búsqueda
        rx.hstack(
            rx.input(
                placeholder="Buscar por clave o nombre...",
                value=TipoServicioState.filtro_busqueda,
                on_change=TipoServicioState.set_filtro_busqueda,
                on_key_down=TipoServicioState.handle_key_down,
                width="250px",
            ),
            rx.icon_button(
                rx.icon("search", size=16),
                on_click=TipoServicioState.buscar_tipos,
                variant="soft",
            ),
            spacing="2",
        ),

        # Toggle inactivas
        rx.hstack(
            rx.checkbox(
                "Mostrar inactivas",
                checked=TipoServicioState.incluir_inactivas,
                on_change=TipoServicioState.toggle_inactivas,
            ),
            spacing="2",
            align="center",
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
            TipoServicioState.total_tipos > 0,
            f"Mostrando {TipoServicioState.total_tipos} tipo(s)",
            "No hay resultados"
        ),
        size="2",
        color="gray",
    )


def contenido_principal() -> rx.Component:
    """Contenido principal de la página"""
    return rx.vstack(
        # Encabezado
       rx.hstack(
            page_header(
                icono="folder-cog",
                titulo="Tipos de Servicio",
                subtitulo="Administre los tipos de servicio del sistema"
            ),
       ),
        # Barra de herramientas
        barra_herramientas(),

        # Contenido: tabla o mensaje vacío
        rx.cond(
            TipoServicioState.loading,
            rx.center(
                rx.spinner(size="3"),
                width="100%",
                min_height="200px",
            ),
            rx.cond(
                TipoServicioState.total_tipos > 0,
                tabla_tipos(),
                tabla_vacia(),
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
