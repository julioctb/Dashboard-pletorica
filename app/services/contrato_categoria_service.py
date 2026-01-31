"""
Servicio de aplicación para gestión de Contrato-Categoría.

Maneja la asignación de categorías de puesto a contratos,
incluyendo validaciones de reglas de negocio.

Accede a Supabase directamente (sin repositorio intermedio).

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (contrato_id + categoria_puesto_id)
- DatabaseError: Errores de conexión o infraestructura
- BusinessRuleError: Reglas de negocio violadas
"""
import logging
from typing import List, Optional
from decimal import Decimal

from app.entities.contrato_categoria import (
    ContratoCategoria,
    ContratoCategoriaCreate,
    ContratoCategoriaUpdate,
    ContratoCategoriaResumen,
    ResumenPersonalContrato,
)
from app.database import db_manager
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, BusinessRuleError

logger = logging.getLogger(__name__)


class ContratoCategoriaService:
    """
    Servicio de aplicación para ContratoCategoria.
    Orquesta las operaciones de negocio y accede a Supabase directamente.
    """

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'contrato_categorias'

    # ==========================================
    # ACCESO A DATOS (antes en repositorio)
    # ==========================================

    async def _db_obtener_por_id(self, id: int) -> ContratoCategoria:
        """
        Obtiene una asignación por su ID desde la BD.

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

    async def _db_obtener_por_contrato(self, contrato_id: int) -> List[ContratoCategoria]:
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

    async def _db_obtener_por_contrato_y_categoria(
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

    async def _db_crear(self, contrato_categoria: ContratoCategoria) -> ContratoCategoria:
        """
        Crea una nueva asignación en la BD.

        Raises:
            DuplicateError: Si ya existe la combinación contrato-categoría
            DatabaseError: Si hay error de conexión
        """
        try:
            # Verificar duplicado
            if await self._db_existe_asignacion(
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

        except (DuplicateError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error creando asignación: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _db_actualizar(self, contrato_categoria: ContratoCategoria) -> ContratoCategoria:
        """
        Actualiza una asignación existente en la BD.

        Raises:
            NotFoundError: Si la asignación no existe
            DatabaseError: Si hay error de conexión
        """
        try:
            # Verificar que existe
            await self._db_obtener_por_id(contrato_categoria.id)

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

    async def _db_eliminar(self, id: int) -> bool:
        """
        Elimina una asignación (Hard Delete).

        Raises:
            NotFoundError: Si la asignación no existe
            DatabaseError: Si hay error de conexión
        """
        try:
            # Verificar que existe
            await self._db_obtener_por_id(id)

            result = self.supabase.table(self.tabla).delete().eq('id', id).execute()

            return bool(result.data)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando asignación {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _db_eliminar_por_contrato(self, contrato_id: int) -> int:
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

    async def _db_existe_asignacion(
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

    async def _db_contar_por_contrato(self, contrato_id: int) -> int:
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

    async def _db_contar_por_categoria(self, categoria_puesto_id: int) -> int:
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

    async def _db_obtener_resumen_por_contrato(self, contrato_id: int) -> List[dict]:
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

    async def _db_obtener_totales_por_contrato(self, contrato_id: int) -> dict:
        """
        Calcula los totales de personal y costos para un contrato.

        Returns:
            Dict con total_minimo, total_maximo, costo_minimo_total, costo_maximo_total
        """
        try:
            asignaciones = await self._db_obtener_por_contrato(contrato_id)

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

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, id: int) -> ContratoCategoria:
        """
        Obtiene una asignación por su ID.

        Raises:
            NotFoundError: Si la asignación no existe
            DatabaseError: Si hay error de BD
        """
        return await self._db_obtener_por_id(id)

    async def obtener_categorias_de_contrato(
        self,
        contrato_id: int
    ) -> List[ContratoCategoria]:
        """
        Obtiene todas las categorías asignadas a un contrato.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._db_obtener_por_contrato(contrato_id)

    async def obtener_resumen_de_contrato(
        self,
        contrato_id: int
    ) -> List[ContratoCategoriaResumen]:
        """
        Obtiene resumen con datos de categoría incluidos.

        Returns:
            Lista de ContratoCategoriaResumen ordenada por orden de categoría
        """
        resumen_data = await self._db_obtener_resumen_por_contrato(contrato_id)

        return [
            ContratoCategoriaResumen(
                id=item['id'],
                contrato_id=item['contrato_id'],
                categoria_puesto_id=item['categoria_puesto_id'],
                cantidad_minima=item['cantidad_minima'],
                cantidad_maxima=item['cantidad_maxima'],
                costo_unitario=Decimal(str(item['costo_unitario'])) if item.get('costo_unitario') else None,
                notas=item.get('notas'),
                categoria_clave=item.get('categoria_clave', ''),
                categoria_nombre=item.get('categoria_nombre', ''),
                costo_minimo=Decimal(str(item['cantidad_minima'])) * Decimal(str(item['costo_unitario'])) if item.get('costo_unitario') else None,
                costo_maximo=Decimal(str(item['cantidad_maxima'])) * Decimal(str(item['costo_unitario'])) if item.get('costo_unitario') else None,
            )
            for item in resumen_data
        ]

    async def obtener_categorias_disponibles(
        self,
        contrato_id: int
    ) -> List[dict]:
        """
        Obtiene las categorías que aún no están asignadas al contrato.

        Filtra por el tipo_servicio_id del contrato.

        Returns:
            Lista de categorías disponibles para asignar
        """
        # Importar dentro del método para evitar imports circulares
        from app.services import contrato_service, categoria_puesto_service

        # Obtener el contrato para conocer su tipo_servicio_id
        contrato = await contrato_service.obtener_por_id(contrato_id)

        if not contrato.tipo_servicio_id:
            return []

        # Obtener todas las categorías del tipo de servicio
        todas_categorias = await categoria_puesto_service.obtener_por_tipo_servicio(
            contrato.tipo_servicio_id,
            incluir_inactivas=False
        )

        # Obtener las ya asignadas
        asignadas = await self._db_obtener_por_contrato(contrato_id)
        ids_asignadas = {a.categoria_puesto_id for a in asignadas}

        # Filtrar las disponibles
        disponibles = [
            {
                'id': cat.id,
                'clave': cat.clave,
                'nombre': cat.nombre,
                'orden': cat.orden,
            }
            for cat in todas_categorias
            if cat.id not in ids_asignadas
        ]

        return disponibles

    async def calcular_total_personal(self, contrato_id: int) -> ResumenPersonalContrato:
        """
        Calcula los totales de personal y costos para un contrato.

        Returns:
            ResumenPersonalContrato con totales
        """
        totales = await self._db_obtener_totales_por_contrato(contrato_id)

        return ResumenPersonalContrato(
            contrato_id=contrato_id,
            cantidad_categorias=totales['cantidad_categorias'],
            total_minimo=totales['total_minimo'],
            total_maximo=totales['total_maximo'],
            costo_minimo_total=totales['costo_minimo_total'],
            costo_maximo_total=totales['costo_maximo_total'],
        )

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(
        self,
        contrato_categoria_create: ContratoCategoriaCreate
    ) -> ContratoCategoria:
        """
        Crea una nueva asignación de categoría a contrato.

        Validaciones:
        - El contrato debe existir y tener tiene_personal = True
        - La categoría debe existir y estar activa
        - La categoría debe pertenecer al tipo_servicio_id del contrato

        Raises:
            BusinessRuleError: Si no cumple reglas de negocio
            DuplicateError: Si la categoría ya está asignada
            DatabaseError: Si hay error de BD
        """
        await self._validar_asignacion(
            contrato_categoria_create.contrato_id,
            contrato_categoria_create.categoria_puesto_id
        )

        contrato_categoria = ContratoCategoria(**contrato_categoria_create.model_dump())

        logger.info(
            f"Creando asignación: contrato={contrato_categoria.contrato_id}, "
            f"categoria={contrato_categoria.categoria_puesto_id}"
        )

        return await self._db_crear(contrato_categoria)

    async def actualizar(
        self,
        id: int,
        contrato_categoria_update: ContratoCategoriaUpdate
    ) -> ContratoCategoria:
        """
        Actualiza una asignación existente.

        Solo permite actualizar cantidades, costo y notas.
        No se puede cambiar el contrato_id ni categoria_puesto_id.

        Raises:
            NotFoundError: Si la asignación no existe
            DatabaseError: Si hay error de BD
        """
        asignacion_actual = await self._db_obtener_por_id(id)

        datos_actualizados = contrato_categoria_update.model_dump(exclude_unset=True)

        # Validar coherencia de cantidades si se actualizan
        nueva_min = datos_actualizados.get('cantidad_minima', asignacion_actual.cantidad_minima)
        nueva_max = datos_actualizados.get('cantidad_maxima', asignacion_actual.cantidad_maxima)

        if nueva_max < nueva_min:
            raise BusinessRuleError(
                f"La cantidad máxima ({nueva_max}) debe ser mayor o igual "
                f"a la cantidad mínima ({nueva_min})"
            )

        for campo, valor in datos_actualizados.items():
            if valor is not None:
                setattr(asignacion_actual, campo, valor)

        logger.info(f"Actualizando asignación ID {id}")

        return await self._db_actualizar(asignacion_actual)

    async def eliminar(self, id: int) -> bool:
        """
        Elimina una asignación (Hard Delete).

        Raises:
            NotFoundError: Si la asignación no existe
            DatabaseError: Si hay error de BD
        """
        asignacion = await self._db_obtener_por_id(id)

        logger.info(
            f"Eliminando asignación: contrato={asignacion.contrato_id}, "
            f"categoria={asignacion.categoria_puesto_id}"
        )

        return await self._db_eliminar(id)

    # ==========================================
    # OPERACIONES EN LOTE
    # ==========================================

    async def asignar_categorias(
        self,
        contrato_id: int,
        categorias: List[dict]
    ) -> List[ContratoCategoria]:
        """
        Asigna múltiples categorías a un contrato.

        Args:
            contrato_id: ID del contrato
            categorias: Lista de dicts con:
                - categoria_puesto_id: int
                - cantidad_minima: int
                - cantidad_maxima: int
                - costo_unitario: Decimal (opcional)
                - notas: str (opcional)

        Returns:
            Lista de asignaciones creadas

        Raises:
            BusinessRuleError: Si alguna categoría no cumple reglas
            DuplicateError: Si alguna categoría ya está asignada
        """
        # Validar el contrato una sola vez
        await self._validar_contrato_permite_personal(contrato_id)

        resultados = []

        for cat_data in categorias:
            categoria_puesto_id = cat_data.get('categoria_puesto_id')

            # Validar la categoría
            await self._validar_categoria_para_contrato(contrato_id, categoria_puesto_id)

            # Crear la asignación
            create_data = ContratoCategoriaCreate(
                contrato_id=contrato_id,
                categoria_puesto_id=categoria_puesto_id,
                cantidad_minima=cat_data.get('cantidad_minima', 0),
                cantidad_maxima=cat_data.get('cantidad_maxima', 0),
                costo_unitario=cat_data.get('costo_unitario'),
                notas=cat_data.get('notas'),
            )

            contrato_categoria = ContratoCategoria(**create_data.model_dump())
            resultado = await self._db_crear(contrato_categoria)
            resultados.append(resultado)

        logger.info(f"Asignadas {len(resultados)} categorías al contrato {contrato_id}")

        return resultados

    async def eliminar_por_contrato(self, contrato_id: int) -> int:
        """
        Elimina todas las asignaciones de un contrato.

        Returns:
            Cantidad de registros eliminados
        """
        cantidad = await self._db_eliminar_por_contrato(contrato_id)

        logger.info(f"Eliminadas {cantidad} asignaciones del contrato {contrato_id}")

        return cantidad

    async def reemplazar_categorias(
        self,
        contrato_id: int,
        categorias: List[dict]
    ) -> List[ContratoCategoria]:
        """
        Reemplaza todas las categorías de un contrato.

        Elimina las existentes y crea las nuevas.

        Returns:
            Lista de nuevas asignaciones
        """
        # Eliminar existentes
        await self.eliminar_por_contrato(contrato_id)

        # Crear nuevas
        if not categorias:
            return []

        return await self.asignar_categorias(contrato_id, categorias)

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_asignacion(
        self,
        contrato_id: int,
        categoria_puesto_id: int
    ) -> None:
        """
        Valida que se puede crear la asignación.

        Reglas:
        - El contrato debe existir y tener tiene_personal = True
        - La categoría debe existir y estar activa
        - La categoría debe pertenecer al tipo_servicio_id del contrato
        """
        await self._validar_contrato_permite_personal(contrato_id)
        await self._validar_categoria_para_contrato(contrato_id, categoria_puesto_id)

    async def _validar_contrato_permite_personal(self, contrato_id: int) -> None:
        """
        Valida que el contrato existe y permite personal.
        """
        # Importar dentro del método para evitar imports circulares
        from app.services import contrato_service

        try:
            contrato = await contrato_service.obtener_por_id(contrato_id)
        except NotFoundError:
            raise BusinessRuleError(f"El contrato con ID {contrato_id} no existe")

        if not contrato.tiene_personal:
            raise BusinessRuleError(
                f"El contrato '{contrato.codigo}' no permite asignación de personal "
                f"(tiene_personal = False)"
            )

    async def _validar_categoria_para_contrato(
        self,
        contrato_id: int,
        categoria_puesto_id: int
    ) -> None:
        """
        Valida que la categoría existe, está activa y pertenece al tipo de servicio del contrato.
        """
        # Importar dentro del método para evitar imports circulares
        from app.services import contrato_service, categoria_puesto_service
        from app.core.enums import Estatus

        # Obtener el contrato
        contrato = await contrato_service.obtener_por_id(contrato_id)

        # Obtener la categoría
        try:
            categoria = await categoria_puesto_service.obtener_por_id(categoria_puesto_id)
        except NotFoundError:
            raise BusinessRuleError(f"La categoría de puesto con ID {categoria_puesto_id} no existe")

        # Validar que está activa
        if categoria.estatus != Estatus.ACTIVO:
            raise BusinessRuleError(
                f"La categoría '{categoria.nombre}' no está activa"
            )

        # Validar que pertenece al mismo tipo de servicio
        if contrato.tipo_servicio_id and categoria.tipo_servicio_id != contrato.tipo_servicio_id:
            raise BusinessRuleError(
                f"La categoría '{categoria.nombre}' no pertenece al tipo de servicio del contrato"
            )

    async def contar_contratos_con_categoria(self, categoria_puesto_id: int) -> int:
        """
        Cuenta cuántos contratos usan una categoría específica.

        Útil para validar si se puede eliminar una categoría.
        """
        return await self._db_contar_por_categoria(categoria_puesto_id)


# ==========================================
# SINGLETON
# ==========================================

contrato_categoria_service = ContratoCategoriaService()
