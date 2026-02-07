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
    """Cards de estadisticas que actuan como filtros."""
    return rx.vstack(
        # Fila 1: Flujo de entrega
        rx.hstack(
            _stat_card(
                "Accion Requerida",
                MisEntregablesState.stats_accion_requerida,
                "triangle-alert",
                "amber",
                MisEntregablesState.filtrar_accion_requerida,
                MisEntregablesState.filtro_es_accion_requerida,
            ),
            _stat_card(
                "En Revision",
                MisEntregablesState.stats_en_revision,
                "search",
                "sky",
                MisEntregablesState.filtrar_en_revision,
                MisEntregablesState.filtro_es_en_revision,
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
        ),
        # Fila 2: Flujo de facturacion
        rx.hstack(
            _stat_card(
                "Por Prefacturar",
                MisEntregablesState.stats_por_prefacturar,
                "file-text",
                "amber",
                MisEntregablesState.filtrar_por_prefacturar,
                MisEntregablesState.filtro_es_por_prefacturar,
            ),
            _stat_card(
                "Por Facturar",
                MisEntregablesState.stats_por_facturar,
                "receipt",
                "sky",
                MisEntregablesState.filtrar_por_facturar,
                MisEntregablesState.filtro_es_por_facturar,
            ),
            _stat_card(
                "Pagados",
                MisEntregablesState.stats_pagados,
                "badge-check",
                "green",
                MisEntregablesState.filtrar_pagados,
                MisEntregablesState.filtro_es_pagado,
            ),
            spacing="3",
            width="100%",
            flex_wrap="wrap",
        ),
        spacing="3",
        width="100%",
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
    """Card para entregable aprobado - requiere subir prefactura."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.badge("APROBADO", color_scheme="green", size="2", variant="soft"),
                rx.text("Suba prefactura para continuar", size="1", color=Colors.WARNING, weight="medium"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            # Info periodo
            rx.hstack(
                rx.text(f"Periodo {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            # Monto aprobado + accion
            rx.cond(
                entregable["monto_aprobado"],
                rx.hstack(
                    rx.icon("banknote", size=14, color=Colors.SUCCESS),
                    rx.text(f"Monto: ${entregable['monto_aprobado']}", size="2", weight="medium", color=Colors.SUCCESS),
                    rx.spacer(),
                    rx.button(
                        rx.icon("file-text", size=14),
                        "Subir Prefactura",
                        size="2",
                        color_scheme="teal",
                        on_click=lambda: MisEntregablesState.abrir_modal_prefactura(entregable["id"]),
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
        _hover={"border_color": Colors.PORTAL_PRIMARY},
    )


def _card_prefactura_enviada(entregable: dict) -> rx.Component:
    """Card para prefactura enviada - esperando validacion BUAP."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge("PREFACTURA ENVIADA", color_scheme="sky", size="2", variant="soft"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.text(f"Periodo {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.icon("clock", size=14, color=Colors.INFO),
                rx.text("Esperando validacion de BUAP", size="2", color=Colors.INFO),
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


def _card_prefactura_rechazada(entregable: dict) -> rx.Component:
    """Card para prefactura rechazada - mostrar observaciones y boton corregir."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge("PREFACTURA RECHAZADA", color_scheme="red", size="2", variant="solid"),
                rx.text("Requiere correccion", size="1", color=Colors.ERROR, weight="medium"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.text(f"Periodo {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            rx.cond(
                entregable["observaciones_prefactura"],
                rx.callout(
                    rx.text(entregable["observaciones_prefactura"], size="2"),
                    icon="message-circle",
                    color_scheme="red",
                    size="1",
                ),
                rx.fragment(),
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    rx.icon("upload", size=14),
                    "Corregir Prefactura",
                    size="2",
                    color_scheme="red",
                    on_click=lambda: MisEntregablesState.abrir_modal_prefactura(entregable["id"]),
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


def _card_prefactura_aprobada(entregable: dict) -> rx.Component:
    """Card para prefactura aprobada - requiere subir factura definitiva."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge("PREFACTURA APROBADA", color_scheme="green", size="2", variant="soft"),
                rx.text("Suba factura definitiva", size="1", color=Colors.WARNING, weight="medium"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.text(f"Periodo {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.cond(
                    entregable["monto_aprobado"],
                    rx.hstack(
                        rx.icon("banknote", size=14, color=Colors.SUCCESS),
                        rx.text(f"Monto: ${entregable['monto_aprobado']}", size="2", weight="medium", color=Colors.SUCCESS),
                        spacing="1",
                        align="center",
                    ),
                    rx.fragment(),
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("receipt", size=14),
                    "Subir Factura",
                    size="2",
                    color_scheme="teal",
                    on_click=lambda: MisEntregablesState.abrir_modal_factura(entregable["id"]),
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
        _hover={"border_color": Colors.PORTAL_PRIMARY},
    )


def _card_facturado(entregable: dict) -> rx.Component:
    """Card para entregable facturado - pendiente de pago."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge("FACTURADO", color_scheme="amber", size="2", variant="soft"),
                rx.text("Pendiente de pago", size="1", color=Colors.WARNING, weight="medium"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.text(f"Periodo {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            rx.cond(
                entregable["folio_fiscal"],
                rx.hstack(
                    rx.icon("hash", size=14, color=Colors.TEXT_MUTED),
                    rx.text(f"Folio fiscal: {entregable['folio_fiscal']}", size="1", color=Colors.TEXT_SECONDARY),
                    spacing="1",
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


def _card_pagado(entregable: dict) -> rx.Component:
    """Card para entregable pagado - proceso completado."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge("PAGADO", color_scheme="green", size="2", variant="soft"),
                rx.spacer(),
                rx.badge(entregable["contrato_codigo"], color_scheme="gray", size="1"),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.text(f"Periodo {entregable['numero_periodo']}", size="3", weight="bold"),
                rx.text("•", color=Colors.TEXT_MUTED),
                rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.cond(
                    entregable["monto_aprobado"],
                    rx.hstack(
                        rx.icon("badge-check", size=14, color=Colors.SUCCESS),
                        rx.text(f"${entregable['monto_aprobado']}", size="2", weight="medium", color=Colors.SUCCESS),
                        spacing="1",
                        align="center",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    entregable["fecha_pago_registrado"],
                    rx.text(f"Pagado: {entregable['fecha_pago_registrado']}", size="1", color=Colors.TEXT_MUTED),
                    rx.fragment(),
                ),
                width="100%",
                align="center",
            ),
            spacing="3",
            width="100%",
        ),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.SUCCESS}",
        border_radius=Radius.MD,
    )


def _card_entregable(entregable: dict) -> rx.Component:
    """Renderiza el card segun el estatus del entregable."""
    return rx.match(
        entregable["estatus"],
        ("RECHAZADO", _card_rechazado(entregable)),
        ("PENDIENTE", _card_pendiente(entregable)),
        ("EN_REVISION", _card_en_revision(entregable)),
        ("APROBADO", _card_aprobado(entregable)),
        ("PREFACTURA_ENVIADA", _card_prefactura_enviada(entregable)),
        ("PREFACTURA_RECHAZADA", _card_prefactura_rechazada(entregable)),
        ("PREFACTURA_APROBADA", _card_prefactura_aprobada(entregable)),
        ("FACTURADO", _card_facturado(entregable)),
        ("PAGADO", _card_pagado(entregable)),
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
# MODAL: SUBIR PREFACTURA
# =============================================================================
def _modal_prefactura() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                MisEntregablesState.entregable_actual,
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Subir Prefactura", size="5", weight="bold"),
                            rx.hstack(
                                rx.badge(MisEntregablesState.entregable_actual["contrato_codigo"], color_scheme="blue", size="1"),
                                rx.text(f"Periodo {MisEntregablesState.entregable_actual['numero_periodo']}", size="2", color=Colors.TEXT_SECONDARY),
                                spacing="2",
                                align="center",
                            ),
                            spacing="1",
                        ),
                        rx.spacer(),
                        rx.dialog.close(
                            rx.button(rx.icon("x", size=16), variant="ghost", size="1", on_click=MisEntregablesState.cerrar_modal_prefactura),
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.divider(),
                    rx.cond(
                        MisEntregablesState.entregable_actual["monto_aprobado"],
                        rx.callout(
                            rx.text(f"Monto aprobado: ${MisEntregablesState.entregable_actual['monto_aprobado']}", weight="bold"),
                            icon="banknote",
                            color_scheme="green",
                            size="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.callout(
                        rx.text("BUAP validara los datos fiscales antes de solicitar la factura definitiva.", size="2"),
                        icon="info",
                        color_scheme="blue",
                        size="1",
                        width="100%",
                    ),
                    # Upload zone
                    rx.upload(
                        rx.vstack(
                            rx.cond(
                                MisEntregablesState.enviando_prefactura,
                                rx.vstack(rx.spinner(size="3"), rx.text("Subiendo...", size="2"), align="center", spacing="2"),
                                rx.vstack(
                                    rx.icon("file-text", size=32, color=Colors.PORTAL_PRIMARY),
                                    rx.text("Click o arrastra el PDF de prefactura", size="3", weight="medium"),
                                    rx.text("Solo PDF", size="2", color=Colors.TEXT_MUTED),
                                    align="center",
                                    spacing="2",
                                ),
                            ),
                            align="center",
                            justify="center",
                            padding=Spacing.XL,
                            width="100%",
                        ),
                        id="upload_prefactura",
                        accept={"application/pdf": [".pdf"]},
                        max_files=1,
                        border=f"2px dashed {Colors.TEXT_MUTED}",
                        border_radius="8px",
                        cursor="pointer",
                        _hover={"borderColor": Colors.PORTAL_PRIMARY},
                        width="100%",
                    ),
                    rx.cond(
                        rx.selected_files("upload_prefactura").length() > 0,
                        rx.hstack(
                            rx.icon("file", size=14, color=Colors.PORTAL_PRIMARY),
                            rx.foreach(rx.selected_files("upload_prefactura"), lambda f: rx.text(f, size="2")),
                            spacing="2",
                            align="center",
                        ),
                        rx.fragment(),
                    ),
                    rx.divider(),
                    rx.hstack(
                        rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=MisEntregablesState.cerrar_modal_prefactura),
                        rx.spacer(),
                        rx.button(
                            rx.icon("send", size=14),
                            "Enviar Prefactura",
                            color_scheme="teal",
                            disabled=rx.selected_files("upload_prefactura").length() == 0,
                            loading=MisEntregablesState.enviando_prefactura,
                            on_click=MisEntregablesState.subir_prefactura(rx.upload_files(upload_id="upload_prefactura")),
                        ),
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.spinner(),
            ),
            max_width="500px",
            padding="5",
        ),
        open=MisEntregablesState.mostrar_modal_prefactura,
        on_open_change=MisEntregablesState.set_mostrar_modal_prefactura,
    )


