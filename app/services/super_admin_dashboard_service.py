"""
Servicio agregador para el Dashboard de Super Admin.

Orquesta consultas a múltiples servicios existentes y retorna métricas
agregadas con tolerancia a fallos parciales.
"""

import asyncio
import logging

from app.entities.super_admin_dashboard import SuperAdminDashboard

logger = logging.getLogger(__name__)


class SuperAdminDashboardService:
    """Servicio fachada para construir métricas del panel de super admin."""

    async def obtener_metricas_super_admin(self) -> tuple[SuperAdminDashboard, list[str]]:
        """
        Obtiene métricas del panel de super admin.

        Returns:
            tuple[SuperAdminDashboard, list[str]]:
                - DTO con métricas (parciales si alguna fuente falla)
                - Lista de advertencias por fallos parciales
        """
        # Imports diferidos para evitar circularidad
        from app.services.dashboard_service import dashboard_service
        from app.services.institucion_service import institucion_service
        from app.services.onboarding_service import onboarding_service
        from app.services.user_service import user_service

        advertencias: list[str] = []
        metricas = SuperAdminDashboard()

        async def _seguro(origen: str, coro):
            try:
                return await coro
            except Exception as e:
                logger.warning("SuperAdminDashboard: error en %s: %s", origen, e)
                advertencias.append(
                    f"No se pudo cargar {origen}. Se muestran datos parciales."
                )
                return None

        usuarios, instituciones, conteos_pipeline, metricas_operativas = await asyncio.gather(
            _seguro(
                "usuarios",
                user_service.listar_usuarios(incluir_inactivos=True, limite=5000),
            ),
            _seguro(
                "instituciones",
                institucion_service.obtener_todas(solo_activas=False),
            ),
            _seguro(
                "onboarding",
                onboarding_service.obtener_conteos_pipeline(),
            ),
            _seguro(
                "métricas operativas",
                dashboard_service.obtener_metricas(),
            ),
        )

        if usuarios is not None:
            metricas.usuarios_activos = sum(
                1 for usuario in usuarios if bool(getattr(usuario, "activo", False))
            )
            metricas.usuarios_inactivos = sum(
                1 for usuario in usuarios if not bool(getattr(usuario, "activo", False))
            )
            metricas.super_admins = sum(
                1
                for usuario in usuarios
                if bool(getattr(usuario, "activo", False))
                and bool(getattr(usuario, "puede_gestionar_usuarios", False))
            )
            metricas.usuarios_sin_ultimo_acceso = sum(
                1 for usuario in usuarios if getattr(usuario, "ultimo_acceso", None) is None
            )

        if instituciones is not None:
            metricas.instituciones_activas = sum(
                1 for institucion in instituciones if bool(getattr(institucion, "activo", False))
            )
            metricas.instituciones_inactivas = sum(
                1 for institucion in instituciones if not bool(getattr(institucion, "activo", False))
            )
            metricas.instituciones_sin_empresas = sum(
                1
                for institucion in instituciones
                if int(getattr(institucion, "cantidad_empresas", 0) or 0) == 0
            )

        if conteos_pipeline is not None:
            metricas.onboarding_en_revision = int(conteos_pipeline.get("EN_REVISION", 0) or 0)
            metricas.onboarding_rechazado = int(conteos_pipeline.get("RECHAZADO", 0) or 0)

        if metricas_operativas is not None:
            metricas.requisiciones_pendientes = int(
                getattr(metricas_operativas, "requisiciones_pendientes", 0) or 0
            )
            metricas.contratos_por_vencer = int(
                getattr(metricas_operativas, "contratos_por_vencer", 0) or 0
            )

        return metricas, advertencias


super_admin_dashboard_service = SuperAdminDashboardService()
