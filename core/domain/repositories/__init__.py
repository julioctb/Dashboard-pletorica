"""
Repositorios de acceso a datos.

Todos los modulos usan el patron Repository para separar
la logica de acceso a datos de la logica de negocio.
"""

# Empresa
from core.domain.repositories.empresa_repository import SupabaseEmpresaRepository

# Tipo de Servicio
from core.domain.repositories.tipo_servicio_repository import SupabaseTipoServicioRepository

# Categoria de Puesto
from core.domain.repositories.categoria_puesto_repository import SupabaseCategoriaPuestoRepository

# Contrato
from core.domain.repositories.contrato_repository import SupabaseContratoRepository

# Contrato-Categoria
from core.domain.repositories.contrato_categoria_repository import SupabaseContratoCategoriaRepository

# Plaza
from core.domain.repositories.plaza_repository import SupabasePlazaRepository

# Empleado
from core.domain.repositories.empleado_repository import SupabaseEmpleadoRepository

# Requisicion
from core.domain.repositories.requisicion_repository import SupabaseRequisicionRepository

# Pago
from core.domain.repositories.pago_repository import SupabasePagoRepository

# Historial Laboral
from core.domain.repositories.historial_laboral_repository import SupabaseHistorialLaboralRepository

# Archivo
from core.domain.repositories.archivo_repository import SupabaseArchivoRepository

# Entregable
from core.domain.repositories.entregable_repository import SupabaseEntregableRepository

# Incapacidad
from core.domain.repositories.incapacidad_repository import SupabaseIncapacidadRepository


__all__ = [
    "SupabaseEmpresaRepository",
    "SupabaseTipoServicioRepository",
    "SupabaseCategoriaPuestoRepository",
    "SupabaseContratoRepository",
    "SupabaseContratoCategoriaRepository",
    "SupabasePlazaRepository",
    "SupabaseEmpleadoRepository",
    "SupabaseRequisicionRepository",
    "SupabasePagoRepository",
    "SupabaseHistorialLaboralRepository",
    "SupabaseArchivoRepository",
    "SupabaseEntregableRepository",
    "SupabaseIncapacidadRepository",
]
