import reflex as rx
from typing import List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal

from app.services.empleado_service import empleado_service
from app.services.empresa_service import empresa_service
from app.database.models.empleado_models import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
    EstatusEmpleado,
    TipoContrato,
    EstadoCivil
)

class EmpleadosState(rx.State):
    """Estado para gestión de empleados"""
    
    # ========================
    # DATOS Y LISTAS
    # ========================
    empleados: List[EmpleadoResumen] = []
    empleado_seleccionado: Optional[Empleado] = None
    empresas_lista: List[Dict] = []
    sedes_lista: List[Dict] = []
    puestos_lista: List[Dict] = []
    
    # ========================
    # FILTROS Y BÚSQUEDA
    # ========================
    filtro_busqueda: str = ""
    filtro_empresa: str = ""
    filtro_sede: str = ""
    filtro_estatus: str = ""
    incluir_bajas: bool = False
    
    # ========================
    # ESTADO DE LA UI
    # ========================
    loading: bool = False
    mostrar_modal_crear: bool = False
    mostrar_modal_editar: bool = False
    mostrar_modal_detalle: bool = False
    mostrar_modal_baja: bool = False
    mensaje_info: str = ""
    tipo_mensaje: str = "info"
    tab_activa: str = "datos_personales"
    
    # ========================
    # FORMULARIO DE EMPLEADO
    # ========================
    # Datos personales
    form_numero_empleado: str = ""
    form_nombre: str = ""
    form_apellido_paterno: str = ""
    form_apellido_materno: str = ""
    form_fecha_nacimiento: str = ""
    form_genero: str = "M"
    form_estado_civil: str = EstadoCivil.SOLTERO.value
    form_rfc: str = ""
    form_curp: str = ""
    form_nss: str = ""
    
    # Datos de contacto
    form_direccion: str = ""
    form_colonia: str = ""
    form_ciudad: str = "Puebla"
    form_estado: str = "Puebla"
    form_codigo_postal: str = ""
    form_telefono: str = ""
    form_telefono_emergencia: str = ""
    form_contacto_emergencia: str = ""
    form_email_personal: str = ""
    
    # Datos laborales
    form_empresa_id: str = ""
    form_sede_id: str = ""
    form_puesto_id: str = ""
    form_departamento_id: str = ""
    form_jefe_directo_id: str = ""
    form_fecha_ingreso: str = ""
    form_tipo_contrato: str = TipoContrato.INDETERMINADO.value
    
    # Datos salariales
    form_salario_diario: str = ""
    form_salario_diario_integrado: str = ""
    form_salario_mensual: str = ""
    
    # Datos bancarios
    form_banco: str = ""
    form_numero_cuenta: str = ""
    form_clabe: str = ""
    
    # Baja
    form_motivo_baja: str = ""
    form_fecha_baja: str = ""
    
    # ========================
    # INICIALIZACIÓN
    # ========================
    async def inicializar(self):
        """Carga datos iniciales"""
        await self.cargar_catalogos()
        await self.cargar_empleados()
    
    async def cargar_catalogos(self):
        """Carga catálogos necesarios"""
        try:
            # Cargar empresas
            empresas = await empresa_service.obtener_todas(incluir_inactivas=False)
            self.empresas_lista = [
                {'id': e.id, 'nombre': e.nombre_comercial} 
                for e in empresas
            ]
            
            # TODO: Cargar sedes y puestos cuando tengas esos servicios
            self.sedes_lista = [
                {'id': 1, 'nombre': 'Ciudad Universitaria'},
                {'id': 2, 'nombre': 'Complejo Cultural'},
                {'id': 3, 'nombre': 'Hospital Universitario'}
            ]
            
            self.puestos_lista = [
                {'id': 1, 'nombre': 'Jardinero'},
                {'id': 2, 'nombre': 'Supervisor'},
                {'id': 3, 'nombre': 'Auxiliar de Limpieza'},
                {'id': 4, 'nombre': 'Electricista'}
            ]
            
        except Exception as e:
            self.mensaje_info = f"Error cargando catálogos: {str(e)}"
            self.tipo_mensaje = "error"
    
    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def cargar_empleados(self):
        """Carga lista de empleados con filtros"""
        self.loading = True
        try:
            # Aplicar búsqueda si existe
            if self.filtro_busqueda:
                self.empleados = await empleado_service.buscar(
                    termino=self.filtro_busqueda,
                    empresa_id=int(self.filtro_empresa) if self.filtro_empresa else None,
                    sede_id=int(self.filtro_sede) if self.filtro_sede else None
                )
            else:
                # Obtener todos con filtros
                empleados_completos = await empleado_service.obtener_todos(
                    empresa_id=int(self.filtro_empresa) if self.filtro_empresa else None,
                    sede_id=int(self.filtro_sede) if self.filtro_sede else None,
                    incluir_bajas=self.incluir_bajas
                )
                
                # Convertir a resumen
                self.empleados = []
                for emp in empleados_completos:
                    resumen = EmpleadoResumen(
                        id=emp.id,
                        numero_empleado=emp.numero_empleado,
                        nombre_completo=emp.nombre_completo,
                        puesto=str(emp.puesto_id),  # TODO: Obtener nombre real
                        sede=str(emp.sede_id),  # TODO: Obtener nombre real
                        empresa=str(emp.empresa_id),  # TODO: Obtener nombre real
                        estatus=emp.estatus,
                        telefono=emp.telefono,
                        fecha_ingreso=emp.fecha_ingreso
                    )
                    self.empleados.append(resumen)
                
                # Aplicar filtro de estatus si existe
                if self.filtro_estatus:
                    self.empleados = [
                        e for e in self.empleados 
                        if e.estatus.value == self.filtro_estatus
                    ]
            
            self.mensaje_info = f"Se encontraron {len(self.empleados)} empleados"
            self.tipo_mensaje = "info"
            
        except Exception as e:
            self.mensaje_info = f"Error al cargar empleados: {str(e)}"
            self.tipo_mensaje = "error"
            self.empleados = []
        finally:
            self.loading = False
    
    async def crear_empleado(self):
        """Crea un nuevo empleado"""
        try:
            # Validar campos obligatorios
            if not all([
                self.form_numero_empleado,
                self.form_nombre,
                self.form_apellido_paterno,
                self.form_fecha_nacimiento,
                self.form_rfc,
                self.form_curp,
                self.form_nss,
                self.form_empresa_id,
                self.form_sede_id,
                self.form_puesto_id
            ]):
                self.mensaje_info = "Todos los campos marcados son obligatorios"
                self.tipo_mensaje = "error"
                return
            
            # Crear objeto EmpleadoCreate
            nuevo_empleado = EmpleadoCreate(
                numero_empleado=self.form_numero_empleado.strip(),
                nombre=self.form_nombre.strip().upper(),
                apellido_paterno=self.form_apellido_paterno.strip().upper(),
                apellido_materno=self.form_apellido_materno.strip().upper() if self.form_apellido_materno else None,
                fecha_nacimiento=date.fromisoformat(self.form_fecha_nacimiento),
                genero=self.form_genero,
                estado_civil=EstadoCivil(self.form_estado_civil),
                rfc=self.form_rfc.strip().upper(),
                curp=self.form_curp.strip().upper(),
                nss=self.form_nss.strip(),
                direccion=self.form_direccion.strip(),
                colonia=self.form_colonia.strip(),
                ciudad=self.form_ciudad.strip(),
                estado=self.form_estado.strip(),
                codigo_postal=self.form_codigo_postal.strip(),
                telefono=self.form_telefono.strip(),
                telefono_emergencia=self.form_telefono_emergencia.strip(),
                contacto_emergencia=self.form_contacto_emergencia.strip(),
                email_personal=self.form_email_personal.strip() if self.form_email_personal else None,
                empresa_id=int(self.form_empresa_id),
                sede_id=int(self.form_sede_id),
                puesto_id=int(self.form_puesto_id),
                departamento_id=int(self.form_departamento_id) if self.form_departamento_id else None,
                jefe_directo_id=int(self.form_jefe_directo_id) if self.form_jefe_directo_id else None,
                fecha_ingreso=date.fromisoformat(self.form_fecha_ingreso),
                tipo_contrato=TipoContrato(self.form_tipo_contrato),
                salario_diario=Decimal(self.form_salario_diario),
                salario_diario_integrado=Decimal(self.form_salario_diario_integrado),
                salario_mensual=Decimal(self.form_salario_mensual),
                banco=self.form_banco.strip() if self.form_banco else None,
                numero_cuenta=self.form_numero_cuenta.strip() if self.form_numero_cuenta else None,
                clabe_interbancaria=self.form_clabe.strip() if self.form_clabe else None
            )
            
            # Crear empleado
            empleado_creado = await empleado_service.crear(nuevo_empleado)
            
            if empleado_creado:
                self.cerrar_modal_crear()
                await self.cargar_empleados()
                self.mensaje_info = f"Empleado '{empleado_creado.nombre_completo}' creado exitosamente"
                self.tipo_mensaje = "success"
                return rx.toast.success(self.mensaje_info)
            else:
                self.mensaje_info = "No se pudo crear el empleado. Verifique que RFC, CURP y NSS no estén duplicados"
                self.tipo_mensaje = "error"
                return rx.toast.error(self.mensaje_info)
                
        except Exception as e:
            self.mensaje_info = f"Error al crear empleado: {str(e)}"
            self.tipo_mensaje = "error"
            return rx.toast.error(self.mensaje_info)