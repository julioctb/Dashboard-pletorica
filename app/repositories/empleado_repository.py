"""
Repositorio de Empleados - Interface y implementación para Supabase.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: CURP duplicado)
- DatabaseError: Errores de conexión o infraestructura
- Propagar otras excepciones hacia arriba
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
import logging

from app.entities.empleado import Empleado, EmpleadoResumen
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class IEmpleadoRepository(ABC):
    """Interface del repositorio de empleados - define el contrato"""

    # =========================================================================
    # CRUD BÁSICO
    # =========================================================================

    @abstractmethod
    async def obtener_por_id(self, empleado_id: int) -> Empleado:
        """Obtiene un empleado por su ID"""
        pass

    @abstractmethod
    async def obtener_por_clave(self, clave: str) -> Optional[Empleado]:
        """Obtiene un empleado por su clave (B25-00001)"""
        pass

    @abstractmethod
    async def obtener_por_curp(self, curp: str) -> Optional[Empleado]:
        """Obtiene un empleado por su CURP"""
        pass

    @abstractmethod
    async def crear(self, empleado: Empleado) -> Empleado:
        """Crea un nuevo empleado"""
        pass

    @abstractmethod
    async def actualizar(self, empleado: Empleado) -> Empleado:
        """Actualiza un empleado existente"""
        pass

    @abstractmethod
    async def eliminar(self, empleado_id: int) -> bool:
        """Elimina (soft delete) un empleado"""
        pass

    # =========================================================================
    # CONSULTAS
    # =========================================================================

    @abstractmethod
    async def obtener_todos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Empleado]:
        """Obtiene todos los empleados con paginación"""
        pass

    @abstractmethod
    async def obtener_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Empleado]:
        """Obtiene empleados de una empresa específica"""
        pass

    @abstractmethod
    async def buscar(
        self,
        texto: str,
        empresa_id: Optional[int] = None,
        limite: int = 20
    ) -> List[Empleado]:
        """Busca empleados por nombre, CURP o clave"""
        pass

    @abstractmethod
    async def contar(
        self,
        empresa_id: Optional[int] = None,
        estatus: Optional[str] = None
    ) -> int:
        """Cuenta empleados con filtros opcionales"""
        pass

    # =========================================================================
    # GENERACIÓN DE CLAVE
    # =========================================================================

    @abstractmethod
    async def obtener_siguiente_consecutivo(self, anio: int) -> int:
        """Obtiene el siguiente número consecutivo para el año dado"""
        pass

    # =========================================================================
    # VERIFICACIONES
    # =========================================================================

    @abstractmethod
    async def existe_curp(self, curp: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si existe un CURP en la base de datos"""
        pass

    @abstractmethod
    async def existe_clave(self, clave: str) -> bool:
        """Verifica si existe una clave en la base de datos"""
        pass


