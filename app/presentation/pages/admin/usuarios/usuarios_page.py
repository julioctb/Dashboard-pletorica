"""
Pagina de gestion de usuarios para administradores.
Muestra tabla de usuarios con filtros, CRUD y gestion de empresas.
"""
import reflex as rx

from app.presentation.pages.admin.usuarios.usuarios_state import UsuariosAdminState
from app.presentation.pages.admin.usuarios.usuarios_modals import (
    modal_crear_usuario,
    modal_editar_usuario,
    modal_gestionar_empresas,
    modal_confirmar_desactivar,
)
from app.presentation.layout import (
    page_layout,
    page_header,
    page_toolbar,
)
from app.presentation.components.ui import skeleton_tabla


# =============================================================================
# BADGES
# =============================================================================

def _badge_rol(rol: str) -> rx.Component:
    """Badge para el rol del usuario."""
    return rx.match(
        rol,
        ("admin", rx.badge("Admin", color_scheme="blue", variant="soft", size="1")),
        ("client", rx.badge("Cliente", color_scheme="gray", variant="soft", size="1")),
        rx.badge(rol, size="1"),
    )


def _badge_estado(activo: rx.Var[bool]) -> rx.Component:
    """Badge para el estado activo/inactivo."""
    return rx.cond(
        activo,
        rx.badge("Activo", color_scheme="green", variant="soft", size="1"),
        rx.badge("Inactivo", color_scheme="red", variant="soft", size="1"),
    )


# =============================================================================
# ACCIONES
# =============================================================================

def _acciones_usuario(usuario: dict) -> rx.Component:
    """Botones de accion para un usuario."""
    return rx.hstack(
        # Editar
        rx.tooltip(
            rx.icon_button(
                rx.icon("pencil", size=14),
                size="1",
                variant="ghost",
                color_scheme="blue",
                on_click=lambda: UsuariosAdminState.abrir_modal_editar(usuario),
            ),
            content="Editar",
        ),
        # Gestionar empresas
        rx.tooltip(
            rx.icon_button(
                rx.icon("building", size=14),
                size="1",
                variant="ghost",
                color_scheme="teal",
                on_click=lambda: UsuariosAdminState.abrir_modal_empresas(usuario),
            ),
            content="Gestionar empresas",
        ),
        # Activar / Desactivar
        rx.cond(
            usuario["activo"],
            rx.tooltip(
                rx.icon_button(
                    rx.icon("user-x", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=lambda: UsuariosAdminState.confirmar_desactivar(usuario),
                ),
                content="Desactivar",
            ),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("user-check", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="green",
                    on_click=lambda: UsuariosAdminState.activar_usuario_accion(
                        usuario["id"].to(str)
                    ),
                ),
                content="Activar",
            ),
        ),
        spacing="1",
    )


# =============================================================================
# FILTROS
# =============================================================================

def _filtros() -> rx.Component:
    """Barra de filtros adicionales."""
    return rx.hstack(
        # Filtro por rol
        rx.select.root(
            rx.select.trigger(placeholder="Todos los roles"),
            rx.select.content(
                rx.select.item("Todos", value="all"),
                rx.select.item("Administradores", value="admin"),
                rx.select.item("Clientes", value="client"),
            ),
            value=UsuariosAdminState.filtro_rol_select,
            on_change=UsuariosAdminState.set_filtro_rol_select,
            size="2",
        ),
        # Incluir inactivos
        rx.hstack(
            rx.checkbox(
                checked=UsuariosAdminState.incluir_inactivos,
                on_change=UsuariosAdminState.set_incluir_inactivos,
                size="1",
            ),
            rx.text("Incluir inactivos", size="2", color="gray"),
            spacing="2",
            align="center",
        ),
        # Boton aplicar
        rx.button(
            rx.icon("filter", size=14),
            "Filtrar",
            on_click=UsuariosAdminState.aplicar_filtros,
            variant="soft",
            size="2",
        ),
        spacing="3",
        align="center",
    )


# =============================================================================
# TABLA
# =============================================================================

