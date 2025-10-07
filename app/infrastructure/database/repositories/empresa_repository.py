"""
Repositorio de Empresas - Interface y implementación para Supabase.
Consolidado desde app/modules/empresas/infrastructure/.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from app.domain.empresas import Empresa, EmpresaResumen

logger = logging.getLogger(__name__)


class IEmpresaRepository(ABC):
    """Interface del repositorio de empresas - define el contrato"""

    @abstractmethod
    async def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        """Obtiene una empresa por su ID"""
        pass

    @abstractmethod
    async def obtener_todas(self, incluir_inactivas: bool = False) -> List[Empresa]:
        """Obtiene todas las empresas"""
        pass

    @abstractmethod
    async def crear(self, empresa: Empresa) -> Empresa:
        """Crea una nueva empresa"""
        pass

    @abstractmethod
    async def actualizar(self, empresa: Empresa) -> Empresa:
        """Actualiza una empresa existente"""
        pass

    @abstractmethod
    async def eliminar(self, empresa_id: int) -> bool:
        """Elimina (inactiva) una empresa"""
        pass

    @abstractmethod
    async def existe_rfc(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si existe un RFC en la base de datos"""
        pass


class SupabaseEmpresaRepository(IEmpresaRepository):
    """Implementación del repositorio usando Supabase"""

    def __init__(self, db_manager=None):
        """
        Inicializa el repositorio con un cliente de Supabase.

        Args:
            db_manager: Gestor de base de datos. Si es None, se importa el global.
        """
        if db_manager is None:
            from app.infrastructure.database.connection import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'empresas'

    async def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        """Obtiene una empresa por su ID"""
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', empresa_id).execute()
            if result.data:
                return Empresa(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error obteniendo empresa {empresa_id}: {e}")
            raise

    async def obtener_todas(self, incluir_inactivas: bool = False) -> List[Empresa]:
        """Obtiene todas las empresas"""
        try:
            query = self.supabase.table(self.tabla).select('*')
            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')
            result = query.order('nombre_comercial').execute()
            return [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo empresas: {e}")
            return []

    async def crear(self, empresa: Empresa) -> Empresa:
        """Crea una nueva empresa"""
        try:
            # Verificar RFC duplicado
            if await self.existe_rfc(empresa.rfc):
                raise ValueError(f"RFC {empresa.rfc} ya existe")

            # Preparar datos excluyendo ID (se asigna en BD)
            datos = empresa.model_dump(exclude={'id'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if result.data:
                return Empresa(**result.data[0])
            raise Exception("No se pudo crear la empresa")
        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            raise

    async def actualizar(self, empresa: Empresa) -> Empresa:
        """Actualiza una empresa existente"""
        try:
            # Excluir campos que no deben actualizarse
            datos = empresa.model_dump(exclude={'id', 'fecha_creacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', empresa.id).execute()

            if result.data:
                return Empresa(**result.data[0])
            raise Exception("No se pudo actualizar la empresa")
        except Exception as e:
            logger.error(f"Error actualizando empresa {empresa.id}: {e}")
            raise

    async def eliminar(self, empresa_id: int) -> bool:
        """Elimina (soft delete) una empresa estableciendo estatus INACTIVO"""
        try:
            result = self.supabase.table(self.tabla).update(
                {'estatus': 'INACTIVO'}
            ).eq('id', empresa_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error eliminando empresa {empresa_id}: {e}")
            return False

    async def existe_rfc(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si existe un RFC en la base de datos"""
        try:
            query = self.supabase.table(self.tabla).select('id').eq('rfc', rfc.upper())
            if excluir_id:
                query = query.neq('id', excluir_id)
            result = query.execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error verificando RFC: {e}")
            return False
