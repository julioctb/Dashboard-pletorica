"""
Pagina de Usuarios de la Empresa — Portal.

Solo accesible para admin_empresa. Permite gestionar el equipo:
crear usuarios, editar rol/permisos, desactivar/reactivar.
"""
import reflex as rx

from core.core.ui_helpers import FILTRO_TODOS
from core.presentation.layouts.backoffice import page_layout, page_header, page_toolbar
from core.presentation.theme import Colors, Typography
from core.core.constants.permisos import ROLES_ASIGNABLES_POR_ADMIN_EMPRESA
from core.presentation.components.ui import (
    empty_state_card,
    filtros_inline,
    select_items_from_options,
    table_cell_actions,
    table_cell_badge,
    table_cell_text,
    table_shell,
    tabla_action_button,
    tabla_action_buttons,
)

from .state import UsuariosEmpresaState
from .modals import (
    modal_crear_usuario_empresa,
    modal_editar_usuario_empresa,
    modal_toggle_activo_usuario,
)


def _badge_rol_usuario(usuario: dict) -> rx.Component:
    """Badge de rol con color."""
    rol = usuario["rol_empresa"]
    return rx.match(
        rol,
        ("rrhh", rx.badge("RRHH", color_scheme="blue", variant="soft", size="1")),
        ("operaciones", rx.badge("Operaciones", color_scheme="amber", variant="soft", size="1")),
        ("contabilidad", rx.badge("Contabilidad", color_scheme="purple", variant="soft", size="1")),
        rx.badge("Solo lectura", color_scheme="gray", variant="soft", size="1"),
    )


def _badge_estado(usuario: dict) -> rx.Component:
    """Badge de estado activo/inactivo."""
    return rx.cond(
        usuario["activo_empresa"].to(bool),
        rx.badge("Activo", color_scheme="green", variant="soft", size="1"),
        rx.badge("Inactivo", color_scheme="red", variant="soft", size="1"),
    )


# =============================================================================
# TABLA DE USUARIOS
# =============================================================================

def _fila_usuario(usuario: dict) -> rx.Component:
    """Fila de la tabla de usuarios."""
    return rx.table.row(
        # Nombre
        table_cell_text(
            usuario["nombre_completo"],
            weight=Typography.WEIGHT_MEDIUM,
            size=Typography.SIZE_SM,
        ),
        # Email
        table_cell_text(
            usuario["email"],
            fallback="—",
            tone="secondary",
            size=Typography.SIZE_SM,
        ),
        # Rol
        table_cell_badge(
            rx.center(
                _badge_rol_usuario(usuario),
                width="100%",
            )
        ),
        # Estado
        table_cell_badge(
            rx.center(
                _badge_estado(usuario),
                width="100%",
            )
        ),
        # Acciones
        table_cell_actions(
            rx.center(
                tabla_action_buttons([
                    tabla_action_button(
                        icon="pencil",
                        tooltip="Editar rol y permisos",
                        on_click=UsuariosEmpresaState.abrir_modal_editar(usuario),
                        color_scheme="blue",
                        disabled=UsuariosEmpresaState.saving,
                    ),
                    tabla_action_button(
                        icon="user-x",
                        tooltip="Desactivar acceso",
                        on_click=UsuariosEmpresaState.abrir_modal_desactivar(usuario),
                        color_scheme="red",
                        visible=usuario["activo_empresa"].to(bool),
                        disabled=UsuariosEmpresaState.saving,
                    ),
                    tabla_action_button(
                        icon="user-check",
                        tooltip="Reactivar acceso",
                        on_click=UsuariosEmpresaState.abrir_modal_desactivar(usuario),
                        color_scheme="green",
                        visible=~usuario["activo_empresa"].to(bool),
                        disabled=UsuariosEmpresaState.saving,
                    ),
                ]),
                width="100%",
            ),
        ),
        align="center",
    )


ENCABEZADOS_USUARIOS_EMPRESA = [
    {"nombre": "Nombre", "ancho": "240px"},
    {"nombre": "Email", "ancho": "240px"},
    {"nombre": "Rol", "ancho": "140px", "header_align": "center"},
    {"nombre": "Estado", "ancho": "110px", "header_align": "center"},
    {"nombre": "Acciones", "ancho": "130px", "header_align": "center"},
]


def _tabla_usuarios() -> rx.Component:
    """Tabla de usuarios de la empresa."""
    return table_shell(
        loading=UsuariosEmpresaState.loading,
        headers=ENCABEZADOS_USUARIOS_EMPRESA,
        rows=UsuariosEmpresaState.usuarios_filtrados,
        row_renderer=_fila_usuario,
        has_rows=UsuariosEmpresaState.total_filtrados > 0,
        empty_component=rx.cond(
            (
                (UsuariosEmpresaState.filtro_busqueda_usr != "")
                | (UsuariosEmpresaState.filtro_rol_usr != FILTRO_TODOS)
            ) & (UsuariosEmpresaState.usuarios_empresa.length() > 0),
            empty_state_card(
                title="No hay resultados para este filtro",
                description="Prueba con otra búsqueda o limpia los filtros para ver más usuarios.",
                icon="search",
            ),
            empty_state_card(
                title="No hay usuarios registrados",
                description="Agrega la primera persona de tu equipo para empezar a gestionar accesos.",
                icon="users",
                action_button=rx.button(
                    rx.icon("plus", size=16),
                    "Agregar usuario",
                    on_click=UsuariosEmpresaState.abrir_modal_crear,
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    variant="soft",
                ),
            ),
        ),
        total_caption="Mostrando " + UsuariosEmpresaState.total_filtrados.to(str) + " usuario(s)",
        loading_rows=5,
        table_size="1",
    )


def _filtro_rol() -> rx.Component:
    """Select para filtrar por rol."""
    opciones = [{"label": "Todos los roles", "value": FILTRO_TODOS}] + list(ROLES_ASIGNABLES_POR_ADMIN_EMPRESA)
    return rx.select.root(
        rx.select.trigger(placeholder="Filtrar por rol"),
        rx.select.content(select_items_from_options(opciones)),
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
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Agregar Usuario",
                    on_click=UsuariosEmpresaState.abrir_modal_crear,
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                ),
            ),
            toolbar=page_toolbar(
                search_value=UsuariosEmpresaState.filtro_busqueda_usr,
                search_placeholder="Buscar por nombre o email...",
                on_search_change=UsuariosEmpresaState.set_filtro_busqueda_usr,
                on_search_clear=lambda: UsuariosEmpresaState.set_filtro_busqueda_usr(""),
                show_view_toggle=False,
                filters=filtros_inline(
                    _filtro_rol(),
                    _contador(),
                ),
            ),
            content=_tabla_usuarios(),
        ),
        # Modales
        modal_crear_usuario_empresa(),
        modal_editar_usuario_empresa(),
        modal_toggle_activo_usuario(),
        width="100%",
        min_height="100vh",
        on_mount=UsuariosEmpresaState.on_mount_usuarios_empresa,
    )
