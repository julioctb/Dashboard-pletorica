"""
Repositorio de Contratos - Interface y implementación para Supabase.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: código duplicado)
- DatabaseError: Errores de conexión o infraestructura
- Propagar otras excepciones hacia arriba
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
import logging

from app.entities import (
    Contrato,
    ContratoResumen,
    EstatusContrato,
)
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class IContratoRepository(ABC):
    """Interface del repositorio de contratos - define el contrato"""

    @abstractmethod
    async def obtener_por_id(self, contrato_id: int) -> Contrato:
        """Obtiene un contrato por su ID"""
        pass

    @abstractmethod
    async def obtener_por_codigo(self, codigo: str) -> Optional[Contrato]:
        """Obtiene un contrato por su código único"""
        pass

    @abstractmethod
    async def obtener_todos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Contrato]:
        """Obtiene todos los contratos con soporte de paginación"""
        pass

    @abstractmethod
    async def obtener_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False
    ) -> List[Contrato]:
        """Obtiene todos los contratos de una empresa"""
        pass

    @abstractmethod
    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivos: bool = False
    ) -> List[Contrato]:
        """Obtiene todos los contratos de un tipo de servicio"""
        pass

    @abstractmethod
    async def crear(self, contrato: Contrato) -> Contrato:
        """Crea un nuevo contrato"""
        pass

    @abstractmethod
    async def actualizar(self, contrato: Contrato) -> Contrato:
        """Actualiza un contrato existente"""
        pass

    @abstractmethod
    async def eliminar(self, contrato_id: int) -> bool:
        """Elimina (cancela) un contrato"""
        pass

    @abstractmethod
    async def existe_codigo(self, codigo: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si existe un código de contrato"""
        pass

    @abstractmethod
    async def obtener_siguiente_consecutivo(
        self,
        codigo_empresa: str,
        clave_servicio: str,
        anio: int
    ) -> int:
        """Obtiene el siguiente consecutivo para generar código de contrato"""
        pass

    @abstractmethod
    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[Contrato]:
        """Busca contratos por código o folio BUAP"""
        pass

    @abstractmethod
    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        empresa_id: Optional[int] = None,
        tipo_servicio_id: Optional[int] = None,
        estatus: Optional[str] = None,
        modalidad: Optional[str] = None,
        fecha_inicio_desde: Optional[date] = None,
        fecha_inicio_hasta: Optional[date] = None,
        incluir_inactivos: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[Contrato]:
        """Busca contratos con filtros combinados"""
        pass

    @abstractmethod
    async def obtener_vigentes(self) -> List[Contrato]:
        """Obtiene contratos activos y dentro de su periodo de vigencia"""
        pass

    @abstractmethod
    async def obtener_por_vencer(self, dias: int = 30) -> List[Contrato]:
        """Obtiene contratos que vencen en los próximos N días"""
        pass


