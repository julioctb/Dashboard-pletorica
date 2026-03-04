"""
Servicio de Instituciones.

Gestiona el catálogo de instituciones cliente y la relación
instituciones_empresas (qué empresas supervisa cada institución).

Patrón: Direct Access (db_manager en servicio, sin repositorio).
"""
import logging
from typing import List, Optional

from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    DatabaseError,
    BusinessRuleError,
)
from app.entities.institucion import (
    Institucion,
    InstitucionCreate,
    InstitucionUpdate,
    InstitucionResumen,
    InstitucionEmpresa,
)
from app.services.direct_service import DirectSupabaseService

logger = logging.getLogger(__name__)


class InstitucionService(DirectSupabaseService):
    """
    Servicio para gestión de instituciones y sus empresas asociadas.

    Las instituciones representan clientes institucionales (BUAP, Gobierno)
    que supervisan empresas proveedoras. Los usuarios con
    user_profiles.rol='institucion' obtienen su acceso a empresas
    a través de instituciones_empresas (NO user_companies).
    """

    def __init__(self):
        super().__init__("instituciones")
        self.tabla_empresas = 'instituciones_empresas'

    # =========================================================================
    # CRUD INSTITUCIONES
    # =========================================================================

    async def obtener_por_id(self, id: int) -> Institucion:
        """Obtiene una institución por ID."""
        try:
            institucion = self._fetch_one(Institucion, filters={"id": id})
            if not institucion:
                raise NotFoundError(f"Institución con ID {id} no encontrada")
            return institucion

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo institución {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_todas(
        self,
        solo_activas: bool = True,
    ) -> List[InstitucionResumen]:
        """Lista todas las instituciones con conteo de empresas."""
        try:
            query = self.supabase.table(self.tabla).select('*')

            if solo_activas:
                query = query.eq('activo', True)

            result = query.order('nombre').execute()

            asignaciones = self.supabase.table(self.tabla_empresas)\
                .select('institucion_id')\
                .execute()
            conteos_empresas: dict[int, int] = {}
            for row in asignaciones.data or []:
                institucion_id = row['institucion_id']
                conteos_empresas[institucion_id] = (
                    conteos_empresas.get(institucion_id, 0) + 1
                )

            resumenes = []
            for data in result.data:
                resumenes.append(InstitucionResumen(
                    id=data['id'],
                    nombre=data['nombre'],
                    codigo=data['codigo'],
                    activo=data['activo'],
                    cantidad_empresas=conteos_empresas.get(data['id'], 0),
                ))

            return resumenes

        except Exception as e:
            logger.error(f"Error listando instituciones: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, datos: InstitucionCreate) -> Institucion:
        """Crea una nueva institución."""
        try:
            result = self._insert_row(datos.model_dump(mode='json'))

            if not result.data:
                raise DatabaseError("No se pudo crear la institución")

            logger.info(f"Institución creada: {datos.codigo}")
            return Institucion(**result.data[0])

        except Exception as e:
            error_msg = str(e).lower()
            if "duplicate" in error_msg or "unique" in error_msg:
                raise DuplicateError(
                    f"Ya existe una institución con código '{datos.codigo}'",
                    field="codigo",
                    value=datos.codigo,
                )
            logger.error(f"Error creando institución: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar(self, id: int, datos: InstitucionUpdate) -> Institucion:
        """Actualiza una institución existente."""
        try:
            actual = await self.obtener_por_id(id)
            self._merge_update_model(actual, datos)
            payload = actual.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'},
            )
            result = self._update_rows(payload, filters={"id": id})

            if not result.data:
                raise NotFoundError(f"Institución con ID {id} no encontrada")

            logger.info(f"Institución {id} actualizada")
            return Institucion(**result.data[0])

        except (NotFoundError, DuplicateError):
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "duplicate" in error_msg or "unique" in error_msg:
                raise DuplicateError(
                    f"Ya existe una institución con ese código",
                    field="codigo",
                    value=datos.codigo or "",
                )
            logger.error(f"Error actualizando institución {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def desactivar(self, id: int) -> Institucion:
        """Desactiva una institución (soft delete)."""
        try:
            institucion = await self.obtener_por_id(id)
            empresas_asignadas = await self._contar_empresas_asignadas(id)
            if empresas_asignadas > 0:
                raise BusinessRuleError(
                    f"No se puede desactivar '{institucion.nombre}' porque tiene "
                    f"{empresas_asignadas} empresa(s) asignada(s)"
                )

            result = self._update_rows({'activo': False}, filters={"id": id})

            if not result.data:
                raise NotFoundError(f"Institución con ID {id} no encontrada")

            logger.info(f"Institución {id} desactivada")
            return Institucion(**result.data[0])

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error desactivando institución {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def activar(self, id: int) -> Institucion:
        """Reactiva una institución."""
        try:
            result = self._update_rows({'activo': True}, filters={"id": id})

            if not result.data:
                raise NotFoundError(f"Institución con ID {id} no encontrada")

            logger.info(f"Institución {id} activada")
            return Institucion(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error activando institución {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # =========================================================================
    # GESTIÓN DE EMPRESAS POR INSTITUCIÓN
    # =========================================================================

    async def obtener_empresas(
        self,
        institucion_id: int,
    ) -> List[InstitucionEmpresa]:
        """Obtiene las empresas que supervisa una institución."""
        try:
            result = self.supabase.table(self.tabla_empresas)\
                .select('*, empresas(nombre_comercial, rfc)')\
                .eq('institucion_id', institucion_id)\
                .execute()

            items = []
            for data in result.data:
                empresa_data = data.get('empresas', {})
                items.append(InstitucionEmpresa(
                    id=data['id'],
                    institucion_id=data['institucion_id'],
                    empresa_id=data['empresa_id'],
                    fecha_creacion=data.get('fecha_creacion'),
                    empresa_nombre=empresa_data.get('nombre_comercial'),
                    empresa_rfc=empresa_data.get('rfc'),
                ))

            return items

        except Exception as e:
            logger.error(
                f"Error obteniendo empresas de institución {institucion_id}: {e}"
            )
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def asignar_empresa(
        self,
        institucion_id: int,
        empresa_id: int,
    ) -> InstitucionEmpresa:
        """Asigna una empresa a una institución."""
        try:
            result = self.supabase.table(self.tabla_empresas)\
                .insert({
                    'institucion_id': institucion_id,
                    'empresa_id': empresa_id,
                })\
                .execute()

            if not result.data:
                raise DatabaseError("No se pudo asignar la empresa")

            logger.info(
                f"Empresa {empresa_id} asignada a institución {institucion_id}"
            )
            return InstitucionEmpresa(**result.data[0])

        except Exception as e:
            error_msg = str(e).lower()
            if "duplicate" in error_msg or "unique" in error_msg:
                raise DuplicateError(
                    f"La empresa {empresa_id} ya está asignada a esta institución",
                    field="empresa_id",
                    value=str(empresa_id),
                )
            logger.error(f"Error asignando empresa a institución: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def quitar_empresa(
        self,
        institucion_id: int,
        empresa_id: int,
    ) -> bool:
        """Remueve una empresa de una institución."""
        try:
            self.supabase.table(self.tabla_empresas)\
                .delete()\
                .eq('institucion_id', institucion_id)\
                .eq('empresa_id', empresa_id)\
                .execute()

            logger.info(
                f"Empresa {empresa_id} removida de institución {institucion_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error removiendo empresa de institución: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_empresas_ids(
        self,
        institucion_id: int,
    ) -> List[int]:
        """
        Obtiene solo los IDs de empresas de una institución.

        Útil para AuthState al determinar acceso del usuario institucional.
        """
        try:
            result = self.supabase.table(self.tabla_empresas)\
                .select('empresa_id')\
                .eq('institucion_id', institucion_id)\
                .execute()

            return [row['empresa_id'] for row in result.data]

        except Exception as e:
            logger.error(
                f"Error obteniendo IDs de empresas para institución {institucion_id}: {e}"
            )
            return []

    async def _contar_empresas_asignadas(self, institucion_id: int) -> int:
        """Cuenta empresas asociadas a la institución."""
        try:
            result = self.supabase.table(self.tabla_empresas)\
                .select('id', count='exact')\
                .eq('institucion_id', institucion_id)\
                .execute()
            return result.count or 0
        except Exception as e:
            logger.error(
                f"Error contando empresas de institución {institucion_id}: {e}"
            )
            raise DatabaseError(f"Error de base de datos: {str(e)}")


# =============================================================================
# SINGLETON
# =============================================================================

institucion_service = InstitucionService()
