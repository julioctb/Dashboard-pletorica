"""
Servicio de aplicación para gestión de empresas.
Accede directamente a Supabase (sin capa de repositorio).

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: RFC duplicado)
- DatabaseError: Errores de conexión o infraestructura
- Las excepciones se propagan hacia arriba al State
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
from app.database import db_manager
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError
from app.core.utils import generar_candidatos_codigo

logger = logging.getLogger(__name__)


class EmpresaService:
    """
    Servicio de aplicación para empresas.
    Orquesta las operaciones de negocio y accede directamente a Supabase.
    """

    def __init__(self):
        """Inicializa el servicio con conexión directa a Supabase."""
        self.supabase = db_manager.get_client()
        self.tabla = 'empresas'

    # ==========================================
    # OPERACIONES CRUD
    # ==========================================

    async def obtener_por_id(self, empresa_id: int) -> Empresa:
        """
        Obtiene una empresa por su ID.

        Args:
            empresa_id: ID de la empresa

        Returns:
            Empresa encontrada

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
        Obtiene todas las empresas con paginación.

        Args:
            incluir_inactivas: Si True, incluye empresas inactivas
            limite: Número máximo de resultados (None = 100 por defecto)
            offset: Número de registros a saltar

        Returns:
            Lista de empresas (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            if not incluir_inactivas:
                query = query.eq('estatus', EstatusEmpresa.ACTIVO)

            query = query.order('fecha_creacion', desc=True)

            if limite is None:
                limite = 100
                logger.debug("Usando límite por defecto de 100 registros")

            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo empresas: {e}")
            raise DatabaseError(f"Error de base de datos al obtener empresas: {str(e)}")

    async def buscar_por_nombre(self, termino: str, limite: int = 10) -> List[Empresa]:
        """
        Busca empresas por nombre comercial o razón social usando índices de base de datos.

        Args:
            termino: Término de búsqueda (mínimo 2 caracteres)
            limite: Número máximo de resultados

        Returns:
            Lista de empresas que coinciden con el término (vacía si no hay o termino < 2 chars)

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino) < 2:
            return []

        return await self._buscar_por_texto(termino, limite)

    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        tipo_empresa: Optional[str] = None,
        estatus: Optional[str] = None,
        incluir_inactivas: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[EmpresaResumen]:
        """
        Busca empresas con filtros combinados aplicados en la base de datos.
        Optimizado para performance con índices y límites.

        Args:
            texto: Término de búsqueda (mínimo 2 caracteres para activar búsqueda)
            tipo_empresa: Filtrar por tipo (NOMINA o MANTENIMIENTO)
            estatus: Filtrar por estatus específico
            incluir_inactivas: Si incluir empresas inactivas
            limite: Número máximo de resultados (default 50 para UI)
            offset: Número de registros a saltar (paginación)

        Returns:
            Lista de resúmenes de empresas que coinciden con los filtros

        Raises:
            DatabaseError: Si hay error de BD
        """
        if texto and len(texto.strip()) < 2:
            texto = None

        try:
            query = self.supabase.table(self.tabla).select('*')

            if texto and texto.strip():
                query = query.or_(
                    f"nombre_comercial.ilike.%{texto}%,"
                    f"razon_social.ilike.%{texto}%"
                )

            if tipo_empresa:
                query = query.eq('tipo_empresa', tipo_empresa)

            if estatus:
                query = query.eq('estatus', estatus)
            elif not incluir_inactivas:
                query = query.eq('estatus', EstatusEmpresa.ACTIVO)

            query = query.order('fecha_creacion', desc=True)

            if limite > 0:
                query = query.range(offset, offset + limite - 1)

            result = query.execute()
            empresas = [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error buscando empresas con filtros: {e}")
            raise DatabaseError(f"Error de base de datos al buscar con filtros: {str(e)}")

        return [EmpresaResumen.from_empresa(empresa) for empresa in empresas]

    async def crear(self, empresa_create: EmpresaCreate) -> Empresa:
        """
        Crea una nueva empresa con código corto autogenerado.

        Args:
            empresa_create: Datos de la empresa a crear

        Returns:
            Empresa creada con ID y codigo_corto asignados

        Raises:
            DuplicateError: Si el RFC ya existe
            ValidationError: Si los datos no son válidos
            DatabaseError: Si hay error de BD
        """
        codigo_corto = await self._generar_codigo_unico(empresa_create.nombre_comercial)

        datos = empresa_create.model_dump()
        datos['codigo_corto'] = codigo_corto
        empresa = Empresa(**datos)

        if empresa.tipo_empresa == TipoEmpresa.NOMINA:
            if not empresa.email:
                logger.warning("Empresa de nómina creada sin email")

        # Verificar RFC duplicado e insertar
        try:
            if await self._existe_rfc(empresa.rfc):
                raise DuplicateError(
                    f"RFC {empresa.rfc} ya existe",
                    field="rfc",
                    value=empresa.rfc
                )

            datos_insert = empresa.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos_insert).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la empresa (sin respuesta de BD)")

            return Empresa(**result.data[0])
        except (DuplicateError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            raise DatabaseError(f"Error de base de datos al crear empresa: {str(e)}")

    async def _generar_codigo_unico(self, nombre_comercial: str) -> str:
        """
        Genera un código corto único para la empresa.

        Algoritmo:
        1. Nivel 1: Primeras 3 letras de primera palabra significativa
        2. Nivel 2: Iniciales de primeras 3 palabras (estilo RFC)
        3. Fallback: Base + número incremental (XX2, XX3...)

        Args:
            nombre_comercial: Nombre comercial de la empresa

        Returns:
            Código único de 3 caracteres

        Raises:
            DatabaseError: Si no se puede generar un código único
        """
        candidatos = generar_candidatos_codigo(nombre_comercial)

        for codigo in candidatos:
            if not await self._existe_codigo_corto(codigo):
                logger.info(f"Código '{codigo}' asignado para '{nombre_comercial}'")
                return codigo

        raise DatabaseError(
            f"No se pudo generar código único para '{nombre_comercial}' "
            f"después de {len(candidatos)} intentos"
        )

    async def actualizar(self, empresa_id: int, empresa_update: EmpresaUpdate) -> Empresa:
        """
        Actualiza una empresa existente.

        Args:
            empresa_id: ID de la empresa a actualizar
            empresa_update: Datos a actualizar

        Returns:
            Empresa actualizada

        Raises:
            NotFoundError: Si la empresa no existe
            ValidationError: Si los datos no son válidos
            DatabaseError: Si hay error de BD
        """
        empresa_actual = await self.obtener_por_id(empresa_id)

        datos_actualizados = empresa_actual.model_dump()
        for campo, valor in empresa_update.model_dump(exclude_unset=True).items():
            if valor is not None:
                datos_actualizados[campo] = valor

        empresa_modificada = Empresa(**datos_actualizados)

        # Actualizar en BD
        try:
            datos = empresa_modificada.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', empresa_modificada.id).execute()

            if not result.data:
                raise NotFoundError(f"Empresa con ID {empresa_modificada.id} no encontrada")

            return Empresa(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando empresa {empresa_modificada.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar empresa: {str(e)}")

    async def cambiar_estatus(self, empresa_id: int, nuevo_estatus: EstatusEmpresa) -> bool:
        """
        Cambia el estatus de una empresa.

        Args:
            empresa_id: ID de la empresa
            nuevo_estatus: Nuevo estatus a asignar

        Returns:
            True si se cambió exitosamente

        Raises:
            NotFoundError: Si la empresa no existe
            DatabaseError: Si hay error de BD
        """
        empresa = await self.obtener_por_id(empresa_id)

        if empresa.estatus == nuevo_estatus:
            logger.warning(f"Empresa {empresa_id} ya tiene estatus {nuevo_estatus.value}")
            return True

        empresa.estatus = nuevo_estatus

        try:
            datos = empresa.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', empresa.id).execute()

            if not result.data:
                raise NotFoundError(f"Empresa con ID {empresa.id} no encontrada")

            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando empresa {empresa.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar empresa: {str(e)}")

    async def eliminar(self, empresa_id: int) -> bool:
        """
        Elimina (inactiva) una empresa.

        Args:
            empresa_id: ID de la empresa a eliminar

        Returns:
            True si se eliminó exitosamente

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

    # ==========================================
    # MÉTODOS INTERNOS DE CONSULTA
    # ==========================================

    async def _existe_rfc(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si existe un RFC en la base de datos.

        Args:
            rfc: RFC a verificar
            excluir_id: ID a excluir de la búsqueda (para actualizaciones)

        Returns:
            True si el RFC ya existe

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
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

    async def _existe_codigo_corto(self, codigo: str) -> bool:
        """
        Verifica si existe un código corto en la base de datos.

        Args:
            codigo: Código corto a verificar (3 caracteres)

        Returns:
            True si el código ya existe, False si está disponible

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('codigo_corto', codigo.upper())\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error verificando código corto '{codigo}': {e}")
            raise DatabaseError(f"Error de base de datos al verificar código corto: {str(e)}")

    async def _buscar_por_texto(self, termino: str, limite: int = 10) -> List[Empresa]:
        """
        Busca empresas por nombre comercial o razón social usando índices de la base de datos.

        Args:
            termino: Término de búsqueda
            limite: Número máximo de resultados (default 10)

        Returns:
            Lista de empresas que coinciden con el término

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
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


# Instancia global del servicio (singleton)
empresa_service = EmpresaService()
