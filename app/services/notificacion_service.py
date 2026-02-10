"""
Servicio para gestion de Notificaciones.

Patron Direct Access (simple CRUD, single table).
Maneja la creacion, consulta y actualizacion de notificaciones
del sistema para usuarios admin y clientes.
"""

import logging
from typing import List, Optional

from app.database import db_manager
from app.core.exceptions import DatabaseError
from app.entities.notificacion import Notificacion, NotificacionCreate

logger = logging.getLogger(__name__)


class NotificacionService:
    """Servicio de notificaciones con acceso directo a Supabase."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'notificaciones'

    async def crear(self, notificacion: NotificacionCreate) -> Notificacion:
        """
        Crea una nueva notificacion.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            datos = notificacion.model_dump(mode='json', exclude_none=True)
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la notificacion")

            return Notificacion(**result.data[0])

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error creando notificacion: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_usuario(
        self,
        usuario_id: str,
        solo_no_leidas: bool = True,
        limite: int = 20,
    ) -> List[Notificacion]:
        """Obtiene notificaciones de un usuario."""
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('usuario_id', usuario_id)

            if solo_no_leidas:
                query = query.eq('leida', False)

            query = query.order('fecha_creacion', desc=True).limit(limite)
            result = query.execute()

            return [Notificacion(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo notificaciones de usuario {usuario_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_empresa(
        self,
        empresa_id: int,
        solo_no_leidas: bool = True,
        limite: int = 20,
    ) -> List[Notificacion]:
        """Obtiene notificaciones de una empresa."""
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('empresa_id', empresa_id)

            if solo_no_leidas:
                query = query.eq('leida', False)

            query = query.order('fecha_creacion', desc=True).limit(limite)
            result = query.execute()

            return [Notificacion(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo notificaciones de empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def marcar_leida(self, notificacion_id: int) -> None:
        """Marca una notificacion como leida."""
        try:
            self.supabase.table(self.tabla)\
                .update({'leida': True})\
                .eq('id', notificacion_id)\
                .execute()

        except Exception as e:
            logger.error(f"Error marcando notificacion {notificacion_id} como leida: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def marcar_todas_leidas(self, usuario_id: str) -> None:
        """Marca todas las notificaciones de un usuario como leidas."""
        try:
            self.supabase.table(self.tabla)\
                .update({'leida': True})\
                .eq('usuario_id', usuario_id)\
                .eq('leida', False)\
                .execute()

        except Exception as e:
            logger.error(f"Error marcando notificaciones como leidas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def marcar_todas_leidas_empresa(self, empresa_id: int) -> None:
        """Marca todas las notificaciones de una empresa como leidas."""
        try:
            self.supabase.table(self.tabla)\
                .update({'leida': True})\
                .eq('empresa_id', empresa_id)\
                .eq('leida', False)\
                .execute()

        except Exception as e:
            logger.error(f"Error marcando notificaciones de empresa como leidas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_admin(
        self,
        solo_no_leidas: bool = True,
        limite: int = 20,
    ) -> List[Notificacion]:
        """Obtiene notificaciones para admin (sin usuario_id ni empresa_id)."""
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .is_('usuario_id', 'null')\
                .is_('empresa_id', 'null')

            if solo_no_leidas:
                query = query.eq('leida', False)

            query = query.order('fecha_creacion', desc=True).limit(limite)
            result = query.execute()

            return [Notificacion(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo notificaciones admin: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_no_leidas_admin(self) -> int:
        """Cuenta notificaciones admin no leidas."""
        try:
            result = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .is_('usuario_id', 'null')\
                .is_('empresa_id', 'null')\
                .eq('leida', False)\
                .execute()

            return result.count or 0

        except Exception as e:
            logger.error(f"Error contando notificaciones admin no leidas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def marcar_todas_leidas_admin(self) -> None:
        """Marca todas las notificaciones admin como leidas."""
        try:
            self.supabase.table(self.tabla)\
                .update({'leida': True})\
                .is_('usuario_id', 'null')\
                .is_('empresa_id', 'null')\
                .eq('leida', False)\
                .execute()

        except Exception as e:
            logger.error(f"Error marcando notificaciones admin como leidas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_no_leidas(self, usuario_id: str) -> int:
        """Cuenta notificaciones no leidas de un usuario."""
        try:
            result = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('usuario_id', usuario_id)\
                .eq('leida', False)\
                .execute()

            return result.count or 0

        except Exception as e:
            logger.error(f"Error contando notificaciones no leidas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_no_leidas_empresa(self, empresa_id: int) -> int:
        """Cuenta notificaciones no leidas de una empresa."""
        try:
            result = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('empresa_id', empresa_id)\
                .eq('leida', False)\
                .execute()

            return result.count or 0

        except Exception as e:
            logger.error(f"Error contando notificaciones de empresa: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # =========================================================================
    # NOTIFICACIONES COMBINADAS (admin + usuario)
    # =========================================================================

    async def obtener_para_usuario_admin(
        self,
        usuario_id: str,
        solo_no_leidas: bool = True,
        limite: int = 20,
    ) -> List[Notificacion]:
        """
        Obtiene notificaciones para un usuario admin.
        Combina: notificaciones admin (sin usuario) + notificaciones personales.
        """
        try:
            # Notificaciones admin (sin usuario_id ni empresa_id)
            query_admin = self.supabase.table(self.tabla)\
                .select('*')\
                .is_('usuario_id', 'null')\
                .is_('empresa_id', 'null')

            if solo_no_leidas:
                query_admin = query_admin.eq('leida', False)

            result_admin = query_admin.order('fecha_creacion', desc=True).limit(limite).execute()

            # Notificaciones personales del usuario
            query_personal = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('usuario_id', usuario_id)

            if solo_no_leidas:
                query_personal = query_personal.eq('leida', False)

            result_personal = query_personal.order('fecha_creacion', desc=True).limit(limite).execute()

            # Combinar y ordenar
            todas = result_admin.data + result_personal.data
            todas.sort(key=lambda x: x.get('fecha_creacion', ''), reverse=True)

            return [Notificacion(**data) for data in todas[:limite]]

        except Exception as e:
            logger.error(f"Error obteniendo notificaciones combinadas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_no_leidas_usuario_admin(self, usuario_id: str) -> int:
        """
        Cuenta notificaciones no leidas para un usuario admin.
        Combina: notificaciones admin + notificaciones personales.
        """
        try:
            # Contar admin
            result_admin = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .is_('usuario_id', 'null')\
                .is_('empresa_id', 'null')\
                .eq('leida', False)\
                .execute()

            # Contar personales
            result_personal = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('usuario_id', usuario_id)\
                .eq('leida', False)\
                .execute()

            return (result_admin.count or 0) + (result_personal.count or 0)

        except Exception as e:
            logger.error(f"Error contando notificaciones combinadas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def marcar_todas_leidas_usuario_admin(self, usuario_id: str) -> None:
        """
        Marca como leidas todas las notificaciones para un usuario admin.
        Incluye: notificaciones admin + notificaciones personales.
        """
        try:
            # Marcar admin
            self.supabase.table(self.tabla)\
                .update({'leida': True})\
                .is_('usuario_id', 'null')\
                .is_('empresa_id', 'null')\
                .eq('leida', False)\
                .execute()

            # Marcar personales
            self.supabase.table(self.tabla)\
                .update({'leida': True})\
                .eq('usuario_id', usuario_id)\
                .eq('leida', False)\
                .execute()

        except Exception as e:
            logger.error(f"Error marcando notificaciones como leidas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")


# =============================================================================
# SINGLETON
# =============================================================================

notificacion_service = NotificacionService()
