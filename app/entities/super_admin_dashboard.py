"""
Entidades del Dashboard de Super Admin.

DTO (Value Object) con métricas agregadas para el panel /admin.
No persiste en base de datos.
"""

from pydantic import BaseModel, Field


class SuperAdminDashboard(BaseModel):
    """Métricas agregadas para el panel de super administración."""

    usuarios_activos: int = Field(default=0)
    usuarios_inactivos: int = Field(default=0)
    super_admins: int = Field(default=0)
    usuarios_sin_ultimo_acceso: int = Field(default=0)

    instituciones_activas: int = Field(default=0)
    instituciones_inactivas: int = Field(default=0)
    instituciones_sin_empresas: int = Field(default=0)

    onboarding_en_revision: int = Field(default=0)
    onboarding_rechazado: int = Field(default=0)

    requisiciones_pendientes: int = Field(default=0)
    contratos_por_vencer: int = Field(default=0)
