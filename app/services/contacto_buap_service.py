"""
Servicio de aplicación para gestión de Contactos BUAP.

Accede directamente a Supabase (sin repository intermedio).
Patrón Direct Access - CRUD simple asociado a sedes.
"""
import logging
from typing import List, Optional

from app.entities import (
    ContactoBuap,
    ContactoBuapCreate,
    ContactoBuapUpdate,
)
from app.core.exceptions import NotFoundError, DatabaseError
from app.services.direct_service import DirectSupabaseService

logger = logging.getLogger(__name__)


class ContactoBuapService(DirectSupabaseService):
    """
    Servicio de aplicación para contactos BUAP.
    Orquesta las operaciones de negocio con acceso directo a Supabase.
    """

    def __init__(self):
        super().__init__("contactos_buap")

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, contacto_id: int) -> ContactoBuap:
        """
        Obtiene un contacto por su ID.

        Raises:
            NotFoundError: Si el contacto no existe
            DatabaseError: Si hay error de BD
        """
        try:
            contacto = self._fetch_one(ContactoBuap, filters={"id": contacto_id})
            if not contacto:
                raise NotFoundError(f"Contacto con ID {contacto_id} no encontrado")
            return contacto

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo contacto {contacto_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener contacto: {str(e)}")

    async def obtener_por_sede(
        self,
        sede_id: int,
        incluir_inactivos: bool = False,
    ) -> List[ContactoBuap]:
        """
        Obtiene todos los contactos de una sede.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self._query().eq('sede_id', sede_id)

            if not incluir_inactivos:
                query = query.eq('estatus', 'ACTIVO')

            query = query.order('es_principal', desc=True).order('nombre')

            return self._fetch_many(ContactoBuap, query)

        except Exception as e:
            logger.error(f"Error obteniendo contactos de sede {sede_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_principal(self, sede_id: int) -> Optional[ContactoBuap]:
        """
        Obtiene el contacto principal de una sede.

        Returns:
            ContactoBuap si existe, None si no

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('sede_id', sede_id)\
                .eq('es_principal', True)\
                .eq('estatus', 'ACTIVO')\
                .limit(1)\
                .execute()

            if not result.data:
                return None

            return ContactoBuap(**result.data[0])

        except Exception as e:
            logger.error(f"Error obteniendo contacto principal de sede {sede_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, contacto_create: ContactoBuapCreate) -> ContactoBuap:
        """
        Crea un nuevo contacto BUAP.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            contacto = ContactoBuap(**contacto_create.model_dump())

            logger.info(f"Creando contacto: {contacto.nombre} para sede {contacto.sede_id}")

            # Si es principal, desmarcar el principal actual
            if contacto.es_principal:
                await self._desmarcar_principal(contacto.sede_id)

            datos = contacto.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'},
            )
            result = self._insert_row(datos)

            if not result.data:
                raise DatabaseError("No se pudo crear el contacto (sin respuesta de BD)")

            return ContactoBuap(**result.data[0])

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error creando contacto: {e}")
            raise DatabaseError(f"Error de base de datos al crear contacto: {str(e)}")

    async def actualizar(self, contacto_id: int, contacto_update: ContactoBuapUpdate) -> ContactoBuap:
        """
        Actualiza un contacto existente.

        Raises:
            NotFoundError: Si el contacto no existe
            DatabaseError: Si hay error de BD
        """
        try:
            contacto_actual = await self.obtener_por_id(contacto_id)
            self._merge_update_model(contacto_actual, contacto_update)

            logger.info(f"Actualizando contacto ID {contacto_id}")

            # Si se marca como principal, desmarcar el actual
            if contacto_actual.es_principal:
                await self._desmarcar_principal(contacto_actual.sede_id, excluir_id=contacto_actual.id)

            datos = contacto_actual.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'},
            )
            result = self._update_rows(datos, filters={"id": contacto_actual.id})

            if not result.data:
                raise NotFoundError(f"Contacto con ID {contacto_actual.id} no encontrado")

            return ContactoBuap(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando contacto {contacto_id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar contacto: {str(e)}")

    async def eliminar(self, contacto_id: int) -> bool:
        """
        Elimina (desactiva) un contacto.

        Raises:
            NotFoundError: Si el contacto no existe
            DatabaseError: Si hay error de BD
        """
        try:
            await self.obtener_por_id(contacto_id)

            logger.info(f"Eliminando (desactivando) contacto ID {contacto_id}")

            result = self._update_rows(
                {'estatus': 'INACTIVO'},
                filters={"id": contacto_id},
            )

            return bool(result.data)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando contacto {contacto_id}: {e}")
            raise DatabaseError(f"Error de base de datos al eliminar contacto: {str(e)}")

    # ==========================================
    # MÉTODOS PRIVADOS
    # ==========================================

    async def _desmarcar_principal(self, sede_id: int, excluir_id: Optional[int] = None) -> None:
        """Desmarca el contacto principal actual de una sede."""
        try:
            query = self.supabase.table(self.tabla)\
                .update({'es_principal': False})\
                .eq('sede_id', sede_id)\
                .eq('es_principal', True)

            if excluir_id:
                query = query.neq('id', excluir_id)

            query.execute()

        except Exception as e:
            logger.error(f"Error desmarcando principal en sede {sede_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")


# ==========================================
# SINGLETON
# ==========================================

contacto_buap_service = ContactoBuapService()
