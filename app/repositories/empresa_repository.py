"""
Repositorio de Empresas - Interface y implementación para Supabase.
Consolidado desde app/modules/empresas/infrastructure/.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: RFC duplicado)
- DatabaseError: Errores de conexión o infraestructura
- Propagar otras excepciones hacia arriba
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from app.entities import Empresa, EmpresaResumen
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class IEmpresaRepository(ABC):
    """Interface del repositorio de empresas - define el contrato"""

    @abstractmethod
    async def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        """Obtiene una empresa por su ID"""
        pass

    @abstractmethod
    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Empresa]:
        """
        Obtiene todas las empresas con soporte de paginación.

        Args:
            incluir_inactivas: Si True, incluye empresas inactivas
            limite: Número máximo de resultados (None = sin límite)
            offset: Número de registros a saltar (para paginación)
        """
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

    @abstractmethod
    async def existe_codigo_corto(self, codigo: str) -> bool:
        """Verifica si existe un código corto en la base de datos"""
        pass

    @abstractmethod
    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[Empresa]:
        """Busca empresas por nombre comercial o razón social en la base de datos"""
        pass

    @abstractmethod
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
        Busca empresas con filtros combinados en la base de datos.

        Args:
            texto: Término de búsqueda en nombre comercial o razón social
            tipo_empresa: Filtrar por tipo (NOMINA o MANTENIMIENTO)
            estatus: Filtrar por estatus específico
            incluir_inactivas: Si incluir empresas inactivas (sobrescribe filtro estatus)
            limite: Número máximo de resultados (default 50 para UI)
            offset: Número de registros a saltar (paginación)

        Returns:
            Lista de empresas que coinciden con todos los filtros
        """
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
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'empresas'

    async def obtener_por_id(self, empresa_id: int) -> Empresa:
        """
        Obtiene una empresa por su ID.

        Args:
            empresa_id: ID de la empresa a buscar

        Returns:
            Empresa encontrada

        Raises:
            NotFoundError: Si la empresa no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', empresa_id).execute()
            if not result.data:
                raise NotFoundError(f"Empresa con ID {empresa_id} no encontrada")
            return Empresa(**result.data[0])
        except NotFoundError:
            raise  # Re-propagar errores de negocio
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
        Obtiene todas las empresas con soporte de paginación.

        Args:
            incluir_inactivas: Si True, incluye empresas inactivas
            limite: Número máximo de resultados (None = 100 por defecto para seguridad)
            offset: Número de registros a saltar (para paginación)

        Returns:
            Lista de empresas (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            # Filtro de estatus
            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')

            # Ordenamiento (usa índice idx_empresas_fecha_creacion para eficiencia)
            query = query.order('fecha_creacion', desc=True)

            # Paginación con límite por defecto para seguridad
            if limite is None:
                limite = 100  # Límite de seguridad por defecto
                logger.debug("Usando límite por defecto de 100 registros")

            # Rango: [offset, offset + limite)
            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo empresas: {e}")
            raise DatabaseError(f"Error de base de datos al obtener empresas: {str(e)}")

    async def crear(self, empresa: Empresa) -> Empresa:
        """
        Crea una nueva empresa.

        Args:
            empresa: Empresa a crear

        Returns:
            Empresa creada con ID asignado

        Raises:
            DuplicateError: Si el RFC ya existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Verificar RFC duplicado
            if await self.existe_rfc(empresa.rfc):
                raise DuplicateError(
                    f"RFC {empresa.rfc} ya existe",
                    field="rfc",
                    value=empresa.rfc
                )

            # Preparar datos excluyendo ID, fecha de creacion y fecha de actualizacion (se asigna en BD)
            datos = empresa.model_dump(exclude={'id', 'fecha_creacion','fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la empresa (sin respuesta de BD)")

            return Empresa(**result.data[0])
        except DuplicateError:
            raise  # Re-propagar errores de negocio
        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            raise DatabaseError(f"Error de base de datos al crear empresa: {str(e)}")

    async def actualizar(self, empresa: Empresa) -> Empresa:
        """
        Actualiza una empresa existente.

        Args:
            empresa: Empresa con datos actualizados

        Returns:
            Empresa actualizada

        Raises:
            NotFoundError: Si la empresa no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Excluir campos que no deben actualizarse
            datos = empresa.model_dump(exclude={'id', 'fecha_creacion','fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', empresa.id).execute()

            if not result.data:
                raise NotFoundError(f"Empresa con ID {empresa.id} no encontrada")

            return Empresa(**result.data[0])
        except NotFoundError:
            raise  # Re-propagar
        except Exception as e:
            logger.error(f"Error actualizando empresa {empresa.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar empresa: {str(e)}")

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

    async def existe_codigo_corto(self, codigo: str) -> bool:
        """
        Verifica si existe un código corto en la base de datos.

        Args:
            codigo: Código corto a verificar (3 caracteres)

        Returns:
            True si el código ya existe, False si está disponible
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('codigo_corto', codigo.upper())\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error verificando código corto '{codigo}': {e}")
            return True  # Por seguridad, asumir que existe si hay error

    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[Empresa]:
        """
        Busca empresas por nombre comercial o razón social usando índices de la base de datos.

        Args:
            termino: Término de búsqueda
            limite: Número máximo de resultados (default 10)

        Returns:
            Lista de empresas que coinciden con el término (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Usar búsqueda en base de datos con ilike (case-insensitive LIKE)
            # Supabase/PostgreSQL usa parámetros seguros automáticamente
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .or_(
                    f"nombre_comercial.ilike.%{termino}%,"
                    f"razon_social.ilike.%{termino}%"
                )\
                .limit(limite)\
                .execute()

            return [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error buscando empresas con término '{termino}': {e}")
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
        Busca empresas con filtros combinados en la base de datos.
        Todos los filtros se aplican en la BD para máxima eficiencia.

        Args:
            texto: Término de búsqueda en nombre comercial o razón social
            tipo_empresa: Filtrar por tipo (NOMINA o MANTENIMIENTO)
            estatus: Filtrar por estatus específico
            incluir_inactivas: Si incluir empresas inactivas (sobrescribe filtro estatus)
            limite: Número máximo de resultados (default 50 para UI)
            offset: Número de registros a saltar (paginación)

        Returns:
            Lista de empresas que coinciden con todos los filtros

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Iniciamos con el query base
            query = self.supabase.table(self.tabla).select('*')

            # Aplicar filtro de texto si existe
            if texto and texto.strip():
                # Búsqueda en nombre comercial o razón social
                query = query.or_(
                    f"nombre_comercial.ilike.%{texto}%,"
                    f"razon_social.ilike.%{texto}%"
                )

            # Aplicar filtro de tipo si existe
            if tipo_empresa:
                query = query.eq('tipo_empresa', tipo_empresa)

            # Aplicar filtro de estatus
            if estatus:
                # Si hay un estatus específico, usarlo
                query = query.eq('estatus', estatus)
            elif not incluir_inactivas:
                # Si no incluir inactivas, filtrar solo activas
                query = query.eq('estatus', 'ACTIVO')
            # Si incluir_inactivas es True, no aplicamos filtro de estatus

            # Ordenamiento (usa índice para eficiencia)
            query = query.order('fecha_creacion', desc=True)

            # Aplicar paginación
            if limite > 0:
                query = query.range(offset, offset + limite - 1)

            # Ejecutar query
            result = query.execute()

            return [Empresa(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error buscando empresas con filtros: {e}")
            raise DatabaseError(f"Error de base de datos al buscar con filtros: {str(e)}")
