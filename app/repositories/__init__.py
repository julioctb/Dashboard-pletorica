"""
Repositorios de acceso a datos.

Este módulo exporta todos los repositorios para facilitar imports:
    from app.repositories import SupabaseEmpresaRepository, etc.
"""

# Empresa
from app.repositories.empresa_repository import (
    IEmpresaRepository,
    SupabaseEmpresaRepository,
)

# Tipo de Servicio
from app.repositories.tipo_servicio_repository import (
    ITipoServicioRepository,
    SupabaseTipoServicioRepository,
)

# Categoría de Puesto
from app.repositories.categoria_puesto_repository import (
    ICategoriaPuestoRepository,
    SupabaseCategoriaPuestoRepository,
)

# Contrato
from app.repositories.contrato_repository import (
    IContratoRepository,
    SupabaseContratoRepository,
)

# Pago
from app.repositories.pago_repository import (
    IPagoRepository,
    SupabasePagoRepository,
)

# ContratoCategoria
from app.repositories.contrato_categoria_repository import (
    IContratoCategoriaRepository,
    SupabaseContratoCategoriaRepository,
)

# Plaza
from app.repositories.plaza_repository import (
    IPlazaRepository,
    SupabasePlazaRepository,
)


__all__ = [
    # Empresa
    "IEmpresaRepository",
    "SupabaseEmpresaRepository",
    # Tipo de Servicio
    "ITipoServicioRepository",
    "SupabaseTipoServicioRepository",
    # Categoría de Puesto
    "ICategoriaPuestoRepository",
    "SupabaseCategoriaPuestoRepository",
    # Contrato
    "IContratoRepository",
    "SupabaseContratoRepository",
    # Pago
    "IPagoRepository",
    "SupabasePagoRepository",
    # ContratoCategoria
    "IContratoCategoriaRepository",
    "SupabaseContratoCategoriaRepository",
    # Plaza
    "IPlazaRepository",
    "SupabasePlazaRepository",
]