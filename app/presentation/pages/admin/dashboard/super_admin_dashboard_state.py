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
    def instituciones_sin_empresas(self) -> int:
        if self.metricas is None:
            return 0
        return self.metricas.instituciones_sin_empresas

    async def verificar_y_redirigir(self):
        """
        Verifica sesión y acceso de super admin.
        """
        await self.verificar_sesion()

        if self.requiere_login and not self.esta_autenticado:
            return rx.redirect("/login")

        if not self.es_super_admin:
            return rx.redirect("/")

        return None

    async def montar_pagina(self):
        """Monta la página: verifica acceso y carga métricas."""
        self.error = None
        self.advertencias = []

        try:
            resultado = await self.verificar_y_redirigir()
            if resultado:
                self.cargando = False
                self.loading = False
                yield resultado
                return
        except Exception as e:
            logger.error("Error verificando acceso de super admin: %s", e)
            self.error = "No se pudo verificar la sesión o los permisos."
            self.cargando = False
            self.loading = False
            yield
            return

        async for _ in self.cargar_metricas():
            yield

    async def cargar_metricas(self):
        """Carga métricas del panel con tolerancia a fallos parciales."""
        self.cargando = True
        self.loading = True
        self.error = None
        yield

        try:
            metricas, advertencias = await super_admin_dashboard_service.obtener_metricas_super_admin()
            self.metricas = metricas
            self.advertencias = advertencias
        except Exception as e:
            logger.error("Error cargando métricas de super admin: %s", e)
            self.metricas = self.metricas or SuperAdminDashboard()
            self.advertencias = [
                "No se pudieron cargar todas las métricas del panel. Intente actualizar."
            ]
        finally:
            self.cargando = False
            self.loading = False
            yield

    async def refrescar(self):
        """Refresca las métricas del panel."""
        async for _ in self.cargar_metricas():
            yield
