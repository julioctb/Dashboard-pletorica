"""
Servicio de aplicación para gestión de Sedes BUAP.

Accede directamente a Supabase (sin repository intermedio).
Patrón Direct Access - CRUD simple con jerarquía auto-referencial.
"""
import logging
from typing import List, Optional

from app.entities import (
    Sede,
    SedeCreate,
    SedeUpdate,
    SedeResumen,
)
from app.core.enums import Estatus
from app.database import db_manager
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, BusinessRuleError

logger = logging.getLogger(__name__)


class SedeService:
    """
    Servicio de aplicación para sedes BUAP.
    Orquesta las operaciones de negocio con acceso directo a Supabase.
    """

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'sedes'

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, sede_id: int) -> Sede:
        """
        Obtiene una sede por su ID.

        Raises:
            NotFoundError: Si la sede no existe
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', sede_id).execute()

            if not result.data:
                raise NotFoundError(f"Sede con ID {sede_id} no encontrada")

            return Sede(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo sede {sede_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener sede: {str(e)}")

    async def obtener_por_codigo(self, codigo: str) -> Optional[Sede]:
        """
        Obtiene una sede por su código.

        Returns:
            Sede si existe, None si no

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('codigo', codigo.upper()).execute()

            if not result.data:
                return None

            return Sede(**result.data[0])

        except Exception as e:
            logger.error(f"Error obteniendo sede por código {codigo}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener sede: {str(e)}")

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0,
    ) -> List[Sede]:
        """
        Obtiene todas las sedes con paginación.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            if not incluir_inactivas:
                query = query.eq('estatus', Estatus.ACTIVO)

            query = query.order('nombre', desc=False)

            if limite is None:
                limite = 100

            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Sede(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo sedes: {e}")
            raise DatabaseError(f"Error de base de datos al obtener sedes: {str(e)}")

    async def obtener_hijos(self, sede_padre_id: int) -> List[Sede]:
        """
        Obtiene las sedes hijas directas de una sede padre.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('sede_padre_id', sede_padre_id)\
                .eq('estatus', Estatus.ACTIVO)\
                .order('nombre')\
                .execute()

            return [Sede(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo hijos de sede {sede_padre_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_arbol(self) -> List[SedeResumen]:
        """
        Obtiene todas las sedes activas con información de jerarquía
        para construir un árbol en el frontend.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            # Obtener todas las sedes activas
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('estatus', Estatus.ACTIVO)\
                .order('nombre')\
                .execute()

            sedes = result.data
            # Crear mapa id→nombre para resolver nombres de padre/ubicación
            mapa_nombres = {s['id']: s.get('nombre_corto') or s['nombre'] for s in sedes}

            resumenes = []
            for data in sedes:
                sede = Sede(**data)
                extras = {}
                if sede.sede_padre_id and sede.sede_padre_id in mapa_nombres:
                    extras['sede_padre_nombre'] = mapa_nombres[sede.sede_padre_id]
                if sede.ubicacion_fisica_id and sede.ubicacion_fisica_id in mapa_nombres:
                    extras['ubicacion_fisica_nombre'] = mapa_nombres[sede.ubicacion_fisica_id]
                resumenes.append(SedeResumen.from_sede(sede, **extras))

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo árbol de sedes: {e}")
            raise DatabaseError(f"Error de base de datos al obtener árbol: {str(e)}")

    async def buscar(self, termino: str, limite: int = 20) -> List[Sede]:
        """
        Busca sedes por nombre, nombre corto o código.

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino.strip()) < 2:
            return []

        try:
            termino_limpio = termino.strip()

            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('estatus', Estatus.ACTIVO)\
                .or_(
                    f"nombre.ilike.%{termino_limpio}%,"
                    f"nombre_corto.ilike.%{termino_limpio}%,"
                    f"codigo.ilike.%{termino_limpio}%"
                )\
                .order('nombre')\
                .limit(limite)\
                .execute()

            return [Sede(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error buscando sedes con término '{termino}': {e}")
            raise DatabaseError(f"Error de base de datos al buscar sedes: {str(e)}")

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """
        Cuenta el total de sedes.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('id', count='exact')

            if not incluir_inactivas:
                query = query.eq('estatus', Estatus.ACTIVO)

            result = query.execute()
            return result.count if result.count else 0

        except Exception as e:
            logger.error(f"Error contando sedes: {e}")
            raise DatabaseError(f"Error de base de datos al contar sedes: {str(e)}")

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, sede_create: SedeCreate) -> Sede:
        """
        Crea una nueva sede.

        Raises:
            DuplicateError: Si el código ya existe
            DatabaseError: Si hay error de BD
        """
        try:
            sede = Sede(**sede_create.model_dump())

            logger.info(f"Creando sede: {sede.codigo} - {sede.nombre}")

            # Verificar código duplicado
            if await self.existe_codigo(sede.codigo):
                raise DuplicateError(
                    f"El código '{sede.codigo}' ya existe",
                    field="codigo",
                    value=sede.codigo,
                )

            # Validar FKs si se proporcionan
            if sede.sede_padre_id:
                await self._validar_sede_existe(sede.sede_padre_id, "sede padre")
            if sede.ubicacion_fisica_id:
                await self._validar_sede_existe(sede.ubicacion_fisica_id, "ubicación física")

            datos = sede.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'},
            )
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la sede (sin respuesta de BD)")

            return Sede(**result.data[0])

        except (DuplicateError, NotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error creando sede: {e}")
            raise DatabaseError(f"Error de base de datos al crear sede: {str(e)}")

    async def actualizar(self, sede_id: int, sede_update: SedeUpdate) -> Sede:
        """
        Actualiza una sede existente.

        Raises:
            NotFoundError: Si la sede no existe
            DuplicateError: Si el nuevo código ya existe
            DatabaseError: Si hay error de BD
        """
        try:
            sede_actual = await self.obtener_por_id(sede_id)

            datos_actualizados = sede_update.model_dump(exclude_unset=True)
            for campo, valor in datos_actualizados.items():
                if valor is not None:
                    setattr(sede_actual, campo, valor)

            logger.info(f"Actualizando sede ID {sede_id}")

            # Verificar código duplicado (excluyendo el registro actual)
            if await self.existe_codigo(sede_actual.codigo, excluir_id=sede_actual.id):
                raise DuplicateError(
                    f"El código '{sede_actual.codigo}' ya existe en otra sede",
                    field="codigo",
                    value=sede_actual.codigo,
                )

            # Validar FKs
            if sede_actual.sede_padre_id:
                if sede_actual.sede_padre_id == sede_actual.id:
                    raise BusinessRuleError("Una sede no puede ser su propia sede padre")
                await self._validar_sede_existe(sede_actual.sede_padre_id, "sede padre")
            if sede_actual.ubicacion_fisica_id:
                if sede_actual.ubicacion_fisica_id == sede_actual.id:
                    raise BusinessRuleError("Una sede no puede ser su propia ubicación física")
                await self._validar_sede_existe(sede_actual.ubicacion_fisica_id, "ubicación física")

            datos = sede_actual.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'},
            )
            result = self.supabase.table(self.tabla).update(datos).eq('id', sede_actual.id).execute()

            if not result.data:
                raise NotFoundError(f"Sede con ID {sede_actual.id} no encontrada")

            return Sede(**result.data[0])

        except (NotFoundError, DuplicateError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando sede {sede_id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar sede: {str(e)}")

    async def eliminar(self, sede_id: int) -> bool:
        """
        Elimina (desactiva) una sede.

        Raises:
            NotFoundError: Si la sede no existe
            BusinessRuleError: Si tiene sedes hijas activas
            DatabaseError: Si hay error de BD
        """
        try:
            sede = await self.obtener_por_id(sede_id)

            await self._validar_puede_eliminar(sede)

            logger.info(f"Eliminando (desactivando) sede: {sede.codigo}")

            result = self.supabase.table(self.tabla).update(
                {'estatus': Estatus.INACTIVO}
            ).eq('id', sede_id).execute()

            return bool(result.data)

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error eliminando sede {sede_id}: {e}")
            raise DatabaseError(f"Error de base de datos al eliminar sede: {str(e)}")

    async def activar(self, sede_id: int) -> Sede:
        """
        Activa una sede que estaba inactiva.

        Raises:
            NotFoundError: Si la sede no existe
            BusinessRuleError: Si ya está activa
            DatabaseError: Si hay error de BD
        """
        try:
            sede = await self.obtener_por_id(sede_id)

            if sede.estatus == Estatus.ACTIVO:
                raise BusinessRuleError("La sede ya está activa")

            logger.info(f"Activando sede: {sede.codigo}")

            result = self.supabase.table(self.tabla).update(
                {'estatus': Estatus.ACTIVO}
            ).eq('id', sede_id).execute()

            if not result.data:
                raise NotFoundError(f"Sede con ID {sede_id} no encontrada")

            return Sede(**result.data[0])

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error activando sede {sede_id}: {e}")
            raise DatabaseError(f"Error de base de datos al activar sede: {str(e)}")

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_puede_eliminar(self, sede: Sede) -> None:
        """Valida si una sede puede ser eliminada."""
        try:
            # Verificar sedes hijas activas
            result = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('sede_padre_id', sede.id)\
                .eq('estatus', Estatus.ACTIVO)\
                .execute()

            hijos = result.count if result.count else 0
            if hijos > 0:
                raise BusinessRuleError(
                    f"No se puede desactivar '{sede.nombre}' porque tiene {hijos} sede(s) hija(s) activa(s)"
                )

            # Verificar sedes que la usan como ubicación física
            result2 = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('ubicacion_fisica_id', sede.id)\
                .eq('estatus', Estatus.ACTIVO)\
                .execute()

            ubicadas = result2.count if result2.count else 0
            if ubicadas > 0:
                raise BusinessRuleError(
                    f"No se puede desactivar '{sede.nombre}' porque {ubicadas} sede(s) la usan como ubicación física"
                )

        except BusinessRuleError:
            raise
        except Exception as e:
            logger.error(f"Error validando eliminación de sede {sede.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _validar_sede_existe(self, sede_id: int, descripcion: str) -> None:
        """Valida que una sede referenciada existe."""
        try:
            result = self.supabase.table(self.tabla).select('id').eq('id', sede_id).execute()
            if not result.data:
                raise NotFoundError(f"La {descripcion} con ID {sede_id} no existe")
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error validando sede {sede_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def existe_codigo(self, codigo: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si un código ya existe."""
        try:
            query = self.supabase.table(self.tabla).select('id').eq('codigo', codigo.upper())

            if excluir_id:
                query = query.neq('id', excluir_id)

            result = query.execute()
            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error verificando código {codigo}: {e}")
            raise DatabaseError(f"Error de base de datos al verificar código: {str(e)}")


# ==========================================
# SINGLETON
# ==========================================

sede_service = SedeService()
