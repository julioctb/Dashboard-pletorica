"""
Servicio de aplicación para gestión de Tipos de Servicio.

Accede directamente a Supabase (sin repository intermedio).

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: clave duplicada)
- DatabaseError: Errores de conexión o infraestructura
- BusinessRuleError: Violaciones de reglas de negocio
- Logging de errores solo para debugging, NO para control de flujo
"""
import logging
from typing import List, Optional

from app.entities import (
    TipoServicio,
    TipoServicioCreate,
    TipoServicioUpdate,
)
from app.core.enums import Estatus
from app.database import db_manager
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, BusinessRuleError

logger = logging.getLogger(__name__)


class TipoServicioService:
    """
    Servicio de aplicación para tipos de servicio.
    Orquesta las operaciones de negocio con acceso directo a Supabase.
    """

    def __init__(self):
        """Inicializa el servicio con conexión directa a Supabase."""
        self.supabase = db_manager.get_client()
        self.tabla = 'tipos_servicio'

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, tipo_id: int) -> TipoServicio:
        """
        Obtiene un tipo de servicio por su ID.

        Args:
            tipo_id: ID del tipo

        Returns:
            TipoServicio encontrado

        Raises:
            NotFoundError: Si el tipo no existe
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', tipo_id).execute()

            if not result.data:
                raise NotFoundError(f"Tipo de servicio con ID {tipo_id} no encontrado")

            return TipoServicio(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo tipo de servicio {tipo_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener tipo: {str(e)}")

    async def obtener_por_clave(self, clave: str) -> Optional[TipoServicio]:
        """
        Obtiene un tipo de servicio por su clave.

        Args:
            clave: Clave del tipo (ej: "JAR", "LIM")

        Returns:
            TipoServicio si existe, None si no

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('clave', clave.upper()).execute()

            if not result.data:
                return None

            return TipoServicio(**result.data[0])

        except Exception as e:
            logger.error(f"Error obteniendo tipo por clave {clave}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener tipo: {str(e)}")

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio con paginación.

        Args:
            incluir_inactivas: Si True, incluye tipos inactivos
            limite: Número máximo de resultados (None = 100 por defecto)
            offset: Número de registros a saltar

        Returns:
            Lista de tipos (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            # Filtro de estatus
            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')

            # Ordenamiento por nombre
            query = query.order('nombre', desc=False)

            # Paginación con límite por defecto
            if limite is None:
                limite = 100
                logger.debug("Usando límite por defecto de 100 registros")

            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [TipoServicio(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo tipos de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al obtener tipos: {str(e)}")

    async def obtener_activas(self) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio activos.
        Método de conveniencia para selects/dropdowns.

        Returns:
            Lista de tipos activos ordenados por nombre

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.obtener_todas(incluir_inactivas=False)

    async def buscar(self, termino: str, limite: int = 10) -> List[TipoServicio]:
        """
        Busca tipos por nombre o clave.

        Args:
            termino: Término de búsqueda (mínimo 1 caracter)
            limite: Número máximo de resultados

        Returns:
            Lista de tipos que coinciden

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino.strip()) < 2:
            return []

        return await self._buscar_por_texto(termino.strip(), limite)

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """
        Cuenta el total de tipos de servicio.

        Args:
            incluir_inactivas: Si True, cuenta también los inactivos

        Returns:
            Número total de tipos

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('id', count='exact')

            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')

            result = query.execute()
            return result.count if result.count else 0

        except Exception as e:
            logger.error(f"Error contando tipos de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al contar tipos: {str(e)}")

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, tipo_create: TipoServicioCreate) -> TipoServicio:
        """
        Crea un nuevo tipo de servicio.

        Args:
            tipo_create: Datos del tipo a crear

        Returns:
            TipoServicio creado con ID asignado

        Raises:
            DuplicateError: Si la clave ya existe
            DatabaseError: Si hay error de BD
        """
        try:
            # Convertir TipoServicioCreate a TipoServicio
            tipo = TipoServicio(**tipo_create.model_dump())

            logger.info(f"Creando tipo de servicio: {tipo.clave} - {tipo.nombre}")

            # Verificar clave duplicada
            if await self.existe_clave(tipo.clave):
                raise DuplicateError(
                    f"La clave '{tipo.clave}' ya existe",
                    field="clave",
                    value=tipo.clave
                )

            # Preparar datos excluyendo campos autogenerados
            datos = tipo.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el tipo de servicio (sin respuesta de BD)")

            return TipoServicio(**result.data[0])

        except (DuplicateError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error creando tipo de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al crear tipo: {str(e)}")

    async def actualizar(self, tipo_id: int, tipo_update: TipoServicioUpdate) -> TipoServicio:
        """
        Actualiza un tipo de servicio existente.

        Args:
            tipo_id: ID del tipo a actualizar
            tipo_update: Datos a actualizar (solo campos con valor)

        Returns:
            TipoServicio actualizado

        Raises:
            NotFoundError: Si el tipo no existe
            DuplicateError: Si la nueva clave ya existe
            DatabaseError: Si hay error de BD
        """
        try:
            # Obtener tipo actual
            tipo_actual = await self.obtener_por_id(tipo_id)

            # Aplicar cambios (solo campos que vienen en el update)
            datos_actualizados = tipo_update.model_dump(exclude_unset=True)

            for campo, valor in datos_actualizados.items():
                if valor is not None:
                    setattr(tipo_actual, campo, valor)

            logger.info(f"Actualizando tipo de servicio ID {tipo_id}")

            # Verificar clave duplicada (excluyendo el registro actual)
            if await self.existe_clave(tipo_actual.clave, excluir_id=tipo_actual.id):
                raise DuplicateError(
                    f"La clave '{tipo_actual.clave}' ya existe en otro tipo",
                    field="clave",
                    value=tipo_actual.clave
                )

            # Preparar datos
            datos = tipo_actual.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', tipo_actual.id).execute()

            if not result.data:
                raise NotFoundError(f"Tipo de servicio con ID {tipo_actual.id} no encontrado")

            return TipoServicio(**result.data[0])

        except (NotFoundError, DuplicateError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando tipo de servicio {tipo_id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar tipo: {str(e)}")

    async def eliminar(self, tipo_id: int) -> bool:
        """
        Elimina (desactiva) un tipo de servicio.

        Reglas de negocio:
        - No se puede eliminar si tiene contratos activos asociados
        - (Se implementará cuando exista el módulo de contratos)

        Args:
            tipo_id: ID del tipo a eliminar

        Returns:
            True si se eliminó correctamente

        Raises:
            NotFoundError: Si el tipo no existe
            BusinessRuleError: Si tiene contratos activos
            DatabaseError: Si hay error de BD
        """
        try:
            # Obtener tipo para validar que existe
            tipo = await self.obtener_por_id(tipo_id)

            # Validar reglas de negocio
            await self._validar_puede_eliminar(tipo)

            logger.info(f"Eliminando (desactivando) tipo de servicio: {tipo.clave}")

            result = self.supabase.table(self.tabla).update(
                {'estatus': 'INACTIVO'}
            ).eq('id', tipo_id).execute()

            return bool(result.data)

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error eliminando tipo de servicio {tipo_id}: {e}")
            raise DatabaseError(f"Error de base de datos al eliminar tipo: {str(e)}")

    async def activar(self, tipo_id: int) -> TipoServicio:
        """
        Activa un tipo de servicio que estaba inactivo.

        Args:
            tipo_id: ID del tipo a activar

        Returns:
            TipoServicio activado

        Raises:
            NotFoundError: Si el tipo no existe
            BusinessRuleError: Si ya está activo
            DatabaseError: Si hay error de BD
        """
        try:
            tipo = await self.obtener_por_id(tipo_id)

            if tipo.estatus == Estatus.ACTIVO:
                raise BusinessRuleError("El tipo ya está activo")

            tipo.estatus = Estatus.ACTIVO

            logger.info(f"Activando tipo de servicio: {tipo.clave}")

            # Actualizar en BD
            datos = tipo.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', tipo.id).execute()

            if not result.data:
                raise NotFoundError(f"Tipo de servicio con ID {tipo.id} no encontrado")

            return TipoServicio(**result.data[0])

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error activando tipo de servicio {tipo_id}: {e}")
            raise DatabaseError(f"Error de base de datos al activar tipo: {str(e)}")

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_puede_eliminar(self, tipo: TipoServicio) -> None:
        """
        Valida si un tipo puede ser eliminado.

        Reglas:
        - No debe tener contratos activos asociados

        Args:
            tipo: Tipo a validar

        Raises:
            BusinessRuleError: Si no cumple las reglas
        """
        # TODO: Cuando exista el módulo de contratos, descomentar:
        # from app.repositories import SupabaseContratoRepository
        # contrato_repo = SupabaseContratoRepository()
        # contratos = await contrato_repo.contar_por_tipo(tipo.id, solo_activos=True)
        # if contratos > 0:
        #     raise BusinessRuleError(
        #         f"No se puede eliminar el tipo '{tipo.nombre}' porque tiene {contratos} contrato(s) activo(s)"
        #     )
        pass

    async def existe_clave(self, clave: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si una clave ya existe.

        Args:
            clave: Clave a verificar
            excluir_id: ID a excluir (para actualizaciones)

        Returns:
            True si existe, False si no

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('id').eq('clave', clave.upper())

            if excluir_id:
                query = query.neq('id', excluir_id)

            result = query.execute()
            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error verificando clave {clave}: {e}")
            raise DatabaseError(f"Error de base de datos al verificar clave: {str(e)}")

    async def _buscar_por_texto(self, termino: str, limite: int = 10, offset: int = 0) -> List[TipoServicio]:
        """
        Busca tipos de servicio por nombre o clave en base de datos.

        Args:
            termino: Término de búsqueda
            limite: Número máximo de resultados (default 10)
            offset: Registros a saltar

        Returns:
            Lista de tipos que coinciden (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            termino_upper = termino.upper()

            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('estatus', 'ACTIVO')\
                .or_(
                    f"nombre.ilike.%{termino_upper}%,"
                    f"clave.ilike.%{termino_upper}%"
                )\
                .range(offset, offset + limite - 1)\
                .execute()

            return [TipoServicio(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error buscando tipos con término '{termino}': {e}")
            raise DatabaseError(f"Error de base de datos al buscar tipos: {str(e)}")


# ==========================================
# SINGLETON
# ==========================================

# Instancia global del servicio para uso en toda la aplicación
tipo_servicio_service = TipoServicioService()
