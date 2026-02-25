"""
Pagina de gestion de usuarios para administradores.
Muestra tabla de usuarios con filtros, CRUD y gestion de empresas.
"""
import reflex as rx

from app.presentation.components.shared.auth_state import AuthState
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
from app.presentation.components.ui import (
    empty_state_card,
    table_cell_text,
    table_shell,
    tabla_action_button,
    tabla_action_buttons,
)


# =============================================================================
# BADGES
# =============================================================================

def _badge_rol(rol: str) -> rx.Component:
    """Badge para el rol del usuario."""
    return rx.match(
        rol,
        ("admin", rx.badge("Admin", color_scheme="blue", variant="soft", size="1")),
        ("superadmin", rx.badge("Super Admin", color_scheme="blue", variant="soft", size="1")),
        ("institucion", rx.badge("Institución", color_scheme="amber", variant="soft", size="1")),
        ("proveedor", rx.badge("Proveedor", color_scheme="teal", variant="soft", size="1")),
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
    es_activo = usuario["activo"]
    puede_gestionar = usuario["_gestionable"]
    puede_gestionar_empresas = usuario["_puede_gestionar_empresas"]

    return tabla_action_buttons([
        # Editar
        tabla_action_button(
            icon="pencil",
            tooltip="Editar",
            on_click=lambda: UsuariosAdminState.abrir_modal_editar(usuario),
            color_scheme="blue",
            visible=puede_gestionar,
        ),
        # Gestionar empresas
        tabla_action_button(
            icon="building",
            tooltip="Gestionar empresas",
            on_click=lambda: UsuariosAdminState.abrir_modal_empresas(usuario),
            color_scheme="teal",
            visible=puede_gestionar & puede_gestionar_empresas,
        ),
        # Desactivar (si activo)
        tabla_action_button(
            icon="user-x",
            tooltip="Desactivar",
            on_click=lambda: UsuariosAdminState.confirmar_desactivar(usuario),
            color_scheme="red",
            visible=es_activo & puede_gestionar,
        ),
        # Activar (si inactivo)
        tabla_action_button(
            icon="user-check",
            tooltip="Activar",
            on_click=lambda: UsuariosAdminState.activar_usuario_accion(usuario["id"].to(str)),
            color_scheme="green",
            visible=(~es_activo) & puede_gestionar,
        ),
    ])


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
                rx.select.item("Instituciones", value="institucion"),
                rx.select.item("Proveedores", value="proveedor"),
                rx.select.item("Clientes (legacy)", value="client"),
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
        table_cell_text(usuario["nombre_completo"], weight="500", size="0.875rem"),
        # Email
        table_cell_text(usuario["email"], fallback="-", tone="secondary", size="0.875rem"),
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
        table_cell_text(usuario["ultimo_acceso"], fallback="Nunca", tone="secondary", size="0.75rem"),
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
    return table_shell(
        loading=UsuariosAdminState.loading,
        headers=ENCABEZADOS_USUARIOS,
        rows=UsuariosAdminState.usuarios,
        row_renderer=_fila_usuario,
        has_rows=UsuariosAdminState.total_usuarios > 0,
        empty_component=empty_state_card(
            title="No hay usuarios registrados",
            description="Cree el primer usuario para iniciar la administración.",
            icon="users",
            action_button=rx.button(
                rx.icon("user-plus", size=16),
                "Crear primer usuario",
                on_click=UsuariosAdminState.abrir_modal_crear,
                color_scheme="blue",
                variant="soft",
            ),
        ),
        total_caption="Mostrando " + UsuariosAdminState.total_usuarios.to(str) + " usuario(s)",
        loading_rows=5,
    )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def usuarios_admin_page() -> rx.Component:
    """Pagina de gestion de usuarios para super admins."""
    return rx.cond(
        AuthState.es_superadmin | AuthState.es_super_admin | AuthState.es_institucion,
        _contenido_usuarios(),
        rx.center(
            rx.vstack(
                rx.icon("shield-x", size=48, color="var(--red-9)"),
                rx.text("Acceso denegado", size="4", weight="bold"),
                rx.text("No tiene permiso para gestionar usuarios.", size="2", color="gray"),
                spacing="3",
                align="center",
            ),
            min_height="60vh",
        ),
    )


def _contenido_usuarios() -> rx.Component:
    """Contenido de la pagina de usuarios (super admin + institucional)."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Gestion de Usuarios",
                subtitulo="Administre usuarios, roles de plataforma y perfiles por empresa",
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
        on_mount=UsuariosAdminState.on_mount_usuarios,
    )
