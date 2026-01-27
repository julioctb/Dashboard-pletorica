"""
Página de Configuración de Requisiciones.

Permite editar los valores predeterminados que se pre-llenan
al crear nuevas requisiciones: área requirente, firmas y entrega.
También gestiona los lugares de entrega disponibles.
"""

import reflex as rx

from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Colors, Spacing, Typography
from app.presentation.components.ui.form_input import form_input
from .configuracion_state import ConfiguracionState


# =============================================================================
# COMPONENTE DE CAMPO EDITABLE
# =============================================================================

def _campo_config(config: dict) -> rx.Component:
    """Renderiza un campo de configuracion editable.

    Replica el patron visual de form_input pero usa rx.cond
    para manejar Vars reactivos de rx.foreach.
    """
    error = config["error"]
    hint = config["hint"]

    return rx.vstack(
        # Label (color rojo si hay error)
        rx.text(
            config["descripcion"],
            size="2",
            weight="medium",
            color=rx.cond(error != "", "var(--red-9)", "var(--gray-11)"),
        ),
        # Input controlado
        rx.input(
            value=config["valor"],
            on_change=lambda val: ConfiguracionState.actualizar_valor(
                config["id"], val
            ),
            on_blur=ConfiguracionState.normalizar_campo(config["id"]),
            placeholder=config["placeholder"],
            width="100%",
        ),
        # Footer: error tiene prioridad sobre hint
        rx.cond(
            error != "",
            rx.text(error, color="var(--red-9)", size="1"),
            rx.cond(
                hint != "",
                rx.text(hint, size="1", color="var(--gray-9)"),
                rx.text("", size="1"),
            ),
        ),
        spacing="1",
        width="100%",
        align_items="stretch",
    )


# =============================================================================
# SECCIONES COLAPSABLES
# =============================================================================

def _seccion_grupo(
    titulo: str,
    icono: str,
    configs: rx.Var,
    value: str,
) -> rx.Component:
    """Accordion item colapsable con un grupo de configuraciones."""
    return rx.accordion.item(
        rx.accordion.header(
            rx.accordion.trigger(
                rx.hstack(
                    rx.icon(icono, size=20, color=Colors.PRIMARY),
                    rx.heading(
                        titulo,
                        size="4",
                        font_weight=Typography.WEIGHT_SEMIBOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    rx.spacer(),
                    rx.accordion.icon(),
                    align="center",
                    width="100%",
                    gap=Spacing.SM,
                ),
            ),
        ),
        rx.accordion.content(
            rx.vstack(
                rx.foreach(configs, _campo_config),
                spacing="4",
                width="100%",
                padding_y=Spacing.MD,
            ),
        ),
        value=value,
    )


def _lugar_entrega_item(lugar: dict) -> rx.Component:
    """Un lugar de entrega con botón de eliminar."""
    return rx.hstack(
        rx.icon("map-pin", size=16, color=Colors.TEXT_MUTED),
        rx.text(
            lugar["nombre"],
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_PRIMARY,
            flex="1",
        ),
        rx.icon_button(
            rx.icon("trash-2", size=14),
            size="1",
            variant="ghost",
            color_scheme="red",
            cursor="pointer",
            on_click=ConfiguracionState.eliminar_lugar(lugar["id"]),
        ),
        align="center",
        width="100%",
        padding=Spacing.SM,
        border_radius="6px",
        style={
            "_hover": {"background": Colors.SIDEBAR_ITEM_HOVER},
        },
    )


def _seccion_lugares_entrega() -> rx.Component:
    """Accordion item para gestionar lugares de entrega."""
    return rx.accordion.item(
        rx.accordion.header(
            rx.accordion.trigger(
                rx.hstack(
                    rx.icon("map-pin", size=20, color=Colors.PRIMARY),
                    rx.heading(
                        "Lugares de Entrega",
                        size="4",
                        font_weight=Typography.WEIGHT_SEMIBOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    rx.spacer(),
                    rx.accordion.icon(),
                    align="center",
                    width="100%",
                    gap=Spacing.SM,
                ),
            ),
        ),
        rx.accordion.content(
            rx.vstack(
                # Input para agregar nuevo lugar
                rx.hstack(
                    form_input(
                        label="Nuevo lugar de entrega",
                        placeholder="Ej: Ciudad Universitaria, Edificio 1A",
                        value=ConfiguracionState.nuevo_lugar,
                        on_change=ConfiguracionState.set_nuevo_lugar,
                        on_blur=ConfiguracionState.validar_nuevo_lugar,
                        error=ConfiguracionState.error_nuevo_lugar,
                        hint="Maximo 255 caracteres",
                    ),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Agregar",
                        on_click=ConfiguracionState.agregar_lugar,
                        disabled=ConfiguracionState.nuevo_lugar == "",
                        size="2",
                        margin_top="1.2em",
                    ),
                    width="100%",
                    align="start",
                ),
                # Lista de lugares existentes
                rx.vstack(
                    rx.foreach(
                        ConfiguracionState.lugares_entrega,
                        _lugar_entrega_item,
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    ConfiguracionState.lugares_entrega.length() == 0,
                    rx.text(
                        "No hay lugares de entrega configurados",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_MUTED,
                        text_align="center",
                        padding_y=Spacing.MD,
                    ),
                ),
                spacing="4",
                width="100%",
                padding_y=Spacing.MD,
            ),
        ),
        value="lugares_entrega",
    )


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

def configuracion_page() -> rx.Component:
    """Página de configuración de requisiciones."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Configuración",
                subtitulo="Valores predeterminados para nuevas requisiciones",
                icono="settings",
                accion_principal=rx.button(
                    rx.icon("save", size=16),
                    "Guardar cambios",
                    on_click=ConfiguracionState.guardar_cambios,
                    disabled=(
                        ~ConfiguracionState.tiene_cambios
                        | ConfiguracionState.tiene_errores
                    ),
                    loading=ConfiguracionState.saving,
                    size="2",
                ),
            ),
            content=rx.cond(
                ConfiguracionState.loading,
                rx.center(
                    rx.spinner(size="3"),
                    width="100%",
                    padding_y="80px",
                ),
                rx.accordion.root(
                    _seccion_grupo(
                        titulo="Área Requirente",
                        icono="building-2",
                        configs=ConfiguracionState.configs_area_requirente,
                        value="area_requirente",
                    ),
                    _seccion_lugares_entrega(),
                    _seccion_grupo(
                        titulo="Firmas",
                        icono="pen-tool",
                        configs=ConfiguracionState.configs_firmas,
                        value="firmas",
                    ),
                    type="multiple",
                    default_value=[
                        "area_requirente",
                        "lugares_entrega",
                        "firmas",
                    ],
                    collapsible=True,
                    width="100%",
                    max_width="800px",
                    variant="outline",
                ),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=ConfiguracionState.on_mount,
    )
