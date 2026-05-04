"""
Repositorios de acceso a datos.

Todos los modulos usan el patron Repository para separar
la logica de acceso a datos de la logica de negocio.
"""

# Empresa
from app.domain.repositories.empresa_repository import SupabaseEmpresaRepository

# Tipo de Servicio
from app.domain.repositories.tipo_servicio_repository import SupabaseTipoServicioRepository

# Categoria de Puesto
from app.domain.repositories.categoria_puesto_repository import SupabaseCategoriaPuestoRepository

# Contrato
from app.domain.repositories.contrato_repository import SupabaseContratoRepository

# Contrato-Categoria
from app.domain.repositories.contrato_categoria_repository import SupabaseContratoCategoriaRepository

# Plaza
from app.domain.repositories.plaza_repository import SupabasePlazaRepository

# Empleado
from app.domain.repositories.empleado_repository import SupabaseEmpleadoRepository

# Requisicion
from app.domain.repositories.requisicion_repository import SupabaseRequisicionRepository

# Pago
from app.domain.repositories.pago_repository import SupabasePagoRepository

# Historial Laboral
from app.domain.repositories.historial_laboral_repository import SupabaseHistorialLaboralRepository

# Archivo
from app.domain.repositories.archivo_repository import SupabaseArchivoRepository

# Entregable
from app.domain.repositories.entregable_repository import SupabaseEntregableRepository

# Incapacidad
from app.domain.repositories.incapacidad_repository import SupabaseIncapacidadRepository


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
