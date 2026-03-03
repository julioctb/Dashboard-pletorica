"""
Componente compartido: Matriz de permisos.

Reutilizado en:
- backoffice: admin/usuarios/modals.py
- portal: usuarios_empresa/modals.py
"""
import reflex as rx


def _fila_permiso_generica(
    modulo: str,
    label: str,
    tiene_autorizar: bool,
    permisos_modulo_var,
    toggle_fn,
) -> rx.Component:
    """Fila de la matriz de permisos para un módulo."""
    return rx.hstack(
        rx.text(label, size="2", width="120px"),
        rx.box(
            rx.checkbox(
                checked=permisos_modulo_var["operar"].to(bool),
                on_change=lambda _v: toggle_fn(modulo, "operar"),
                size="2",
            ),
            width="70px",
            text_align="center",
            display="flex",
            justify_content="center",
        ),
        rx.box(
            rx.cond(
                tiene_autorizar,
                rx.checkbox(
                    checked=permisos_modulo_var["autorizar"].to(bool),
                    on_change=lambda _v: toggle_fn(modulo, "autorizar"),
                    size="2",
                ),
                rx.text("--", size="2", color="var(--gray-7)"),
            ),
            width="70px",
            text_align="center",
            display="flex",
            justify_content="center",
        ),
        padding_y="6px",
        border_bottom="1px solid var(--gray-3)",
        width="100%",
    )


def matriz_permisos_component(
    permisos_var,
    toggle_fn,
    superadmin_condition=None,
    gestion_usuarios_var=None,
    gestion_usuarios_fn=None,
) -> rx.Component:
    """
    Matriz de permisos con checkboxes (operar/autorizar por módulo).

    Args:
        permisos_var: rx.Var del dict de permisos (6 módulos)
        toggle_fn: event handler(modulo, accion) — toggling un permiso
        superadmin_condition: rx.Var bool — si se pasa, muestra la fila de gestión de usuarios
                              condicionada a este Var (solo backoffice)
        gestion_usuarios_var: rx.Var bool para el checkbox de gestión de usuarios
        gestion_usuarios_fn: setter para el checkbox de gestión de usuarios
    """
    # Sección opcional de gestión de usuarios (solo backoffice con superadmin)
    if superadmin_condition is not None and gestion_usuarios_var is not None:
        seccion_superadmin = rx.cond(
            superadmin_condition,
            rx.vstack(
                rx.separator(),
                rx.hstack(
                    rx.checkbox(
                        "Puede gestionar usuarios (super admin)",
                        checked=gestion_usuarios_var,
                        on_change=gestion_usuarios_fn,
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        )
    else:
        seccion_superadmin = rx.fragment()

    return rx.vstack(
        rx.text("Permisos del usuario", size="2", weight="bold", color="var(--gray-11)"),
        rx.box(
            # Header
            rx.hstack(
                rx.text("Modulo", size="1", weight="bold", color="var(--gray-9)", width="120px"),
                rx.text("Operar", size="1", weight="bold", color="var(--gray-9)", width="70px", text_align="center"),
                rx.text("Autorizar", size="1", weight="bold", color="var(--gray-9)", width="70px", text_align="center"),
                padding_bottom="8px",
                border_bottom="1px solid var(--gray-5)",
                width="100%",
            ),
            # Filas por módulo
            _fila_permiso_generica(
                "requisiciones", "Requisiciones", True,
                permisos_var["requisiciones"].to(dict), toggle_fn,
            ),
            _fila_permiso_generica(
                "entregables", "Entregables", True,
                permisos_var["entregables"].to(dict), toggle_fn,
            ),
            _fila_permiso_generica(
                "pagos", "Pagos", True,
                permisos_var["pagos"].to(dict), toggle_fn,
            ),
            _fila_permiso_generica(
                "contratos", "Contratos", False,
                permisos_var["contratos"].to(dict), toggle_fn,
            ),
            _fila_permiso_generica(
                "empresas", "Empresas", False,
                permisos_var["empresas"].to(dict), toggle_fn,
            ),
            _fila_permiso_generica(
                "empleados", "Empleados", False,
                permisos_var["empleados"].to(dict), toggle_fn,
            ),
            width="100%",
        ),
        seccion_superadmin,
        spacing="3",
        width="100%",
        padding="12px",
        border="1px solid var(--gray-5)",
        border_radius="8px",
        background="var(--gray-2)",
    )
