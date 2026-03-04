"""
Pagina Mis Contratos del portal de cliente.

Muestra la lista de contratos de la empresa.
Permite búsqueda, filtro por estatus, detalle, edición y cambios de estatus para admin_empresa.
"""
import reflex as rx
from typing import List

from app.presentation.constants import FILTRO_TODOS
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.pages.contratos.contratos_modals import modal_contrato
from app.presentation.pages.contratos.contratos_state import ContratosState
from app.presentation.portal.state.portal_state import PortalState
from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.components.ui import (
    entity_card,
    entity_grid,
    boton_cancelar,
    boton_eliminar,
)
from app.presentation.theme import Colors, Typography, Spacing
from app.services import contrato_service
from app.core.exceptions import DatabaseError, BusinessRuleError


# =============================================================================
# STATE
# =============================================================================

class MisContratosState(PortalState):
    """State para la lista de contratos del portal."""

    contratos: List[dict] = []
    total_contratos_lista: int = 0

    # Filtros
    filtro_busqueda_cto: str = ""
    filtro_estatus_cto: str = "ACTIVO"

    # Detalle
    contrato_detalle: dict = {}
    modal_detalle_abierto: bool = False
    mostrar_modal_confirmar_cancelar: bool = False
    saving_accion_contrato: bool = False

    # Setters
    def set_filtro_busqueda_cto(self, value: str):
        self.filtro_busqueda_cto = value

    def set_filtro_estatus_cto(self, value: str):
        self.filtro_estatus_cto = value

    async def on_mount_contratos(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.mostrar_seccion_contrato:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_contratos):
            yield

    async def _fetch_contratos(self):
        """Carga contratos de la empresa del usuario (sin manejo de loading)."""
        if not self.id_empresa_actual:
            return

        try:
            incluir_inactivos = self.filtro_estatus_cto != "ACTIVO"
            contratos = await contrato_service.obtener_por_empresa(
                empresa_id=self.id_empresa_actual,
                incluir_inactivos=incluir_inactivos,
            )
            self.contratos = [
                c.model_dump(mode='json') if hasattr(c, 'model_dump') else c
                for c in contratos
            ]
            self.total_contratos_lista = len(self.contratos)
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando contratos: {e}", "error")
            self.contratos = []
            self.total_contratos_lista = 0
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.contratos = []
            self.total_contratos_lista = 0

    async def cargar_contratos(self):
        """Recarga contratos con skeleton (filtros)."""
        async for _ in self._recargar_datos(self._fetch_contratos):
            yield

    async def aplicar_filtros_cto(self):
        async for _ in self.cargar_contratos():
            yield

    def abrir_detalle(self, contrato: dict):
        """Abre el modal de detalle de un contrato."""
        self.contrato_detalle = contrato
        self.modal_detalle_abierto = True

    def cerrar_detalle(self):
        self.modal_detalle_abierto = False
        self.contrato_detalle = {}

    def abrir_confirmar_cancelar(self):
        """Abre la confirmación de cancelación para el contrato en detalle."""
        if not self.contrato_detalle:
            return rx.toast.error("No hay contrato seleccionado")
        self.modal_detalle_abierto = False
        self.mostrar_modal_confirmar_cancelar = True

    def cerrar_confirmar_cancelar(self):
        self.mostrar_modal_confirmar_cancelar = False

    async def abrir_edicion_contrato(self):
        """Abre el modal de edición del contrato seleccionado desde el detalle."""
        if not self.es_admin_empresa:
            return rx.toast.error("Solo admin_empresa puede editar contratos en el portal")

        contrato = self.contrato_detalle
        if not contrato:
            return rx.toast.error("No hay contrato seleccionado")

        contrato_empresa_id = int(contrato.get("empresa_id") or 0)
        if not self.id_empresa_actual or contrato_empresa_id != int(self.id_empresa_actual):
            return rx.toast.error("Solo puedes editar contratos de la empresa activa")

        contratos_state = await self.get_state(ContratosState)
        await contratos_state.cargar_empresas()
        await contratos_state.cargar_tipos_servicio()

        self.cerrar_detalle()
        return contratos_state.abrir_modal_editar(contrato)

    def _asegurar_permiso_operar_contrato(self, contrato: dict):
        """Valida que el contrato pertenezca a la empresa activa del portal."""
        if not self.es_admin_empresa:
            raise BusinessRuleError("Solo admin_empresa puede operar contratos en el portal")

        if not contrato:
            raise BusinessRuleError("No hay contrato seleccionado")

        contrato_empresa_id = int(contrato.get("empresa_id") or 0)
        if not self.id_empresa_actual or contrato_empresa_id != int(self.id_empresa_actual):
            raise BusinessRuleError("Solo puedes operar contratos de la empresa activa")

    async def activar_contrato(self):
        """Activa un contrato en borrador desde el portal."""
        contrato = self.contrato_detalle
        try:
            self._asegurar_permiso_operar_contrato(contrato)
            self.saving_accion_contrato = True
            codigo = contrato.get("codigo", "")
            await contrato_service.activar(int(contrato["id"]))
            self.cerrar_detalle()
            await self._fetch_contratos()
            return rx.toast.success(f"Contrato '{codigo}' activado exitosamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "activando contrato")
        finally:
            self.saving_accion_contrato = False

    async def suspender_contrato(self):
        """Suspende un contrato activo desde el portal."""
        contrato = self.contrato_detalle
        try:
            self._asegurar_permiso_operar_contrato(contrato)
            self.saving_accion_contrato = True
            codigo = contrato.get("codigo", "")
            await contrato_service.suspender(int(contrato["id"]))
            self.cerrar_detalle()
            await self._fetch_contratos()
            return rx.toast.success(f"Contrato '{codigo}' suspendido exitosamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "suspendiendo contrato")
        finally:
            self.saving_accion_contrato = False

    async def reactivar_contrato(self):
        """Reactiva un contrato suspendido desde el portal."""
        contrato = self.contrato_detalle
        try:
            self._asegurar_permiso_operar_contrato(contrato)
            self.saving_accion_contrato = True
            codigo = contrato.get("codigo", "")
            await contrato_service.reactivar(int(contrato["id"]))
            self.cerrar_detalle()
            await self._fetch_contratos()
            return rx.toast.success(f"Contrato '{codigo}' reactivado exitosamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "reactivando contrato")
        finally:
            self.saving_accion_contrato = False

    async def cancelar_contrato(self):
        """Cancela el contrato seleccionado desde el portal."""
        contrato = self.contrato_detalle
        try:
            self._asegurar_permiso_operar_contrato(contrato)
            self.saving_accion_contrato = True
            codigo = contrato.get("codigo", "")
            await contrato_service.cancelar(int(contrato["id"]))
            self.cerrar_confirmar_cancelar()
            self.contrato_detalle = {}
            await self._fetch_contratos()
            return rx.toast.success(f"Contrato '{codigo}' cancelado exitosamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "cancelando contrato")
        finally:
            self.saving_accion_contrato = False

    @rx.var
    def contratos_filtrados(self) -> List[dict]:
        """Filtra contratos por texto de busqueda."""
        if not self.filtro_busqueda_cto:
            return self.contratos
        termino = self.filtro_busqueda_cto.lower()
        return [
            c for c in self.contratos
            if termino in (c.get("codigo") or "").lower()
            or termino in (c.get("numero_folio_buap") or "").lower()
            or termino in (c.get("descripcion_objeto") or "").lower()
        ]

    @rx.var
    def puede_editar_detalle(self) -> bool:
        contrato = self.contrato_detalle
        if not self.es_admin_empresa or not contrato:
            return False
        estatus = str(contrato.get("estatus", ""))
        return estatus in ("BORRADOR", "SUSPENDIDO")

    @rx.var
    def puede_activar_detalle(self) -> bool:
        contrato = self.contrato_detalle
        return bool(self.es_admin_empresa and contrato and contrato.get("estatus") == "BORRADOR")

    @rx.var
    def puede_suspender_detalle(self) -> bool:
        contrato = self.contrato_detalle
        return bool(self.es_admin_empresa and contrato and contrato.get("estatus") == "ACTIVO")

    @rx.var
    def puede_reactivar_detalle(self) -> bool:
        contrato = self.contrato_detalle
        return bool(self.es_admin_empresa and contrato and contrato.get("estatus") == "SUSPENDIDO")

    @rx.var
    def puede_cancelar_detalle(self) -> bool:
        contrato = self.contrato_detalle
        return bool(self.es_admin_empresa and contrato and contrato.get("estatus") != "CANCELADO")


# =============================================================================
# COMPONENTES
# =============================================================================

def _card_contrato(cto: dict) -> rx.Component:
    """Card de un contrato individual."""
    return entity_card(
        icono="file-text",
        color_icono=Colors.PORTAL_PRIMARY,
        titulo=cto["codigo"],
        subtitulo=cto["descripcion_objeto"],
        status=cto["estatus"],
        badge_superior=rx.badge(
            cto["tipo_contrato"],
            color_scheme="teal",
            variant="soft",
            size="1",
        ),
        campos=[
            ("Folio BUAP", rx.cond(cto["numero_folio_buap"], cto["numero_folio_buap"], "-")),
            ("Inicio", rx.cond(cto["fecha_inicio"], cto["fecha_inicio"], "-")),
            ("Fin", rx.cond(cto["fecha_fin"], cto["fecha_fin"], "Indefinido")),
        ],
        on_click=MisContratosState.abrir_detalle(cto),
    )


def _grid_contratos() -> rx.Component:
    """Grid de cards de contratos."""
    return rx.cond(
        MisContratosState.loading,
        rx.center(
            rx.spinner(size="3"),
            padding=Spacing.MD,
            width="100%",
        ),
        rx.cond(
            MisContratosState.total_contratos_lista > 0,
            rx.vstack(
                entity_grid(
                    items=MisContratosState.contratos_filtrados,
                    render_card=_card_contrato,
                ),
                rx.text(
                    "Mostrando ",
                    MisContratosState.total_contratos_lista,
                    " contrato(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                width="100%",
                spacing="3",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("file-text", size=48, color=Colors.TEXT_MUTED),
                    rx.text(
                        "No hay contratos registrados",
                        font_size=Typography.SIZE_LG,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="3",
                    align="center",
                ),
                padding=Spacing.MD,
                width="100%",
            ),
        ),
    )


def _filtros_contratos() -> rx.Component:
    """Filtros de la tabla de contratos."""
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(placeholder="Estatus"),
            rx.select.content(
                rx.select.item("Activos", value="ACTIVO"),
                rx.select.item("Todos", value=FILTRO_TODOS),
            ),
            value=MisContratosState.filtro_estatus_cto,
            on_change=MisContratosState.set_filtro_estatus_cto,
            size="2",
        ),
        rx.button(
            rx.icon("filter", size=14),
            "Filtrar",
            on_click=MisContratosState.aplicar_filtros_cto,
            variant="soft",
            size="2",
        ),
        spacing="3",
        align="center",
    )


# =============================================================================
# MODAL DE DETALLE
# =============================================================================

def _campo_detalle(label: str, valor: rx.Var) -> rx.Component:
    """Campo de detalle en modo solo lectura."""
    return rx.vstack(
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing=Typography.LETTER_SPACING_WIDE,
        ),
        rx.cond(
            valor,
            rx.text(
                valor,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                "No disponible",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
                font_style="italic",
            ),
        ),
        spacing="1",
        width="100%",
    )


def _modal_detalle_contrato() -> rx.Component:
    """Modal con detalle del contrato seleccionado."""
    datos = MisContratosState.contrato_detalle

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("file-text", size=20, color=Colors.PORTAL_PRIMARY),
                    rx.text("Detalle del Contrato"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.dialog.description(
                rx.text(
                    datos["codigo"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
            ),
            rx.separator(),
            rx.vstack(
                # Identificacion
                rx.grid(
                    _campo_detalle("Codigo", datos["codigo"]),
                    _campo_detalle("Folio BUAP", datos["numero_folio_buap"]),
                    _campo_detalle("Tipo Contrato", datos["tipo_contrato"]),
                    _campo_detalle("Estatus", datos["estatus"]),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    spacing="4",
                    width="100%",
                ),
                rx.separator(),
                # Descripcion
                _campo_detalle("Descripcion del Objeto", datos["descripcion_objeto"]),
                rx.separator(),
                # Vigencia
                rx.grid(
                    _campo_detalle("Fecha Inicio", datos["fecha_inicio"]),
                    _campo_detalle("Fecha Fin", datos["fecha_fin"]),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    spacing="4",
                    width="100%",
                ),
                rx.separator(),
                # Montos
                rx.grid(
                    _campo_detalle("Monto Minimo", datos["monto_minimo"]),
                    _campo_detalle("Monto Maximo", datos["monto_maximo"]),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    spacing="4",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding_y=Spacing.BASE,
            ),
            rx.vstack(
                rx.hstack(
                    rx.cond(
                        MisContratosState.puede_editar_detalle,
                        rx.button(
                            rx.icon("pencil", size=16),
                            "Editar contrato",
                            on_click=MisContratosState.abrir_edicion_contrato,
                            color_scheme="teal",
                            variant="soft",
                            disabled=MisContratosState.saving_accion_contrato,
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        MisContratosState.puede_activar_detalle,
                        rx.button(
                            rx.icon("check", size=16),
                            "Activar",
                            on_click=MisContratosState.activar_contrato,
                            color_scheme="green",
                            variant="soft",
                            disabled=MisContratosState.saving_accion_contrato,
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        MisContratosState.puede_suspender_detalle,
                        rx.button(
                            rx.icon("pause", size=16),
                            "Suspender",
                            on_click=MisContratosState.suspender_contrato,
                            color_scheme="orange",
                            variant="soft",
                            disabled=MisContratosState.saving_accion_contrato,
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        MisContratosState.puede_reactivar_detalle,
                        rx.button(
                            rx.icon("play", size=16),
                            "Reactivar",
                            on_click=MisContratosState.reactivar_contrato,
                            color_scheme="green",
                            variant="soft",
                            disabled=MisContratosState.saving_accion_contrato,
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        MisContratosState.puede_cancelar_detalle,
                        rx.button(
                            rx.icon("x", size=16),
                            "Cancelar contrato",
                            on_click=MisContratosState.abrir_confirmar_cancelar,
                            color_scheme="red",
                            variant="soft",
                            disabled=MisContratosState.saving_accion_contrato,
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    wrap="wrap",
                    width="100%",
                ),
                rx.hstack(
                    rx.spacer(),
                    boton_cancelar(
                        texto="Cerrar",
                        on_click=MisContratosState.cerrar_detalle,
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="600px",
        ),
        open=MisContratosState.modal_detalle_abierto,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def _modal_confirmar_cancelar() -> rx.Component:
    """Modal de confirmación para cancelar el contrato desde el portal."""
    datos = MisContratosState.contrato_detalle

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Cancelar contrato"),
            rx.dialog.description(
                rx.cond(
                    datos,
                    rx.text(
                        "¿Está seguro que desea cancelar el contrato ",
                        rx.text(datos["codigo"], weight="bold", as_="span"),
                        "? Esta acción no se puede deshacer.",
                    ),
                    rx.text("¿Está seguro que desea cancelar este contrato?"),
                ),
            ),
            rx.hstack(
                boton_cancelar(
                    texto="No, conservar",
                    on_click=MisContratosState.cerrar_confirmar_cancelar,
                    disabled=MisContratosState.saving_accion_contrato,
                ),
                boton_eliminar(
                    texto="Sí, cancelar",
                    texto_eliminando="Cancelando...",
                    on_click=MisContratosState.cancelar_contrato,
                    saving=MisContratosState.saving_accion_contrato,
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),
            max_width="500px",
        ),
        open=MisContratosState.mostrar_modal_confirmar_cancelar,
        on_open_change=rx.noop,
    )


# =============================================================================
# PAGINA
# =============================================================================

def mis_contratos_page() -> rx.Component:
    """Pagina de lista de contratos del portal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Contratos",
                subtitulo="Contratos de la empresa",
                icono="file-text",
                accion_principal=rx.cond(
                    AuthState.es_admin_empresa,
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo Contrato",
                        on_click=ContratosState.abrir_modal_crear_portal,
                        color_scheme="blue",
                    ),
                    rx.fragment(),
                ),
            ),
            toolbar=page_toolbar(
                search_value=MisContratosState.filtro_busqueda_cto,
                search_placeholder="Buscar por codigo, folio o descripcion...",
                on_search_change=MisContratosState.set_filtro_busqueda_cto,
                on_search_clear=lambda: MisContratosState.set_filtro_busqueda_cto(""),
                show_view_toggle=False,
                filters=_filtros_contratos(),
            ),
            content=rx.vstack(
                _grid_contratos(),
                _modal_detalle_contrato(),
                _modal_confirmar_cancelar(),
                modal_contrato(),
                width="100%",
                spacing="4",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MisContratosState.on_mount_contratos,
    )