def _fila_usuario(usuario: dict) -> rx.Component:
    """Fila de la tabla para un usuario."""
    return rx.table.row(
        # Nombre
        rx.table.cell(
            rx.text(usuario["nombre_completo"], weight="medium", size="2"),
        ),
        # Email
        rx.table.cell(
            rx.cond(
                usuario["email"],
                rx.text(usuario["email"], size="2", color="gray"),
                rx.text("-", size="2", color="gray"),
            ),
        ),
        # Rol
        rx.table.cell(
            _badge_rol(usuario["rol"]),
        ),
        # Estado
        rx.table.cell(
            _badge_estado(usuario["activo"]),
        ),
        # Empresas
        rx.table.cell(
            rx.hstack(
                rx.text(usuario["cantidad_empresas"], size="2"),
                rx.cond(
                    usuario["empresa_principal"],
                    rx.text(
                        usuario["empresa_principal"],
                        size="1",
                        color="gray",
                        style={"max_width": "120px", "overflow": "hidden", "text_overflow": "ellipsis", "white_space": "nowrap"},
                    ),
                ),
                spacing="2",
                align="center",
            ),
        ),
        # Ultimo acceso
        rx.table.cell(
            rx.cond(
                usuario["ultimo_acceso"],
                rx.text(usuario["ultimo_acceso"], size="1", color="gray"),
                rx.text("Nunca", size="1", color="gray"),
            ),
        ),
        # Acciones
        rx.table.cell(
            _acciones_usuario(usuario),
        ),
    )


ENCABEZADOS_USUARIOS = [
    {"nombre": "Nombre", "ancho": "auto"},
    {"nombre": "Email", "ancho": "200px"},
    {"nombre": "Rol", "ancho": "100px"},
    {"nombre": "Estado", "ancho": "90px"},
    {"nombre": "Empresas", "ancho": "160px"},
    {"nombre": "Ultimo acceso", "ancho": "140px"},
    {"nombre": "Acciones", "ancho": "120px"},
]


def _tabla_usuarios() -> rx.Component:
    """Tabla principal de usuarios."""
    return rx.cond(
        UsuariosAdminState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_USUARIOS, filas=5),
        rx.cond(
            UsuariosAdminState.total_usuarios > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_USUARIOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            UsuariosAdminState.usuarios,
                            _fila_usuario,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                # Contador
                rx.text(
                    "Mostrando ", UsuariosAdminState.total_usuarios, " usuario(s)",
                    size="2",
                    color="gray",
                ),
                width="100%",
                spacing="3",
            ),
            # Estado vacio
            rx.center(
                rx.vstack(
                    rx.icon("users", size=48, color="var(--gray-6)"),
                    rx.text("No hay usuarios registrados", color="gray", size="3"),
                    rx.button(
                        rx.icon("user-plus", size=16),
                        "Crear primer usuario",
                        on_click=UsuariosAdminState.abrir_modal_crear,
                        color_scheme="blue",
                        variant="soft",
                    ),
                    spacing="3",
                    align="center",
                ),
                padding="12",
            ),
        ),
    )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def usuarios_admin_page() -> rx.Component:
    """Pagina de gestion de usuarios para administradores."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Gestion de Usuarios",
                subtitulo="Administre los usuarios del sistema y sus permisos",
                icono="users",
                accion_principal=rx.button(
                    rx.icon("user-plus", size=16),
                    "Nuevo Usuario",
                    on_click=UsuariosAdminState.abrir_modal_crear,
                    color_scheme="blue",
                ),
            ),
            toolbar=page_toolbar(
                search_value=UsuariosAdminState.filtro_busqueda,
                search_placeholder="Buscar por nombre...",
                on_search_change=UsuariosAdminState.set_filtro_busqueda,
                on_search_clear=lambda: UsuariosAdminState.set_filtro_busqueda(""),
                show_view_toggle=False,
                filters=_filtros(),
            ),
            content=rx.vstack(
                _tabla_usuarios(),

                # Modales
                modal_crear_usuario(),
                modal_editar_usuario(),
                modal_gestionar_empresas(),
                modal_confirmar_desactivar(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=UsuariosAdminState.on_mount_admin,
    )
