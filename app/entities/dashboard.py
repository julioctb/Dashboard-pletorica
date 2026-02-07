"""
Entidades del Dashboard Administrativo.

DTOs (Data Transfer Objects) para transportar métricas agregadas
desde el DashboardService hacia el DashboardState.

No persisten en base de datos — son Value Objects de lectura.

Uso:
    from app.entities import DashboardMetricas
    
    metricas = DashboardMetricas(
        empresas_activas=5,
        empleados_activos=389,
        ...
    )
"""

from pydantic import BaseModel, Field


class DashboardMetricas(BaseModel):
    """
    Métricas KPI agregadas del sistema.

    Cada campo representa un indicador clave que se muestra
    como metric_card en el dashboard administrativo.
    """

    # Métricas principales
    empresas_activas: int = Field(default=0, description="Empresas con estatus ACTIVO")
    empleados_activos: int = Field(default=0, description="Empleados con estatus ACTIVO")
    contratos_activos: int = Field(default=0, description="Contratos con estatus ACTIVO")
    plazas_ocupadas: int = Field(default=0, description="Plazas con estatus OCUPADA")
    plazas_vacantes: int = Field(default=0, description="Plazas con estatus VACANTE")

    # Alertas (conteos)
    requisiciones_pendientes: int = Field(
        default=0,
        description="Requisiciones en estado BORRADOR o EN_REVISION",
    )
    contratos_por_vencer: int = Field(
        default=0,
        description="Contratos activos que vencen en los próximos 30 días",
    )