class SupabaseEmpleadoRepository(IEmpleadoRepository):
    """Implementación del repositorio usando Supabase"""

    def __init__(self, db_manager=None):
        """
        Inicializa el repositorio con un cliente de Supabase.

        Args:
            db_manager: Gestor de base de datos. Si es None, se importa el global.
        """
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'empleados'

    # =========================================================================
    # CRUD BÁSICO
    # =========================================================================

    async def obtener_por_id(self, empleado_id: int) -> Empleado:
        """
        Obtiene un empleado por su ID.

        Raises:
            NotFoundError: Si el empleado no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('id', empleado_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Empleado con ID {empleado_id} no encontrado")

            return Empleado(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo empleado {empleado_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener empleado: {str(e)}")

    async def obtener_por_clave(self, clave: str) -> Optional[Empleado]:
        """
        Obtiene un empleado por su clave (B25-00001).

        Returns:
            Empleado si existe, None si no existe

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('clave', clave.upper())\
                .execute()

            if not result.data:
                return None

            return Empleado(**result.data[0])

        except Exception as e:
            logger.error(f"Error obteniendo empleado por clave {clave}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_curp(self, curp: str) -> Optional[Empleado]:
        """
        Obtiene un empleado por su CURP.

        Returns:
            Empleado si existe, None si no existe

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('curp', curp.upper())\
                .execute()

            if not result.data:
                return None

            return Empleado(**result.data[0])

        except Exception as e:
            logger.error(f"Error obteniendo empleado por CURP {curp}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, empleado: Empleado) -> Empleado:
        """
        Crea un nuevo empleado.

        Raises:
            DuplicateError: Si el CURP o clave ya existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Verificar CURP duplicado
            if await self.existe_curp(empleado.curp):
                raise DuplicateError(
                    f"CURP {empleado.curp} ya existe",
                    field="curp",
                    value=empleado.curp
                )

            # Verificar clave duplicada
            if await self.existe_clave(empleado.clave):
                raise DuplicateError(
                    f"Clave {empleado.clave} ya existe",
                    field="clave",
                    value=empleado.clave
                )

            # Preparar datos (mode='json' para serializar date/datetime)
            datos = empleado.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'}
            )

            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el empleado (sin respuesta de BD)")

            return Empleado(**result.data[0])

        except DuplicateError:
            raise
        except Exception as e:
            logger.error(f"Error creando empleado: {e}")
            raise DatabaseError(f"Error de base de datos al crear empleado: {str(e)}")

    async def actualizar(self, empleado: Empleado) -> Empleado:
        """
        Actualiza un empleado existente.

        Raises:
            NotFoundError: Si el empleado no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Excluir campos que no deben actualizarse
            datos = empleado.model_dump(
                mode='json',
                exclude={'id', 'clave', 'curp', 'fecha_creacion', 'fecha_actualizacion'}
            )

            result = self.supabase.table(self.tabla)\
                .update(datos)\
                .eq('id', empleado.id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Empleado con ID {empleado.id} no encontrado")

            return Empleado(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando empleado {empleado.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar empleado: {str(e)}")

    async def eliminar(self, empleado_id: int) -> bool:
        """
        Elimina (soft delete) un empleado estableciendo estatus INACTIVO.

        Returns:
            True si se eliminó correctamente, False si falló
        """
        try:
            result = self.supabase.table(self.tabla)\
                .update({
                    'estatus': 'INACTIVO',
                    'fecha_baja': date.today().isoformat()
                })\
                .eq('id', empleado_id)\
                .execute()

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error eliminando empleado {empleado_id}: {e}")
            return False

    # =========================================================================
    # CONSULTAS
    # =========================================================================

    async def obtener_todos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Empleado]:
        """
        Obtiene todos los empleados con paginación.

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            if not incluir_inactivos:
                query = query.eq('estatus', 'ACTIVO')

            query = query.order('fecha_creacion', desc=True)

            if limite is None:
                limite = 100

            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Empleado(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo empleados: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Empleado]:
        """
        Obtiene empleados de una empresa específica.

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('empresa_id', empresa_id)

            if not incluir_inactivos:
                query = query.eq('estatus', 'ACTIVO')

            query = query.order('apellido_paterno', desc=False)

            if limite is None:
                limite = 100

            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Empleado(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo empleados de empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def buscar(
        self,
        texto: str,
        empresa_id: Optional[int] = None,
        limite: int = 20,
        offset: int = 0
    ) -> List[Empleado]:
        """
        Busca empleados por nombre, CURP o clave.

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .or_(
                    f"nombre.ilike.%{texto}%,"
                    f"apellido_paterno.ilike.%{texto}%,"
                    f"apellido_materno.ilike.%{texto}%,"
                    f"curp.ilike.%{texto}%,"
                    f"clave.ilike.%{texto}%"
                )

            if empresa_id:
                query = query.eq('empresa_id', empresa_id)

            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Empleado(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error buscando empleados con texto '{texto}': {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar(
        self,
        empresa_id: Optional[int] = None,
        estatus: Optional[str] = None
    ) -> int:
        """
        Cuenta empleados con filtros opcionales.

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('id', count='exact')

            if empresa_id:
                query = query.eq('empresa_id', empresa_id)

            if estatus:
                query = query.eq('estatus', estatus)

            result = query.execute()
            return result.count or 0

        except Exception as e:
            logger.error(f"Error contando empleados: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # =========================================================================
    # GENERACIÓN DE CLAVE
    # =========================================================================

    async def obtener_siguiente_consecutivo(self, anio: int) -> int:
        """
        Obtiene el siguiente número consecutivo para el año dado.
        Busca la última clave del año y retorna el siguiente número.

        Args:
            anio: Año para el que se busca consecutivo (ej: 2025)

        Returns:
            Siguiente número consecutivo (ej: si existe B25-00003, retorna 4)

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Buscar claves que empiecen con B[anio]
            anio_corto = str(anio)[-2:]
            prefijo = f"B{anio_corto}-"

            result = self.supabase.table(self.tabla)\
                .select('clave')\
                .ilike('clave', f'{prefijo}%')\
                .order('clave', desc=True)\
                .limit(1)\
                .execute()

            if not result.data:
                return 1  # Primer empleado del año

            # Extraer el número de la última clave (B25-00003 -> 3)
            ultima_clave = result.data[0]['clave']
            ultimo_numero = int(ultima_clave.split('-')[1])

            return ultimo_numero + 1

        except Exception as e:
            logger.error(f"Error obteniendo consecutivo para año {anio}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # =========================================================================
    # VERIFICACIONES
    # =========================================================================

    async def existe_curp(self, curp: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si existe un CURP en la base de datos.

        Args:
            curp: CURP a verificar
            excluir_id: ID de empleado a excluir de la búsqueda (para actualizaciones)

        Returns:
            True si el CURP ya existe, False si está disponible

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('curp', curp.upper())

            if excluir_id:
                query = query.neq('id', excluir_id)

            result = query.execute()
            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error verificando CURP: {e}")
            raise DatabaseError(f"Error de base de datos al verificar CURP: {str(e)}")

    async def existe_clave(self, clave: str) -> bool:
        """
        Verifica si existe una clave en la base de datos.

        Returns:
            True si la clave ya existe, False si está disponible

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('clave', clave.upper())\
                .execute()

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error verificando clave: {e}")
            raise DatabaseError(f"Error de base de datos al verificar clave: {str(e)}")

    # =========================================================================
    # MÉTODOS DE RESUMEN
    # =========================================================================

    async def obtener_resumen_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """
        Obtiene resumen de empleados con nombre de empresa.

        Returns:
            Lista de diccionarios con datos de resumen
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('*, empresas(nombre_comercial)')\
                .eq('empresa_id', empresa_id)

            if not incluir_inactivos:
                query = query.eq('estatus', 'ACTIVO')

            query = query.order('apellido_paterno')\
                .range(offset, offset + limite - 1)

            result = query.execute()

            resumenes = []
            for data in result.data:
                empresa_nombre = None
                if data.get('empresas'):
                    empresa_nombre = data['empresas'].get('nombre_comercial')

                # Construir nombre completo
                nombre_completo = data['nombre']
                if data.get('apellido_paterno'):
                    nombre_completo += f" {data['apellido_paterno']}"
                if data.get('apellido_materno'):
                    nombre_completo += f" {data['apellido_materno']}"

                resumenes.append({
                    'id': data['id'],
                    'clave': data['clave'],
                    'curp': data['curp'],
                    'nombre_completo': nombre_completo,
                    'empresa_id': data['empresa_id'],
                    'empresa_nombre': empresa_nombre,
                    'estatus': data['estatus'],
                    'fecha_ingreso': data['fecha_ingreso'],
                    'telefono': data.get('telefono'),
                    'email': data.get('email'),
                })

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo resumen de empleados: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_disponibles_para_asignacion(
        self,
        limite: int = 100
    ) -> List[EmpleadoResumen]:
        """
        Obtiene empleados disponibles para asignar a una plaza.

        Un empleado está disponible si:
        - Está activo (estatus = ACTIVO)
        - No tiene una asignación activa en historial_laboral

        Returns:
            Lista de EmpleadoResumen de empleados disponibles

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            # Obtener IDs de empleados con asignación activa
            result_historial = self.supabase.table('historial_laboral')\
                .select('empleado_id')\
                .eq('estatus', 'ACTIVA')\
                .execute()

            empleados_asignados = set(
                h['empleado_id'] for h in result_historial.data
                if h.get('empleado_id') is not None
            )

            # Obtener empleados activos
            query = self.supabase.table(self.tabla)\
                .select('*, empresas(nombre_comercial)')\
                .eq('estatus', 'ACTIVO')\
                .order('apellido_paterno')\
                .limit(limite)

            result = query.execute()

            # Filtrar empleados que no están asignados
            empleados_disponibles = []
            for data in result.data:
                if data['id'] in empleados_asignados:
                    continue  # Saltar empleados ya asignados

                empresa_nombre = None
                if data.get('empresas'):
                    empresa_nombre = data['empresas'].get('nombre_comercial')

                empleados_disponibles.append(
                    EmpleadoResumen.from_empleado_dict(data, empresa_nombre)
                )

            return empleados_disponibles

        except Exception as e:
            logger.error(f"Error obteniendo empleados disponibles: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
