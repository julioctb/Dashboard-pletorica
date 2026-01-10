"""
Entidades de dominio del sistema.

Este módulo exporta todas las entidades de negocio para facilitar imports:
    from app.entities import Empresa, AreaServicio, etc.
"""

# Empresa
from app.entities.empresa import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
    TipoEmpresa,
    EstatusEmpresa,
)

# Área de Servicio
from app.entities.area_servicio import (
    AreaServicio,
    AreaServicioCreate,
    AreaServicioUpdate,
    EstatusAreaServicio,
)

# Costo Patronal (si existe)
try:
    from app.entities.costo_patronal import (
        ConfiguracionEmpresa,
        Trabajador,
        ResultadoCuotas,
    )
except ImportError:
    pass  # El módulo puede no existir aún


__all__ = [
    # Empresa
    "Empresa",
    "EmpresaCreate",
    "EmpresaUpdate",
    "EmpresaResumen",
    "TipoEmpresa",
    "EstatusEmpresa",
    # Área de Servicio
    "AreaServicio",
    "AreaServicioCreate",
    "AreaServicioUpdate",
    "EstatusAreaServicio",
    # Costo Patronal
    "ConfiguracionEmpresa",
    "Trabajador",
    "ResultadoCuotas",
]