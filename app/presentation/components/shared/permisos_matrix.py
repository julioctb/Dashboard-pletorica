"""
Componente compartido: Matriz de permisos.

Reutilizado en:
- backoffice: admin/usuarios/modals.py
- portal: usuarios_empresa/modals.py
"""
import reflex as rx

from app.presentation.theme import Colors, Radius, Spacing, Typography


PERMISSION_ROWS = [
    ("requisiciones", "Requisiciones", True),
    ("entregables", "Entregables", True),
    ("pagos", "Pagos", True),
    ("contratos", "Contratos", False),
    ("empresas", "Empresas", False),
    ("empleados", "Empleados", False),
]
PERMISSION_ACTION_COLUMN_WIDTH = f"calc({Spacing.XL} * 4)"


def _fila_permiso_generica(
    modulo: str,
    label: str,
    tiene_autorizar: bool,
    permisos_modulo_var,
    toggle_fn,
    variant: str = "default",
    checkbox_color_scheme: str = "blue",
    show_unavailable_checkbox: bool = False,
    is_last: bool = False,
) -> rx.Component:
    """Fila de la matriz de permisos para un módulo."""
    if variant == "portal":
        checkbox_operar = rx.checkbox(
            checked=permisos_modulo_var["operar"].to(bool),
            on_change=lambda _v: toggle_fn(modulo, "operar"),
            size="2",
            color_scheme=checkbox_color_scheme,
        )
        checkbox_autorizar = (
            rx.checkbox(
                checked=permisos_modulo_var["autorizar"].to(bool),
                on_change=lambda _v: toggle_fn(modulo, "autorizar"),
                size="2",
                color_scheme=checkbox_color_scheme,
            )
            if tiene_autorizar
            else (
                rx.checkbox(
                    checked=False,
                    disabled=True,
                    size="2",
                    color_scheme=checkbox_color_scheme,
                )
                if show_unavailable_checkbox
                else rx.text("-", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED)
            )
        )

        return rx.hstack(
            rx.text(
                label,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
                flex="1",
            ),
            rx.box(
                checkbox_operar,
                width=PERMISSION_ACTION_COLUMN_WIDTH,
                display="flex",
                justify_content="center",
                align_items="center",
                flex_shrink="0",
            ),
            rx.box(
                checkbox_autorizar,
                width=PERMISSION_ACTION_COLUMN_WIDTH,
                display="flex",
                justify_content="center",
                align_items="center",
                flex_shrink="0",
            ),
            align="center",
            width="100%",
            padding_top=Spacing.MD,
            padding_bottom=Spacing.MD,
            padding_left=Spacing.BASE,
            padding_right=Spacing.BASE,
            border_bottom=f"1px solid {Colors.BORDER}" if not is_last else "none",
        )

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
    variant: str = "default",
    checkbox_color_scheme: str = "blue",
    show_unavailable_checkbox: bool = False,
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
    rows = [
        _fila_permiso_generica(
            modulo,
            label,
            tiene_autorizar,
            permisos_var[modulo].to(dict),
            toggle_fn,
            variant=variant,
            checkbox_color_scheme=checkbox_color_scheme,
            show_unavailable_checkbox=show_unavailable_checkbox,
            is_last=index == len(PERMISSION_ROWS) - 1,
        )
        for index, (modulo, label, tiene_autorizar) in enumerate(PERMISSION_ROWS)
    ]

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

    if variant == "portal":
        return rx.vstack(
            rx.box(
                rx.box(
                    rx.text(
                        "PERMISOS DEL USUARIO",
                        font_size=Typography.SIZE_XS,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing="0.04em",
                    ),
                    padding=f"{Spacing.SM} {Spacing.BASE}",
                    background=Colors.SECONDARY_LIGHT,
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            "Modulo",
                            font_size=Typography.SIZE_XS,
                            font_weight=Typography.WEIGHT_MEDIUM,
                            color=Colors.TEXT_SECONDARY,
                            flex="1",
                        ),
                        rx.box(
                            rx.text(
                                "Operar",
                                font_size=Typography.SIZE_XS,
                                font_weight=Typography.WEIGHT_MEDIUM,
                                color=Colors.TEXT_SECONDARY,
                                text_align="center",
                            ),
                            width=PERMISSION_ACTION_COLUMN_WIDTH,
                            display="flex",
                            justify_content="center",
                            flex_shrink="0",
                        ),
                        rx.box(
                            rx.text(
                                "Autorizar",
                                font_size=Typography.SIZE_XS,
                                font_weight=Typography.WEIGHT_MEDIUM,
                                color=Colors.TEXT_SECONDARY,
                                text_align="center",
                            ),
                            width=PERMISSION_ACTION_COLUMN_WIDTH,
                            display="flex",
                            justify_content="center",
                            flex_shrink="0",
                        ),
                        align="center",
                        width="100%",
                        padding_top=Spacing.SM,
                        padding_bottom=Spacing.SM,
                        padding_left=Spacing.BASE,
                        padding_right=Spacing.BASE,
                        border_bottom=f"1px solid {Colors.BORDER}",
                    ),
                    *rows,
                    gap=Spacing.NONE,
                    width="100%",
                    background=Colors.SURFACE,
                ),
                width="100%",
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.LG,
                overflow="hidden",
                background=Colors.SURFACE,
            ),
            seccion_superadmin,
            gap=Spacing.BASE,
            width="100%",
        )

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
            *rows,
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
