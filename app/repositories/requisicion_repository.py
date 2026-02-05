"""
Repositorio de Requisiciones - Implementación para Supabase.

Maneja 4 tablas: configuracion_requisicion, requisicion, requisicion_item, requisicion_partida.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: número duplicado)
- DatabaseError: Errores de conexión o infraestructura
- Propagar otras excepciones hacia arriba
"""
from typing import List, Optional
import logging

from app.entities.requisicion import (
    ConfiguracionRequisicion,
    LugarEntrega,
    Requisicion,
    RequisicionItem,
    RequisicionPartida,
)
from app.core.enums import EstadoRequisicion
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class SupabaseRequisicionRepository:
    """Implementación del repositorio usando Supabase."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'requisicion'
        self.tabla_items = 'requisicion_item'
        self.tabla_partidas = 'requisicion_partida'
        self.tabla_config = 'configuracion_requisicion'
        self.tabla_lugares = 'lugar_entrega'

    # ========================
    # REQUISICIÓN PRINCIPAL
    # ========================

    async def obtener_por_id(self, requisicion_id: int) -> Requisicion:
        """
        Obtiene una requisición por su ID, incluyendo items y partidas.

        Raises:
            NotFoundError: Si la requisición no existe
            DatabaseError: Si hay error de BD
        """
        try:
            # Obtener requisición
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('id', requisicion_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Requisición con ID {requisicion_id} no encontrada")

            requisicion_data = result.data[0]

            # Cargar items y partidas
            items = await self.obtener_items(requisicion_id)
            partidas = await self.obtener_partidas(requisicion_id)

            requisicion_data['items'] = [i.model_dump() for i in items]
            requisicion_data['partidas'] = [p.model_dump() for p in partidas]

            return Requisicion(**requisicion_data)
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo requisición {requisicion_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener requisición: {str(e)}")

    async def obtener_por_numero(self, numero: str) -> Optional[Requisicion]:
        """
        Obtiene una requisición por su número único.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('numero_requisicion', numero.upper())\
                .execute()

            if not result.data:
                return None

            requisicion_id = result.data[0]['id']
            return await self.obtener_por_id(requisicion_id)
        except Exception as e:
            logger.error(f"Error obteniendo requisición por número {numero}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_todos(
        self,
        estado: Optional[str] = None,
        tipo_contratacion: Optional[str] = None,
        incluir_canceladas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0,
    ) -> List[Requisicion]:
        """
        Obtiene requisiciones con filtros y paginación.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            # Filtro de estado
            if estado:
                query = query.eq('estado', estado)
            elif not incluir_canceladas:
                query = query.neq('estado', EstadoRequisicion.CANCELADA.value)

            # Filtro de tipo
            if tipo_contratacion:
                query = query.eq('tipo_contratacion', tipo_contratacion)

            # Ordenamiento
            query = query.order('created_at', desc=True)

            # Paginación
            if limite is None:
                limite = 100
            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Requisicion(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo requisiciones: {e}")
            raise DatabaseError(f"Error de base de datos al obtener requisiciones: {str(e)}")

    async def crear(self, requisicion: Requisicion) -> Requisicion:
        """
        Crea una nueva requisición con sus items y partidas.

        Raises:
            DuplicateError: Si el número ya existe
            DatabaseError: Si hay error de BD
        """
        try:
            # Verificar número duplicado
            if await self.existe_numero(requisicion.numero_requisicion):
                raise DuplicateError(
                    f"Número de requisición {requisicion.numero_requisicion} ya existe",
                    field="numero_requisicion",
                    value=requisicion.numero_requisicion,
                )

            # Preparar datos de la requisición (sin items, partidas ni campos auto)
            datos = requisicion.model_dump(
                mode='json',
                exclude={'id', 'created_at', 'updated_at', 'items', 'partidas', 'archivos'},
            )

            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la requisición (sin respuesta de BD)")

            requisicion_id = result.data[0]['id']

            # Crear items
            for item in requisicion.items:
                item_data = item.model_dump(
                    mode='json',
                    exclude={'id', 'created_at', 'requisicion_id', 'archivos'},
                )
                item_data['requisicion_id'] = requisicion_id
                # Calcular subtotal
                if item.precio_unitario_estimado and item.cantidad:
                    item_data['subtotal_estimado'] = str(item.cantidad * item.precio_unitario_estimado)
                self.supabase.table(self.tabla_items).insert(item_data).execute()

            # Crear partidas
            for partida in requisicion.partidas:
                partida_data = partida.model_dump(
                    mode='json',
                    exclude={'id', 'created_at', 'requisicion_id', 'archivos'},
                )
                partida_data['requisicion_id'] = requisicion_id
                self.supabase.table(self.tabla_partidas).insert(partida_data).execute()

            # Retornar requisición completa
            return await self.obtener_por_id(requisicion_id)
        except (DuplicateError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error creando requisición: {e}")
            raise DatabaseError(f"Error de base de datos al crear requisición: {str(e)}")

    async def actualizar(self, requisicion: Requisicion) -> Requisicion:
        """
        Actualiza una requisición existente (sin items ni partidas).

        Raises:
            NotFoundError: Si la requisición no existe
            DatabaseError: Si hay error de BD
        """
        try:
            datos = requisicion.model_dump(
                mode='json',
                exclude={'id', 'created_at', 'updated_at', 'items', 'partidas', 'archivos'},
            )

            result = self.supabase.table(self.tabla)\
                .update(datos)\
                .eq('id', requisicion.id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Requisición con ID {requisicion.id} no encontrada")

            return await self.obtener_por_id(requisicion.id)
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando requisición {requisicion.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar requisición: {str(e)}")

    async def eliminar(self, requisicion_id: int) -> bool:
        """
        Elimina una requisición y sus hijos (CASCADE).

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla)\
                .delete()\
                .eq('id', requisicion_id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error eliminando requisición {requisicion_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def existe_numero(self, numero: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si existe un número de requisición."""
        try:
            query = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('numero_requisicion', numero.upper())
            if excluir_id:
                query = query.neq('id', excluir_id)
            result = query.execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error verificando número: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_siguiente_consecutivo(self, anio: int) -> int:
        """
        Obtiene el siguiente consecutivo para el año dado.
        Busca el último REQ-SA-{AÑO}-XXXX y suma 1.
        """
        try:
            patron = f"REQ-SA-{anio}-%"

            result = self.supabase.table(self.tabla)\
                .select('numero_requisicion')\
                .ilike('numero_requisicion', patron)\
                .order('numero_requisicion', desc=True)\
                .limit(1)\
                .execute()

            if not result.data:
                return 1

            # REQ-SA-2025-0001 -> 0001 -> 1
            ultimo = result.data[0]['numero_requisicion']
            consecutivo_str = ultimo.split('-')[-1]
            return int(consecutivo_str) + 1
        except Exception as e:
            logger.error(f"Error obteniendo consecutivo: {e}")
            return 1

    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        estado: Optional[str] = None,
        tipo_contratacion: Optional[str] = None,
        incluir_canceladas: bool = False,
        limite: int = 50,
        offset: int = 0,
    ) -> List[Requisicion]:
        """
        Busca requisiciones con filtros combinados.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            # Filtro de texto
            if texto and texto.strip():
                query = query.or_(
                    f"numero_requisicion.ilike.%{texto}%,"
                    f"objeto_contratacion.ilike.%{texto}%,"
                    f"dependencia_requirente.ilike.%{texto}%"
                )

            # Filtro de estado
            if estado:
                query = query.eq('estado', estado)
            elif not incluir_canceladas:
                query = query.neq('estado', EstadoRequisicion.CANCELADA.value)

            # Filtro de tipo
            if tipo_contratacion:
                query = query.eq('tipo_contratacion', tipo_contratacion)

            # Ordenamiento y paginación
            query = query.order('created_at', desc=True)
            if limite > 0:
                query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Requisicion(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error buscando requisiciones con filtros: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def cambiar_estado(
        self, requisicion_id: int, nuevo_estado: EstadoRequisicion
    ) -> Requisicion:
        """
        Cambia el estado de una requisición.

        Raises:
            NotFoundError: Si la requisición no existe
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla)\
                .update({'estado': nuevo_estado.value})\
                .eq('id', requisicion_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Requisición con ID {requisicion_id} no encontrada")

            return await self.obtener_por_id(requisicion_id)
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error cambiando estado de requisición {requisicion_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # ========================
    # ITEMS
    # ========================

    async def obtener_items(self, requisicion_id: int) -> List[RequisicionItem]:
        """Obtiene los items de una requisición, ordenados por numero_item."""
        try:
            result = self.supabase.table(self.tabla_items)\
                .select('*')\
                .eq('requisicion_id', requisicion_id)\
                .order('numero_item')\
                .execute()
            return [RequisicionItem(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo items de requisición {requisicion_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear_item(self, requisicion_id: int, item: RequisicionItem) -> RequisicionItem:
        """Crea un item en una requisición."""
        try:
            datos = item.model_dump(mode='json', exclude={'id', 'created_at', 'requisicion_id', 'archivos'})
            datos['requisicion_id'] = requisicion_id

            # Calcular subtotal
            if item.precio_unitario_estimado and item.cantidad:
                datos['subtotal_estimado'] = str(item.cantidad * item.precio_unitario_estimado)

            result = self.supabase.table(self.tabla_items).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el item")

            return RequisicionItem(**result.data[0])
        except Exception as e:
            logger.error(f"Error creando item: {e}")
            raise DatabaseError(f"Error de base de datos al crear item: {str(e)}")

    async def actualizar_item(self, item: RequisicionItem) -> RequisicionItem:
        """Actualiza un item existente."""
        try:
            datos = item.model_dump(mode='json', exclude={'id', 'created_at', 'requisicion_id', 'archivos'})

            # Recalcular subtotal
            if item.precio_unitario_estimado and item.cantidad:
                datos['subtotal_estimado'] = str(item.cantidad * item.precio_unitario_estimado)

            result = self.supabase.table(self.tabla_items)\
                .update(datos)\
                .eq('id', item.id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Item con ID {item.id} no encontrado")

            return RequisicionItem(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando item {item.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar_item(self, item_id: int) -> bool:
        """Elimina un item."""
        try:
            result = self.supabase.table(self.tabla_items)\
                .delete()\
                .eq('id', item_id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error eliminando item {item_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar_items_requisicion(self, requisicion_id: int) -> bool:
        """Elimina todos los items de una requisición."""
        try:
            result = self.supabase.table(self.tabla_items)\
                .delete()\
                .eq('requisicion_id', requisicion_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error eliminando items de requisición {requisicion_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # ========================
    # PARTIDAS
    # ========================

    async def obtener_partidas(self, requisicion_id: int) -> List[RequisicionPartida]:
        """Obtiene las partidas de una requisición."""
        try:
            result = self.supabase.table(self.tabla_partidas)\
                .select('*')\
                .eq('requisicion_id', requisicion_id)\
                .order('id')\
                .execute()
            return [RequisicionPartida(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo partidas de requisición {requisicion_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear_partida(self, requisicion_id: int, partida: RequisicionPartida) -> RequisicionPartida:
        """Crea una partida en una requisición."""
        try:
            datos = partida.model_dump(mode='json', exclude={'id', 'created_at', 'requisicion_id', 'archivos'})
            datos['requisicion_id'] = requisicion_id

            result = self.supabase.table(self.tabla_partidas).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la partida")

            return RequisicionPartida(**result.data[0])
        except Exception as e:
            logger.error(f"Error creando partida: {e}")
            raise DatabaseError(f"Error de base de datos al crear partida: {str(e)}")

    async def actualizar_partida(self, partida: RequisicionPartida) -> RequisicionPartida:
        """Actualiza una partida existente."""
        try:
            datos = partida.model_dump(mode='json', exclude={'id', 'created_at', 'requisicion_id', 'archivos'})

            result = self.supabase.table(self.tabla_partidas)\
                .update(datos)\
                .eq('id', partida.id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Partida con ID {partida.id} no encontrada")

            return RequisicionPartida(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando partida {partida.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar_partida(self, partida_id: int) -> bool:
        """Elimina una partida."""
        try:
            result = self.supabase.table(self.tabla_partidas)\
                .delete()\
                .eq('id', partida_id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error eliminando partida {partida_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar_partidas_requisicion(self, requisicion_id: int) -> bool:
        """Elimina todas las partidas de una requisición."""
        try:
            result = self.supabase.table(self.tabla_partidas)\
                .delete()\
                .eq('requisicion_id', requisicion_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error eliminando partidas de requisición {requisicion_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # ========================
    # CONFIGURACIÓN
    # ========================

    async def obtener_configuracion(self, grupo: Optional[str] = None) -> List[ConfiguracionRequisicion]:
        """Obtiene valores de configuración activos, opcionalmente filtrados por grupo."""
        try:
            query = self.supabase.table(self.tabla_config)\
                .select('*')\
                .eq('activo', True)

            if grupo:
                query = query.eq('grupo', grupo)

            query = query.order('orden')
            result = query.execute()
            return [ConfiguracionRequisicion(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar_configuracion(self, config_id: int, valor: str) -> ConfiguracionRequisicion:
        """Actualiza el valor de una configuración."""
        try:
            result = self.supabase.table(self.tabla_config)\
                .update({'valor': valor})\
                .eq('id', config_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Configuración con ID {config_id} no encontrada")

            return ConfiguracionRequisicion(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando configuración {config_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # ========================
    # LUGARES DE ENTREGA
    # ========================

    async def obtener_lugares_entrega(self) -> List[LugarEntrega]:
        """Obtiene todos los lugares de entrega activos."""
        try:
            result = self.supabase.table(self.tabla_lugares)\
                .select('*')\
                .eq('activo', True)\
                .order('nombre')\
                .execute()
            return [LugarEntrega(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo lugares de entrega: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear_lugar_entrega(self, nombre: str) -> LugarEntrega:
        """Crea un nuevo lugar de entrega."""
        try:
            result = self.supabase.table(self.tabla_lugares)\
                .insert({'nombre': nombre})\
                .execute()
            return LugarEntrega(**result.data[0])
        except Exception as e:
            logger.error(f"Error creando lugar de entrega: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar_lugar_entrega(self, lugar_id: int) -> bool:
        """Elimina (desactiva) un lugar de entrega."""
        try:
            result = self.supabase.table(self.tabla_lugares)\
                .update({'activo': False})\
                .eq('id', lugar_id)\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error eliminando lugar de entrega {lugar_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
