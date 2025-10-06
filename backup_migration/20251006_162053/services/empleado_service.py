from typing import List, Optional, Dict
import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.database.connection import db_manager
from app.database.models.empleado_models import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
    EstatusEmpleado
)

logger = logging.getLogger(__name__)

class EmpleadoService:
    """Servicio para gestión de empleados"""
    
    def __init__(self):
        self.supabase = db_manager.get_client()
    
    # ===============================
    # OPERACIONES CRUD BÁSICAS
    # ===============================
    
    async def obtener_todos(
        self, 
        empresa_id: Optional[int] = None,
        sede_id: Optional[int] = None,
        incluir_bajas: bool = False
    ) -> List[Empleado]:
        """Obtiene lista de empleados con filtros"""
        try:
            query = self.supabase.table('empleados').select('*')
            
            if empresa_id:
                query = query.eq('empresa_id', empresa_id)
            
            if sede_id:
                query = query.eq('sede_id', sede_id)
            
            if not incluir_bajas:
                query = query.in_('estatus', ['ACTIVO', 'SUSPENDIDO', 'INCAPACIDAD', 'VACACIONES'])
            
            result = query.order('apellido_paterno, apellido_materno, nombre').execute()
            
            empleados = []
            for data in result.data:
                empleado = Empleado.model_validate(data)
                empleados.append(empleado)
            
            logger.info(f'Obtenidos {len(empleados)} empleados')
            return empleados
            
        except Exception as e:
            logger.error(f'Error obteniendo empleados: {e}')
            return []
    
    async def obtener_por_id(self, empleado_id: int) -> Optional[Empleado]:
        """Obtiene un empleado por ID"""
        try:
            result = self.supabase.table('empleados').select('*').eq('id', empleado_id).execute()
            
            if result.data:
                empleado = Empleado.model_validate(result.data[0])
                logger.info(f'Empleado encontrado: {empleado.nombre_completo}')
                return empleado
            else:
                logger.warning(f'Empleado {empleado_id} no encontrado')
                return None
                
        except Exception as e:
            logger.error(f'Error obteniendo empleado {empleado_id}: {e}')
            return None
    
    async def obtener_por_uuid(self, empleado_uuid: UUID) -> Optional[Empleado]:
        """Obtiene un empleado por UUID (más seguro para URLs públicas)"""
        try:
            result = self.supabase.table('empleados').select('*').eq('uuid', str(empleado_uuid)).execute()
            
            if result.data:
                empleado = Empleado.model_validate(result.data[0])
                logger.info(f'Empleado encontrado por UUID: {empleado.nombre_completo}')
                return empleado
            else:
                logger.warning(f'Empleado con UUID {empleado_uuid} no encontrado')
                return None
                
        except Exception as e:
            logger.error(f'Error obteniendo empleado por UUID {empleado_uuid}: {e}')
            return None
    
    async def crear(self, empleado_data: EmpleadoCreate) -> Optional[Empleado]:
        """Crea un nuevo empleado"""
        try:
            # Validar unicidad de RFC, CURP y NSS
            validaciones = await self.validar_documentos_unicos(
                rfc=empleado_data.rfc,
                curp=empleado_data.curp,
                nss=empleado_data.nss
            )
            
            if not all(validaciones.values()):
                errores = [k for k, v in validaciones.items() if not v]
                logger.error(f'Documentos duplicados: {errores}')
                return None
            
            # Convertir a dict y agregar timestamps
            data = empleado_data.model_dump(exclude_unset=True)
            data['fecha_creacion'] = datetime.now().isoformat()
            
            result = self.supabase.table('empleados').insert(data).execute()
            
            if result.data:
                empleado = Empleado.model_validate(result.data[0])
                logger.info(f'Empleado creado: {empleado.nombre_completo}')
                
                # Crear registro en historial laboral
                await self._crear_historial_laboral(empleado)
                
                return empleado
            else:
                logger.error('No se pudo crear el empleado')
                return None
                
        except Exception as e:
            logger.error(f'Error creando empleado: {e}')
            return None
    
    async def actualizar(
        self, 
        empleado_id: int, 
        empleado_data: EmpleadoUpdate,
        usuario_id: Optional[int] = None
    ) -> Optional[Empleado]:
        """Actualiza un empleado existente"""
        try:
            # Convertir a dict excluyendo None
            data = empleado_data.model_dump(exclude_unset=True, exclude_none=True)
            
            if not data:
                logger.warning('No hay datos para actualizar')
                return None
            
            # Agregar metadata de actualización
            data['fecha_actualizacion'] = datetime.now().isoformat()
            if usuario_id:
                data['actualizado_por'] = usuario_id
            
            # Si se cambia de sede, registrar en historial
            if 'sede_id' in data:
                empleado_actual = await self.obtener_por_id(empleado_id)
                if empleado_actual and empleado_actual.sede_id != data['sede_id']:
                    await self._registrar_cambio_sede(empleado_id, empleado_actual.sede_id, data['sede_id'])
            
            result = self.supabase.table('empleados').update(data).eq('id', empleado_id).execute()
            
            if result.data:
                empleado = Empleado.model_validate(result.data[0])
                logger.info(f'Empleado actualizado: {empleado.nombre_completo}')
                return empleado
            else:
                logger.error(f'No se pudo actualizar empleado {empleado_id}')
                return None
                
        except Exception as e:
            logger.error(f'Error actualizando empleado {empleado_id}: {e}')
            return None
    
    async def dar_baja(
        self, 
        empleado_id: int, 
        motivo: str,
        fecha_baja: Optional[date] = None
    ) -> bool:
        """Da de baja a un empleado"""
        try:
            data = {
                'estatus': EstatusEmpleado.BAJA.value,
                'fecha_baja': (fecha_baja or date.today()).isoformat(),
                'motivo_baja': motivo,
                'fecha_actualizacion': datetime.now().isoformat()
            }
            
            result = self.supabase.table('empleados').update(data).eq('id', empleado_id).execute()
            
            if result.data:
                # Registrar en historial
                await self._registrar_baja_historial(empleado_id, motivo, fecha_baja)
                logger.info(f'Empleado {empleado_id} dado de baja')
                return True
            else:
                logger.error(f'No se pudo dar de baja al empleado {empleado_id}')
                return False
                
        except Exception as e:
            logger.error(f'Error dando de baja empleado {empleado_id}: {e}')
            return False
    
    # ===============================
    # BÚSQUEDAS Y FILTROS
    # ===============================
    
    async def buscar(
        self,
        termino: str,
        empresa_id: Optional[int] = None,
        sede_id: Optional[int] = None
    ) -> List[EmpleadoResumen]:
        """Busca empleados por nombre, RFC o número"""
        try:
            # Búsqueda por múltiples campos
            query = self.supabase.table('empleados').select(
                'id, numero_empleado, nombre, apellido_paterno, apellido_materno, '
                'puesto_id, sede_id, empresa_id, estatus, telefono, fecha_ingreso'
            )
            
            # Aplicar filtros de empresa/sede si existen
            if empresa_id:
                query = query.eq('empresa_id', empresa_id)
            if sede_id:
                query = query.eq('sede_id', sede_id)
            
            # Buscar en múltiples campos
            query = query.or_(
                f"nombre.ilike.%{termino}%,"
                f"apellido_paterno.ilike.%{termino}%,"
                f"apellido_materno.ilike.%{termino}%,"
                f"rfc.ilike.%{termino}%,"
                f"numero_empleado.ilike.%{termino}%"
            )
            
            result = query.execute()
            
            resumenes = []
            for data in result.data:
                # Construir nombre completo
                nombre_completo = f"{data['nombre']} {data['apellido_paterno']}"
                if data.get('apellido_materno'):
                    nombre_completo += f" {data['apellido_materno']}"
                
                # Obtener nombres de puesto, sede y empresa (deberías hacer joins)
                resumen = EmpleadoResumen(
                    id=data['id'],
                    numero_empleado=data['numero_empleado'],
                    nombre_completo=nombre_completo,
                    puesto='Puesto',  # TODO: Join con tabla puestos
                    sede='Sede',  # TODO: Join con tabla sedes
                    empresa='Empresa',  # TODO: Join con tabla empresas
                    estatus=EstatusEmpleado(data['estatus']),
                    telefono=data['telefono'],
                    fecha_ingreso=data['fecha_ingreso']
                )
                resumenes.append(resumen)
            
            logger.info(f'Encontrados {len(resumenes)} empleados para "{termino}"')
            return resumenes
            
        except Exception as e:
            logger.error(f'Error buscando empleados: {e}')
            return []
    
    async def obtener_por_sede(self, sede_id: int) -> List[EmpleadoResumen]:
        """Obtiene empleados de una sede específica"""
        try:
            result = self.supabase.table('empleados').select(
                'id, numero_empleado, nombre, apellido_paterno, apellido_materno, '
                'estatus, telefono, fecha_ingreso'
            ).eq('sede_id', sede_id).eq('estatus', 'ACTIVO').execute()
            
            resumenes = []
            for data in result.data:
                nombre_completo = f"{data['nombre']} {data['apellido_paterno']}"
                if data.get('apellido_materno'):
                    nombre_completo += f" {data['apellido_materno']}"
                
                resumen = EmpleadoResumen(
                    id=data['id'],
                    numero_empleado=data['numero_empleado'],
                    nombre_completo=nombre_completo,
                    puesto='',
                    sede='',
                    empresa='',
                    estatus=EstatusEmpleado(data['estatus']),
                    telefono=data['telefono'],
                    fecha_ingreso=data['fecha_ingreso']
                )
                resumenes.append(resumen)
            
            return resumenes
            
        except Exception as e:
            logger.error(f'Error obteniendo empleados de sede {sede_id}: {e}')
            return []
    
    # ===============================
    # VALIDACIONES
    # ===============================
    
    async def validar_documentos_unicos(
        self,
        rfc: str,
        curp: str,
        nss: str,
        excluir_id: Optional[int] = None
    ) -> Dict[str, bool]:
        """Valida que RFC, CURP y NSS sean únicos"""
        try:
            validaciones = {
                'rfc_valido': True,
                'curp_valido': True,
                'nss_valido': True
            }
            
            # Validar RFC
            query = self.supabase.table('empleados').select('id').eq('rfc', rfc)
            if excluir_id:
                query = query.neq('id', excluir_id)
            result = query.execute()
            validaciones['rfc_valido'] = len(result.data) == 0
            
            # Validar CURP
            query = self.supabase.table('empleados').select('id').eq('curp', curp)
            if excluir_id:
                query = query.neq('id', excluir_id)
            result = query.execute()
            validaciones['curp_valido'] = len(result.data) == 0
            
            # Validar NSS
            query = self.supabase.table('empleados').select('id').eq('nss', nss)
            if excluir_id:
                query = query.neq('id', excluir_id)
            result = query.execute()
            validaciones['nss_valido'] = len(result.data) == 0
            
            return validaciones
            
        except Exception as e:
            logger.error(f'Error validando documentos: {e}')
            return {'rfc_valido': False, 'curp_valido': False, 'nss_valido': False}
    
    # ===============================
    # OPERACIONES AUXILIARES
    # ===============================
    
    async def _crear_historial_laboral(self, empleado: Empleado) -> bool:
        """Crea registro inicial en historial laboral"""
        try:
            historial = {
                'empleado_id': empleado.id,
                'fecha_movimiento': empleado.fecha_ingreso.isoformat(),
                'tipo_movimiento': 'ALTA',
                'empresa_id': empleado.empresa_id,
                'sede_id': empleado.sede_id,
                'puesto_id': empleado.puesto_id,
                'salario_diario': float(empleado.salario_diario),
                'observaciones': 'Alta inicial en el sistema',
                'fecha_creacion': datetime.now().isoformat()
            }
            
            # Incluir UUID del empleado
            if 'uuid' in data:
                historial['empleado_uuid'] = data['uuid']
            
            result = self.supabase.table('historial_laboral').insert(historial).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f'Error creando historial laboral: {e}')
            return False
    
    async def _registrar_cambio_sede(
        self,
        empleado_id: int,
        sede_anterior_id: int,
        sede_nueva_id: int
    ) -> bool:
        """Registra cambio de sede en historial"""
        try:
            historial = {
                'empleado_id': empleado_id,
                'fecha_movimiento': date.today().isoformat(),
                'tipo_movimiento': 'CAMBIO_SEDE',
                'sede_anterior_id': sede_anterior_id,
                'sede_id': sede_nueva_id,
                'observaciones': f'Cambio de sede {sede_anterior_id} a {sede_nueva_id}',
                'fecha_creacion': datetime.now().isoformat()
            }
            
            result = self.supabase.table('historial_laboral').insert(historial).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f'Error registrando cambio de sede: {e}')
            return False
    
    async def _registrar_baja_historial(
        self,
        empleado_id: int,
        motivo: str,
        fecha_baja: Optional[date] = None
    ) -> bool:
        """Registra baja en historial laboral"""
        try:
            historial = {
                'empleado_id': empleado_id,
                'fecha_movimiento': (fecha_baja or date.today()).isoformat(),
                'tipo_movimiento': 'BAJA',
                'observaciones': motivo,
                'fecha_creacion': datetime.now().isoformat()
            }
            
            result = self.supabase.table('historial_laboral').insert(historial).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f'Error registrando baja en historial: {e}')
            return False
    
    async def generar_numero_empleado(self, empresa_id: int) -> str:
        """
        Genera número de empleado con formato: PLT-2024-001 o MNT-2024-001
        
        Args:
            empresa_id: ID de la empresa
            
        Returns:
            Número de empleado generado
        """
        try:
            # Obtener prefijo según empresa
            empresa_result = self.supabase.table('empresas').select('nombre_comercial').eq('id', empresa_id).execute()
            
            if not empresa_result.data:
                prefijo = "EMP"
            else:
                nombre = empresa_result.data[0]['nombre_comercial'].upper()
                if 'PLETORICA' in nombre:
                    prefijo = 'PLT'
                elif 'MANTISER' in nombre:
                    prefijo = 'MNT'
                else:
                    prefijo = 'EMP'
            
            # Año actual
            anio = date.today().year
            
            # Obtener el último número para esta empresa y año
            pattern = f"{prefijo}-{anio}-%"
            result = self.supabase.table('empleados').select('numero_empleado').like(
                'numero_empleado', pattern
            ).order('numero_empleado', desc=True).limit(1).execute()
            
            if result.data:
                # Extraer el número y sumar 1
                ultimo = result.data[0]['numero_empleado']
                numero_actual = int(ultimo.split('-')[-1])
                siguiente = numero_actual + 1
            else:
                siguiente = 1
            
            # Formatear con ceros a la izquierda
            numero_empleado = f"{prefijo}-{anio}-{siguiente:03d}"
            
            logger.info(f'Número de empleado generado: {numero_empleado}')
            return numero_empleado
            
        except Exception as e:
            logger.error(f'Error generando número de empleado: {e}')
            # Fallback con timestamp
            import time
            return f"EMP-{int(time.time())}"
    
    async def obtener_url_publica(self, empleado_uuid: UUID) -> str:
        """
        Genera URL pública segura para compartir con BUAP
        
        Args:
            empleado_uuid: UUID del empleado
            
        Returns:
            URL pública para consulta
        """
        # Esta URL usa UUID en lugar de ID secuencial
        base_url = "https://tusistema.com/consulta/empleado"
        return f"{base_url}/{empleado_uuid}"
    
    # ===============================
    # OPERACIONES DE HISTORIAL
    # ===============================
    
    async def obtener_historial(self, empleado_id: int) -> List[Dict]:
        """Obtiene el historial laboral completo de un empleado"""
        try:
            result = self.supabase.table('historial_laboral').select('*').eq(
                'empleado_id', empleado_id
            ).order('fecha_movimiento', desc=True).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f'Error obteniendo historial de empleado {empleado_id}: {e}')
            return []
    
    async def obtener_historial_por_uuid(self, empleado_uuid: UUID) -> List[Dict]:
        """
        Obtiene historial usando UUID (más confiable para auditorías)
        Encuentra TODOS los movimientos aunque el ID haya cambiado
        """
        try:
            result = self.supabase.table('historial_laboral').select('*').eq(
                'empleado_uuid', str(empleado_uuid)
            ).order('fecha_movimiento', desc=True).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f'Error obteniendo historial por UUID {empleado_uuid}: {e}')
            return []


# Instancia global del servicio
empleado_service = EmpleadoService()