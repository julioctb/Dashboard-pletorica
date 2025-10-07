"""
Servicio de aplicación para gestión de empresas.
Consolidado y simplificado desde app/services/empresa_service.py
"""
import logging
from typing import List, Optional

from app.entities import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
    TipoEmpresa,
    EstatusEmpresa,
)
from app.repositories import SupabaseEmpresaRepository

logger = logging.getLogger(__name__)


class EmpresaService:
    """
    Servicio de aplicación para empresas.
    Orquesta las operaciones de negocio.
    """

    def __init__(self, repository=None):
        """
        Inicializa el servicio con un repository.

        Args:
            repository: Implementación del repository. Si es None, usa Supabase por defecto.
        """
        if repository is None:
            repository = SupabaseEmpresaRepository()
        self.repository = repository

    # ==========================================
    # OPERACIONES CRUD
    # ==========================================

    async def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        """Obtiene una empresa por su ID"""
        try:
            return await self.repository.obtener_por_id(empresa_id)
        except Exception as e:
            logger.error(f"Error obteniendo empresa {empresa_id}: {e}")
            raise

    async def obtener_todas(self, incluir_inactivas: bool = False) -> List[Empresa]:
        """Obtiene todas las empresas"""
        try:
            return await self.repository.obtener_todas(incluir_inactivas)
        except Exception as e:
            logger.error(f"Error obteniendo empresas: {e}")
            return []

    async def obtener_resumen_empresas(self, incluir_inactivas: bool = False) -> List[EmpresaResumen]:
        """Obtiene un resumen de todas las empresas"""
        try:
            empresas = await self.repository.obtener_todas(incluir_inactivas)
            resumenes = []
            for empresa in empresas:
                contacto = empresa.email or empresa.telefono or "Sin contacto"
                resumen = EmpresaResumen(
                    id=empresa.id,
                    nombre_comercial=empresa.nombre_comercial,
                    tipo_empresa=empresa.tipo_empresa,
                    estatus=empresa.estatus,
                    contacto_principal=contacto,
                    fecha_creacion=empresa.fecha_creacion
                )
                resumenes.append(resumen)
            return resumenes
        except Exception as e:
            logger.error(f"Error obteniendo resumen de empresas: {e}")
            return []

    async def buscar_por_nombre(self, termino: str, limite: int = 10) -> List[Empresa]:
        """Busca empresas por nombre comercial o razón social"""
        try:
            if not termino or len(termino) < 2:
                return []

            todas = await self.repository.obtener_todas(incluir_inactivas=True)
            termino_lower = termino.lower()

            # Filtrado simple en memoria
            resultados = [
                empresa for empresa in todas
                if termino_lower in empresa.nombre_comercial.lower()
                or termino_lower in empresa.razon_social.lower()
            ]

            return resultados[:limite]
        except Exception as e:
            logger.error(f"Error buscando empresas: {e}")
            return []

    async def crear(self, empresa_create: EmpresaCreate) -> Optional[Empresa]:
        """Crea una nueva empresa"""
        try:
            # Convertir EmpresaCreate a Empresa
            empresa = Empresa(**empresa_create.model_dump())

            # Validación de negocio básica
            if empresa.tipo_empresa == TipoEmpresa.NOMINA:
                if not empresa.email:
                    logger.warning("Empresa de nómina creada sin email")

            return await self.repository.crear(empresa)
        except ValueError as e:
            logger.error(f"Error de validación creando empresa: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            raise

    async def actualizar(self, empresa_id: int, empresa_update: EmpresaUpdate) -> Optional[Empresa]:
        """Actualiza una empresa existente"""
        try:
            # Obtener empresa actual
            empresa_actual = await self.repository.obtener_por_id(empresa_id)
            if not empresa_actual:
                logger.error(f"Empresa {empresa_id} no encontrada")
                return None

            # Aplicar actualizaciones
            datos_actualizados = empresa_actual.model_dump()
            for campo, valor in empresa_update.model_dump(exclude_unset=True).items():
                if valor is not None:
                    datos_actualizados[campo] = valor

            empresa_modificada = Empresa(**datos_actualizados)
            return await self.repository.actualizar(empresa_modificada)
        except Exception as e:
            logger.error(f"Error actualizando empresa {empresa_id}: {e}")
            raise

    async def cambiar_estatus(self, empresa_id: int, nuevo_estatus: EstatusEmpresa) -> bool:
        """Cambia el estatus de una empresa"""
        try:
            empresa = await self.repository.obtener_por_id(empresa_id)
            if not empresa:
                return False

            if empresa.estatus == nuevo_estatus:
                logger.warning(f"Empresa {empresa_id} ya tiene estatus {nuevo_estatus.value}")
                return True

            empresa.estatus = nuevo_estatus
            result = await self.repository.actualizar(empresa)
            return result is not None
        except Exception as e:
            logger.error(f"Error cambiando estatus de empresa {empresa_id}: {e}")
            return False

    async def eliminar(self, empresa_id: int) -> bool:
        """Elimina (inactiva) una empresa"""
        try:
            return await self.repository.eliminar(empresa_id)
        except Exception as e:
            logger.error(f"Error eliminando empresa {empresa_id}: {e}")
            return False

    # ==========================================
    # OPERACIONES DE CONSULTA ESPECÍFICAS
    # ==========================================

    async def obtener_empresas_nomina(self) -> List[Empresa]:
        """Obtiene solo empresas de tipo NOMINA activas"""
        try:
            todas = await self.repository.obtener_todas(incluir_inactivas=False)
            return [e for e in todas if e.tipo_empresa == TipoEmpresa.NOMINA]
        except Exception as e:
            logger.error(f"Error obteniendo empresas de nómina: {e}")
            return []

    async def obtener_empresas_mantenimiento(self) -> List[Empresa]:
        """Obtiene solo empresas de tipo MANTENIMIENTO activas"""
        try:
            todas = await self.repository.obtener_todas(incluir_inactivas=False)
            return [e for e in todas if e.tipo_empresa == TipoEmpresa.MANTENIMIENTO]
        except Exception as e:
            logger.error(f"Error obteniendo empresas de mantenimiento: {e}")
            return []


# Instancia global del servicio (singleton)
empresa_service = EmpresaService()
