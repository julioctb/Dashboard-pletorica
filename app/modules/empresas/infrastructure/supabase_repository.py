"""Implementación del repositorio usando Supabase"""
from typing import List, Optional
import logging
from app.modules.shared.database.connection import db_manager
from ..domain.repository_interface import IEmpresaRepository
from ..domain.entities import Empresa

logger = logging.getLogger(__name__)

class SupabaseEmpresaRepository(IEmpresaRepository):
    """Implementación específica para Supabase"""
    
    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'empresas'
    
    async def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', empresa_id).execute()
            if result.data:
                return Empresa(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    async def obtener_todas(self, incluir_inactivas: bool = False) -> List[Empresa]:
        try:
            query = self.supabase.table(self.tabla).select('*')
            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')
            result = query.order('nombre_comercial').execute()
            return [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    
    async def crear(self, empresa: Empresa) -> Empresa:
        try:
            if await self.existe_rfc(empresa.rfc):
                raise ValueError(f"RFC {empresa.rfc} ya existe")
            
            datos = empresa.model_dump(exclude={'id'})
            result = self.supabase.table(self.tabla).insert(datos).execute()
            
            if result.data:
                return Empresa(**result.data[0])
            raise Exception("No se pudo crear")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    async def actualizar(self, empresa: Empresa) -> Empresa:
        try:
            datos = empresa.model_dump(exclude={'id', 'fecha_creacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', empresa.id).execute()
            
            if result.data:
                return Empresa(**result.data[0])
            raise Exception("No se pudo actualizar")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    async def eliminar(self, empresa_id: int) -> bool:
        try:
            result = self.supabase.table(self.tabla).update({'estatus': 'INACTIVO'}).eq('id', empresa_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
    
    async def existe_rfc(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        try:
            query = self.supabase.table(self.tabla).select('id').eq('rfc', rfc.upper())
            if excluir_id:
                query = query.neq('id', excluir_id)
            result = query.execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
