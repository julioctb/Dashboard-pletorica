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
    # Enums de Contrato
    TipoContrato,
    ModalidadAdjudicacion,
    TipoDuracion,
    EstatusContrato,
    # Enums de Plaza
    EstatusPlaza,
    # Enums de Empleado
    EstatusEmpleado,
    GeneroEmpleado,
    MotivoBaja,
    # Enums de Historial Laboral
    EstatusHistorial,
    TipoMovimiento,
    MotivoFinHistorial,  # Alias deprecated
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

# Categoría de Puesto
from app.entities.categoria_puesto import (
    CategoriaPuesto,
    CategoriaPuestoCreate,
    CategoriaPuestoUpdate,
)

# Contrato
from app.entities.contrato import (
    Contrato,
    ContratoCreate,
    ContratoUpdate,
    ContratoResumen,
)

# Pago
from app.entities.pago import (
    Pago,
    PagoCreate,
    PagoUpdate,
    PagoResumen,
    ResumenPagosContrato,
)

# ContratoCategoria
from app.entities.contrato_categoria import (
    ContratoCategoria,
    ContratoCategoriaCreate,
    ContratoCategoriaUpdate,
    ContratoCategoriaResumen,
    ResumenPersonalContrato,
)

# Plaza
from app.entities.plaza import (
    Plaza,
    PlazaCreate,
    PlazaUpdate,
    PlazaResumen,
    ResumenPlazasContrato,
    ResumenPlazasCategoria,
)

# Empleado
from app.entities.empleado import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
)

# Historial Laboral
from app.entities.historial_laboral import (
    HistorialLaboral,
    HistorialLaboralInterno,
    HistorialLaboralResumen,
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
    "TipoContrato",
    "ModalidadAdjudicacion",
    "TipoDuracion",
    "EstatusContrato",
    "EstatusPlaza",
    "EstatusEmpleado",
    "GeneroEmpleado",
    "MotivoBaja",
    "EstatusHistorial",
    "TipoMovimiento",
    "MotivoFinHistorial",
    # Empresa
    "Empresa",
    "EmpresaCreate",
    "EmpresaUpdate",
    "EmpresaResumen",
    # Tipo de Servicio
    "TipoServicio",
    "TipoServicioCreate",
    "TipoServicioUpdate",
    # Categoría de Puesto
    "CategoriaPuesto",
    "CategoriaPuestoCreate",
    "CategoriaPuestoUpdate",
    # Contrato
    "Contrato",
    "ContratoCreate",
    "ContratoUpdate",
    "ContratoResumen",
    # Pago
    "Pago",
    "PagoCreate",
    "PagoUpdate",
    "PagoResumen",
    "ResumenPagosContrato",
    # ContratoCategoria
    "ContratoCategoria",
    "ContratoCategoriaCreate",
    "ContratoCategoriaUpdate",
    "ContratoCategoriaResumen",
    "ResumenPersonalContrato",
    # Plaza
    "Plaza",
    "PlazaCreate",
    "PlazaUpdate",
    "PlazaResumen",
    "ResumenPlazasContrato",
    "ResumenPlazasCategoria",
    # Empleado
    "Empleado",
    "EmpleadoCreate",
    "EmpleadoUpdate",
    "EmpleadoResumen",
    # Historial Laboral
    "HistorialLaboral",
    "HistorialLaboralInterno",
    "HistorialLaboralResumen",
    # Costo Patronal
    "ConfiguracionEmpresa",
    "Trabajador",
    "ResultadoCuotas",
]