"""
Repositorio de Contrato-Categoria - Implementacion para Supabase.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (contrato_id + categoria_puesto_id)
- DatabaseError: Errores de conexion o infraestructura
"""
import logging
from typing import List, Optional
from decimal import Decimal

from app.domain.models.contrato_categoria import ContratoCategoria
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class SupabaseContratoCategoriaRepository:
    """Implementacion del repositorio de contrato-categoria usando Supabase."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'contrato_categorias'

    def _es_error_tabla_faltante(self, error: Exception) -> bool:
        mensaje = str(error)
        return "PGRST205" in mensaje and self.tabla in mensaje

    def _database_error_tabla_faltante(self) -> DatabaseError:
        return DatabaseError(
            "La tabla 'contrato_categorias' no existe en la base de datos actual. "
            "Aplique la migracion '050_restore_contrato_categorias_planning.sql' "
            "antes de usar categorias por contrato."
        )

    async def obtener_por_id(self, id: int) -> ContratoCategoria:
        """
        Obtiene una asignacion por su ID.

        Raises:
            NotFoundError: Si la asignacion no existe
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', id).execute()

            if not result.data:
                raise NotFoundError(f"Asignacion con ID {id} no encontrada")

            return ContratoCategoria(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo asignacion {id}: {e}")
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_contrato(self, contrato_id: int) -> List[ContratoCategoria]:
        """
        Obtiene todas las categorias asignadas a un contrato.

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
            logger.error(f"Error obteniendo categorias del contrato {contrato_id}: {e}")
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_contrato_y_categoria(
        self,
        contrato_id: int,
        categoria_puesto_id: int
    ) -> Optional[ContratoCategoria]:
        """
        Obtiene una asignacion especifica por contrato y categoria.

        Returns:
            La asignacion si existe, None si no
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
            logger.error(f"Error buscando asignacion contrato={contrato_id}, categoria={categoria_puesto_id}: {e}")
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, contrato_categoria: ContratoCategoria) -> ContratoCategoria:
        """
        Crea una nueva asignacion.

        Raises:
            DuplicateError: Si ya existe la combinacion contrato-categoria
            DatabaseError: Si hay error de conexion
        """
        try:
            if await self.existe_asignacion(
                contrato_categoria.contrato_id,
                contrato_categoria.categoria_puesto_id
            ):
                raise DuplicateError(
                    "La categoria ya esta asignada a este contrato",
                    field="categoria_puesto_id",
                    value=str(contrato_categoria.categoria_puesto_id)
                )

            datos = contrato_categoria.model_dump(
                mode="json",
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'}
            )

            # Convertir Decimal serializado a float para persistencia numérica
            for campo in ('costo_unitario', 'costo_contractual', 'sueldo_base'):
                if datos.get(campo) is not None:
                    datos[campo] = float(datos[campo])

            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la asignacion")

            return ContratoCategoria(**result.data[0])

        except (DuplicateError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error creando asignacion: {e}")
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar(self, contrato_categoria: ContratoCategoria) -> ContratoCategoria:
        """
        Actualiza una asignacion existente.

        Raises:
            NotFoundError: Si la asignacion no existe
            DatabaseError: Si hay error de conexion
        """
        try:
            await self.obtener_por_id(contrato_categoria.id)

            datos = contrato_categoria.model_dump(
                mode="json",
                exclude={'id', 'contrato_id', 'categoria_puesto_id', 'fecha_creacion', 'fecha_actualizacion'}
            )

            # Convertir Decimal serializado a float para persistencia numérica
            for campo in ('costo_unitario', 'costo_contractual', 'sueldo_base'):
                if datos.get(campo) is not None:
                    datos[campo] = float(datos[campo])

            result = self.supabase.table(self.tabla)\
                .update(datos)\
                .eq('id', contrato_categoria.id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Asignacion con ID {contrato_categoria.id} no encontrada")

            return ContratoCategoria(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando asignacion {contrato_categoria.id}: {e}")
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar(self, id: int) -> bool:
        """
        Elimina una asignacion (Hard Delete).

        Raises:
            NotFoundError: Si la asignacion no existe
            DatabaseError: Si hay error de conexion
        """
        try:
            await self.obtener_por_id(id)

            result = self.supabase.table(self.tabla).delete().eq('id', id).execute()

            return bool(result.data)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando asignacion {id}: {e}")
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
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
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def existe_asignacion(
        self,
        contrato_id: int,
        categoria_puesto_id: int,
        excluir_id: Optional[int] = None
    ) -> bool:
        """Verifica si ya existe la asignacion contrato-categoria."""
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
            logger.error(f"Error verificando asignacion: {e}")
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_por_contrato(self, contrato_id: int) -> int:
        """Cuenta las categorias asignadas a un contrato."""
        try:
            result = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('contrato_id', contrato_id)\
                .execute()

            return result.count if result.count is not None else 0

        except Exception as e:
            logger.error(f"Error contando categorias del contrato {contrato_id}: {e}")
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_por_categoria(self, categoria_puesto_id: int) -> int:
        """Cuenta los contratos que usan una categoria."""
        try:
            result = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('categoria_puesto_id', categoria_puesto_id)\
                .execute()

            return result.count if result.count is not None else 0

        except Exception as e:
            logger.error(f"Error contando contratos de la categoria {categoria_puesto_id}: {e}")
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_por_categorias(self, categorias_puesto_ids: list[int]) -> dict[int, int]:
        """Cuenta en lote cuántos contratos usan cada categoría."""
        ids = [int(categoria_id or 0) for categoria_id in categorias_puesto_ids if int(categoria_id or 0) > 0]
        if not ids:
            return {}

        try:
            result = (
                self.supabase.table(self.tabla)
                .select("categoria_puesto_id")
                .in_("categoria_puesto_id", ids)
                .execute()
            )
            conteos = {categoria_id: 0 for categoria_id in ids}
            for fila in result.data or []:
                categoria_id = int(fila.get("categoria_puesto_id") or 0)
                if categoria_id <= 0:
                    continue
                conteos[categoria_id] = conteos.get(categoria_id, 0) + 1
            return conteos
        except Exception as e:
            logger.error("Error contando contratos por categorías %s: %s", ids, e)
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_por_contrato(self, contrato_id: int) -> List[dict]:
        """
        Obtiene resumen con datos de categoria incluidos (JOIN).

        Returns:
            Lista de dicts con datos de la asignacion y de la categoria
        """
        try:
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
                    'categoria_nombre': data.get('nombre') or categoria_data.get('nombre', ''),
                    'categoria_nombre_catalogo': categoria_data.get('nombre', ''),
                    'categoria_orden': categoria_data.get('orden', 0),
                }
                resumen.append(item)

            resumen.sort(key=lambda x: (x.get('categoria_orden', 0), x.get('categoria_nombre', '')))

            return resumen

        except Exception as e:
            logger.error(f"Error obteniendo resumen del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_nombres_por_empresa(self, empresa_id: int) -> List[str]:
        """
        Obtiene los nombres distintos de categorias ya usados por los contratos
        de una empresa. Sirve para sugerencias de autocompletado al crear una
        categoria nueva.
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .select('nombre, contratos!inner(empresa_id)')
                .eq('contratos.empresa_id', empresa_id)
                .execute()
            )
            vistos: set[str] = set()
            nombres: List[str] = []
            for fila in result.data or []:
                raw = str(fila.get('nombre') or '').strip()
                if not raw:
                    continue
                clave = raw.upper()
                if clave in vistos:
                    continue
                vistos.add(clave)
                nombres.append(raw)
            nombres.sort(key=lambda n: n.lower())
            return nombres
        except Exception as e:
            logger.error(
                f"Error obteniendo nombres de categorias de empresa {empresa_id}: {e}"
            )
            if self._es_error_tabla_faltante(e):
                raise self._database_error_tabla_faltante()
            return []

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
