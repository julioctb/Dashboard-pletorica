"""
Página del Portal del Cliente - Mis Entregables.
Nueva vista global: muestra todos los entregables, con Pendientes+Rechazados por defecto.
Cards de estadísticas son clickeables para filtrar.
"""

import reflex as rx

from app.presentation.portal.pages.mis_entregables_state import MisEntregablesState
from app.presentation.components.ui import status_badge_reactive, tabla_vacia
from app.presentation.theme import Colors, Spacing, Typography, Radius, Shadows


# =============================================================================
# STAT CARDS (CLICKEABLES)
# =============================================================================
def _stat_card(
    titulo: str,
    valor: rx.Var,
    icono: str,
    color_scheme: str,
    on_click,
    is_active: rx.Var,
) -> rx.Component:
    """Card de estadística clickeable que actúa como filtro."""
    color_map = {
        "amber": (Colors.WARNING_LIGHT, Colors.WARNING),
        "sky": (Colors.INFO_LIGHT, Colors.INFO),
        "green": (Colors.SUCCESS_LIGHT, Colors.SUCCESS),
        "red": (Colors.ERROR_LIGHT, Colors.ERROR),
    }
    bg, icon_color = color_map.get(color_scheme, (Colors.SECONDARY_LIGHT, Colors.SECONDARY))

    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(icono, size=20, color=icon_color),
                width="40px",
                height="40px",
                border_radius=Radius.LG,
                background=bg,
            ),
            rx.vstack(
                rx.text(titulo, size="1", color=Colors.TEXT_MUTED),
                rx.text(valor, size="5", weight="bold"),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        padding=Spacing.MD,
        background=rx.cond(is_active, Colors.PORTAL_PRIMARY_LIGHT, Colors.SURFACE),
        border=rx.cond(
            is_active,
            f"2px solid {Colors.PORTAL_PRIMARY}",
            f"1px solid {Colors.BORDER}",
        ),
        border_radius=Radius.LG,
        flex="1",
        min_width="140px",
        cursor="pointer",
        on_click=on_click,
        _hover={
            "box_shadow": Shadows.MD,
            "border_color": Colors.PORTAL_PRIMARY,
        },
        transition="all 0.2s ease",
    )


def _seccion_estadisticas() -> rx.Component:
    """Cards de estadísticas que actúan como filtros."""
    return rx.hstack(
        _stat_card(
            "Acción Requerida",
            MisEntregablesState.stats_accion_requerida,
            "triangle-alert",
            "amber",
            MisEntregablesState.filtrar_accion_requerida,
            MisEntregablesState.filtro_es_accion_requerida,
        ),
        _stat_card(
            "En Revisión",
            MisEntregablesState.stats_en_revision,
            "search",
            "sky",
            MisEntregablesState.filtrar_en_revision,
            MisEntregablesState.filtro_es_en_revision,
        ),
        _stat_card(
            "Aprobados",
            MisEntregablesState.stats_aprobados,
            "circle-check",
            "green",
            MisEntregablesState.filtrar_aprobados,
            MisEntregablesState.filtro_es_aprobado,
        ),
        _stat_card(
            "Rechazados",
            MisEntregablesState.stats_rechazados,
            "circle-x",
            "red",
            MisEntregablesState.filtrar_rechazados,
            MisEntregablesState.filtro_es_rechazado,
        ),
        spacing="3",
        width="100%",
        flex_wrap="wrap",
    )


