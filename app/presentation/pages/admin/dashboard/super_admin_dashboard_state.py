"""
State para el panel de Super Admin (/admin).
"""

import logging
from typing import List, Optional

import reflex as rx

from app.entities.super_admin_dashboard import SuperAdminDashboard
from app.presentation.components.shared.auth_state import AuthState
from app.services.super_admin_dashboard_service import super_admin_dashboard_service

logger = logging.getLogger(__name__)


class SuperAdminDashboardState(AuthState):
    """Estado del panel de super admin."""

    metricas: Optional[SuperAdminDashboard] = None
    cargando: bool = False
    error: Optional[str] = None
    advertencias: List[str] = []

    @rx.var
    def metricas_dict(self) -> dict:
        """Métricas serializadas con defaults seguros para UI."""
        if self.metricas is None:
            return SuperAdminDashboard().model_dump()
        return self.metricas.model_dump()

    @rx.var
    def metricas_cargadas(self) -> bool:
        return self.metricas is not None

    @rx.var
    def usuarios_sin_ultimo_acceso(self) -> int:
        if self.metricas is None:
            return 0
        return self.metricas.usuarios_sin_ultimo_acceso

    @rx.var
    def onboarding_rechazado(self) -> int:
        if self.metricas is None:
            return 0
        return self.metricas.onboarding_rechazado

    @rx.var
    def contratos_por_vencer(self) -> int:
        if self.metricas is None:
            return 0
        return self.metricas.contratos_por_vencer

    @rx.var
    def instituciones_sin_empresas(self) -> int:
        if self.metricas is None:
            return 0
        return self.metricas.instituciones_sin_empresas

    async def _cargar_metricas_core(self):
        """Carga métricas sin manejar flags de loading (reutilizable)."""
        try:
            metricas, advertencias = await super_admin_dashboard_service.obtener_metricas_super_admin()
            self.metricas = metricas
            self.advertencias = advertencias
        except Exception as e:
            logger.error("Error cargando metricas de super admin: %s", e)
            self.metricas = self.metricas or SuperAdminDashboard()
            self.advertencias = [
                "No se pudieron cargar todas las metricas del panel. Intente actualizar."
            ]

    async def montar_pagina(self):
        """Monta la pagina: valida acceso y carga métricas (auth la maneja el layout)."""
        self.error = None
        self.advertencias = []

        # Auth ya se verifica en el wrapper global index(...). Aquí solo autorizamos.
        # Leemos el AuthState raíz para evitar desincronización entre states heredados en Reflex.
        auth = await self.get_state(AuthState)
        if not (auth.es_superadmin or auth.es_super_admin):
            self.loading = False
            self.cargando = False
            yield rx.redirect("/")
            return

        # Cargar metricas con skeleton
        async for _ in self._montar_pagina(self._cargar_metricas_core):
            yield

    async def cargar_metricas(self):
        """Carga métricas del panel con tolerancia a fallos parciales."""
        self.cargando = True
        self.loading = True
        self.error = None
        yield

        try:
            await self._cargar_metricas_core()
        finally:
            self.cargando = False
            self.loading = False
            yield

    async def refrescar(self):
        """Refresca las métricas del panel."""
        async for _ in self.cargar_metricas():
            yield
