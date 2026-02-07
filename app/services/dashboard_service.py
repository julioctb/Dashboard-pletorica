"""
Servicio del Dashboard Administrativo.

Fachada (Facade Pattern) que orquesta llamadas a servicios existentes
para agregar métricas del sistema en una sola invocación.

Patrón B (sin repository): No tiene tabla propia en BD.
Solo consume servicios existentes y retorna DTOs agregados.

Uso:
    from app.services import dashboard_service
    
    metricas = await dashboard_service.obtener_metricas()
"""

import logging
from typing import Optional

from app.entities.dashboard import DashboardMetricas
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Servicio fachada para el dashboard administrativo.

    Agrega métricas de múltiples servicios sin duplicar lógica de negocio.
    Cada método delega a los servicios especializados existentes.
    """

    async def obtener_metricas(self) -> DashboardMetricas:
        """
        Obtiene todas las métricas KPI del dashboard en una sola llamada.

        Orquesta llamadas a:
        - empresa_service.obtener_todas()
        - empleado_service.contar()
        - contrato_service.obtener_todos() / obtener_por_vencer()
        - plaza_service.calcular_totales_contrato()
        - requisicion_service.buscar_con_filtros()

        Returns:
            DashboardMetricas con todos los indicadores poblados.

        Raises:
            DatabaseError: Si algún servicio subyacente falla.
        """
        # Imports lazy para evitar circularidad en el singleton
        from app.services import (
            empresa_service,
            empleado_service,
            contrato_service,
            plaza_service,
            requisicion_service,
        )

        # Recolectar métricas con tolerancia a fallos parciales.
        # Si un servicio falla, se loguea y se deja en 0.
        empresas_activas = 0
        empleados_activos = 0
        contratos_activos = 0
        plazas_ocupadas = 0
        plazas_vacantes = 0
        requisiciones_pendientes = 0
        contratos_por_vencer = 0

        # --- Empresas activas ---
        try:
            empresas = await empresa_service.obtener_todas(
                incluir_inactivas=False, limite=500
            )
            empresas_activas = len(empresas)
        except Exception as e:
            logger.error(f"Dashboard: Error obteniendo empresas: {e}")

        # --- Empleados activos ---
        try:
            empleados_activos = await empleado_service.contar(estatus="ACTIVO")
        except Exception as e:
            logger.error(f"Dashboard: Error contando empleados: {e}")

        # --- Contratos activos ---
        try:
            contratos = await contrato_service.obtener_todos(
                incluir_inactivos=False, limite=500
            )
            contratos_activos = len(contratos)
        except Exception as e:
            logger.error(f"Dashboard: Error obteniendo contratos: {e}")

        # --- Plazas (ocupadas y vacantes) ---
        # Iteramos contratos activos para calcular totales.
        # Mismo patrón que usa PortalState pero centralizado aquí.
        try:
            if contratos_activos == 0:
                # Re-obtener contratos si el bloque anterior falló
                contratos = await contrato_service.obtener_todos(
                    incluir_inactivos=False, limite=500
                )

            for contrato in contratos:
                try:
                    resumen = await plaza_service.calcular_totales_contrato(
                        contrato.id
                    )
                    plazas_ocupadas += resumen.plazas_ocupadas
                    plazas_vacantes += resumen.plazas_vacantes
                except Exception:
                    # Contrato sin plazas o error puntual, continuar
                    pass
        except Exception as e:
            logger.error(f"Dashboard: Error calculando plazas: {e}")

        # --- Contratos por vencer (próximos 30 días) ---
        try:
            por_vencer = await contrato_service.obtener_por_vencer(dias=30)
            contratos_por_vencer = len(por_vencer)
        except Exception as e:
            logger.error(f"Dashboard: Error obteniendo contratos por vencer: {e}")

        # --- Requisiciones pendientes (BORRADOR + EN_REVISION) ---
        try:
            req_borrador = await requisicion_service.buscar_con_filtros(
                estado="BORRADOR", limite=500
            )
            req_revision = await requisicion_service.buscar_con_filtros(
                estado="EN_REVISION", limite=500
            )
            requisiciones_pendientes = len(req_borrador) + len(req_revision)
        except Exception as e:
            logger.error(f"Dashboard: Error contando requisiciones: {e}")

        return DashboardMetricas(
            empresas_activas=empresas_activas,
            empleados_activos=empleados_activos,
            contratos_activos=contratos_activos,
            plazas_ocupadas=plazas_ocupadas,
            plazas_vacantes=plazas_vacantes,
            requisiciones_pendientes=requisiciones_pendientes,
            contratos_por_vencer=contratos_por_vencer,
        )


# Singleton
dashboard_service = DashboardService()