# =============================================================================
# BARRA DE FILTROS
# =============================================================================
def _barra_filtros() -> rx.Component:
    return rx.hstack(
        rx.text(
            MisEntregablesState.titulo_filtro_actual,
            size="4",
            weight="bold",
            color=Colors.TEXT_PRIMARY,
        ),
        rx.spacer(),
        rx.input(
            placeholder="Buscar período o contrato...",
            value=MisEntregablesState.filtro_busqueda,
            on_change=MisEntregablesState.set_filtro_busqueda,
            width="220px",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Todos los contratos", width="200px"),
            rx.select.content(
                rx.foreach(
                    MisEntregablesState.opciones_contratos,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=MisEntregablesState.filtro_contrato_id,
            on_change=MisEntregablesState.set_filtro_contrato,
        ),
        spacing="3",
        width="100%",
        align="center",
        padding_y=Spacing.SM,
    )


# =============================================================================
# CARDS DE ENTREGABLES
# =============================================================================
def _card_rechazado(entregable: dict) -> rx.Component:
    """Card para entregable rechazado - muestra observaciones."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.badge("RECHAZADO", color_scheme="red", size="2", variant="solid"),
                rx.text("Requiere corrección", size="1", color=Colors.ERROR, weight="medium"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            # Info período
            rx.hstack(
                rx.text(f"Período {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            # Observaciones
            rx.cond(
                entregable["observaciones_rechazo"],
                rx.callout(
                    rx.text(entregable["observaciones_rechazo"], size="2"),
                    icon="message-circle",
                    color_scheme="red",
                    size="1",
                ),
                rx.fragment(),
            ),
            # Acción
            rx.hstack(
                rx.spacer(),
                rx.button(
                    rx.icon("upload", size=14),
                    "Corregir y reenviar",
                    size="2",
                    color_scheme="red",
                    on_click=lambda: MisEntregablesState.abrir_entregable(entregable["id"]),
                ),
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"2px solid {Colors.ERROR}",
        border_radius=Radius.MD,
    )


def _card_pendiente(entregable: dict) -> rx.Component:
    """Card para entregable pendiente."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.badge("PENDIENTE", color_scheme="amber", size="2", variant="soft"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            # Info período
            rx.hstack(
                rx.text(f"Período {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            # Acción
            rx.hstack(
                rx.spacer(),
                rx.button(
                    rx.icon("upload", size=14),
                    "Subir archivos",
                    size="2",
                    color_scheme="teal",
                    on_click=lambda: MisEntregablesState.abrir_entregable(entregable["id"]),
                ),
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        _hover={"border_color": Colors.PORTAL_PRIMARY},
    )


def _card_en_revision(entregable: dict) -> rx.Component:
    """Card para entregable en revisión."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.badge("EN REVISIÓN", color_scheme="sky", size="2", variant="soft"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            # Info período
            rx.hstack(
                rx.text(f"Período {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            # Fecha envío
            rx.cond(
                entregable["fecha_entrega"],
                rx.hstack(
                    rx.icon("calendar", size=14, color=Colors.TEXT_MUTED),
                    rx.text(f"Enviado: {entregable['fecha_entrega']}", size="1", color=Colors.TEXT_MUTED),
                    spacing="1",
                    align="center",
                ),
                rx.fragment(),
            ),
            # Estado
            rx.hstack(
                rx.icon("clock", size=14, color=Colors.INFO),
                rx.text("Esperando revisión de BUAP", size="2", color=Colors.INFO),
                rx.spacer(),
                rx.button(
                    rx.icon("eye", size=14),
                    "Ver archivos",
                    size="1",
                    variant="ghost",
                    on_click=lambda: MisEntregablesState.abrir_entregable(entregable["id"]),
                ),
                width="100%",
                align="center",
            ),
            spacing="3",
            width="100%",
        ),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
    )


def _card_aprobado(entregable: dict) -> rx.Component:
    """Card para entregable aprobado."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.badge("APROBADO", color_scheme="green", size="2", variant="soft"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            # Info período
            rx.hstack(
                rx.text(f"Período {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            # Monto aprobado
            rx.cond(
                entregable["monto_aprobado"],
                rx.hstack(
                    rx.icon("banknote", size=14, color=Colors.SUCCESS),
                    rx.text(f"Monto: ${entregable['monto_aprobado']}", size="2", weight="medium", color=Colors.SUCCESS),
                    rx.spacer(),
                    rx.button(
                        rx.icon("eye", size=14),
                        "Ver detalle",
                        size="1",
                        variant="ghost",
                        on_click=lambda: MisEntregablesState.abrir_entregable(entregable["id"]),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
        ),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
    )


def _card_entregable(entregable: dict) -> rx.Component:
    """Renderiza el card según el estatus del entregable."""
    return rx.match(
        entregable["estatus"],
        ("RECHAZADO", _card_rechazado(entregable)),
        ("PENDIENTE", _card_pendiente(entregable)),
        ("EN_REVISION", _card_en_revision(entregable)),
        ("APROBADO", _card_aprobado(entregable)),
        _card_pendiente(entregable),  # Default
    )


def _lista_entregables() -> rx.Component:
    return rx.cond(
        MisEntregablesState.tiene_entregables,
        rx.vstack(
            rx.foreach(MisEntregablesState.entregables_filtrados, _card_entregable),
            rx.text(
                "Mostrando ",
                MisEntregablesState.total_mostrados,
                " entregable(s)",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
            ),
            spacing="3",
            width="100%",
        ),
        tabla_vacia(
            mensaje="No hay entregables con este filtro",
            submensaje="Prueba seleccionando otro estado o contrato",
        ),
    )


# =============================================================================
# MODAL DE ENTREGABLE
# =============================================================================
def _archivo_item(archivo: dict) -> rx.Component:
    """Renderiza un item de archivo."""
    return rx.hstack(
        rx.center(
            rx.cond(
                archivo["es_imagen"],
                rx.icon("image", size=16, color=Colors.PORTAL_PRIMARY),
                rx.icon("file-text", size=16, color=Colors.ERROR),
            ),
            width="32px",
            height="32px",
            border_radius="6px",
            background=rx.cond(
                archivo["es_imagen"],
                Colors.PORTAL_PRIMARY_LIGHT,
                "var(--red-3)",
            ),
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(archivo["nombre"], font_size=Typography.SIZE_SM, weight="medium", no_of_lines=1),
            rx.text(f"{archivo['tamanio_mb']} MB", font_size=Typography.SIZE_XS, color=Colors.TEXT_MUTED),
            spacing="0",
            align="start",
            flex="1",
        ),
        rx.cond(
            MisEntregablesState.entregable_actual["puede_editar"],
            rx.button(
                rx.icon("trash-2", size=14),
                size="1",
                variant="ghost",
                color_scheme="red",
                on_click=MisEntregablesState.eliminar_archivo(archivo["id"]),
            ),
            rx.fragment(),
        ),
        padding=Spacing.SM,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
        width="100%",
        align="center",
        spacing="3",
    )


def _seccion_archivos_modal() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Archivos subidos", font_size=Typography.SIZE_SM, weight="bold"),
            rx.badge(MisEntregablesState.archivos_entregable.length(), color_scheme="gray", size="1"),
            spacing="2",
            align="center",
        ),
        rx.cond(
            MisEntregablesState.archivos_entregable.length() > 0,
            rx.vstack(
                rx.foreach(MisEntregablesState.archivos_entregable.to(list[dict]), _archivo_item),
                spacing="2",
                width="100%",
            ),
            rx.center(
                rx.text("No hay archivos subidos", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
                padding="4",
            ),
        ),
        # Zona de upload (solo si puede editar)
        rx.cond(
            MisEntregablesState.entregable_actual["puede_editar"],
            rx.vstack(
                rx.separator(),
                rx.upload(
                    rx.vstack(
                        rx.cond(
                            MisEntregablesState.subiendo_archivo,
                            rx.vstack(
                                rx.spinner(size="3"),
                                rx.text("Subiendo...", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                                align="center",
                                spacing="2",
                            ),
                            rx.vstack(
                                rx.icon("upload", size=32, color=Colors.PORTAL_PRIMARY),
                                rx.text("Click o arrastra archivos", font_size=Typography.SIZE_LG, weight="medium"),
                                rx.text("JPG, PNG, PDF | Máx 10 archivos", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
                                align="center",
                                spacing="2",
                            ),
                        ),
                        align="center",
                        justify="center",
                        padding=Spacing.XL,
                        width="100%",
                    ),
                    id="upload_entregable",
                    accept={"image/*": [".jpg", ".jpeg", ".png"], "application/pdf": [".pdf"]},
                    max_files=10,
                    no_click=MisEntregablesState.subiendo_archivo,
                    no_drag=MisEntregablesState.subiendo_archivo,
                    border=f"2px dashed {Colors.TEXT_MUTED}",
                    border_radius="8px",
                    cursor=rx.cond(MisEntregablesState.subiendo_archivo, "wait", "pointer"),
                    _hover={"borderColor": Colors.PORTAL_PRIMARY, "background": Colors.PORTAL_PRIMARY_LIGHTER},
                    width="100%",
                ),
                rx.cond(
                    rx.selected_files("upload_entregable").length() > 0,
                    rx.vstack(
                        rx.text("Archivos seleccionados:", font_size=Typography.SIZE_SM, weight="bold"),
                        rx.foreach(
                            rx.selected_files("upload_entregable"),
                            lambda f: rx.hstack(
                                rx.icon("file", size=14, color=Colors.PORTAL_PRIMARY),
                                rx.text(f, font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                                spacing="2",
                                align="center",
                            ),
                        ),
                        rx.hstack(
                            rx.button("Cancelar", on_click=rx.clear_selected_files("upload_entregable"), variant="outline", size="2"),
                            rx.button(
                                rx.cond(
                                    MisEntregablesState.subiendo_archivo,
                                    rx.hstack(rx.spinner(size="1"), rx.text("Subiendo..."), spacing="2"),
                                    rx.hstack(rx.icon("cloud-upload", size=16), rx.text("Subir"), spacing="2"),
                                ),
                                on_click=MisEntregablesState.subir_archivos(rx.upload_files(upload_id="upload_entregable")),
                                disabled=MisEntregablesState.subiendo_archivo,
                                size="2",
                                color_scheme="teal",
                            ),
                            spacing="3",
                            width="100%",
                            justify="end",
                        ),
                        spacing="3",
                        width="100%",
                        padding=Spacing.MD,
                        background=Colors.PORTAL_PRIMARY_LIGHTER,
                        border=f"1px solid {Colors.PORTAL_PRIMARY}",
                        border_radius="8px",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                width="100%",
            ),
            rx.fragment(),
        ),
        spacing="3",
        width="100%",
    )


def _modal_entregable() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                MisEntregablesState.entregable_actual,
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.hstack(
                                rx.badge(MisEntregablesState.entregable_actual["contrato_codigo"], color_scheme="blue", size="1"),
                                rx.text(f"Período {MisEntregablesState.entregable_actual['numero_periodo']}", size="5", weight="bold"),
                                spacing="2",
                                align="center",
                            ),
                            rx.text(MisEntregablesState.entregable_actual["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                            spacing="0",
                        ),
                        rx.spacer(),
                        status_badge_reactive(MisEntregablesState.entregable_actual["estatus"]),
                        width="100%",
                        align="start",
                    ),
                    rx.divider(),
                    # Observaciones de rechazo
                    rx.cond(
                        MisEntregablesState.entregable_actual["observaciones_rechazo"],
                        rx.callout(
                            rx.vstack(
                                rx.text("Observaciones de BUAP:", size="2", weight="bold"),
                                rx.text(MisEntregablesState.entregable_actual["observaciones_rechazo"], size="2"),
                                spacing="1",
                                align="start",
                            ),
                            icon="triangle-alert",
                            color_scheme="red",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    _seccion_archivos_modal(),
                    rx.divider(),
                    rx.hstack(
                        rx.button(
                            "Cerrar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=MisEntregablesState.cerrar_modal_entregable,
                        ),
                        rx.spacer(),
                        rx.cond(
                            MisEntregablesState.puede_entregar,
                            rx.button(
                                rx.icon("send", size=14),
                                "Enviar para revisión",
                                color_scheme="teal",
                                on_click=MisEntregablesState.enviar_para_revision,
                                loading=MisEntregablesState.enviando,
                            ),
                            rx.cond(
                                MisEntregablesState.esta_en_revision,
                                rx.badge("Esperando revisión de BUAP", color_scheme="sky", size="2"),
                                rx.fragment(),
                            ),
                        ),
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.spinner(),
            ),
            max_width="550px",
            padding="5",
        ),
        open=MisEntregablesState.mostrar_modal_entregable,
        on_open_change=MisEntregablesState.set_mostrar_modal,
    )


# =============================================================================
# PÁGINA
# =============================================================================
def _contenido_principal() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Mis Entregables", size="6", weight="bold"),
                rx.text("Suba archivos y envíe para revisión de BUAP", size="2", color=Colors.TEXT_SECONDARY),
                spacing="0",
            ),
            width="100%",
        ),
        rx.divider(),
        _seccion_estadisticas(),
        rx.divider(),
        _barra_filtros(),
        rx.cond(
            MisEntregablesState.cargando,
            rx.center(rx.spinner(size="3"), padding="8"),
            _lista_entregables(),
        ),
        _modal_entregable(),
        spacing="4",
        width="100%",
    )


def mis_entregables_page() -> rx.Component:
    return rx.box(
        _contenido_principal(),
        on_mount=MisEntregablesState.on_load_mis_entregables,
    )
