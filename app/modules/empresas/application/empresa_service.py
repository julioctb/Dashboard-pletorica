# app/application/services/empresa_service.py
"""
Servicio de aplicación para gestión de empresas.
Orquesta las operaciones de negocio sin conocer detalles de implementación.
"""
import logging
from typing import List, Optional, Dict, Any

from app.domain.repositories.empresa_repository_interface import IEmpresaRepository
from app.domain.entities.empresa_entity import (
    EmpresaEntity,
    EmpresaResumenEntity,
    TipoEmpresa,
    EstatusEmpresa
)
from app.domain.exceptions.empresa_exceptions import (
    EmpresaNoEncontrada,
    EmpresaDuplicada,
    EmpresaValidacionError,
    EmpresaOperacionNoPermitida,
    EmpresaTipoInvalido
)

logger = logging.getLogger(__name__)


class EmpresaService:
    """
    Servicio de aplicación para empresas.
    NO sabe si usas Supabase, PostgreSQL o Excel.
    Solo sabe que tiene un repository que cumple el contrato.
    """
    
    def __init__(self, repository: IEmpresaRepository = None):
        """
        Inicializa el servicio con un repository.
        
        Args:
            repository: Implementación del repository. 
                       Si es None, se usará el modo legacy (compatibilidad)
        """
        if repository:
            self.repository = repository
            self.modo_legacy = False
            logger.info("EmpresaService iniciado con repository inyectado")
        else:
            # Modo legacy para compatibilidad con código existente
            from ..infrastructure.supabase_repository import SupabaseEmpresaRepository
            self.repository = db_manager.get_client()
            self.modo_legacy = True
            logger.warning("EmpresaService en modo legacy - considere migrar a repository")
    
    # ==========================================
    # OPERACIONES CRUD CON LÓGICA DE NEGOCIO
    # ==========================================
    
    async def crear_empresa(self, datos: Dict[str, Any]) -> EmpresaEntity:
        """
        Crea una nueva empresa con todas las validaciones de negocio.
        
        Args:
            datos: Diccionario con los datos de la empresa
            
        Returns:
            EmpresaEntity creada
            
        Raises:
            EmpresaDuplicada: Si el RFC ya existe
            EmpresaValidacionError: Si hay errores en los datos
            EmpresaTipoInvalido: Si el tipo requiere datos adicionales
        """
        try:
            logger.info(f"Creando empresa: {datos.get('nombre_comercial')}")
            
            # 1. Validaciones de negocio específicas por tipo
            tipo_empresa = TipoEmpresa(datos.get('tipo_empresa'))
            
            if tipo_empresa == TipoEmpresa.NOMINA:
                # Empresas de nómina requieren ciertos campos
                if not datos.get('email'):
                    raise EmpresaValidacionError(
                        'email',
                        '',
                        'Empresas de nómina requieren email para envío de recibos'
                    )
                # Aquí podrías validar registro patronal IMSS, etc.
            
            elif tipo_empresa == TipoEmpresa.MANTENIMIENTO:
                # Empresas de mantenimiento podrían tener otras validaciones
                pass
            
            # 2. Crear entidad de dominio (se auto-valida)
            empresa = EmpresaEntity(
                id=None,  # Se asignará en BD
                nombre_comercial=datos.get('nombre_comercial'),
                razon_social=datos.get('razon_social'),
                tipo_empresa=tipo_empresa,
                rfc=datos.get('rfc'),
                direccion=datos.get('direccion'),
                codigo_postal=datos.get('codigo_postal'),
                telefono=datos.get('telefono'),
                email=datos.get('email'),
                pagina_web=datos.get('pagina_web'),
                estatus=EstatusEmpresa.ACTIVO,  # Siempre inicia activa
                notas=datos.get('notas'),
                fecha_creacion=None,  # Se asigna en BD
                fecha_actualizacion=None
            )
            
            # 3. Validaciones de negocio adicionales
            if not empresa.puede_facturar():
                logger.warning("Creando empresa que no puede facturar inmediatamente")
            
            # 4. Persistir usando el repository
            if self.modo_legacy:
                return await self._crear_legacy(empresa)
            
            empresa_creada = await self.repository.crear(empresa)
            
            logger.info(f"Empresa creada exitosamente con ID: {empresa_creada.id}")
            
            # 5. Aquí podrías enviar eventos, notificaciones, etc.
            # await self._notificar_nueva_empresa(empresa_creada)
            
            return empresa_creada
            
        except (EmpresaDuplicada, EmpresaValidacionError, EmpresaTipoInvalido):
            raise
        except Exception as e:
            logger.error(f"Error inesperado creando empresa: {e}")
            raise EmpresaValidacionError(
                "empresa",
                str(datos),
                f"Error al crear empresa: {str(e)}"
            )
    
    async def actualizar_empresa(
        self, 
        empresa_id: int, 
        datos: Dict[str, Any]
    ) -> EmpresaEntity:
        """
        Actualiza una empresa con validaciones.
        
        Args:
            empresa_id: ID de la empresa a actualizar
            datos: Datos a actualizar
            
        Returns:
            EmpresaEntity actualizada
        """
        try:
            logger.info(f"Actualizando empresa {empresa_id}")
            
            # 1. Obtener empresa actual
            if self.modo_legacy:
                empresa_actual = await self._obtener_por_id_legacy(empresa_id)
            else:
                empresa_actual = await self.repository.obtener_por_id(empresa_id)
            
            if not empresa_actual:
                raise EmpresaNoEncontrada(empresa_id=empresa_id)
            
            # 2. Validar cambios de tipo de empresa
            nuevo_tipo = datos.get('tipo_empresa')
            if nuevo_tipo and nuevo_tipo != empresa_actual.tipo_empresa.value:
                # Verificar que puede cambiar de tipo
                if empresa_actual.tipo_empresa == TipoEmpresa.NOMINA:
                    if await self._tiene_empleados_activos(empresa_id):
                        raise EmpresaOperacionNoPermitida(
                            "cambio de tipo",
                            "La empresa tiene empleados activos"
                        )
            
            # 3. Crear entidad actualizada
            empresa_actualizada = EmpresaEntity(
                id=empresa_id,
                nombre_comercial=datos.get('nombre_comercial', empresa_actual.nombre_comercial),
                razon_social=datos.get('razon_social', empresa_actual.razon_social),
                tipo_empresa=TipoEmpresa(datos.get('tipo_empresa', empresa_actual.tipo_empresa.value)),
                rfc=datos.get('rfc', empresa_actual.rfc),
                direccion=datos.get('direccion', empresa_actual.direccion),
                codigo_postal=datos.get('codigo_postal', empresa_actual.codigo_postal),
                telefono=datos.get('telefono', empresa_actual.telefono),
                email=datos.get('email', empresa_actual.email),
                pagina_web=datos.get('pagina_web', empresa_actual.pagina_web),
                estatus=EstatusEmpresa(datos.get('estatus', empresa_actual.estatus.value)),
                notas=datos.get('notas', empresa_actual.notas),
                fecha_creacion=empresa_actual.fecha_creacion,
                fecha_actualizacion=None  # Se actualiza en BD
            )
            
            # 4. Persistir cambios
            if self.modo_legacy:
                return await self._actualizar_legacy(empresa_actualizada)
            
            resultado = await self.repository.actualizar(empresa_actualizada)
            
            logger.info(f"Empresa {empresa_id} actualizada exitosamente")
            return resultado
            
        except (EmpresaNoEncontrada, EmpresaOperacionNoPermitida):
            raise
        except Exception as e:
            logger.error(f"Error actualizando empresa {empresa_id}: {e}")
            raise
    
    async def eliminar_empresa(self, empresa_id: int) -> bool:
        """
        Elimina una empresa (soft delete) con validaciones.
        
        Args:
            empresa_id: ID de la empresa
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            EmpresaNoEncontrada: Si no existe
            EmpresaOperacionNoPermitida: Si no puede eliminarse
        """
        try:
            logger.info(f"Intentando eliminar empresa {empresa_id}")
            
            # 1. Verificar que puede ser eliminada
            puede_eliminar, razon = await self.puede_eliminar_empresa(empresa_id)
            
            if not puede_eliminar:
                raise EmpresaOperacionNoPermitida(
                    "eliminación",
                    razon
                )
            
            # 2. Realizar soft delete
            if self.modo_legacy:
                return await self._eliminar_legacy(empresa_id)
            
            eliminado = await self.repository.eliminar(empresa_id)
            
            if eliminado:
                logger.info(f"Empresa {empresa_id} eliminada (soft delete)")
                # Aquí podrías enviar notificaciones
            
            return eliminado
            
        except EmpresaOperacionNoPermitida:
            raise
        except Exception as e:
            logger.error(f"Error eliminando empresa {empresa_id}: {e}")
            raise
    
    # ==========================================
    # OPERACIONES DE CONSULTA
    # ==========================================
    
    async def obtener_empresa_por_id(self, empresa_id: int) -> Optional[EmpresaEntity]:
        """Obtiene una empresa por su ID"""
        try:
            if self.modo_legacy:
                return await self._obtener_por_id_legacy(empresa_id)
            
            return await self.repository.obtener_por_id(empresa_id)
            
        except Exception as e:
            logger.error(f"Error obteniendo empresa {empresa_id}: {e}")
            raise
    
    async def obtener_todas_las_empresas(
        self,
        incluir_inactivas: bool = False,
        limite: int = None,
        offset: int = 0
    ) -> List[EmpresaEntity]:
        """Obtiene todas las empresas"""
        try:
            if self.modo_legacy:
                return await self._obtener_todas_legacy(incluir_inactivas)
            
            return await self.repository.obtener_todas(
                incluir_inactivas=incluir_inactivas,
                limite=limite,
                offset=offset
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo empresas: {e}")
            raise
    
    async def buscar_empresas(
        self,
        termino: str,
        limite: int = 10
    ) -> List[EmpresaEntity]:
        """Busca empresas por nombre"""
        try:
            if not termino or len(termino) < 2:
                raise EmpresaValidacionError(
                    "termino",
                    termino,
                    "El término de búsqueda debe tener al menos 2 caracteres"
                )
            
            if self.modo_legacy:
                return await self._buscar_legacy(termino)
            
            return await self.repository.buscar_por_nombre(termino, limite)
            
        except EmpresaValidacionError:
            raise
        except Exception as e:
            logger.error(f"Error buscando empresas: {e}")
            raise
    
    async def obtener_empresas_nomina(self) -> List[EmpresaEntity]:
        """Obtiene solo empresas de tipo NOMINA activas"""
        try:
            if self.modo_legacy:
                return await self._obtener_por_tipo_legacy(TipoEmpresa.NOMINA)
            
            return await self.repository.buscar_por_tipo(
                TipoEmpresa.NOMINA,
                incluir_inactivas=False
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo empresas de nómina: {e}")
            raise
    
    async def obtener_empresas_mantenimiento(self) -> List[EmpresaEntity]:
        """Obtiene solo empresas de tipo MANTENIMIENTO activas"""
        try:
            if self.modo_legacy:
                return await self._obtener_por_tipo_legacy(TipoEmpresa.MANTENIMIENTO)
            
            return await self.repository.buscar_por_tipo(
                TipoEmpresa.MANTENIMIENTO,
                incluir_inactivas=False
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo empresas de mantenimiento: {e}")
            raise
    
    # ==========================================
    # OPERACIONES DE RESUMEN Y PAGINACIÓN
    # ==========================================
    
    async def obtener_resumen_paginado(
        self,
        filtros: Dict[str, Any] = None,
        limite: int = 10,
        offset: int = 0
    ) -> List[EmpresaResumenEntity]:
        """
        Obtiene resumen de empresas con paginación y filtros.
        
        Args:
            filtros: Diccionario con filtros opcionales
            limite: Número máximo de resultados
            offset: Número de registros a saltar
            
        Returns:
            Lista de resúmenes de empresa
        """
        try:
            if self.modo_legacy:
                # En modo legacy, obtener todas y paginar manualmente
                empresas = await self._obtener_todas_legacy(
                    incluir_inactivas=filtros.get('incluir_inactivas', False)
                )
                # Convertir a resumen
                resumenes = [
                    EmpresaResumenEntity.from_empresa(emp) 
                    for emp in empresas[offset:offset+limite]
                ]
                return resumenes
            
            return await self.repository.obtener_resumen(
                filtros=filtros,
                limite=limite,
                offset=offset
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen paginado: {e}")
            raise
    
    async def contar_empresas(
        self,
        filtros: Dict[str, Any] = None
    ) -> int:
        """Cuenta el total de empresas según filtros"""
        try:
            if self.modo_legacy:
                empresas = await self._obtener_todas_legacy(
                    incluir_inactivas=filtros.get('incluir_inactivas', False)
                )
                return len(empresas)
            
            return await self.repository.contar(filtros)
            
        except Exception as e:
            logger.error(f"Error contando empresas: {e}")
            raise
    
    # ==========================================
    # OPERACIONES DE VALIDACIÓN DE NEGOCIO
    # ==========================================
    
    async def puede_eliminar_empresa(
        self, 
        empresa_id: int
    ) -> tuple[bool, str]:
        """
        Verifica si una empresa puede ser eliminada según reglas de negocio.
        
        Args:
            empresa_id: ID de la empresa
            
        Returns:
            Tupla (puede_eliminar, razón si no puede)
        """
        try:
            # Verificar que existe
            empresa = await self.obtener_empresa_por_id(empresa_id)
            if not empresa:
                return False, "La empresa no existe"
            
            # Reglas de negocio para eliminación
            if self.modo_legacy:
                tiene_empleados = await self._tiene_empleados_legacy(empresa_id)
                tiene_sedes = await self._tiene_sedes_legacy(empresa_id)
            else:
                tiene_empleados = await self.repository.tiene_empleados(empresa_id)
                tiene_sedes = await self.repository.tiene_sedes(empresa_id)
            
            if tiene_empleados:
                return False, "La empresa tiene empleados activos"
            
            if tiene_sedes:
                return False, "La empresa tiene sedes asociadas"
            
            # Más reglas de negocio
            if empresa.tipo_empresa == TipoEmpresa.NOMINA:
                # Verificar que no tenga nóminas pendientes
                # if await self._tiene_nominas_pendientes(empresa_id):
                #     return False, "La empresa tiene nóminas pendientes"
                pass
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error verificando si puede eliminar: {e}")
            return False, f"Error al verificar: {str(e)}"
    
    async def cambiar_estatus_empresa(
        self,
        empresa_id: int,
        nuevo_estatus: EstatusEmpresa
    ) -> EmpresaEntity:
        """
        Cambia el estatus de una empresa con validaciones.
        
        Args:
            empresa_id: ID de la empresa
            nuevo_estatus: Nuevo estatus
            
        Returns:
            Empresa actualizada
        """
        try:
            # Obtener empresa actual
            empresa = await self.obtener_empresa_por_id(empresa_id)
            if not empresa:
                raise EmpresaNoEncontrada(empresa_id=empresa_id)
            
            # Validar transición de estatus
            if empresa.estatus == nuevo_estatus:
                raise EmpresaOperacionNoPermitida(
                    "cambio de estatus",
                    f"La empresa ya está {nuevo_estatus.value}"
                )
            
            # Reglas de negocio para cambio de estatus
            if nuevo_estatus == EstatusEmpresa.INACTIVO:
                if await self._tiene_empleados_activos(empresa_id):
                    raise EmpresaOperacionNoPermitida(
                        "inactivación",
                        "No se puede inactivar empresa con empleados activos"
                    )
            
            # Cambiar estatus
            if self.modo_legacy:
                return await self._cambiar_estatus_legacy(empresa_id, nuevo_estatus)
            
            return await self.repository.cambiar_estatus(empresa_id, nuevo_estatus)
            
        except (EmpresaNoEncontrada, EmpresaOperacionNoPermitida):
            raise
        except Exception as e:
            logger.error(f"Error cambiando estatus: {e}")
            raise
    
    # ==========================================
    # MÉTODOS LEGACY (para compatibilidad)
    # ==========================================
    
    async def _crear_legacy(self, empresa: EmpresaEntity) -> EmpresaEntity:
        """Crear empresa en modo legacy"""
        # Implementación usando Supabase directamente
        # Este es tu código actual
        pass
    
    async def _obtener_por_id_legacy(self, empresa_id: int) -> Optional[EmpresaEntity]:
        """Obtener por ID en modo legacy"""
        # Tu código actual
        pass
    
    async def _obtener_todas_legacy(self, incluir_inactivas: bool) -> List[EmpresaEntity]:
        """Obtener todas en modo legacy"""
        # Tu código actual
        pass
    
    async def _tiene_empleados_legacy(self, empresa_id: int) -> bool:
        """Verificar empleados en modo legacy"""
        # Tu código actual
        pass
    
    async def _tiene_sedes_legacy(self, empresa_id: int) -> bool:
        """Verificar sedes en modo legacy"""
        # Tu código actual
        pass
    
    async def _tiene_empleados_activos(self, empresa_id: int) -> bool:
        """Verifica si tiene empleados activos"""
        if self.modo_legacy:
            return await self._tiene_empleados_legacy(empresa_id)
        return await self.repository.tiene_empleados(empresa_id)


# ==========================================
# CONFIGURACIÓN DE DEPENDENCIAS
# ==========================================

def crear_empresa_service() -> EmpresaService:
    """
    Factory function para crear el servicio con las dependencias correctas.
    """
    try:
        # Intentar crear con el nuevo repository
        from app.infrastructure.repositories.supabase_empresa_repository import (
            SupabaseEmpresaRepository
        )
        repository = SupabaseEmpresaRepository()
        return EmpresaService(repository=repository)
    except ImportError:
        # Si no existe el repository, usar modo legacy
        logger.warning("Repository no disponible, usando modo legacy")
        return EmpresaService()


# Instancia global del servicio (singleton)
empresa_service = crear_empresa_service()