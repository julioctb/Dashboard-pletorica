"""
Repositorio de Plaza - Interface e implementación para Supabase.

Una Plaza es una instancia individual de un puesto dentro de un ContratoCategoría.
Usa Soft Delete (estatus = CANCELADA) para mantener historial.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (contrato_categoria_id + numero_plaza)
- DatabaseError: Errores de conexión o infraestructura
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal
import logging

from app.entities.plaza import Plaza
from app.core.enums import EstatusPlaza
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class IPlazaRepository(ABC):
    """Interface del repositorio de Plaza"""

    @abstractmethod
    async def obtener_por_id(self, id: int) -> Plaza:
        """Obtiene una plaza por su ID"""
        pass

    @abstractmethod
    async def obtener_por_contrato_categoria(
        self,
        contrato_categoria_id: int,
        incluir_canceladas: bool = False
    ) -> List[Plaza]:
        """Obtiene todas las plazas de una ContratoCategoria"""
        pass

    @abstractmethod
    async def obtener_por_contrato(
        self,
        contrato_id: int,
        incluir_canceladas: bool = False
    ) -> List[Plaza]:
        """Obtiene todas las plazas de un contrato (a través de contrato_categorias)"""
        pass

    @abstractmethod
    async def obtener_vacantes_por_contrato_categoria(
        self,
        contrato_categoria_id: int
    ) -> List[Plaza]:
        """Obtiene las plazas vacantes de una ContratoCategoria"""
        pass

    @abstractmethod
    async def crear(self, plaza: Plaza) -> Plaza:
        """Crea una nueva plaza"""
        pass

    @abstractmethod
    async def actualizar(self, plaza: Plaza) -> Plaza:
        """Actualiza una plaza existente"""
        pass

    @abstractmethod
    async def cancelar(self, id: int) -> Plaza:
        """Cancela una plaza (Soft Delete)"""
        pass

    @abstractmethod
    async def existe_numero_plaza(
        self,
        contrato_categoria_id: int,
        numero_plaza: int,
        excluir_id: Optional[int] = None
    ) -> bool:
        """Verifica si ya existe el número de plaza en la categoría"""
        pass

    @abstractmethod
    async def contar_por_contrato_categoria(
        self,
        contrato_categoria_id: int,
        estatus: Optional[EstatusPlaza] = None
    ) -> int:
        """Cuenta las plazas de una ContratoCategoria"""
        pass

    @abstractmethod
    async def contar_por_contrato(
        self,
        contrato_id: int,
        estatus: Optional[EstatusPlaza] = None
    ) -> int:
        """Cuenta las plazas de un contrato"""
        pass

    @abstractmethod
    async def obtener_siguiente_numero_plaza(
        self,
        contrato_categoria_id: int
    ) -> int:
        """Obtiene el siguiente número de plaza disponible"""
        pass

    @abstractmethod
    async def obtener_resumen_por_contrato(self, contrato_id: int) -> List[dict]:
        """Obtiene resumen con datos de contrato y categoría incluidos"""
        pass

    @abstractmethod
    async def obtener_totales_por_contrato(self, contrato_id: int) -> dict:
        """Calcula totales de plazas por estatus para un contrato"""
        pass


class SupabasePlazaRepository(IPlazaRepository):
    """Implementación del repositorio usando Supabase"""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'plazas'

    async def obtener_por_id(self, id: int) -> Plaza:
        """
        Obtiene una plaza por su ID.

        Raises:
            NotFoundError: Si la plaza no existe
            DatabaseError: Si hay error de conexión
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', id).execute()

            if not result.data:
                raise NotFoundError(f"Plaza con ID {id} no encontrada")

            return Plaza(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo plaza {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_contrato_categoria(
        self,
        contrato_categoria_id: int,
        incluir_canceladas: bool = False
    ) -> List[Plaza]:
        """
        Obtiene todas las plazas de una ContratoCategoria.

        Returns:
            Lista ordenada por numero_plaza
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_categoria_id', contrato_categoria_id)

            if not incluir_canceladas:
                query = query.neq('estatus', EstatusPlaza.CANCELADA.value)

            query = query.order('numero_plaza', desc=False)

            result = query.execute()

            return [Plaza(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo plazas de contrato_categoria {contrato_categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_contrato(
        self,
        contrato_id: int,
        incluir_canceladas: bool = False
    ) -> List[Plaza]:
        """
        Obtiene todas las plazas de un contrato.

        Hace JOIN con contrato_categorias para obtener las plazas del contrato.
        """
        try:
            # Primero obtenemos los IDs de contrato_categorias del contrato
            result_cc = self.supabase.table('contrato_categorias')\
                .select('id')\
                .eq('contrato_id', contrato_id)\
                .execute()

            if not result_cc.data:
                return []

            cc_ids = [cc['id'] for cc in result_cc.data]

            # Luego obtenemos las plazas
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .in_('contrato_categoria_id', cc_ids)

            if not incluir_canceladas:
                query = query.neq('estatus', EstatusPlaza.CANCELADA.value)

            query = query.order('contrato_categoria_id', desc=False)\
                .order('numero_plaza', desc=False)

            result = query.execute()

            return [Plaza(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo plazas del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_vacantes_por_contrato_categoria(
        self,
        contrato_categoria_id: int
    ) -> List[Plaza]:
        """
        Obtiene las plazas vacantes de una ContratoCategoria.
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_categoria_id', contrato_categoria_id)\
                .eq('estatus', EstatusPlaza.VACANTE.value)\
                .order('numero_plaza', desc=False)\
                .execute()

            return [Plaza(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo plazas vacantes de contrato_categoria {contrato_categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, plaza: Plaza) -> Plaza:
        """
        Crea una nueva plaza.

        Raises:
            DuplicateError: Si ya existe el numero_plaza en la categoría
            DatabaseError: Si hay error de conexión
        """
        try:
            # Verificar duplicado de numero_plaza
            if await self.existe_numero_plaza(
                plaza.contrato_categoria_id,
                plaza.numero_plaza
            ):
                raise DuplicateError(
                    f"Ya existe la plaza #{plaza.numero_plaza} en esta categoría",
                    field="numero_plaza",
                    value=str(plaza.numero_plaza)
                )

            datos = plaza.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'}
            )

            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la plaza")

            return Plaza(**result.data[0])

        except DuplicateError:
            raise
        except Exception as e:
            logger.error(f"Error creando plaza: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar(self, plaza: Plaza) -> Plaza:
        """
        Actualiza una plaza existente.

        Raises:
            NotFoundError: Si la plaza no existe
            DatabaseError: Si hay error de conexión
        """
        try:
            # Verificar que existe
            await self.obtener_por_id(plaza.id)

            datos = plaza.model_dump(
                mode='json',
                exclude={'id', 'contrato_categoria_id', 'numero_plaza', 'fecha_creacion', 'fecha_actualizacion'}
            )

            result = self.supabase.table(self.tabla)\
                .update(datos)\
                .eq('id', plaza.id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Plaza con ID {plaza.id} no encontrada")

            return Plaza(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando plaza {plaza.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def cancelar(self, id: int) -> Plaza:
        """
        Cancela una plaza (Soft Delete).

        Raises:
            NotFoundError: Si la plaza no existe
            DatabaseError: Si hay error de conexión
        """
        try:
            plaza = await self.obtener_por_id(id)

            result = self.supabase.table(self.tabla)\
                .update({'estatus': EstatusPlaza.CANCELADA.value, 'empleado_id': None})\
                .eq('id', id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Plaza con ID {id} no encontrada")

            return Plaza(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error cancelando plaza {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def existe_numero_plaza(
        self,
        contrato_categoria_id: int,
        numero_plaza: int,
        excluir_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si ya existe el número de plaza en la categoría.
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('contrato_categoria_id', contrato_categoria_id)\
                .eq('numero_plaza', numero_plaza)

            if excluir_id:
                query = query.neq('id', excluir_id)

            result = query.execute()
            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error verificando numero_plaza: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_por_contrato_categoria(
        self,
        contrato_categoria_id: int,
        estatus: Optional[EstatusPlaza] = None
    ) -> int:
        """
        Cuenta las plazas de una ContratoCategoria.
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('contrato_categoria_id', contrato_categoria_id)

            if estatus:
                query = query.eq('estatus', estatus.value)

            result = query.execute()

            return result.count if result.count is not None else 0

        except Exception as e:
            logger.error(f"Error contando plazas de contrato_categoria {contrato_categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_por_contrato(
        self,
        contrato_id: int,
        estatus: Optional[EstatusPlaza] = None
    ) -> int:
        """
        Cuenta las plazas de un contrato.
        """
        try:
            # Primero obtenemos los IDs de contrato_categorias del contrato
            result_cc = self.supabase.table('contrato_categorias')\
                .select('id')\
                .eq('contrato_id', contrato_id)\
                .execute()

            if not result_cc.data:
                return 0

            cc_ids = [cc['id'] for cc in result_cc.data]

            query = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .in_('contrato_categoria_id', cc_ids)

            if estatus:
                query = query.eq('estatus', estatus.value)

            result = query.execute()

            return result.count if result.count is not None else 0

        except Exception as e:
            logger.error(f"Error contando plazas del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_siguiente_numero_plaza(
        self,
        contrato_categoria_id: int
    ) -> int:
        """
        Obtiene el siguiente número de plaza disponible.
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('numero_plaza')\
                .eq('contrato_categoria_id', contrato_categoria_id)\
                .order('numero_plaza', desc=True)\
                .limit(1)\
                .execute()

            if not result.data:
                return 1

            return result.data[0]['numero_plaza'] + 1

        except Exception as e:
            logger.error(f"Error obteniendo siguiente numero_plaza: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_por_contrato(self, contrato_id: int) -> List[dict]:
        """
        Obtiene resumen con datos de contrato, categoría y empleado incluidos (JOIN).

        Returns:
            Lista de dicts con datos de la plaza y datos enriquecidos
        """
        try:
            # Primero obtenemos los contrato_categorias con sus categorías
            result_cc = self.supabase.table('contrato_categorias')\
                .select(
                    'id, contrato_id, categoria_puesto_id, '
                    'categorias_puesto:categoria_puesto_id(id, clave, nombre)'
                )\
                .eq('contrato_id', contrato_id)\
                .execute()

            if not result_cc.data:
                return []

            # Crear mapa de contrato_categoria -> datos
            cc_map = {}
            for cc in result_cc.data:
                cat_data = cc.get('categorias_puesto', {}) or {}
                cc_map[cc['id']] = {
                    'contrato_id': cc['contrato_id'],
                    'categoria_puesto_id': cc['categoria_puesto_id'],
                    'categoria_clave': cat_data.get('clave', ''),
                    'categoria_nombre': cat_data.get('nombre', ''),
                }

            cc_ids = list(cc_map.keys())

            # Obtener las plazas
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .in_('contrato_categoria_id', cc_ids)\
                .neq('estatus', EstatusPlaza.CANCELADA.value)\
                .order('contrato_categoria_id', desc=False)\
                .order('numero_plaza', desc=False)\
                .execute()

            # Obtener el código del contrato
            result_contrato = self.supabase.table('contratos')\
                .select('codigo')\
                .eq('id', contrato_id)\
                .execute()

            contrato_codigo = result_contrato.data[0]['codigo'] if result_contrato.data else ''

            # Obtener IDs de empleados únicos (no nulos)
            empleado_ids = list(set(
                p['empleado_id'] for p in result.data
                if p.get('empleado_id') is not None
            ))

            # Obtener datos de empleados en una sola consulta
            empleados_map = {}
            if empleado_ids:
                result_emp = self.supabase.table('empleados')\
                    .select('id, nombre, apellido_paterno, apellido_materno, curp')\
                    .in_('id', empleado_ids)\
                    .execute()

                for emp in result_emp.data:
                    nombre = emp.get('nombre', '')
                    apellido_p = emp.get('apellido_paterno', '')
                    apellido_m = emp.get('apellido_materno', '')
                    empleados_map[emp['id']] = {
                        'nombre': f"{nombre} {apellido_p} {apellido_m}".strip(),
                        'curp': emp.get('curp', ''),
                    }

            resumen = []
            for data in result.data:
                cc_data = cc_map.get(data['contrato_categoria_id'], {})
                empleado_id = data.get('empleado_id')
                empleado_data = empleados_map.get(empleado_id, {}) if empleado_id else {}

                item = {
                    **data,
                    'contrato_id': contrato_id,
                    'contrato_codigo': contrato_codigo,
                    'categoria_puesto_id': cc_data.get('categoria_puesto_id', 0),
                    'categoria_clave': cc_data.get('categoria_clave', ''),
                    'categoria_nombre': cc_data.get('categoria_nombre', ''),
                    'empleado_nombre': empleado_data.get('nombre', ''),
                    'empleado_curp': empleado_data.get('curp', ''),
                }
                resumen.append(item)

            return resumen

        except Exception as e:
            logger.error(f"Error obteniendo resumen del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_por_contrato_categoria(
        self,
        contrato_categoria_id: int,
        incluir_canceladas: bool = False
    ) -> List[dict]:
        """
        Obtiene plazas de una categoría con datos del empleado incluidos.

        Returns:
            Lista de dicts con datos de la plaza y empleado
        """
        try:
            # Obtener las plazas
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_categoria_id', contrato_categoria_id)

            if not incluir_canceladas:
                query = query.neq('estatus', EstatusPlaza.CANCELADA.value)

            query = query.order('numero_plaza', desc=False)

            result = query.execute()

            if not result.data:
                return []

            # Obtener IDs de empleados únicos (no nulos)
            empleado_ids = list(set(
                p['empleado_id'] for p in result.data
                if p.get('empleado_id') is not None
            ))

            # Obtener datos de empleados en una sola consulta
            empleados_map = {}
            if empleado_ids:
                result_emp = self.supabase.table('empleados')\
                    .select('id, nombre, apellido_paterno, apellido_materno, curp')\
                    .in_('id', empleado_ids)\
                    .execute()

                for emp in result_emp.data:
                    nombre = emp.get('nombre', '')
                    apellido_p = emp.get('apellido_paterno', '')
                    apellido_m = emp.get('apellido_materno', '')
                    empleados_map[emp['id']] = {
                        'nombre': f"{nombre} {apellido_p} {apellido_m}".strip(),
                        'curp': emp.get('curp', ''),
                    }

            # Construir resumen con datos de empleado
            resumen = []
            for data in result.data:
                empleado_id = data.get('empleado_id')
                empleado_data = empleados_map.get(empleado_id, {}) if empleado_id else {}

                item = {
                    **data,
                    'empleado_nombre': empleado_data.get('nombre', ''),
                    'empleado_curp': empleado_data.get('curp', ''),
                }
                resumen.append(item)

            return resumen

        except Exception as e:
            logger.error(f"Error obteniendo resumen de contrato_categoria {contrato_categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_totales_por_contrato(self, contrato_id: int) -> dict:
        """
        Calcula totales de plazas por estatus para un contrato.

        Returns:
            Dict con totales por estatus y costo total mensual
        """
        try:
            plazas = await self.obtener_por_contrato(contrato_id, incluir_canceladas=True)

            totales = {
                'total_plazas': len(plazas),
                'plazas_vacantes': 0,
                'plazas_ocupadas': 0,
                'plazas_suspendidas': 0,
                'plazas_canceladas': 0,
                'costo_total_mensual': Decimal('0'),
            }

            for plaza in plazas:
                if plaza.estatus == EstatusPlaza.VACANTE:
                    totales['plazas_vacantes'] += 1
                elif plaza.estatus == EstatusPlaza.OCUPADA:
                    totales['plazas_ocupadas'] += 1
                    totales['costo_total_mensual'] += plaza.salario_mensual
                elif plaza.estatus == EstatusPlaza.SUSPENDIDA:
                    totales['plazas_suspendidas'] += 1
                elif plaza.estatus == EstatusPlaza.CANCELADA:
                    totales['plazas_canceladas'] += 1

            return totales

        except Exception as e:
            logger.error(f"Error calculando totales del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_totales_por_contrato_categoria(
        self,
        contrato_categoria_id: int
    ) -> dict:
        """
        Calcula totales de plazas por estatus para una ContratoCategoria.

        Returns:
            Dict con totales por estatus y costo total mensual
        """
        try:
            plazas = await self.obtener_por_contrato_categoria(
                contrato_categoria_id,
                incluir_canceladas=True
            )

            totales = {
                'total_plazas': len(plazas),
                'plazas_vacantes': 0,
                'plazas_ocupadas': 0,
                'plazas_suspendidas': 0,
                'plazas_canceladas': 0,
                'costo_total_mensual': Decimal('0'),
            }

            for plaza in plazas:
                if plaza.estatus == EstatusPlaza.VACANTE:
                    totales['plazas_vacantes'] += 1
                elif plaza.estatus == EstatusPlaza.OCUPADA:
                    totales['plazas_ocupadas'] += 1
                    totales['costo_total_mensual'] += plaza.salario_mensual
                elif plaza.estatus == EstatusPlaza.SUSPENDIDA:
                    totales['plazas_suspendidas'] += 1
                elif plaza.estatus == EstatusPlaza.CANCELADA:
                    totales['plazas_canceladas'] += 1

            return totales

        except Exception as e:
            logger.error(f"Error calculando totales de contrato_categoria {contrato_categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_categorias_con_plazas(self) -> List[dict]:
        """
        Obtiene un resumen de todas las categorías de contrato que tienen plazas.

        Returns:
            Lista de dicts con:
            - contrato_categoria_id
            - empresa_nombre
            - contrato_codigo
            - categoria_clave
            - categoria_nombre
            - total_plazas
            - plazas_vacantes
            - plazas_ocupadas
        """
        try:
            # Obtener contrato_categorias con datos relacionados
            result_cc = self.supabase.table('contrato_categorias')\
                .select(
                    'id, contrato_id, '
                    'contratos:contrato_id(id, codigo, empresa_id, '
                    'empresas:empresa_id(id, nombre_comercial)), '
                    'categorias_puesto:categoria_puesto_id(id, clave, nombre)'
                )\
                .execute()

            if not result_cc.data:
                return []

            # Obtener todas las plazas no canceladas
            result_plazas = self.supabase.table(self.tabla)\
                .select('contrato_categoria_id, estatus')\
                .neq('estatus', EstatusPlaza.CANCELADA.value)\
                .execute()

            # Contar plazas por contrato_categoria
            conteo_plazas = {}
            for plaza in result_plazas.data:
                cc_id = plaza['contrato_categoria_id']
                if cc_id not in conteo_plazas:
                    conteo_plazas[cc_id] = {'total': 0, 'vacantes': 0, 'ocupadas': 0}
                conteo_plazas[cc_id]['total'] += 1
                if plaza['estatus'] == EstatusPlaza.VACANTE.value:
                    conteo_plazas[cc_id]['vacantes'] += 1
                elif plaza['estatus'] == EstatusPlaza.OCUPADA.value:
                    conteo_plazas[cc_id]['ocupadas'] += 1

            # Solo incluir categorías que tienen plazas
            resumen = []
            for cc in result_cc.data:
                cc_id = cc['id']
                if cc_id not in conteo_plazas:
                    continue  # Saltar categorías sin plazas

                contrato = cc.get('contratos') or {}
                empresa = contrato.get('empresas') or {}
                categoria = cc.get('categorias_puesto') or {}

                resumen.append({
                    'contrato_categoria_id': cc_id,
                    'contrato_id': cc.get('contrato_id'),
                    'empresa_nombre': empresa.get('nombre_comercial', ''),
                    'contrato_codigo': contrato.get('codigo', ''),
                    'categoria_clave': categoria.get('clave', ''),
                    'categoria_nombre': categoria.get('nombre', ''),
                    'total_plazas': conteo_plazas[cc_id]['total'],
                    'plazas_vacantes': conteo_plazas[cc_id]['vacantes'],
                    'plazas_ocupadas': conteo_plazas[cc_id]['ocupadas'],
                })

            # Ordenar por empresa, contrato, categoría
            resumen.sort(key=lambda x: (
                x['empresa_nombre'],
                x['contrato_codigo'],
                x['categoria_clave']
            ))

            return resumen

        except Exception as e:
            logger.error(f"Error obteniendo resumen de categorías con plazas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_contratos_con_plazas_pendientes(self) -> List[dict]:
        """
        Obtiene contratos que tienen categorías con plazas pendientes por crear.
        (donde cantidad_actual < cantidad_maxima)

        Returns:
            Lista de dicts con datos del contrato y categorías disponibles
        """
        try:
            # Obtener contrato_categorias con datos relacionados
            result_cc = self.supabase.table('contrato_categorias')\
                .select(
                    'id, contrato_id, cantidad_maxima, '
                    'contratos:contrato_id(id, codigo, empresa_id, tiene_personal, estatus, '
                    'empresas:empresa_id(id, nombre_comercial))'
                )\
                .execute()

            if not result_cc.data:
                return []

            # Obtener conteo de plazas por contrato_categoria (no canceladas)
            result_plazas = self.supabase.table(self.tabla)\
                .select('contrato_categoria_id')\
                .neq('estatus', EstatusPlaza.CANCELADA.value)\
                .execute()

            # Contar plazas por contrato_categoria
            conteo_plazas = {}
            for plaza in result_plazas.data:
                cc_id = plaza['contrato_categoria_id']
                conteo_plazas[cc_id] = conteo_plazas.get(cc_id, 0) + 1

            # Agrupar por contrato y verificar si tiene plazas pendientes
            contratos_map = {}
            for cc in result_cc.data:
                contrato = cc.get('contratos') or {}

                # Solo contratos activos con personal
                if not contrato.get('tiene_personal') or contrato.get('estatus') != 'ACTIVO':
                    continue

                cc_id = cc['id']
                contrato_id = cc.get('contrato_id')
                cantidad_maxima = cc.get('cantidad_maxima', 0)
                plazas_actuales = conteo_plazas.get(cc_id, 0)
                plazas_pendientes = cantidad_maxima - plazas_actuales

                if plazas_pendientes > 0:
                    if contrato_id not in contratos_map:
                        empresa = contrato.get('empresas') or {}
                        contratos_map[contrato_id] = {
                            'id': contrato_id,
                            'codigo': contrato.get('codigo', ''),
                            'empresa_nombre': empresa.get('nombre_comercial', ''),
                            'total_pendientes': 0,
                        }
                    contratos_map[contrato_id]['total_pendientes'] += plazas_pendientes

            # Convertir a lista y ordenar
            resultado = list(contratos_map.values())
            resultado.sort(key=lambda x: (x['empresa_nombre'], x['codigo']))

            return resultado

        except Exception as e:
            logger.error(f"Error obteniendo contratos con plazas pendientes: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_empleados_asignados(self) -> List[int]:
        """
        Obtiene los IDs de empleados que están asignados a plazas ocupadas.

        Returns:
            Lista de IDs de empleados únicos
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('empleado_id')\
                .eq('estatus', EstatusPlaza.OCUPADA.value)\
                .not_.is_('empleado_id', 'null')\
                .execute()

            # Extraer IDs únicos
            empleado_ids = list(set(
                p['empleado_id'] for p in result.data
                if p.get('empleado_id') is not None
            ))

            return empleado_ids

        except Exception as e:
            logger.error(f"Error obteniendo empleados asignados: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
