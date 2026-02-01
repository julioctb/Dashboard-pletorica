"""
Pagina Mis Empleados del portal de cliente.

Muestra la lista de empleados de la empresa en modo solo lectura.
Permite busqueda y filtro por estatus.
"""
import reflex as rx
from typing import List

from app.presentation.portal.state.portal_state import PortalState
from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.components.ui import skeleton_tabla
from app.presentation.theme import Colors, Typography
from app.services import empleado_service
from app.core.exceptions import DatabaseError


# =============================================================================
# STATE
# =============================================================================

class MisEmpleadosState(PortalState):
    """State para la lista de empleados del portal."""

    empleados: List[dict] = []
    total_empleados_lista: int = 0

    # Filtros
    filtro_busqueda_emp: str = ""
    filtro_estatus_emp: str = "ACTIVO"

    # Setters
    def set_filtro_busqueda_emp(self, value: str):
        self.filtro_busqueda_emp = value

    def set_filtro_estatus_emp(self, value: str):
        self.filtro_estatus_emp = value

    async def on_mount_empleados(self):
        resultado = await self.on_mount_portal()
        if resultado:
            return resultado
        await self.cargar_empleados()

    async def cargar_empleados(self):
        """Carga empleados de la empresa del usuario."""
        if not self.id_empresa_actual:
            return

        self.loading = True
        try:
            incluir_inactivos = self.filtro_estatus_emp != "ACTIVO"
            empleados = await empleado_service.obtener_resumen_por_empresa(
                empresa_id=self.id_empresa_actual,
                incluir_inactivos=incluir_inactivos,
                limite=200,
            )
            self.empleados = [e.model_dump(mode='json') if hasattr(e, 'model_dump') else e for e in empleados]
            self.total_empleados_lista = len(self.empleados)
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando empleados: {e}", "error")
            self.empleados = []
            self.total_empleados_lista = 0
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.empleados = []
            self.total_empleados_lista = 0
        finally:
            self.loading = False

    async def aplicar_filtros_emp(self):
        await self.cargar_empleados()

    @rx.var
    def empleados_filtrados(self) -> List[dict]:
        """Filtra empleados por texto de busqueda."""
        if not self.filtro_busqueda_emp:
            return self.empleados
        termino = self.filtro_busqueda_emp.lower()
        return [
            e for e in self.empleados
            if termino in (e.get("nombre_completo") or "").lower()
            or termino in (e.get("clave") or "").lower()
            or termino in (e.get("curp") or "").lower()
        ]


# =============================================================================
# COMPONENTES
# =============================================================================

def _badge_estatus(estatus: str) -> rx.Component:
    """Badge de estatus del empleado."""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("Activo", color_scheme="green", variant="soft", size="1")),
        ("INACTIVO", rx.badge("Inactivo", color_scheme="red", variant="soft", size="1")),
        ("SUSPENDIDO", rx.badge("Suspendido", color_scheme="orange", variant="soft", size="1")),
        rx.badge(estatus, size="1"),
    )


def _fila_empleado(emp: dict) -> rx.Component:
    """Fila de la tabla de empleados."""
    return rx.table.row(
        rx.table.cell(
            rx.text(emp["clave"], size="2", weight="medium", color="var(--teal-11)"),
        ),
        rx.table.cell(
            rx.text(emp["nombre_completo"], size="2", weight="medium"),
        ),
        rx.table.cell(
            rx.text(emp["curp"], size="2", color="gray"),
        ),
        rx.table.cell(
            _badge_estatus(emp["estatus"]),
        ),
    )


ENCABEZADOS_EMPLEADOS = [
    {"nombre": "Clave", "ancho": "120px"},
    {"nombre": "Nombre", "ancho": "auto"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Estatus", "ancho": "100px"},
]


def _tabla_empleados() -> rx.Component:
    """Tabla de empleados."""
    return rx.cond(
        MisEmpleadosState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_EMPLEADOS, filas=5),
        rx.cond(
            MisEmpleadosState.total_empleados_lista > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_EMPLEADOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            MisEmpleadosState.empleados_filtrados,
                            _fila_empleado,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.text(
                    "Mostrando ",
                    MisEmpleadosState.total_empleados_lista,
                    " empleado(s)",
                    size="2",
                    color="gray",
                ),
                width="100%",
                spacing="3",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("users", size=48, color="var(--gray-6)"),
                    rx.text("No hay empleados registrados", color="gray", size="3"),
                    spacing="3",
                    align="center",
                ),
                padding="12",
            ),
        ),
    )


def _filtros_empleados() -> rx.Component:
    """Filtros de la tabla de empleados."""
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(placeholder="Estatus"),
            rx.select.content(
                rx.select.item("Activos", value="ACTIVO"),
                rx.select.item("Todos", value="TODOS"),
            ),
            value=MisEmpleadosState.filtro_estatus_emp,
            on_change=MisEmpleadosState.set_filtro_estatus_emp,
            size="2",
        ),
        rx.button(
            rx.icon("filter", size=14),
            "Filtrar",
            on_click=MisEmpleadosState.aplicar_filtros_emp,
            variant="soft",
            size="2",
        ),
        spacing="3",
        align="center",
    )


# =============================================================================
# PAGINA
# =============================================================================

def mis_empleados_page() -> rx.Component:
    """Pagina de lista de empleados (solo lectura)."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Empleados",
                subtitulo="Empleados de la empresa",
                icono="users",
            ),
            toolbar=page_toolbar(
                search_value=MisEmpleadosState.filtro_busqueda_emp,
                search_placeholder="Buscar por nombre, clave o CURP...",
                on_search_change=MisEmpleadosState.set_filtro_busqueda_emp,
                on_search_clear=lambda: MisEmpleadosState.set_filtro_busqueda_emp(""),
                show_view_toggle=False,
                filters=_filtros_empleados(),
            ),
            content=_tabla_empleados(),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MisEmpleadosState.on_mount_empleados,
    )
