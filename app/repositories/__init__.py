"""
Repositorios de acceso a datos.

Todos los modulos usan el patron Repository para separar
la logica de acceso a datos de la logica de negocio.
"""

# Empresa
from app.repositories.empresa_repository import SupabaseEmpresaRepository

# Tipo de Servicio
from app.repositories.tipo_servicio_repository import SupabaseTipoServicioRepository

# Categoria de Puesto
from app.repositories.categoria_puesto_repository import SupabaseCategoriaPuestoRepository

# Contrato
from app.repositories.contrato_repository import SupabaseContratoRepository

# Contrato-Categoria
from app.repositories.contrato_categoria_repository import SupabaseContratoCategoriaRepository

# Plaza
from app.repositories.plaza_repository import SupabasePlazaRepository

# Empleado
from app.repositories.empleado_repository import SupabaseEmpleadoRepository

# Requisicion
from app.repositories.requisicion_repository import SupabaseRequisicionRepository

# Pago
from app.repositories.pago_repository import SupabasePagoRepository

# Historial Laboral
from app.repositories.historial_laboral_repository import SupabaseHistorialLaboralRepository

# Archivo
from app.repositories.archivo_repository import SupabaseArchivoRepository

# Entregable
from app.repositories.entregable_repository import SupabaseEntregableRepository


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
]
