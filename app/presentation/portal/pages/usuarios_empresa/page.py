"""
Pagina de Usuarios de la Empresa — Portal.

Solo accesible para admin_empresa. Permite gestionar el equipo:
crear usuarios, editar rol/permisos, desactivar/reactivar.
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.theme import Colors, Typography, Spacing
from app.core.constants.permisos import ROLES_ASIGNABLES_POR_ADMIN_EMPRESA

from .state import UsuariosEmpresaState
from .modals import (
    modal_crear_usuario_empresa,
    modal_editar_usuario_empresa,
    modal_toggle_activo_usuario,
)


# =============================================================================
# BADGE DE ROL
# =============================================================================

_ROL_COLORES = {
    "rrhh": "blue",
    "operaciones": "orange",
    "contabilidad": "purple",
    "lectura": "gray",
}


def _badge_rol(rol: str) -> rx.Component:
    """Badge con el rol de empresa."""
    labels = {
        "rrhh": "RRHH",
        "operaciones": "Operaciones",
        "contabilidad": "Contabilidad",
        "lectura": "Solo lectura",
    }
    return rx.foreach(
        ROLES_ASIGNABLES_POR_ADMIN_EMPRESA,
        lambda _: rx.fragment(),  # dummy — ver abajo
    )


def _badge_rol_usuario(usuario: dict) -> rx.Component:
    """Badge de rol con color."""
    rol = usuario["rol_empresa"]
    return rx.badge(
        rx.cond(rol == "rrhh", "RRHH",
            rx.cond(rol == "operaciones", "Operaciones",
                rx.cond(rol == "contabilidad", "Contabilidad",
                    "Solo lectura"
                )
            )
        ),
        color_scheme=rx.cond(rol == "rrhh", "blue",
            rx.cond(rol == "operaciones", "orange",
                rx.cond(rol == "contabilidad", "purple",
                    "gray"
                )
            )
        ),
        size="1",
    )


def _badge_estado(usuario: dict) -> rx.Component:
    """Badge de estado activo/inactivo."""
    return rx.cond(
        usuario["activo_empresa"].to(bool),
        rx.badge("Activo", color_scheme="green", size="1"),
        rx.badge("Inactivo", color_scheme="red", size="1"),
    )


# =============================================================================
# TABLA DE USUARIOS
# =============================================================================

def _fila_usuario(usuario: dict) -> rx.Component:
    """Fila de la tabla de usuarios."""
    return rx.table.row(
        # Nombre
        rx.table.cell(
            rx.text(
                usuario["nombre_completo"],
                size="2",
                weight="medium",
                color=Colors.TEXT_PRIMARY,
            ),
        ),
        # Email
        rx.table.cell(
            rx.text(
                usuario["email"],
                size="2",
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        # Rol
        rx.table.cell(_badge_rol_usuario(usuario)),
        # Estado
        rx.table.cell(_badge_estado(usuario)),
        # Acciones
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("pencil", size=14),
                        size="1",
                        variant="ghost",
                        color_scheme="blue",
                        on_click=UsuariosEmpresaState.abrir_modal_editar(usuario),
                    ),
                    content="Editar rol y permisos",
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.cond(
                            usuario["activo_empresa"].to(bool),
                            rx.icon("user-x", size=14),
                            rx.icon("user-check", size=14),
                        ),
                        size="1",
                        variant="ghost",
                        color_scheme=rx.cond(
                            usuario["activo_empresa"].to(bool),
                            "red",
                            "green",
                        ),
                        on_click=UsuariosEmpresaState.abrir_modal_desactivar(usuario),
                    ),
                    content=rx.cond(
                        usuario["activo_empresa"].to(bool),
                        "Desactivar acceso",
                        "Reactivar acceso",
                    ),
                ),
                spacing="1",
                align="center",
            ),
            text_align="right",
        ),
        align="center",
    )


def _tabla_usuarios() -> rx.Component:
    """Tabla de usuarios de la empresa."""
    return rx.cond(
        UsuariosEmpresaState.usuarios_filtrados.length() > 0,
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nombre"),
                        rx.table.column_header_cell("Email"),
                        rx.table.column_header_cell("Rol"),
                        rx.table.column_header_cell("Estado"),
                        rx.table.column_header_cell("Acciones", text_align="right"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        UsuariosEmpresaState.usuarios_filtrados,
                        _fila_usuario,
                    )
                ),
                width="100%",
                variant="surface",
            ),
            width="100%",
            overflow_x="auto",
        ),
        # Empty state
        rx.center(
            rx.vstack(
                rx.icon("users", size=40, color=Colors.TEXT_MUTED),
                rx.text(
                    "No hay usuarios registrados",
                    size="3",
                    color=Colors.TEXT_SECONDARY,
                    weight="medium",
                ),
                rx.text(
                    "Agrega el primer usuario de tu equipo.",
                    size="2",
                    color=Colors.TEXT_MUTED,
                ),
                spacing="2",
                align="center",
            ),
            padding_y="48px",
            width="100%",
        ),
    )


def _filtro_rol() -> rx.Component:
    """Select para filtrar por rol."""
    opciones = [{"label": "Todos los roles", "value": "all"}] + list(ROLES_ASIGNABLES_POR_ADMIN_EMPRESA)
    return rx.select.root(
        rx.select.trigger(placeholder="Filtrar por rol"),
        rx.select.content(
            rx.foreach(
                opciones,
                lambda op: rx.select.item(op["label"], value=op["value"]),
            ),
        ),
        value=UsuariosEmpresaState.filtro_rol_select,
        on_change=UsuariosEmpresaState.set_filtro_rol_usr,
        size="2",
    )


def _contador() -> rx.Component:
    """Contador de usuarios filtrados."""
    return rx.text(
        UsuariosEmpresaState.total_filtrados.to(str),
        " usuario(s)",
        size="2",
        color=Colors.TEXT_MUTED,
    )


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

def usuarios_empresa_page() -> rx.Component:
    """Pagina de gestión de usuarios de la empresa."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Usuarios",
                subtitulo="Gestion del equipo de la empresa",
                icono="users-round",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Agregar Usuario",
                    on_click=UsuariosEmpresaState.abrir_modal_crear,
                    color_scheme="teal",
                ),
            ),
            toolbar=page_toolbar(
                search_value=UsuariosEmpresaState.filtro_busqueda_usr,
                search_placeholder="Buscar por nombre o email...",
                on_search_change=UsuariosEmpresaState.set_filtro_busqueda_usr,
                on_search_clear=lambda: UsuariosEmpresaState.set_filtro_busqueda_usr(""),
                show_view_toggle=False,
                filters=rx.hstack(
                    _filtro_rol(),
                    _contador(),
                    spacing="3",
                    align="center",
                ),
            ),
            content=rx.cond(
                UsuariosEmpresaState.loading,
                rx.vstack(
                    rx.skeleton(height="40px", width="100%"),
                    rx.skeleton(height="40px", width="100%"),
                    rx.skeleton(height="40px", width="100%"),
                    spacing="2",
                    width="100%",
                ),
                _tabla_usuarios(),
            ),
        ),
        # Modales
        modal_crear_usuario_empresa(),
        modal_editar_usuario_empresa(),
        modal_toggle_activo_usuario(),
        width="100%",
        min_height="100vh",
        on_mount=UsuariosEmpresaState.on_mount_usuarios_empresa,
    )
