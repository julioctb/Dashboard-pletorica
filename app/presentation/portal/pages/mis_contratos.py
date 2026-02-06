"""
Pagina Mis Contratos del portal de cliente.

Muestra la lista de contratos de la empresa en modo solo lectura.
Permite busqueda y filtro por estatus. Incluye detalle expandible.
"""
import reflex as rx
from typing import List

from app.presentation.portal.state.portal_state import PortalState
from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.components.ui import skeleton_tabla
from app.presentation.theme import Colors, Typography, Spacing
from app.services import contrato_service
from app.core.exceptions import DatabaseError


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

    # Setters
    def set_filtro_busqueda_cto(self, value: str):
        self.filtro_busqueda_cto = value

    def set_filtro_estatus_cto(self, value: str):
        self.filtro_estatus_cto = value

    async def on_mount_contratos(self):
        resultado = await self.on_mount_portal()
        if resultado:
            return resultado
        await self.cargar_contratos()

    async def cargar_contratos(self):
        """Carga contratos de la empresa del usuario."""
        if not self.id_empresa_actual:
            return

        self.loading = True
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
        finally:
            self.loading = False

    async def aplicar_filtros_cto(self):
        await self.cargar_contratos()

    def abrir_detalle(self, contrato: dict):
        """Abre el modal de detalle de un contrato."""
        self.contrato_detalle = contrato
        self.modal_detalle_abierto = True

    def cerrar_detalle(self):
        self.modal_detalle_abierto = False
        self.contrato_detalle = {}

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


# =============================================================================
# COMPONENTES
# =============================================================================

def _badge_estatus_contrato(estatus: str) -> rx.Component:
    """Badge de estatus del contrato."""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("Activo", color_scheme="green", variant="soft", size="1")),
        ("BORRADOR", rx.badge("Borrador", color_scheme="gray", variant="soft", size="1")),
        ("SUSPENDIDO", rx.badge("Suspendido", color_scheme="orange", variant="soft", size="1")),
        ("VENCIDO", rx.badge("Vencido", color_scheme="red", variant="soft", size="1")),
        ("CANCELADO", rx.badge("Cancelado", color_scheme="red", variant="soft", size="1")),
        rx.badge(estatus, size="1"),
    )


def _fila_contrato(cto: dict) -> rx.Component:
    """Fila de la tabla de contratos."""
    return rx.table.row(
        rx.table.cell(
            rx.text(
                cto["codigo"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.PORTAL_PRIMARY_TEXT,
            ),
        ),
        rx.table.cell(
            rx.text(
                rx.cond(cto["numero_folio_buap"], cto["numero_folio_buap"], "-"),
                font_size=Typography.SIZE_SM,
            ),
        ),
        rx.table.cell(
            rx.text(
                cto["tipo_contrato"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.text(
                    rx.cond(cto["fecha_inicio"], cto["fecha_inicio"], "-"),
                    font_size=Typography.SIZE_SM,
                ),
                rx.text(
                    " - ",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text(
                    rx.cond(cto["fecha_fin"], cto["fecha_fin"], "Indefinido"),
                    font_size=Typography.SIZE_SM,
                ),
                spacing="1",
            ),
        ),
        rx.table.cell(
            _badge_estatus_contrato(cto["estatus"]),
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("eye", size=14),
                variant="ghost",
                size="1",
                on_click=MisContratosState.abrir_detalle(cto),
                cursor="pointer",
            ),
        ),
    )


ENCABEZADOS_CONTRATOS = [
    {"nombre": "Codigo", "ancho": "150px"},
    {"nombre": "Folio BUAP", "ancho": "150px"},
    {"nombre": "Tipo", "ancho": "120px"},
    {"nombre": "Vigencia", "ancho": "auto"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "", "ancho": "50px"},
]


def _tabla_contratos() -> rx.Component:
    """Tabla de contratos."""
    return rx.cond(
        MisContratosState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_CONTRATOS, filas=5),
        rx.cond(
            MisContratosState.total_contratos_lista > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_CONTRATOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            MisContratosState.contratos_filtrados,
                            _fila_contrato,
                        ),
                    ),
                    width="100%",
                    variant="surface",
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
                rx.select.item("Todos", value="TODOS"),
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
            rx.button(
                "Cerrar",
                variant="outline",
                size="2",
                width="100%",
                on_click=MisContratosState.cerrar_detalle,
            ),
            max_width="600px",
        ),
        open=MisContratosState.modal_detalle_abierto,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


# =============================================================================
# PAGINA
# =============================================================================

def mis_contratos_page() -> rx.Component:
    """Pagina de lista de contratos (solo lectura)."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Contratos",
                subtitulo="Contratos de la empresa",
                icono="file-text",
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
                _tabla_contratos(),
                _modal_detalle_contrato(),
                width="100%",
                spacing="4",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MisContratosState.on_mount_contratos,
    )
