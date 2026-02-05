"""
Repositorio de Historial Laboral - Implementacion para Supabase.

Maneja operaciones de base de datos para el historial laboral,
incluyendo JOINs con empleados, empresas y plazas.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un registro
- DatabaseError: Errores de conexion o infraestructura
"""
import logging
from typing import List, Optional
from datetime import date

from app.core.exceptions import NotFoundError, DatabaseError
from app.entities.historial_laboral import (
    HistorialLaboral,
    HistorialLaboralInterno,
)

logger = logging.getLogger(__name__)


class SupabaseHistorialLaboralRepository:
    """Implementacion del repositorio de historial laboral usando Supabase."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'historial_laboral'

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, historial_id: int) -> HistorialLaboral:
        """
        Obtiene un registro por ID.

        Raises:
            NotFoundError: Si el registro no existe
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('id', historial_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Historial con ID {historial_id} no encontrado")

            return HistorialLaboral(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo historial {historial_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_empleado_con_join(
        self,
        empleado_id: int,
        limite: int = 50
    ) -> List[dict]:
        """
        Obtiene el historial de un empleado con datos enriquecidos (JOIN).

        Returns:
            Lista de dicts con datos del historial y empleado

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('''
                    *,
                    empleados!inner(id, clave, nombre, apellido_paterno, apellido_materno, empresas(nombre_comercial))
                ''')\
                .eq('empleado_id', empleado_id)\
                .order('fecha_inicio', desc=True)\
                .limit(limite)\
                .execute()

            return result.data

        except Exception as e:
            logger.error(f"Error obteniendo historial de empleado {empleado_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_todos_con_join(
        self,
        empleado_id: Optional[int] = None,
        limite: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """
        Obtiene registros con filtros opcionales y JOINs.

        Returns:
            Lista de dicts con datos del historial y empleado

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('''
                    *,
                    empleados!inner(id, clave, nombre, apellido_paterno, apellido_materno, empresas(nombre_comercial))
                ''')

            if empleado_id:
                query = query.eq('empleado_id', empleado_id)

            query = query.order('fecha_inicio', desc=True)\
                .range(offset, offset + limite - 1)

            result = query.execute()
            return result.data

        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar(self, empleado_id: Optional[int] = None) -> int:
        """
        Cuenta registros con filtros.

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('id', count='exact')

            if empleado_id:
                query = query.eq('empleado_id', empleado_id)

            result = query.execute()
            return result.count or 0

        except Exception as e:
            logger.error(f"Error contando historial: {e}")
            return 0

    async def obtener_registro_activo(self, empleado_id: int) -> Optional[HistorialLaboral]:
        """
        Obtiene el registro activo (sin fecha_fin) de un empleado.

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('empleado_id', empleado_id)\
                .is_('fecha_fin', 'null')\
                .execute()

            if not result.data:
                return None

            return HistorialLaboral(**result.data[0])

        except Exception as e:
            logger.error(f"Error obteniendo registro activo: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_datos_plaza(self, plaza_id: int) -> Optional[dict]:
        """Obtiene datos enriquecidos de una plaza via Supabase JOIN."""
        try:
            result = self.supabase.table('plazas')\
                .select('''
                    id, numero_plaza,
                    contrato_categorias!inner(
                        id,
                        categorias_puesto!inner(nombre),
                        contratos!inner(codigo, empresas!inner(nombre_comercial))
                    )
                ''')\
                .eq('id', plaza_id)\
                .execute()

            if not result.data:
                return None

            data = result.data[0]
            cc = data.get('contrato_categorias', {})
            cat = cc.get('categorias_puesto', {})
            contrato = cc.get('contratos', {})
            empresa = contrato.get('empresas', {})

            return {
                'numero_plaza': data.get('numero_plaza'),
                'categoria_nombre': cat.get('nombre'),
                'contrato_codigo': contrato.get('codigo'),
                'empresa_nombre': empresa.get('nombre_comercial'),
            }

        except Exception as e:
            logger.error(f"Error obteniendo datos de plaza {plaza_id}: {e}")
            return None

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, datos: HistorialLaboralInterno) -> HistorialLaboral:
        """
        Crea un nuevo registro de historial.

        Raises:
            DatabaseError: Si no se pudo crear el registro
        """
        try:
            data_dict = datos.model_dump(mode='json')

            result = self.supabase.table(self.tabla)\
                .insert(data_dict)\
                .execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el registro")

            return HistorialLaboral(**result.data[0])

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error creando historial: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def cerrar_registro(
        self,
        historial_id: int,
        fecha_fin: date
    ) -> HistorialLaboral:
        """
        Cierra un registro estableciendo fecha_fin.

        Raises:
            NotFoundError: Si el registro no existe
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla)\
                .update({'fecha_fin': fecha_fin.isoformat()})\
                .eq('id', historial_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Historial {historial_id} no encontrado")

            return HistorialLaboral(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error cerrando registro: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