# =============================================================================
# MODAL: SUBIR FACTURA + XML
# =============================================================================
def _validacion_xml() -> rx.Component:
    """Muestra resultado de validacion XML CFDI."""
    return rx.cond(
        MisEntregablesState.resultado_validacion_xml,
        rx.vstack(
            rx.text("Validacion CFDI", size="3", weight="bold"),
            rx.hstack(
                rx.cond(
                    MisEntregablesState.resultado_validacion_xml["es_valido"],
                    rx.badge(rx.hstack(rx.icon("check", size=12), "Valido", spacing="1"), color_scheme="green"),
                    rx.badge(rx.hstack(rx.icon("x", size=12), "Con errores", spacing="1"), color_scheme="red"),
                ),
                spacing="2",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text("RFC Emisor:", size="2", weight="medium", min_width="100px"),
                    rx.text(MisEntregablesState.resultado_validacion_xml["rfc_emisor"], size="2"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.text("RFC Receptor:", size="2", weight="medium", min_width="100px"),
                    rx.text(MisEntregablesState.resultado_validacion_xml["rfc_receptor"], size="2"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.text("Monto:", size="2", weight="medium", min_width="100px"),
                    rx.text(f"${MisEntregablesState.resultado_validacion_xml['monto_total']}", size="2"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.text("Folio Fiscal:", size="2", weight="medium", min_width="100px"),
                    rx.text(MisEntregablesState.resultado_validacion_xml["folio_fiscal"], size="2"),
                    spacing="2",
                    align="center",
                ),
                spacing="1",
                padding=Spacing.SM,
                background=Colors.SECONDARY_LIGHT,
                border_radius=Radius.MD,
                width="100%",
            ),
            rx.cond(
                MisEntregablesState.resultado_validacion_xml["errores"].to(list[str]).length() > 0,
                rx.callout(
                    rx.vstack(
                        rx.foreach(
                            MisEntregablesState.resultado_validacion_xml["errores"].to(list[str]),
                            lambda err: rx.text(err, size="2"),
                        ),
                        spacing="1",
                    ),
                    icon="triangle-alert",
                    color_scheme="red",
                    size="1",
                    width="100%",
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
        ),
        rx.fragment(),
    )


def _modal_factura() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                MisEntregablesState.entregable_actual,
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Subir Factura", size="5", weight="bold"),
                            rx.hstack(
                                rx.badge(MisEntregablesState.entregable_actual["contrato_codigo"], color_scheme="blue", size="1"),
                                rx.text(f"Periodo {MisEntregablesState.entregable_actual['numero_periodo']}", size="2", color=Colors.TEXT_SECONDARY),
                                spacing="2",
                                align="center",
                            ),
                            spacing="1",
                        ),
                        rx.spacer(),
                        rx.dialog.close(
                            rx.button(rx.icon("x", size=16), variant="ghost", size="1", on_click=MisEntregablesState.cerrar_modal_factura),
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.divider(),
                    rx.cond(
                        MisEntregablesState.entregable_actual["monto_aprobado"],
                        rx.callout(
                            rx.text(f"Monto aprobado: ${MisEntregablesState.entregable_actual['monto_aprobado']}", weight="bold"),
                            icon="banknote",
                            color_scheme="green",
                            size="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    # 1. Upload Factura PDF
                    rx.vstack(
                        rx.text("1. Factura PDF", size="3", weight="bold"),
                        rx.upload(
                            rx.vstack(
                                rx.icon("file-text", size=24, color=Colors.PORTAL_PRIMARY),
                                rx.text("Subir PDF de factura", size="2", weight="medium"),
                                align="center",
                                spacing="1",
                                padding=Spacing.MD,
                            ),
                            id="upload_factura_pdf",
                            accept={"application/pdf": [".pdf"]},
                            max_files=1,
                            border=f"2px dashed {Colors.TEXT_MUTED}",
                            border_radius="8px",
                            cursor="pointer",
                            _hover={"borderColor": Colors.PORTAL_PRIMARY},
                            width="100%",
                        ),
                        rx.cond(
                            rx.selected_files("upload_factura_pdf").length() > 0,
                            rx.hstack(
                                rx.button(
                                    "Subir PDF",
                                    size="2",
                                    color_scheme="teal",
                                    loading=MisEntregablesState.subiendo_factura_pdf,
                                    on_click=MisEntregablesState.subir_factura_pdf(rx.upload_files(upload_id="upload_factura_pdf")),
                                ),
                                spacing="2",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    # 2. Upload XML CFDI
                    rx.vstack(
                        rx.text("2. XML CFDI", size="3", weight="bold"),
                        rx.upload(
                            rx.vstack(
                                rx.icon("code-xml", size=24, color=Colors.PORTAL_PRIMARY),
                                rx.text("Subir XML del CFDI", size="2", weight="medium"),
                                align="center",
                                spacing="1",
                                padding=Spacing.MD,
                            ),
                            id="upload_factura_xml",
                            accept={"application/xml": [".xml"], "text/xml": [".xml"]},
                            max_files=1,
                            border=f"2px dashed {Colors.TEXT_MUTED}",
                            border_radius="8px",
                            cursor="pointer",
                            _hover={"borderColor": Colors.PORTAL_PRIMARY},
                            width="100%",
                        ),
                        rx.cond(
                            rx.selected_files("upload_factura_xml").length() > 0,
                            rx.hstack(
                                rx.button(
                                    "Subir y Validar XML",
                                    size="2",
                                    color_scheme="teal",
                                    loading=MisEntregablesState.subiendo_factura_xml,
                                    on_click=MisEntregablesState.subir_factura_xml(rx.upload_files(upload_id="upload_factura_xml")),
                                ),
                                spacing="2",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    # 3. Resultado de validacion
                    _validacion_xml(),
                    rx.divider(),
                    rx.hstack(
                        rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=MisEntregablesState.cerrar_modal_factura),
                        rx.spacer(),
                        rx.button(
                            rx.icon("send", size=14),
                            "Enviar Factura",
                            color_scheme="teal",
                            disabled=MisEntregablesState.folio_fiscal_xml == "",
                            loading=MisEntregablesState.enviando_factura,
                            on_click=MisEntregablesState.enviar_factura,
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
        open=MisEntregablesState.mostrar_modal_factura,
        on_open_change=MisEntregablesState.set_mostrar_modal_factura,
    )


# =============================================================================
# PAGINA
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
        _modal_prefactura(),
        _modal_factura(),
        spacing="4",
        width="100%",
    )


def mis_entregables_page() -> rx.Component:
    return rx.box(
        _contenido_principal(),
        on_mount=MisEntregablesState.on_load_mis_entregables,
    )
