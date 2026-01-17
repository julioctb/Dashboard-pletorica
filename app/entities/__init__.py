"""
Entidades de dominio del sistema.

Este módulo exporta todas las entidades de negocio para facilitar imports:
    from app.entities import Empresa, AreaServicio, etc.
"""

# Enums centralizados
from app.core.enums import (
    Estatus,
    EstatusEmpresa,
    TipoEmpresa,
)

# Empresa
from app.entities.empresa import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
)

# Tipo de Servicio
from app.entities.tipo_servicio import (
    TipoServicio,
    TipoServicioCreate,
    TipoServicioUpdate,
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
    # Enums
    "Estatus",
    "EstatusEmpresa",
    "TipoEmpresa",
    # Empresa
    "Empresa",
    "EmpresaCreate",
    "EmpresaUpdate",
    "EmpresaResumen",
    # Tipo de Servicio
    "TipoServicio",
    "TipoServicioCreate",
    "TipoServicioUpdate",
    # Costo Patronal
    "ConfiguracionEmpresa",
    "Trabajador",
    "ResultadoCuotas",
]