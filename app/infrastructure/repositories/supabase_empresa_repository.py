"""
Implementación del repositorio de Empresa usando Supabase.
Esta es la única clase que sabe cómo interactuar con Supabase.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database.connection import db_manager
from app.database.models.empresa_models import (
    Empresa as EmpresaModel,  # Tu modelo actual de Pydantic
    TipoEmpresa,
    EstatusEmpresa
)
from app.domain.repositories.empresa_repository_interface import IEmpresaRepository
from app.domain.entities.empresa_entity import (
    EmpresaEntity,
    EmpresaResumenEntity
)
from app.domain.exceptions.empresa_exceptions import (
    EmpresaNoEncontrada,
    EmpresaDuplicada,
    EmpresaConexionError,
    EmpresaValidacionError
)

logger = logging.getLogger(__name__)


class SupabaseEmpresaRepository(IEmpresaRepository):
    """
    Implementación concreta del repositorio usando Supabase.
    Convierte entre los modelos de dominio y los modelos de base de datos.
    """
    
    def __init__(self):
        """Inicializa el repositorio con la conexión de Supabase"""
        try:
            self.supabase = db_manager.get_client()
            self.tabla = 'empresas'
        except Exception as e:
            logger.error(f"Error conectando con Supabase: {e}")
            raise EmpresaConexionError(f"No se pudo conectar a la base de datos: {str(e)}")
    
    # ==========================================
    # MÉTODOS DE CONVERSIÓN
    # ==========================================
    
    def _modelo_a_entidad(self, modelo: EmpresaModel) -> EmpresaEntity:
        """Convierte un modelo de BD a una entidad de dominio"""
        return EmpresaEntity(
            id=modelo.id,
            nombre_comercial=modelo.nombre_comercial,
            razon_social=modelo.razon_social,
            tipo_empresa=TipoEmpresa(modelo.tipo_empresa),
            rfc=modelo.rfc,
            direccion=modelo.direccion,
            codigo_postal=modelo.codigo_postal,
            telefono=modelo.telefono,
            email=modelo.email,
            pagina_web=modelo.pagina_web,
            estatus=EstatusEmpresa(modelo.estatus),
            notas=modelo.notas,
            fecha_creacion=modelo.fecha_creacion,
            fecha_actualizacion=modelo.fecha_actualizacion
        )
    
    def _entidad_a_dict(self, entidad: EmpresaEntity) -> dict:
        """Convierte una entidad de dominio a dict para Supabase"""
        return {
            'nombre_comercial': entidad.nombre_comercial,
            'razon_social': entidad.razon_social,
            'tipo_empresa': entidad.tipo_empresa.value,
            'rfc': entidad.rfc.upper(),
            'direccion': entidad.direccion,
            'codigo_postal': entidad.codigo_postal,
            'telefono': entidad.telefono,
            'email': entidad.email,
            'pagina_web': entidad.pagina_web,
            'estatus': entidad.estatus.value,
            'notas': entidad.notas
        }
    
    def _dict_a_resumen(self, data: dict) -> EmpresaResumenEntity:
        """Convierte dict de Supabase a resumen de empresa"""
        contacto = data.get('email') or data.get('telefono') or "Sin contacto"
        return EmpresaResumenEntity(
            id=data['id'],
            nombre_comercial=data['nombre_comercial'],
            tipo_empresa=TipoEmpresa(data['tipo_empresa']),
            estatus=EstatusEmpresa(data['estatus']),
            contacto_principal=contacto,
            fecha_creacion=datetime.fromisoformat(data['fecha_creacion']) if data.get('fecha_creacion') else None
        )
    
    # ==========================================
    # OPERACIONES CRUD BÁSICAS
    # ==========================================
    
    async def obtener_por_id(self, empresa_id: int) -> Optional[EmpresaEntity]:
        """Obtiene una empresa por su ID"""
        try:
            logger.info(f"Obteniendo empresa con ID: {empresa_id}")
            
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('id', empresa_id)\
                .execute()
            
            if not result.data:
                logger.warning(f"Empresa {empresa_id} no encontrada")
                return None
            
            # Convertir a modelo y luego a entidad
            modelo = EmpresaModel.model_validate(result.data[0])
            entidad = self._modelo_a_entidad(modelo)
            
            logger.info(f"Empresa encontrada: {entidad.nombre_comercial}")
            return entidad
            
        except Exception as e:
            logger.error(f"Error obteniendo empresa {empresa_id}: {e}")
            raise EmpresaConexionError(f"Error al obtener empresa: {str(e)}")
    
    async def obtener_todas(
        self, 
        incluir_inactivas: bool = False,
        limite: int = None,
        offset: int = 0
    ) -> List[EmpresaEntity]:
        """Obtiene todas las empresas con paginación opcional"""
        try:
            logger.info(f"Obteniendo empresas. Incluir inactivas: {incluir_inactivas}")
            
            query = self.supabase.table(self.tabla).select('*')
            
            # Filtrar por estatus si es necesario
            if not incluir_inactivas:
                query = query.in_('estatus', [
                    EstatusEmpresa.ACTIVO.value,
                    EstatusEmpresa.SUSPENDIDO.value
                ])
            
            # Aplicar paginación
            if limite:
                query = query.range(offset, offset + limite - 1)
            
            # Ordenar por nombre
            query = query.order('nombre_comercial')
            
            result = query.execute()
            
            # Convertir a entidades
            empresas = []
            for data in result.data:
                modelo = EmpresaModel.model_validate(data)
                entidad = self._modelo_a_entidad(modelo)
                empresas.append(entidad)
            
            logger.info(f"Obtenidas {len(empresas)} empresas")
            return empresas
            
        except Exception as e:
            logger.error(f"Error obteniendo empresas: {e}")
            raise EmpresaConexionError(f"Error al obtener empresas: {str(e)}")
    
    async def crear(self, empresa: EmpresaEntity) -> EmpresaEntity:
        """Crea una nueva empresa"""
        try:
            logger.info(f"Creando empresa: {empresa.nombre_comercial}")
            
            # Verificar que no existe el RFC
            if await self.existe_rfc(empresa.rfc):
                raise EmpresaDuplicada(empresa.rfc)
            
            # Convertir entidad a dict para Supabase
            datos = self._entidad_a_dict(empresa)
            
            # Insertar en Supabase
            result = self.supabase.table(self.tabla).insert(datos).execute()
            
            if not result.data:
                raise EmpresaValidacionError(
                    "empresa",
                    str(datos),
                    "No se pudo crear la empresa"
                )
            
            # Convertir respuesta a entidad
            modelo = EmpresaModel.model_validate(result.data[0])
            entidad_creada = self._modelo_a_entidad(modelo)
            
            logger.info(f"Empresa creada con ID: {entidad_creada.id}")
            return entidad_creada
            
        except EmpresaDuplicada:
            raise
        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            raise EmpresaConexionError(f"Error al crear empresa: {str(e)}")
    
    async def actualizar(self, empresa: EmpresaEntity) -> EmpresaEntity:
        """Actualiza una empresa existente"""
        try:
            if not empresa.id:
                raise EmpresaValidacionError(
                    "id",
                    "None",
                    "ID es requerido para actualizar"
                )
            
            logger.info(f"Actualizando empresa {empresa.id}")
            
            # Verificar que existe
            if not await self.obtener_por_id(empresa.id):
                raise EmpresaNoEncontrada(empresa_id=empresa.id)
            
            # Si cambió el RFC, verificar que no exista
            empresa_actual = await self.obtener_por_id(empresa.id)
            if empresa_actual.rfc != empresa.rfc:
                if await self.existe_rfc(empresa.rfc, excluir_id=empresa.id):
                    raise EmpresaDuplicada(empresa.rfc)
            
            # Convertir y actualizar
            datos = self._entidad_a_dict(empresa)
            
            result = self.supabase.table(self.tabla)\
                .update(datos)\
                .eq('id', empresa.id)\
                .execute()
            
            if not result.data:
                raise EmpresaValidacionError(
                    "empresa",
                    str(empresa.id),
                    "No se pudo actualizar"
                )
            
            # Convertir respuesta
            modelo = EmpresaModel.model_validate(result.data[0])
            entidad_actualizada = self._modelo_a_entidad(modelo)
            
            logger.info(f"Empresa {empresa.id} actualizada")
            return entidad_actualizada
            
        except (EmpresaNoEncontrada, EmpresaDuplicada, EmpresaValidacionError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando empresa {empresa.id}: {e}")
            raise EmpresaConexionError(f"Error al actualizar: {str(e)}")
    
    async def eliminar(self, empresa_id: int) -> bool:
        """Elimina una empresa (soft delete - cambia estatus a INACTIVO)"""
        try:
            logger.info(f"Eliminando empresa {empresa_id}")
            
            # Verificar que puede ser eliminada
            puede, razon = await self.puede_eliminar(empresa_id)
            if not puede:
                raise EmpresaValidacionError(
                    "empresa",
                    str(empresa_id),
                    f"No se puede eliminar: {razon}"
                )
            
            # Soft delete - cambiar estatus
            result = self.supabase.table(self.tabla)\
                .update({'estatus': EstatusEmpresa.INACTIVO.value})\
                .eq('id', empresa_id)\
                .execute()
            
            eliminado = bool(result.data)
            
            if eliminado:
                logger.info(f"Empresa {empresa_id} marcada como INACTIVA")
            else:
                logger.warning(f"Empresa {empresa_id} no encontrada para eliminar")
            
            return eliminado
            
        except EmpresaValidacionError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando empresa {empresa_id}: {e}")
            raise EmpresaConexionError(f"Error al eliminar: {str(e)}")
    
    # ==========================================
    # OPERACIONES DE BÚSQUEDA
    # ==========================================
    
    async def buscar_por_rfc(self, rfc: str) -> Optional[EmpresaEntity]:
        """Busca una empresa por su RFC"""
        try:
            rfc_upper = rfc.upper()
            logger.info(f"Buscando empresa con RFC: {rfc_upper}")
            
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('rfc', rfc_upper)\
                .execute()
            
            if not result.data:
                return None
            
            modelo = EmpresaModel.model_validate(result.data[0])
            return self._modelo_a_entidad(modelo)
            
        except Exception as e:
            logger.error(f"Error buscando por RFC {rfc}: {e}")
            raise EmpresaConexionError(f"Error en búsqueda: {str(e)}")
    
    async def buscar_por_nombre(
        self, 
        termino: str,
        limite: int = 10
    ) -> List[EmpresaEntity]:
        """Busca empresas por nombre comercial o razón social"""
        try:
            logger.info(f"Buscando empresas con término: {termino}")
            
            # Búsqueda insensible a mayúsculas
            pattern = f"%{termino}%"
            
            # Buscar en nombre_comercial O razon_social
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .or_(f"nombre_comercial.ilike.{pattern},razon_social.ilike.{pattern}")\
                .limit(limite)\
                .execute()
            
            empresas = []
            for data in result.data:
                modelo = EmpresaModel.model_validate(data)
                empresas.append(self._modelo_a_entidad(modelo))
            
            logger.info(f"Encontradas {len(empresas)} empresas")
            return empresas
            
        except Exception as e:
            logger.error(f"Error buscando por nombre '{termino}': {e}")
            raise EmpresaConexionError(f"Error en búsqueda: {str(e)}")
    
    async def buscar_por_tipo(
        self,
        tipo: TipoEmpresa,
        incluir_inactivas: bool = False
    ) -> List[EmpresaEntity]:
        """Obtiene empresas de un tipo específico"""
        try:
            logger.info(f"Buscando empresas tipo: {tipo.value}")
            
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('tipo_empresa', tipo.value)
            
            if not incluir_inactivas:
                query = query.in_('estatus', [
                    EstatusEmpresa.ACTIVO.value,
                    EstatusEmpresa.SUSPENDIDO.value
                ])
            
            result = query.order('nombre_comercial').execute()
            
            empresas = []
            for data in result.data:
                modelo = EmpresaModel.model_validate(data)
                empresas.append(self._modelo_a_entidad(modelo))
            
            logger.info(f"Encontradas {len(empresas)} empresas de tipo {tipo.value}")
            return empresas
            
        except Exception as e:
            logger.error(f"Error buscando por tipo {tipo}: {e}")
            raise EmpresaConexionError(f"Error en búsqueda: {str(e)}")
    
    # ==========================================
    # OPERACIONES DE RESUMEN/AGREGACIÓN
    # ==========================================
    
    async def obtener_resumen(
        self,
        filtros: Dict[str, Any] = None,
        limite: int = 100,
        offset: int = 0
    ) -> List[EmpresaResumenEntity]:
        """Obtiene resumen de empresas para listados"""
        try:
            logger.info(f"Obteniendo resumen con filtros: {filtros}")
            
            # Query base con campos necesarios para resumen
            query = self.supabase.table(self.tabla).select(
                'id, nombre_comercial, tipo_empresa, estatus, email, telefono, fecha_creacion'
            )
            
            # Aplicar filtros si existen
            if filtros:
                if filtros.get('busqueda'):
                    pattern = f"%{filtros['busqueda']}%"
                    query = query.or_(
                        f"nombre_comercial.ilike.{pattern},razon_social.ilike.{pattern}"
                    )
                
                if filtros.get('tipo'):
                    query = query.eq('tipo_empresa', filtros['tipo'])
                
                if filtros.get('estatus'):
                    query = query.eq('estatus', filtros['estatus'])
                elif not filtros.get('incluir_inactivas'):
                    query = query.neq('estatus', EstatusEmpresa.INACTIVO.value)
            
            # Paginación y orden
            query = query.range(offset, offset + limite - 1)\
                        .order('nombre_comercial')
            
            result = query.execute()
            
            # Convertir a resúmenes
            resumenes = []
            for data in result.data:
                resumenes.append(self._dict_a_resumen(data))
            
            logger.info(f"Obtenidos {len(resumenes)} resúmenes")
            return resumenes
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {e}")
            raise EmpresaConexionError(f"Error al obtener resumen: {str(e)}")
    
    async def contar(self, filtros: Dict[str, Any] = None) -> int:
        """Cuenta empresas según filtros"""
        try:
            # Supabase no tiene count directo, usamos un select y contamos
            query = self.supabase.table(self.tabla).select('id', count='exact')
            
            if filtros:
                if filtros.get('tipo'):
                    query = query.eq('tipo_empresa', filtros['tipo'])
                if filtros.get('estatus'):
                    query = query.eq('estatus', filtros['estatus'])
                elif not filtros.get('incluir_inactivas'):
                    query = query.neq('estatus', EstatusEmpresa.INACTIVO.value)
            
            result = query.execute()
            return result.count if hasattr(result, 'count') else len(result.data)
            
        except Exception as e:
            logger.error(f"Error contando empresas: {e}")
            raise EmpresaConexionError(f"Error al contar: {str(e)}")
    
    async def existe_rfc(self, rfc: str, excluir_id: int = None) -> bool:
        """Verifica si existe un RFC"""
        try:
            rfc_upper = rfc.upper()
            query = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('rfc', rfc_upper)
            
            if excluir_id:
                query = query.neq('id', excluir_id)
            
            result = query.execute()
            existe = len(result.data) > 0
            
            logger.debug(f"RFC {rfc_upper} existe: {existe}")
            return existe
            
        except Exception as e:
            logger.error(f"Error verificando RFC {rfc}: {e}")
            raise EmpresaConexionError(f"Error al verificar RFC: {str(e)}")
    
    # ==========================================
    # OPERACIONES DE ESTADO
    # ==========================================
    
    async def cambiar_estatus(
        self,
        empresa_id: int,
        nuevo_estatus: EstatusEmpresa
    ) -> EmpresaEntity:
        """Cambia el estatus de una empresa"""
        try:
            logger.info(f"Cambiando estatus de empresa {empresa_id} a {nuevo_estatus.value}")
            
            # Verificar que existe
            empresa = await self.obtener_por_id(empresa_id)
            if not empresa:
                raise EmpresaNoEncontrada(empresa_id=empresa_id)
            
            # Actualizar estatus
            result = self.supabase.table(self.tabla)\
                .update({'estatus': nuevo_estatus.value})\
                .eq('id', empresa_id)\
                .execute()
            
            if not result.data:
                raise EmpresaValidacionError(
                    "estatus",
                    nuevo_estatus.value,
                    "No se pudo cambiar el estatus"
                )
            
            modelo = EmpresaModel.model_validate(result.data[0])
            return self._modelo_a_entidad(modelo)
            
        except (EmpresaNoEncontrada, EmpresaValidacionError):
            raise
        except Exception as e:
            logger.error(f"Error cambiando estatus: {e}")
            raise EmpresaConexionError(f"Error al cambiar estatus: {str(e)}")
    
    # ==========================================
    # OPERACIONES DE VALIDACIÓN
    # ==========================================
    
    async def puede_eliminar(self, empresa_id: int) -> tuple[bool, str]:
        """Verifica si una empresa puede ser eliminada"""
        try:
            # Verificar que existe
            empresa = await self.obtener_por_id(empresa_id)
            if not empresa:
                return False, "La empresa no existe"
            
            # Verificar empleados
            if await self.tiene_empleados(empresa_id):
                return False, "La empresa tiene empleados activos"
            
            # Verificar sedes
            if await self.tiene_sedes(empresa_id):
                return False, "La empresa tiene sedes asociadas"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error verificando si puede eliminar: {e}")
            return False, f"Error al verificar: {str(e)}"
    
    async def tiene_empleados(self, empresa_id: int) -> bool:
        """Verifica si una empresa tiene empleados"""
        try:
            result = self.supabase.table('empleados')\
                .select('id')\
                .eq('empresa_id', empresa_id)\
                .limit(1)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error verificando empleados: {e}")
            return True  # Por seguridad, asumimos que sí tiene
    
    async def tiene_sedes(self, empresa_id: int) -> bool:
        """Verifica si una empresa tiene sedes"""
        try:
            result = self.supabase.table('sedes')\
                .select('id')\
                .eq('empresa_id', empresa_id)\
                .limit(1)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error verificando sedes: {e}")
            return True  # Por seguridad, asumimos que sí tiene