"""
Estado del módulo de Entregables (Admin).
Nuevo flujo: Vista global de todos los entregables, filtrado por estado.
Por defecto muestra los que requieren atención (EN_REVISION).
"""

import reflex as rx
from typing import List, Optional

from app.presentation.components.shared.base_state import BaseState
from app.services import entregable_service, contrato_service
from app.core.enums import EstatusEntregable
from app.core.exceptions import NotFoundError


class EntregablesState(BaseState):
    """Estado para la gestión de entregables del admin - Vista Global."""

    # =========================================================================
    # DATOS
    # =========================================================================
    entregables: List[dict] = []
    estadisticas: dict = {}
    contratos_disponibles: List[dict] = []

    # =========================================================================
    # UI / FILTROS
    # =========================================================================
    cargando: bool = False
    filtro_estatus: str = "EN_REVISION"  # Default: mostrar los que requieren atención
    filtro_contrato_id: str = "all"  # Filtro opcional por contrato ("all" = todos)
    filtro_busqueda: str = ""

    # =========================================================================
    # SETTERS
    # =========================================================================
    def set_filtro_busqueda(self, value: str):
        self.filtro_busqueda = value

    # =========================================================================
    # COMPUTED VARS
    # =========================================================================
    @rx.var
    def tiene_entregables(self) -> bool:
        return len(self.entregables) > 0

    @rx.var
    def entregables_filtrados(self) -> List[dict]:
        """Filtra por búsqueda de texto (período, contrato, empresa)."""
        resultado = self.entregables
        if self.filtro_busqueda:
            termino = self.filtro_busqueda.lower()
            resultado = [
                e for e in resultado
                if termino in str(e.get("numero_periodo", "")).lower()
                or termino in (e.get("periodo_texto", "") or "").lower()
                or termino in (e.get("contrato_codigo", "") or "").lower()
                or termino in (e.get("empresa_nombre", "") or "").lower()
            ]
        return resultado

    @rx.var
    def total_mostrados(self) -> int:
        """Cantidad de entregables mostrados después del filtro de búsqueda."""
        return len(self.entregables_filtrados)

    @rx.var
    def opciones_estatus(self) -> List[dict]:
        return [
            {"value": "all", "label": "Todos los estados"},
            {"value": "EN_REVISION", "label": "En revisión"},
            {"value": "PENDIENTE", "label": "Pendientes"},
            {"value": "APROBADO", "label": "Aprobados"},
            {"value": "RECHAZADO", "label": "Rechazados"},
            {"value": "PREFACTURA_ENVIADA", "label": "Prefactura enviada"},
            {"value": "PREFACTURA_APROBADA", "label": "Prefactura aprobada"},
            {"value": "FACTURADO", "label": "Facturado"},
            {"value": "PAGADO", "label": "Pagado"},
        ]

    @rx.var
    def opciones_contratos(self) -> List[dict]:
        return [{"value": "all", "label": "Todos los contratos"}] + self.contratos_disponibles

    @rx.var
    def stats_total(self) -> int:
        return self.estadisticas.get("total", 0)

    @rx.var
    def stats_pendientes(self) -> int:
        return self.estadisticas.get("pendientes", 0)

    @rx.var
    def stats_en_revision(self) -> int:
        return self.estadisticas.get("en_revision", 0)

    @rx.var
    def stats_aprobados(self) -> int:
        return self.estadisticas.get("aprobados", 0)

    @rx.var
    def stats_rechazados(self) -> int:
        return self.estadisticas.get("rechazados", 0)

    @rx.var
    def stats_prefactura_enviada(self) -> int:
        return self.estadisticas.get("prefactura_enviada", 0)

    @rx.var
    def stats_facturados(self) -> int:
        return self.estadisticas.get("facturados", 0)

    @rx.var
    def stats_pagados(self) -> int:
        return self.estadisticas.get("pagados", 0)

    @rx.var
    def filtro_activo_es_todos(self) -> bool:
        return self.filtro_estatus == "all"

    @rx.var
    def filtro_activo_es_en_revision(self) -> bool:
        return self.filtro_estatus == "EN_REVISION"

    @rx.var
    def filtro_activo_es_pendiente(self) -> bool:
        return self.filtro_estatus == "PENDIENTE"

    @rx.var
    def filtro_activo_es_aprobado(self) -> bool:
        return self.filtro_estatus == "APROBADO"

    @rx.var
    def filtro_activo_es_rechazado(self) -> bool:
        return self.filtro_estatus == "RECHAZADO"

    @rx.var
    def filtro_activo_es_prefactura(self) -> bool:
        return self.filtro_estatus == "PREFACTURA_ENVIADA"

    @rx.var
    def filtro_activo_es_facturado(self) -> bool:
        return self.filtro_estatus == "FACTURADO"

    @rx.var
    def filtro_activo_es_pagado(self) -> bool:
        return self.filtro_estatus == "PAGADO"

    @rx.var
    def titulo_filtro_actual(self) -> str:
        """Título descriptivo del filtro actual."""
        titulos = {
            "all": "Todos los Entregables",
            "EN_REVISION": "Entregables en Revisión",
            "PENDIENTE": "Entregables Pendientes",
            "APROBADO": "Entregables Aprobados",
            "RECHAZADO": "Entregables Rechazados",
            "PREFACTURA_ENVIADA": "Prefacturas por Revisar",
            "PREFACTURA_APROBADA": "Prefacturas Aprobadas",
            "FACTURADO": "Entregables Facturados",
            "PAGADO": "Entregables Pagados",
        }
        return titulos.get(self.filtro_estatus, "Entregables")

    # =========================================================================
    # CARGA DE DATOS
    # =========================================================================
    async def on_load_entregables(self):
        """Carga inicial: contratos para filtro y entregables con filtro default."""
        async for _ in self._montar_pagina(
            self._cargar_contratos_disponibles,
            self._cargar_estadisticas,
            self._fetch_entregables,
        ):
            yield

    async def _cargar_contratos_disponibles(self):
        """Carga lista de contratos para el filtro."""
        try:
            contratos = await contrato_service.obtener_vigentes()
            self.contratos_disponibles = [
                {"value": str(c.id), "label": f"{c.codigo} - {getattr(c, 'empresa_nombre', '') or 'Sin empresa'}"}
                for c in contratos
            ]
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar contratos: {str(e)}", "error")

    async def _cargar_estadisticas(self):
        """Carga estadísticas globales para las cards."""
        try:
            self.estadisticas = await entregable_service.obtener_estadisticas_global()
        except Exception:
            self.estadisticas = {
                "total": 0,
                "pendientes": 0,
                "en_revision": 0,
                "aprobados": 0,
                "rechazados": 0,
                "prefactura_enviada": 0,
                "por_facturar": 0,
                "facturados": 0,
                "pagados": 0,
            }

    async def _fetch_entregables(self):
        """Carga entregables desde BD (sin manejo de loading)."""
        try:
            estatus = None if self.filtro_estatus == "all" else self.filtro_estatus
            contrato_id = None if self.filtro_contrato_id == "all" else int(self.filtro_contrato_id)

            entregables = await entregable_service.obtener_global(
                estatus=estatus,
                contrato_id=contrato_id,
                limite=100,
            )

            self.entregables = [
                {
                    "id": e.id,
                    "contrato_id": e.contrato_id,
                    "contrato_codigo": e.contrato_codigo,
                    "empresa_nombre": e.empresa_nombre,
                    "numero_periodo": e.numero_periodo,
                    "periodo_inicio": str(e.periodo_inicio),
                    "periodo_fin": str(e.periodo_fin),
                    "periodo_texto": e.periodo_texto,
                    "estatus": e.estatus.value if hasattr(e.estatus, 'value') else e.estatus,
                    "fecha_entrega": str(e.fecha_entrega) if e.fecha_entrega else None,
                    "monto_aprobado": str(e.monto_aprobado) if e.monto_aprobado else None,
                    "puede_revisar": (e.estatus == EstatusEntregable.EN_REVISION or e.estatus == "EN_REVISION"),
                    "requiere_accion": (
                        e.estatus in [EstatusEntregable.EN_REVISION, "EN_REVISION",
                                      EstatusEntregable.PREFACTURA_ENVIADA, "PREFACTURA_ENVIADA",
                                      EstatusEntregable.FACTURADO, "FACTURADO"]
                    ),
                }
                for e in entregables
            ]
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar entregables: {str(e)}", "error")

    async def _cargar_entregables(self):
        """Carga entregables con indicador de carga para la lista."""
        self.cargando = True
        try:
            await self._fetch_entregables()
        finally:
            self.cargando = False

    # =========================================================================
    # FILTROS (CLICK EN STAT CARDS)
    # =========================================================================
    async def filtrar_por_estatus(self, estatus: str):
        """Filtra por estatus al hacer click en una stat card."""
        self.filtro_estatus = estatus
        await self._cargar_entregables()

    async def filtrar_todos(self):
        """Muestra todos los entregables."""
        await self.filtrar_por_estatus("all")

    async def filtrar_en_revision(self):
        """Filtra solo en revisión."""
        await self.filtrar_por_estatus("EN_REVISION")

    async def filtrar_pendientes(self):
        """Filtra solo pendientes."""
        await self.filtrar_por_estatus("PENDIENTE")

    async def filtrar_aprobados(self):
        """Filtra solo aprobados."""
        await self.filtrar_por_estatus("APROBADO")

    async def filtrar_rechazados(self):
        """Filtra solo rechazados."""
        await self.filtrar_por_estatus("RECHAZADO")

    async def filtrar_prefacturas(self):
        """Filtra prefacturas pendientes de revisión."""
        await self.filtrar_por_estatus("PREFACTURA_ENVIADA")

    async def filtrar_facturados(self):
        """Filtra entregables facturados."""
        await self.filtrar_por_estatus("FACTURADO")

    async def filtrar_pagados(self):
        """Filtra entregables pagados."""
        await self.filtrar_por_estatus("PAGADO")

    async def set_filtro_contrato(self, contrato_id: str):
        """Cambia el filtro de contrato y recarga."""
        self.filtro_contrato_id = contrato_id if contrato_id else "all"
        await self._cargar_entregables()

    # =========================================================================
    # NAVEGACIÓN
    # =========================================================================
    def ir_a_detalle(self, entregable_id: int):
        """Navega al detalle del entregable."""
        return rx.redirect(f"/entregables/{entregable_id}")
