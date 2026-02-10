"""
Estado de Reflex para el Dashboard Administrativo.

Maneja la carga y refresco de métricas KPI.
Delega toda la lógica de agregación al DashboardService (fachada).

Solo para administradores BUAP — no filtra por empresa.
"""

import logging
import reflex as rx

from app.presentation.components.shared.base_state import BaseState
from app.services.dashboard_service import dashboard_service

logger = logging.getLogger(__name__)


class DashboardState(BaseState):
    """Estado del dashboard administrativo."""

    # ========================
    # ESTADO DE DATOS
    # ========================

    # Métricas KPI serializadas como dict (Reflex 0.8.21 serializa a JSON)
    metricas: dict = {
        "empresas_activas": 0,
        "empleados_activos": 0,
        "contratos_activos": 0,
        "plazas_ocupadas": 0,
        "plazas_vacantes": 0,
        "requisiciones_pendientes": 0,
        "contratos_por_vencer": 0,
    }

    metricas_cargadas: bool = False

    # ========================
    # COMPUTED VARS
    # ========================

    @rx.var
    def total_plazas(self) -> int:
        """Total de plazas (ocupadas + vacantes)."""
        return (
            self.metricas.get("plazas_ocupadas", 0)
            + self.metricas.get("plazas_vacantes", 0)
        )

    @rx.var
    def tiene_alertas(self) -> bool:
        """Indica si hay contratos por vencer o requisiciones pendientes."""
        return (
            self.metricas.get("contratos_por_vencer", 0) > 0
            or self.metricas.get("requisiciones_pendientes", 0) > 0
        )

    # ========================
    # CARGA DE DATOS
    # ========================

    async def _fetch_metricas(self):
        """Carga las métricas desde el servicio (sin manejo de loading)."""
        try:
            resultado = await dashboard_service.obtener_metricas()
            self.metricas = resultado.model_dump()
            self.metricas_cargadas = True
        except Exception as e:
            logger.error(f"Error cargando métricas del dashboard: {e}")
            self.manejar_error(e, "cargar métricas")

    async def cargar_metricas(self):
        """Carga inicial de métricas (on_mount)."""
        async for _ in self._montar_pagina(self._fetch_metricas):
            yield

    async def refrescar(self):
        """Refresca las métricas (botón manual)."""
        async for _ in self._recargar_datos(self._fetch_metricas):
            yield
        yield rx.toast.success("Métricas actualizadas", duration=2000)
