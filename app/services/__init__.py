"""
Servicios de aplicación (lógica de negocio).

Este módulo exporta todos los servicios para facilitar imports:
    from app.services import empresa_service, area_servicio_service
"""

# Empresa
from app.services.empresa_service import (
    EmpresaService,
    empresa_service,
)

# Tipo de Servicio
from app.services.tipo_servicio_service import (
    TipoServicioService,
    tipo_servicio_service,
)

# Categoría de Puesto
from app.services.categoria_puesto_service import (
    CategoriaPuestoService,
    categoria_puesto_service,
)

# Contrato
from app.services.contrato_service import (
    ContratoService,
    contrato_service,
)

# Pago
from app.services.pago_service import (
    PagoService,
    pago_service,
)

# ContratoCategoria
from app.services.contrato_categoria_service import (
    ContratoCategoriaService,
    contrato_categoria_service,
)

# Plaza
from app.services.plaza_service import (
    PlazaService,
    plaza_service,
)


__all__ = [
    # Empresa
    "EmpresaService",
    "empresa_service",
    # Tipo de Servicio
    "TipoServicioService",
    "tipo_servicio_service",
    # Categoría de Puesto
    "CategoriaPuestoService",
    "categoria_puesto_service",
    # Contrato
    "ContratoService",
    "contrato_service",
    # Pago
    "PagoService",
    "pago_service",
    # ContratoCategoria
    "ContratoCategoriaService",
    "contrato_categoria_service",
    # Plaza
    "PlazaService",
    "plaza_service",
]