"""
State para la pagina Admin Onboarding.

Vista pipeline de onboarding de empleados para admins internos BUAP.
Muestra empleados de TODAS las empresas con conteos por estatus.
"""
import reflex as rx
from typing import List

from app.presentation.components.shared.auth_state import AuthState
from app.services.onboarding_service import onboarding_service
from app.core.exceptions import DatabaseError


class AdminOnboardingState(AuthState):
    """State del pipeline de onboarding para admin BUAP."""

    # ========================
    # DATOS
    # ========================
    empleados_pipeline: List[dict] = []
    conteos_pipeline: dict = {}
    filtro_estatus_onboarding: str = ""
    total_pipeline: int = 0

    # ========================
    # SETTERS
    # ========================
    def set_filtro_estatus_onboarding(self, value: str):
        self.filtro_estatus_onboarding = value

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def empleados_filtrados(self) -> List[dict]:
        """Filtra empleados por estatus seleccionado."""
        if not self.filtro_estatus_onboarding:
            return self.empleados_pipeline
        return [
            e for e in self.empleados_pipeline
            if e.get("estatus_onboarding") == self.filtro_estatus_onboarding
        ]

    @rx.var
    def total_filtrados(self) -> int:
        if not self.filtro_estatus_onboarding:
            return self.total_pipeline
        return len(self.empleados_filtrados)

    @rx.var
    def conteo_datos_pendientes(self) -> int:
        return self.conteos_pipeline.get("DATOS_PENDIENTES", 0)

    @rx.var
    def conteo_docs_pendientes(self) -> int:
        return self.conteos_pipeline.get("DOCUMENTOS_PENDIENTES", 0)

    @rx.var
    def conteo_en_revision(self) -> int:
        return self.conteos_pipeline.get("EN_REVISION", 0)

    @rx.var
    def conteo_aprobado(self) -> int:
        return self.conteos_pipeline.get("APROBADO", 0)

    @rx.var
    def conteo_rechazado(self) -> int:
        return self.conteos_pipeline.get("RECHAZADO", 0)

    @rx.var
    def opciones_estatus_pipeline(self) -> List[dict]:
        return [
            {"value": "", "label": "Todos"},
            {"value": "DATOS_PENDIENTES", "label": "Datos Pendientes"},
            {"value": "DOCUMENTOS_PENDIENTES", "label": "Docs Pendientes"},
            {"value": "EN_REVISION", "label": "En Revision"},
            {"value": "APROBADO", "label": "Aprobado"},
            {"value": "RECHAZADO", "label": "Rechazado"},
            {"value": "ACTIVO_COMPLETO", "label": "Activo Completo"},
        ]

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_admin_onboarding(self):
        async for _ in self._montar_pagina(self._fetch_pipeline):
            yield

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_pipeline(self):
        """Carga empleados y conteos del pipeline."""
        try:
            empleados = await onboarding_service.obtener_empleados_onboarding_global()
            self.empleados_pipeline = empleados
            self.total_pipeline = len(empleados)

            conteos = await onboarding_service.obtener_conteos_pipeline()
            self.conteos_pipeline = conteos
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando pipeline: {e}", "error")
            self.empleados_pipeline = []
            self.total_pipeline = 0
            self.conteos_pipeline = {}
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.empleados_pipeline = []
            self.total_pipeline = 0
            self.conteos_pipeline = {}

    async def recargar_pipeline(self):
        """Recarga con skeleton."""
        async for _ in self._recargar_datos(self._fetch_pipeline):
            yield

    def filtrar_por_estatus(self, estatus: str):
        """Filtra la tabla por estatus clickeado en pipeline card."""
        if self.filtro_estatus_onboarding == estatus:
            self.filtro_estatus_onboarding = ""
        else:
            self.filtro_estatus_onboarding = estatus
