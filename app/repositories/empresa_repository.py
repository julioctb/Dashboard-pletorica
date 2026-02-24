"""
Repositorio de Empresas - Implementacion para Supabase.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: RFC duplicado)
- DatabaseError: Errores de conexion o infraestructura
"""
import logging
from typing import List, Optional

from app.entities import (
    Empresa,
    EmpresaResumen,
    EstatusEmpresa,
)
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError
from app.repositories.shared import (
    apply_eq_filters,
    apply_order,
    apply_pagination,
    build_ilike_or,
)

logger = logging.getLogger(__name__)


class SupabaseEmpresaRepository:
    """Implementacion del repositorio de empresas usando Supabase."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'empresas'

    async def obtener_por_id(self, empresa_id: int) -> Empresa:
        """
        Obtiene una empresa por su ID.

        Raises:
            NotFoundError: Si la empresa no existe
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', empresa_id).execute()
            if not result.data:
                raise NotFoundError(f"Empresa con ID {empresa_id} no encontrada")
            return Empresa(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener empresa: {str(e)}")

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Empresa]:
        """
        Obtiene todas las empresas con paginacion.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            if not incluir_inactivas:
                query = query.eq('estatus', EstatusEmpresa.ACTIVO.value)

            query = apply_order(query, 'fecha_creacion', desc=True)

            if limite is None:
                limite = 100

            query = apply_pagination(query, limite, offset)

            result = query.execute()
            return [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo empresas: {e}")
            raise DatabaseError(f"Error de base de datos al obtener empresas: {str(e)}")

    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[Empresa]:
        """
        Busca empresas por nombre comercial o razon social.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            or_clause = build_ilike_or(termino, ['nombre_comercial', 'razon_social'])
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .or_(or_clause)\
                .limit(limite)\
                .execute()

            return [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error buscando empresas con termino '{termino}': {e}")
            raise DatabaseError(f"Error de base de datos al buscar empresas: {str(e)}")

    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        tipo_empresa: Optional[str] = None,
        estatus: Optional[str] = None,
        incluir_inactivas: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[Empresa]:
        """
        Busca empresas con filtros combinados.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            if texto and texto.strip():
                query = query.or_(build_ilike_or(texto, ['nombre_comercial', 'razon_social']))

            estatus_filtro = estatus if estatus else (
                None if incluir_inactivas else EstatusEmpresa.ACTIVO.value
            )
            query = apply_eq_filters(
                query,
                {
                    'tipo_empresa': tipo_empresa,
                    'estatus': estatus_filtro,
                },
            )

            query = apply_order(query, 'fecha_creacion', desc=True)

            if limite > 0:
                query = apply_pagination(query, limite, offset)

            result = query.execute()
            return [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error buscando empresas con filtros: {e}")
            raise DatabaseError(f"Error de base de datos al buscar con filtros: {str(e)}")

    async def crear(self, empresa: Empresa) -> Empresa:
        """
        Crea una nueva empresa.

        Raises:
            DuplicateError: Si el RFC ya existe
            DatabaseError: Si hay error de BD
        """
        try:
            if await self.existe_rfc(empresa.rfc):
                raise DuplicateError(
                    f"RFC {empresa.rfc} ya existe",
                    field="rfc",
                    value=empresa.rfc
                )

            datos = empresa.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la empresa (sin respuesta de BD)")

            return Empresa(**result.data[0])
        except (DuplicateError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            raise DatabaseError(f"Error de base de datos al crear empresa: {str(e)}")

    async def actualizar(self, empresa: Empresa) -> Empresa:
        """
        Actualiza una empresa existente.

        Raises:
            NotFoundError: Si la empresa no existe
            DatabaseError: Si hay error de BD
        """
        try:
            datos = empresa.model_dump(mode='json', exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', empresa.id).execute()

            if not result.data:
                raise NotFoundError(f"Empresa con ID {empresa.id} no encontrada")

            return Empresa(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando empresa {empresa.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar empresa: {str(e)}")

    async def eliminar(self, empresa_id: int) -> bool:
        """
        Elimina (inactiva) una empresa.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).update(
                {'estatus': 'INACTIVO'}
            ).eq('id', empresa_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error eliminando empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error de base de datos al eliminar empresa: {str(e)}")

    async def existe_rfc(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si existe un RFC en la base de datos.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('id').eq('rfc', rfc.upper())
            if excluir_id:
                query = query.neq('id', excluir_id)
            result = query.execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error verificando RFC: {e}")
            raise DatabaseError(f"Error de base de datos al verificar RFC: {str(e)}")

    async def existe_codigo_corto(self, codigo: str) -> bool:
        """
        Verifica si existe un codigo corto.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('codigo_corto', codigo.upper())\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error verificando codigo corto '{codigo}': {e}")
            raise DatabaseError(f"Error de base de datos al verificar codigo corto: {str(e)}")