class SupabaseContratoRepository(IContratoRepository):
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
        self.tabla = 'contratos'

    async def obtener_por_id(self, contrato_id: int) -> Contrato:
        """
        Obtiene un contrato por su ID.

        Args:
            contrato_id: ID del contrato a buscar

        Returns:
            Contrato encontrado

        Raises:
            NotFoundError: Si el contrato no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', contrato_id).execute()
            if not result.data:
                raise NotFoundError(f"Contrato con ID {contrato_id} no encontrado")
            return Contrato(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener contrato: {str(e)}")

    async def obtener_por_codigo(self, codigo: str) -> Optional[Contrato]:
        """
        Obtiene un contrato por su código único.

        Args:
            codigo: Código del contrato (ej: MAN-JAR-25001)

        Returns:
            Contrato encontrado o None si no existe

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('codigo', codigo.upper())\
                .execute()
            if not result.data:
                return None
            return Contrato(**result.data[0])
        except Exception as e:
            logger.error(f"Error obteniendo contrato por código {codigo}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_todos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Contrato]:
        """
        Obtiene todos los contratos con soporte de paginación.

        Args:
            incluir_inactivos: Si True, incluye contratos cancelados/vencidos
            limite: Número máximo de resultados (None = 100 por defecto)
            offset: Número de registros a saltar

        Returns:
            Lista de contratos

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            # Filtro de estatus (excluir cancelados, vencidos y cerrados por defecto)
            if not incluir_inactivos:
                query = query.in_('estatus', [
                    EstatusContrato.BORRADOR.value,
                    EstatusContrato.ACTIVO.value,
                    EstatusContrato.SUSPENDIDO.value,
                    EstatusContrato.CERRADO.value
                ])

            # Ordenamiento por fecha de creación
            query = query.order('fecha_creacion', desc=True)

            # Paginación
            if limite is None:
                limite = 100
            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Contrato(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo contratos: {e}")
            raise DatabaseError(f"Error de base de datos al obtener contratos: {str(e)}")

    async def obtener_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False
    ) -> List[Contrato]:
        """
        Obtiene todos los contratos de una empresa.

        Args:
            empresa_id: ID de la empresa
            incluir_inactivos: Si True, incluye contratos cancelados/vencidos

        Returns:
            Lista de contratos de la empresa

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('empresa_id', empresa_id)

            if not incluir_inactivos:
                query = query.in_('estatus', [
                    EstatusContrato.BORRADOR.value,
                    EstatusContrato.ACTIVO.value,
                    EstatusContrato.SUSPENDIDO.value,
                    EstatusContrato.CERRADO.value
                ])

            query = query.order('fecha_creacion', desc=True)
            result = query.execute()
            return [Contrato(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo contratos de empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivos: bool = False
    ) -> List[Contrato]:
        """
        Obtiene todos los contratos de un tipo de servicio.

        Args:
            tipo_servicio_id: ID del tipo de servicio
            incluir_inactivos: Si True, incluye contratos cancelados/vencidos

        Returns:
            Lista de contratos del tipo de servicio

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('tipo_servicio_id', tipo_servicio_id)

            if not incluir_inactivos:
                query = query.in_('estatus', [
                    EstatusContrato.BORRADOR.value,
                    EstatusContrato.ACTIVO.value,
                    EstatusContrato.SUSPENDIDO.value,
                    EstatusContrato.CERRADO.value
                ])

            query = query.order('fecha_creacion', desc=True)
            result = query.execute()
            return [Contrato(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo contratos de tipo servicio {tipo_servicio_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, contrato: Contrato) -> Contrato:
        """
        Crea un nuevo contrato.

        Args:
            contrato: Contrato a crear

        Returns:
            Contrato creado con ID asignado

        Raises:
            DuplicateError: Si el código ya existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Verificar código duplicado
            if await self.existe_codigo(contrato.codigo):
                raise DuplicateError(
                    f"Código de contrato {contrato.codigo} ya existe",
                    field="codigo",
                    value=contrato.codigo
                )

            # Preparar datos excluyendo campos autogenerados
            # mode='json' convierte dates a ISO strings para serialización
            datos = contrato.model_dump(mode='json', exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el contrato (sin respuesta de BD)")

            return Contrato(**result.data[0])
        except DuplicateError:
            raise
        except Exception as e:
            logger.error(f"Error creando contrato: {e}")
            raise DatabaseError(f"Error de base de datos al crear contrato: {str(e)}")

    async def actualizar(self, contrato: Contrato) -> Contrato:
        """
        Actualiza un contrato existente.

        Args:
            contrato: Contrato con datos actualizados

        Returns:
            Contrato actualizado

        Raises:
            NotFoundError: Si el contrato no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # mode='json' convierte dates a ISO strings para serialización
            datos = contrato.model_dump(mode='json', exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla)\
                .update(datos)\
                .eq('id', contrato.id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Contrato con ID {contrato.id} no encontrado")

            return Contrato(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando contrato {contrato.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar contrato: {str(e)}")

    async def eliminar(self, contrato_id: int) -> bool:
        """
        Elimina (soft delete) un contrato estableciendo estatus CANCELADO.

        Args:
            contrato_id: ID del contrato a cancelar

        Returns:
            True si se canceló exitosamente

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla)\
                .update({'estatus': EstatusContrato.CANCELADO.value})\
                .eq('id', contrato_id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error eliminando contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def existe_codigo(self, codigo: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si existe un código de contrato.

        Args:
            codigo: Código a verificar
            excluir_id: ID a excluir de la búsqueda (para ediciones)

        Returns:
            True si el código ya existe
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('codigo', codigo.upper())
            if excluir_id:
                query = query.neq('id', excluir_id)
            result = query.execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error verificando código: {e}")
            return True  # Por seguridad, asumir que existe

    async def obtener_siguiente_consecutivo(
        self,
        codigo_empresa: str,
        clave_servicio: str,
        anio: int
    ) -> int:
        """
        Obtiene el siguiente consecutivo para generar código de contrato.

        El código tiene formato: [EMPRESA]-[SERVICIO]-[AÑO][CONSECUTIVO]
        Ejemplo: MAN-JAR-25001

        Args:
            codigo_empresa: Código corto de la empresa (3 letras)
            clave_servicio: Clave del tipo de servicio (2-5 letras)
            anio: Año del contrato

        Returns:
            Siguiente número consecutivo disponible
        """
        try:
            # Buscar el patrón: MAN-JAR-25%
            anio_corto = str(anio)[-2:]
            patron = f"{codigo_empresa.upper()}-{clave_servicio.upper()}-{anio_corto}%"

            result = self.supabase.table(self.tabla)\
                .select('codigo')\
                .ilike('codigo', patron)\
                .order('codigo', desc=True)\
                .limit(1)\
                .execute()

            if not result.data:
                return 1

            # Extraer el consecutivo del último código
            ultimo_codigo = result.data[0]['codigo']
            # MAN-JAR-25001 -> 001 -> 1
            consecutivo_str = ultimo_codigo.split('-')[-1][2:]  # Quitar los 2 dígitos del año
            return int(consecutivo_str) + 1
        except Exception as e:
            logger.error(f"Error obteniendo consecutivo: {e}")
            return 1

    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[Contrato]:
        """
        Busca contratos por código o folio BUAP.

        Args:
            termino: Término de búsqueda
            limite: Número máximo de resultados

        Returns:
            Lista de contratos que coinciden

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .or_(
                    f"codigo.ilike.%{termino}%,"
                    f"numero_folio_buap.ilike.%{termino}%"
                )\
                .limit(limite)\
                .execute()

            return [Contrato(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error buscando contratos: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        empresa_id: Optional[int] = None,
        tipo_servicio_id: Optional[int] = None,
        estatus: Optional[str] = None,
        modalidad: Optional[str] = None,
        fecha_inicio_desde: Optional[date] = None,
        fecha_inicio_hasta: Optional[date] = None,
        incluir_inactivos: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[Contrato]:
        """
        Busca contratos con filtros combinados.

        Args:
            texto: Término de búsqueda en código o folio
            empresa_id: Filtrar por empresa
            tipo_servicio_id: Filtrar por tipo de servicio
            estatus: Filtrar por estatus específico
            modalidad: Filtrar por modalidad de adjudicación
            fecha_inicio_desde: Fecha de inicio mínima
            fecha_inicio_hasta: Fecha de inicio máxima
            incluir_inactivos: Si incluir cancelados/vencidos
            limite: Número máximo de resultados
            offset: Registros a saltar

        Returns:
            Lista de contratos que coinciden con los filtros

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            # Filtro de texto (busca en código, folio BUAP y descripción/concepto)
            if texto and texto.strip():
                query = query.or_(
                    f"codigo.ilike.%{texto}%,"
                    f"numero_folio_buap.ilike.%{texto}%,"
                    f"descripcion_objeto.ilike.%{texto}%"
                )

            # Filtros exactos
            if empresa_id:
                query = query.eq('empresa_id', empresa_id)
            if tipo_servicio_id:
                query = query.eq('tipo_servicio_id', tipo_servicio_id)
            if modalidad:
                query = query.eq('modalidad_adjudicacion', modalidad)

            # Filtro de estatus
            if estatus:
                query = query.eq('estatus', estatus)
            elif not incluir_inactivos:
                query = query.in_('estatus', [
                    EstatusContrato.BORRADOR.value,
                    EstatusContrato.ACTIVO.value,
                    EstatusContrato.SUSPENDIDO.value,
                    EstatusContrato.CERRADO.value
                ])

            # Filtros de fecha
            if fecha_inicio_desde:
                query = query.gte('fecha_inicio', fecha_inicio_desde.isoformat())
            if fecha_inicio_hasta:
                query = query.lte('fecha_inicio', fecha_inicio_hasta.isoformat())

            # Ordenamiento y paginación
            query = query.order('fecha_creacion', desc=True)
            if limite > 0:
                query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Contrato(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error buscando contratos con filtros: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_vigentes(self) -> List[Contrato]:
        """
        Obtiene contratos activos y dentro de su periodo de vigencia.

        Returns:
            Lista de contratos vigentes

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            hoy = date.today().isoformat()
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('estatus', EstatusContrato.ACTIVO.value)\
                .lte('fecha_inicio', hoy)\
                .or_(f"fecha_fin.is.null,fecha_fin.gte.{hoy}")\
                .order('fecha_fin', desc=False, nulls_first=False)\
                .execute()

            return [Contrato(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo contratos vigentes: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_vencer(self, dias: int = 30) -> List[Contrato]:
        """
        Obtiene contratos que vencen en los próximos N días.

        Args:
            dias: Número de días hacia adelante para buscar

        Returns:
            Lista de contratos por vencer

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            from datetime import timedelta
            hoy = date.today()
            fecha_limite = (hoy + timedelta(days=dias)).isoformat()

            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('estatus', EstatusContrato.ACTIVO.value)\
                .not_.is_('fecha_fin', 'null')\
                .gte('fecha_fin', hoy.isoformat())\
                .lte('fecha_fin', fecha_limite)\
                .order('fecha_fin', desc=False)\
                .execute()

            return [Contrato(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo contratos por vencer: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def cambiar_estatus(self, contrato_id: int, nuevo_estatus: EstatusContrato) -> Contrato:
        """
        Cambia el estatus de un contrato.

        Args:
            contrato_id: ID del contrato
            nuevo_estatus: Nuevo estatus a asignar

        Returns:
            Contrato actualizado

        Raises:
            NotFoundError: Si el contrato no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla)\
                .update({'estatus': nuevo_estatus.value})\
                .eq('id', contrato_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Contrato con ID {contrato_id} no encontrado")

            return Contrato(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error cambiando estatus de contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
