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

import asyncio
import logging

from app.entities.dashboard import DashboardMetricas

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

        async def _seguro(coro, default, label: str):
            try:
                return await coro
            except Exception as e:
                logger.error("Dashboard: Error %s: %s", label, e)
                return default

        empresas, empleados_activos, contratos, por_vencer, req_borrador, req_revision = await asyncio.gather(
            _seguro(
                empresa_service.obtener_todas(incluir_inactivas=False, limite=500),
                [],
                "obteniendo empresas",
            ),
            _seguro(
                empleado_service.contar(estatus="ACTIVO"),
                0,
                "contando empleados",
            ),
            _seguro(
                contrato_service.obtener_todos(incluir_inactivos=False, limite=500),
                [],
                "obteniendo contratos",
            ),
            _seguro(
                contrato_service.obtener_por_vencer(dias=30),
                [],
                "obteniendo contratos por vencer",
            ),
            _seguro(
                requisicion_service.buscar_con_filtros(estado="BORRADOR", limite=500),
                [],
                "contando requisiciones BORRADOR",
            ),
            _seguro(
                requisicion_service.buscar_con_filtros(estado="EN_REVISION", limite=500),
                [],
                "contando requisiciones EN_REVISION",
            ),
        )

        empresas_activas = len(empresas)
        contratos_activos = len(contratos)
        contratos_por_vencer = len(por_vencer)
        requisiciones_pendientes = len(req_borrador) + len(req_revision)

        plazas_ocupadas = 0
        plazas_vacantes = 0

        # --- Plazas (ocupadas y vacantes) ---
        # Ejecutar cálculos por contrato en paralelo para reducir latencia.
        if contratos:
            resultados_plazas = await asyncio.gather(
                *(
                    plaza_service.calcular_totales_contrato(contrato.id)
                    for contrato in contratos
                ),
                return_exceptions=True,
            )
            for resultado in resultados_plazas:
                if isinstance(resultado, Exception):
                    logger.debug("Dashboard: Error puntual calculando plazas: %s", resultado)
                    continue
                plazas_ocupadas += resultado.plazas_ocupadas
                plazas_vacantes += resultado.plazas_vacantes

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
