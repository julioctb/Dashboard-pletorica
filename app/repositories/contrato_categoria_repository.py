"""
Repositorio de ContratoCategoria - Interface e implementación para Supabase.

Tabla intermedia que relaciona Contratos con Categorías de Puesto.
Usa Hard Delete (no soft delete) porque es una tabla de relación sin historial.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (contrato_id + categoria_puesto_id)
- DatabaseError: Errores de conexión o infraestructura
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal
import logging

from app.entities.contrato_categoria import ContratoCategoria
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class IContratoCategoriaRepository(ABC):
    """Interface del repositorio de ContratoCategoria"""

    @abstractmethod
    async def obtener_por_id(self, id: int) -> ContratoCategoria:
        """Obtiene una asignación por su ID"""
        pass

    @abstractmethod
    async def obtener_por_contrato(self, contrato_id: int) -> List[ContratoCategoria]:
        """Obtiene todas las categorías asignadas a un contrato"""
        pass

    @abstractmethod
    async def obtener_por_contrato_y_categoria(
        self,
        contrato_id: int,
        categoria_puesto_id: int
    ) -> Optional[ContratoCategoria]:
        """Obtiene una asignación específica por contrato y categoría"""
        pass

    @abstractmethod
    async def crear(self, contrato_categoria: ContratoCategoria) -> ContratoCategoria:
        """Crea una nueva asignación"""
        pass

    @abstractmethod
    async def actualizar(self, contrato_categoria: ContratoCategoria) -> ContratoCategoria:
        """Actualiza una asignación existente"""
        pass

    @abstractmethod
    async def eliminar(self, id: int) -> bool:
        """Elimina una asignación (Hard Delete)"""
        pass

    @abstractmethod
    async def eliminar_por_contrato(self, contrato_id: int) -> int:
        """Elimina todas las asignaciones de un contrato"""
        pass

    @abstractmethod
    async def existe_asignacion(
        self,
        contrato_id: int,
        categoria_puesto_id: int,
        excluir_id: Optional[int] = None
    ) -> bool:
        """Verifica si ya existe la asignación"""
        pass

    @abstractmethod
    async def contar_por_contrato(self, contrato_id: int) -> int:
        """Cuenta las categorías asignadas a un contrato"""
        pass

    @abstractmethod
    async def contar_por_categoria(self, categoria_puesto_id: int) -> int:
        """Cuenta los contratos que usan una categoría"""
        pass

    @abstractmethod
    async def obtener_resumen_por_contrato(self, contrato_id: int) -> List[dict]:
        """Obtiene resumen con datos de categoría incluidos"""
        pass


class SupabaseContratoCategoriaRepository(IContratoCategoriaRepository):
    """Implementación del repositorio usando Supabase"""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'contrato_categorias'

    async def obtener_por_id(self, id: int) -> ContratoCategoria:
        """
        Obtiene una asignación por su ID.

        Raises:
            NotFoundError: Si la asignación no existe
            DatabaseError: Si hay error de conexión
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', id).execute()

            if not result.data:
                raise NotFoundError(f"Asignación con ID {id} no encontrada")

            return ContratoCategoria(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo asignación {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_contrato(self, contrato_id: int) -> List[ContratoCategoria]:
        """
        Obtiene todas las categorías asignadas a un contrato.

        Returns:
            Lista ordenada por categoria_puesto_id
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_id', contrato_id)\
                .order('categoria_puesto_id', desc=False)\
                .execute()

            return [ContratoCategoria(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo categorías del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_contrato_y_categoria(
        self,
        contrato_id: int,
        categoria_puesto_id: int
    ) -> Optional[ContratoCategoria]:
        """
        Obtiene una asignación específica por contrato y categoría.

        Returns:
            La asignación si existe, None si no
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_id', contrato_id)\
                .eq('categoria_puesto_id', categoria_puesto_id)\
                .execute()

            if not result.data:
                return None

            return ContratoCategoria(**result.data[0])

        except Exception as e:
            logger.error(f"Error buscando asignación contrato={contrato_id}, categoria={categoria_puesto_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, contrato_categoria: ContratoCategoria) -> ContratoCategoria:
        """
        Crea una nueva asignación.

        Raises:
            DuplicateError: Si ya existe la combinación contrato-categoría
            DatabaseError: Si hay error de conexión
        """
        try:
            # Verificar duplicado
            if await self.existe_asignacion(
                contrato_categoria.contrato_id,
                contrato_categoria.categoria_puesto_id
            ):
                raise DuplicateError(
                    f"La categoría ya está asignada a este contrato",
                    field="categoria_puesto_id",
                    value=str(contrato_categoria.categoria_puesto_id)
                )

            datos = contrato_categoria.model_dump(
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'}
            )

            # Convertir Decimal a float para JSON
            if datos.get('costo_unitario') is not None:
                datos['costo_unitario'] = float(datos['costo_unitario'])

            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la asignación")

            return ContratoCategoria(**result.data[0])

        except DuplicateError:
            raise
        except Exception as e:
            logger.error(f"Error creando asignación: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar(self, contrato_categoria: ContratoCategoria) -> ContratoCategoria:
        """
        Actualiza una asignación existente.

        Raises:
            NotFoundError: Si la asignación no existe
            DatabaseError: Si hay error de conexión
        """
        try:
            # Verificar que existe
            await self.obtener_por_id(contrato_categoria.id)

            datos = contrato_categoria.model_dump(
                exclude={'id', 'contrato_id', 'categoria_puesto_id', 'fecha_creacion', 'fecha_actualizacion'}
            )

            # Convertir Decimal a float para JSON
            if datos.get('costo_unitario') is not None:
                datos['costo_unitario'] = float(datos['costo_unitario'])

            result = self.supabase.table(self.tabla)\
                .update(datos)\
                .eq('id', contrato_categoria.id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Asignación con ID {contrato_categoria.id} no encontrada")

            return ContratoCategoria(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando asignación {contrato_categoria.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar(self, id: int) -> bool:
        """
        Elimina una asignación (Hard Delete).

        Raises:
            NotFoundError: Si la asignación no existe
            DatabaseError: Si hay error de conexión
        """
        try:
            # Verificar que existe
            await self.obtener_por_id(id)

            result = self.supabase.table(self.tabla).delete().eq('id', id).execute()

            return bool(result.data)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando asignación {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar_por_contrato(self, contrato_id: int) -> int:
        """
        Elimina todas las asignaciones de un contrato.

        Returns:
            Cantidad de registros eliminados
        """
        try:
            result = self.supabase.table(self.tabla)\
                .delete()\
                .eq('contrato_id', contrato_id)\
                .execute()

            return len(result.data) if result.data else 0

        except Exception as e:
            logger.error(f"Error eliminando asignaciones del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def existe_asignacion(
        self,
        contrato_id: int,
        categoria_puesto_id: int,
        excluir_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si ya existe la asignación contrato-categoría.
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('contrato_id', contrato_id)\
                .eq('categoria_puesto_id', categoria_puesto_id)

            if excluir_id:
                query = query.neq('id', excluir_id)

            result = query.execute()
            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error verificando asignación: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_por_contrato(self, contrato_id: int) -> int:
        """
        Cuenta las categorías asignadas a un contrato.
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('contrato_id', contrato_id)\
                .execute()

            return result.count if result.count is not None else 0

        except Exception as e:
            logger.error(f"Error contando categorías del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_por_categoria(self, categoria_puesto_id: int) -> int:
        """
        Cuenta los contratos que usan una categoría.
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('categoria_puesto_id', categoria_puesto_id)\
                .execute()

            return result.count if result.count is not None else 0

        except Exception as e:
            logger.error(f"Error contando contratos de la categoría {categoria_puesto_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_por_contrato(self, contrato_id: int) -> List[dict]:
        """
        Obtiene resumen con datos de categoría incluidos (JOIN).

        Returns:
            Lista de dicts con datos de la asignación y de la categoría
        """
        try:
            # Supabase permite hacer joins con la sintaxis de select
            result = self.supabase.table(self.tabla)\
                .select(
                    '*, '
                    'categorias_puesto:categoria_puesto_id(id, clave, nombre, orden)'
                )\
                .eq('contrato_id', contrato_id)\
                .execute()

            resumen = []
            for data in result.data:
                categoria_data = data.pop('categorias_puesto', {}) or {}
                item = {
                    **data,
                    'categoria_clave': categoria_data.get('clave', ''),
                    'categoria_nombre': categoria_data.get('nombre', ''),
                    'categoria_orden': categoria_data.get('orden', 0),
                }
                resumen.append(item)

            # Ordenar por orden de categoría
            resumen.sort(key=lambda x: (x.get('categoria_orden', 0), x.get('categoria_nombre', '')))

            return resumen

        except Exception as e:
            logger.error(f"Error obteniendo resumen del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_totales_por_contrato(self, contrato_id: int) -> dict:
        """
        Calcula los totales de personal y costos para un contrato.

        Returns:
            Dict con total_minimo, total_maximo, costo_minimo_total, costo_maximo_total
        """
        try:
            asignaciones = await self.obtener_por_contrato(contrato_id)

            total_minimo = 0
            total_maximo = 0
            costo_minimo_total = Decimal('0')
            costo_maximo_total = Decimal('0')
            tiene_costos = False

            for a in asignaciones:
                total_minimo += a.cantidad_minima
                total_maximo += a.cantidad_maxima

                if a.costo_unitario is not None:
                    tiene_costos = True
                    costo_minimo_total += a.cantidad_minima * a.costo_unitario
                    costo_maximo_total += a.cantidad_maxima * a.costo_unitario

            return {
                'cantidad_categorias': len(asignaciones),
                'total_minimo': total_minimo,
                'total_maximo': total_maximo,
                'costo_minimo_total': costo_minimo_total if tiene_costos else None,
                'costo_maximo_total': costo_maximo_total if tiene_costos else None,
            }

        except Exception as e:
            logger.error(f"Error calculando totales del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
