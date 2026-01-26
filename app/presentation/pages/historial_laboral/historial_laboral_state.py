"""
Estado de Reflex para el módulo de Historial Laboral.

Este módulo es de SOLO LECTURA.
Los registros se crean automáticamente desde empleado_service.
"""
import reflex as rx
from typing import List, Optional

from app.presentation.components.shared.base_state import BaseState
from app.presentation.constants import FILTRO_TODOS
from app.services.historial_laboral_service import historial_laboral_service
from app.core.enums import EstatusHistorial, TipoMovimiento
from app.core.exceptions import DatabaseError


class HistorialLaboralState(BaseState):
    """Estado para el módulo de Historial Laboral (solo lectura)"""

    # ========================
    # ESTADO DE VISTA
    # ========================
    view_mode: str = "table"

    # ========================
    # DATOS
    # ========================
    historial: List[dict] = []
    registro_seleccionado: Optional[dict] = None
    total_registros: int = 0

    # ========================
    # FILTROS
    # ========================
    # filtro_busqueda heredado de BaseState
    filtro_estatus: str = FILTRO_TODOS
    filtro_empleado_id: str = ""

    # ========================
    # MODALES
    # ========================
    mostrar_modal_detalle: bool = False

    # ========================
    # SETTERS DE FILTROS
    # ========================
    def set_filtro_estatus(self, value: str):
        self.filtro_estatus = value if value else FILTRO_TODOS

    def set_filtro_empleado_id(self, value: str):
        self.filtro_empleado_id = value if value else ""

    # ========================
    # SETTERS DE VISTA
    # ========================
    def set_view_table(self):
        self.view_mode = "table"

    def set_view_cards(self):
        self.view_mode = "cards"

    @rx.var
    def is_table_view(self) -> bool:
        return self.view_mode == "table"

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def historial_filtrado(self) -> List[dict]:
        """Filtra historial por búsqueda en memoria"""
        if not self.filtro_busqueda:
            return self.historial

        termino = self.filtro_busqueda.lower()
        return [
            h for h in self.historial
            if termino in (h.get("empleado_nombre") or "").lower()
            or termino in (h.get("empleado_clave") or "").lower()
            or termino in str(h.get("plaza_numero") or "").lower()
            or termino in (h.get("categoria_nombre") or "").lower()
            or termino in (h.get("empresa_nombre") or "").lower()
            or termino in (h.get("tipo_movimiento") or "").lower()
        ]

    @rx.var
    def tiene_historial(self) -> bool:
        return len(self.historial) > 0

    @rx.var
    def total_filtrado(self) -> int:
        return len(self.historial_filtrado)

    @rx.var
    def opciones_estatus(self) -> List[dict]:
        return [
            {"value": FILTRO_TODOS, "label": "Todos"},
            {"value": "ACTIVO", "label": "Activo"},
            {"value": "INACTIVO", "label": "Inactivo"},
            {"value": "SUSPENDIDO", "label": "Suspendido"},
        ]

    @rx.var
    def opciones_tipo_movimiento(self) -> List[dict]:
        return [
            {"value": m.value, "label": m.descripcion}
            for m in TipoMovimiento
        ]

    # ========================
    # CARGA DE DATOS
    # ========================
    async def on_mount(self):
        """Se ejecuta al montar la página"""
        await self.cargar_historial()

    async def cargar_historial(self):
        """Carga el historial con filtros"""
        self.loading = True
        try:
            # Preparar filtros
            empleado_id = int(self.filtro_empleado_id) if self.filtro_empleado_id else None
            estatus = self.filtro_estatus if self.filtro_estatus != FILTRO_TODOS else None

            # Obtener historial
            registros = await historial_laboral_service.obtener_todos(
                empleado_id=empleado_id,
                estatus=estatus,
                limite=100,
                offset=0
            )

            # Convertir a dict
            self.historial = [r.model_dump() if hasattr(r, 'model_dump') else r for r in registros]
            self.total_registros = len(self.historial)

        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando historial: {e}", "error")
            self.historial = []
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.historial = []
        finally:
            self.loading = False

    async def aplicar_filtros(self):
        """Aplica filtros y recarga"""
        await self.cargar_historial()

    async def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.filtro_busqueda = ""
        self.filtro_estatus = FILTRO_TODOS
        self.filtro_empleado_id = ""
        await self.cargar_historial()

    # ========================
    # MODAL DETALLE
    # ========================
    def abrir_modal_detalle(self, registro: dict):
        """Abre modal de detalle"""
        self.registro_seleccionado = registro
        self.mostrar_modal_detalle = True

    def cerrar_modal_detalle(self):
        """Cierra modal de detalle"""
        self.mostrar_modal_detalle = False
        self.registro_seleccionado = None
