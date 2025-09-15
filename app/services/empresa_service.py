from typing import List, Optional
import logging

from app.database.connection import db_manager
from app.database.models.empresa_models import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
    TipoEmpresa,
    EstatusEmpresa
)

logger = logging.getLogger(__name__)

#Clase para manejar las operaciones de la empresa
class EmpresaService:

    def __init__(self):
        self.supabase = db_manager.get_client()

    #Operaciones basicas de CRUD

    #Obtener empresas
    async def obtener_todas(self, incluir_inactivas: bool = False ) -> List[Empresa] :
        try:
            query = self.supabase.table('empresas').select('*')

            if not incluir_inactivas:
                query = query.in_('estatus',['ACTIVO'])

            result = query.order('nombre_comercial').execute()

            empresas = []
            for data in result.data:
                empresa = Empresa.model_validate(data)
                empresas.append(empresa)

                logger.info(f'Obtenidas {len(empresas)} empresas')
                return empresas
        
        except Exception as e:
            logger.error(f'Error obteniendo empresas: {e}')
            return []
        
    #Obtener empresas por id
    async def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        """Obtiene una empresa por su ID"""
        try:
            result = self.supabase.table("empresas").select("*").eq("id", empresa_id).execute()
            
            if result.data:
                empresa = Empresa.model_validate(result.data[0])  # Pydantic v2
                logger.info(f"Empresa encontrada: {empresa.nombre_comercial}")
                return empresa
            else:
                logger.warning(f"Empresa con ID {empresa_id} no encontrada")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo empresa {empresa_id}: {e}")
            return None
    
    async def crear(self, empresa_data: EmpresaCreate) -> Optional[Empresa]:
        """Crea una nueva empresa"""
        try:
            # Validar que el RFC no exista
            rfc_existe = not await self.validar_rfc_unico(empresa_data.rfc)
            if rfc_existe:
                logger.error(f"RFC {empresa_data.rfc} ya existe")
                return None
            
            # Convertir a diccionario - Pydantic v2
            data = empresa_data.model_dump(exclude_unset=True)
            
            # Insertar en Supabase
            result = self.supabase.table("empresas").insert(data).execute()
            
            if result.data:
                empresa = Empresa.model_validate(result.data[0])  # Pydantic v2
                logger.info(f"Empresa creada: {empresa.nombre_comercial}")
                return empresa
            else:
                logger.error("No se pudo crear la empresa")
                return None
                
        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            return None
    
    async def actualizar(self, empresa_id: int, empresa_data: EmpresaUpdate) -> Optional[Empresa]:
        """Actualiza una empresa existente"""
        try:
            # Solo enviar campos que no son None - Pydantic v2
            data = empresa_data.model_dump(exclude_unset=True, exclude_none=True)
            
            if not data:
                logger.warning("No hay datos para actualizar")
                return None
            
            # Si se actualiza el RFC, validar que sea único
            if "rfc" in data:
                rfc_valido = await self.validar_rfc_unico(data["rfc"], excluir_id=empresa_id)
                if not rfc_valido:
                    logger.error(f"RFC {data['rfc']} ya existe en otra empresa")
                    return None
            
            result = self.supabase.table("empresas").update(data).eq("id", empresa_id).execute()
            
            if result.data:
                empresa = Empresa.model_validate(result.data[0])  # Pydantic v2
                logger.info(f"Empresa actualizada: {empresa.nombre_comercial}")
                return empresa
            else:
                logger.error(f"No se pudo actualizar empresa {empresa_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error actualizando empresa {empresa_id}: {e}")
            return None
    
    async def cambiar_estatus(self, empresa_id: int, nuevo_estatus: EstatusEmpresa) -> bool:
        """Cambia el estatus de una empresa"""
        try:
            result = self.supabase.table("empresas").update(
                {"estatus": nuevo_estatus.value}
            ).eq("id", empresa_id).execute()
            
            if result.data:
                logger.info(f"Empresa {empresa_id} cambió a estatus: {nuevo_estatus.value}")
                return True
            else:
                logger.error(f"No se pudo cambiar estatus de empresa {empresa_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error cambiando estatus empresa {empresa_id}: {e}")
            return False
    
    # ===============================
    # OPERACIONES ESPECÍFICAS POR TIPO
    # ===============================
    
    async def obtener_empresa_nomina(self) -> Optional[Empresa]:
        """Obtiene la empresa de nómina (PLETORICA)"""
        try:
            result = self.supabase.table("empresas").select("*").eq(
                "tipo_empresa", TipoEmpresa.NOMINA.value
            ).eq("estatus", EstatusEmpresa.ACTIVO.value).execute()
            
            if result.data:
                empresa = Empresa.model_validate(result.data[0])  # Pydantic v2
                logger.info(f"Empresa de nómina: {empresa.nombre_comercial}")
                return empresa
            else:
                logger.warning("No se encontró empresa de nómina activa")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo empresa de nómina: {e}")
            return None
    
    async def obtener_empresas_mantenimiento(self) -> List[Empresa]:
        """Obtiene empresas de mantenimiento (MANTISER, etc.)"""
        try:
            result = self.supabase.table("empresas").select("*").eq(
                "tipo_empresa", TipoEmpresa.MANTENIMIENTO.value
            ).in_("estatus", ["activo", "suspendido"]).execute()
            
            empresas = []
            for data in result.data:
                empresa = Empresa.model_validate(data)  # Pydantic v2
                empresas.append(empresa)
            
            logger.info(f"Obtenidas {len(empresas)} empresas de mantenimiento")
            return empresas
            
        except Exception as e:
            logger.error(f"Error obteniendo empresas de mantenimiento: {e}")
            return []
    
    # ===============================
    # OPERACIONES DE BÚSQUEDA Y VALIDACIÓN
    # ===============================
    
    async def obtener_por_rfc(self, rfc: str) -> Optional[Empresa]:
        """Obtiene empresa por RFC"""
        try:
            result = self.supabase.table("empresas").select("*").eq("rfc", rfc).execute()
            
            if result.data:
                empresa = Empresa.model_validate(result.data[0])  # Pydantic v2
                return empresa
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error buscando empresa por RFC '{rfc}': {e}")
            return None
    
    async def buscar_por_nombre(self, nombre: str) -> List[Empresa]:
        """Busca empresas por nombre comercial (búsqueda parcial)"""
        try:
            # Supabase usa ilike para búsqueda insensible a mayúsculas
            result = self.supabase.table("empresas").select("*").ilike(
                "nombre_comercial", f"%{nombre}%"
            ).execute()
            
            empresas = []
            for data in result.data:
                empresa = Empresa.model_validate(data)  # Pydantic v2
                empresas.append(empresa)
            
            logger.info(f"Encontradas {len(empresas)} empresas con nombre '{nombre}'")
            return empresas
            
        except Exception as e:
            logger.error(f"Error buscando empresas por nombre '{nombre}': {e}")
            return []
    
    async def validar_rfc_unico(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        """Valida que un RFC no esté ya en uso"""
        try:
            query = self.supabase.table("empresas").select("id").eq("rfc", rfc)
            
            if excluir_id:
                query = query.neq("id", excluir_id)
            
            result = query.execute()
            
            # Si no hay resultados, el RFC está disponible
            disponible = len(result.data) == 0
            
            if not disponible:
                logger.warning(f"RFC {rfc} ya está en uso")
            
            return disponible
            
        except Exception as e:
            logger.error(f"Error validando RFC {rfc}: {e}")
            return False
    
    # ===============================
    # OPERACIONES DE RESUMEN Y ESTADÍSTICAS
    # ===============================
    
    async def obtener_resumen_empresas(self) -> List[EmpresaResumen]:
        """Obtiene resumen de todas las empresas"""
        try:
            result = self.supabase.table("empresas").select(
                "id, nombre_comercial, tipo_empresa, estatus, email, telefono, fecha_creacion"
            ).order("nombre_comercial").execute()
            
            resumenes = []
            for data in result.data:
                # Determinar contacto principal
                contacto = data.get("email") or data.get("telefono") or "Sin contacto"
                
                # Crear resumen usando Pydantic v2
                resumen_data = {
                    "id": data["id"],
                    "nombre_comercial": data["nombre_comercial"],
                    "tipo_empresa": TipoEmpresa(data["tipo_empresa"]),
                    "estatus": EstatusEmpresa(data["estatus"]),
                    "contacto_principal": contacto,
                    "fecha_creacion": data["fecha_creacion"]
                }
                
                resumen = EmpresaResumen.model_validate(resumen_data)  # Pydantic v2
                resumenes.append(resumen)
            
            return resumenes
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de empresas: {e}")
            return []
    
    async def contar_por_estatus(self) -> dict:
        """Cuenta empresas por estatus"""
        try:
            result = self.supabase.table("empresas").select("estatus").execute()
            
            conteos = {"activo": 0, "inactivo": 0, "suspendido": 0}
            
            for data in result.data:
                estatus = data.get("estatus", "activo")
                if estatus in conteos:
                    conteos[estatus] += 1
            
            logger.info(f"Conteos por estatus: {conteos}")
            return conteos
            
        except Exception as e:
            logger.error(f"Error contando empresas por estatus: {e}")
            return {"activo": 0, "inactivo": 0, "suspendido": 0}

# Instancia global del servicio
empresa_service = EmpresaService()