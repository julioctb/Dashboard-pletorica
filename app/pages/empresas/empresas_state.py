import reflex as rx
from typing import List
from app.services import empresa_service
from app.database.models import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
    TipoEmpresa,
    EstatusEmpresa
)

class EmpresasState(rx.State):
    """Estado para la gestión de empresas"""
    
    # ========================
    # DATOS Y LISTAS
    # ========================
    empresas: List[EmpresaResumen] = []
    empresa_seleccionada: Empresa | None = None
    
    # ========================
    # FILTROS Y BÚSQUEDA
    # ========================
    filtro_tipo: str = ""
    filtro_estatus: str = ""
    filtro_busqueda: str = ""
    incluir_inactivas: bool = False
    
    # ========================
    # ESTADO DE LA UI
    # ========================
    loading: bool = False
    mostrar_modal_crear: bool = False
    mostrar_modal_editar: bool = False
    mostrar_modal_detalle: bool = False
    mensaje_info: str = ""
    tipo_mensaje: str = "info"  # info, success, error
    
    # ========================
    # FORMULARIO DE EMPRESA
    # ========================
    form_nombre_comercial: str = ""
    form_razon_social: str = ""
    form_tipo_empresa: str = TipoEmpresa.NOMINA.value
    form_rfc: str = ""
    form_direccion: str = ""
    form_codigo_postal: str = ""
    form_telefono: str = ""
    form_email: str = ""
    form_pagina_web: str = ""
    form_estatus: str = EstatusEmpresa.ACTIVO.value
    form_notas: str = ""
    
    # ========================
    # SETTERS EXPLÍCITOS (Reflex v0.8.9+)
    # ========================
    def set_filtro_tipo(self, value: str):
        self.filtro_tipo = value
    
    def set_filtro_estatus(self, value: str):
        self.filtro_estatus = value
    
    def set_filtro_busqueda(self, value: str):
        self.filtro_busqueda = value
    
    def set_incluir_inactivas(self, value: bool):
        self.incluir_inactivas = value
    
    def set_mostrar_modal_crear(self, value: bool):
        self.mostrar_modal_crear = value
    
    def set_mostrar_modal_editar(self, value: bool):
        self.mostrar_modal_editar = value
    
    def set_mostrar_modal_detalle(self, value: bool):
        self.mostrar_modal_detalle = value
    
    # Setters del formulario
    def set_form_nombre_comercial(self, value: str):
        self.form_nombre_comercial = value
    
    def set_form_razon_social(self, value: str):
        self.form_razon_social = value
    
    def set_form_tipo_empresa(self, value: str):
        self.form_tipo_empresa = value
    
    def set_form_rfc(self, value: str):
        self.form_rfc = value
    
    def set_form_direccion(self, value: str):
        self.form_direccion = value
    
    def set_form_codigo_postal(self, value: str):
        self.form_codigo_postal = value
    
    def set_form_telefono(self, value: str):
        self.form_telefono = value
    
    def set_form_email(self, value: str):
        self.form_email = value
    
    def set_form_pagina_web(self, value: str):
        self.form_pagina_web = value
    
    def set_form_estatus(self, value: str):
        self.form_estatus = value
    
    def set_form_notas(self, value: str):
        self.form_notas = value
    
    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def cargar_empresas(self):
        """Cargar la lista de empresas aplicando filtros"""
        self.loading = True
        try:
            if self.filtro_busqueda:
                # Buscar por nombre
                empresas_completas = await empresa_service.buscar_por_nombre(self.filtro_busqueda)
                # Convertir a resumen
                self.empresas = []
                for empresa in empresas_completas:
                    resumen = EmpresaResumen(
                        id=empresa.id,
                        nombre_comercial=empresa.nombre_comercial,
                        tipo_empresa=empresa.tipo_empresa,
                        estatus=empresa.estatus,
                        contacto_principal=empresa.email or empresa.telefono or "Sin contacto",
                        fecha_creacion=empresa.fecha_creacion
                    )
                    self.empresas.append(resumen)
            else:
                # Obtener resumen de todas las empresas
                self.empresas = await empresa_service.obtener_resumen_empresas()
                
                # Aplicar filtros
                if self.filtro_tipo:
                    self.empresas = [e for e in self.empresas if e.tipo_empresa.value == self.filtro_tipo]
                
                if self.filtro_estatus:
                    self.empresas = [e for e in self.empresas if e.estatus.value == self.filtro_estatus]
                
                if not self.incluir_inactivas:
                    self.empresas = [e for e in self.empresas if e.estatus == EstatusEmpresa.ACTIVO]
            
            self.mensaje_info = f"Se encontraron {len(self.empresas)} empresas"
            self.tipo_mensaje = "info"
            
        except Exception as e:
            self.mensaje_info = f"Error al cargar empresas: {str(e)}"
            self.tipo_mensaje = "error"
            self.empresas = []
        finally:
            self.loading = False
    
    async def crear_empresa(self):
        """Crear una nueva empresa"""
        try:
            # Validar campos obligatorios
            if not self.form_nombre_comercial or not self.form_razon_social or not self.form_rfc:
                self.mensaje_info = "Nombre comercial, razón social y RFC son obligatorios"
                self.tipo_mensaje = "error"
                return
            
            # Crear objeto EmpresaCreate
            nueva_empresa = EmpresaCreate(
                nombre_comercial=self.form_nombre_comercial.strip(),
                razon_social=self.form_razon_social.strip(),
                tipo_empresa=TipoEmpresa(self.form_tipo_empresa),
                rfc=self.form_rfc.strip().upper(),
                direccion=self.form_direccion.strip() or None,
                codigo_postal=self.form_codigo_postal.strip() or None,
                telefono=self.form_telefono.strip() or None,
                email=self.form_email.strip() or None,
                pagina_web=self.form_pagina_web.strip() or None,
                estatus=EstatusEmpresa(self.form_estatus),
                notas=self.form_notas.strip() or None
            )
            
            # Crear la empresa
            empresa_creada = await empresa_service.crear(nueva_empresa)
            
            if empresa_creada:
                # Cerrar modal y recargar lista
                self.cerrar_modal_crear()
                await self.cargar_empresas()
                
                self.mensaje_info = f"Empresa '{empresa_creada.nombre_comercial}' creada exitosamente"
                self.tipo_mensaje = "success"
            else:
                self.mensaje_info = "No se pudo crear la empresa. Verifique que el RFC no esté duplicado"
                self.tipo_mensaje = "error"
            
        except Exception as e:
            self.mensaje_info = f"Error al crear empresa: {str(e)}"
            self.tipo_mensaje = "error"
    
    async def actualizar_empresa(self):
        """Actualizar empresa existente"""
        try:
            if not self.empresa_seleccionada:
                return
            
            # Crear objeto EmpresaUpdate con solo los campos modificados
            update_data = EmpresaUpdate(
                nombre_comercial=self.form_nombre_comercial.strip() or None,
                razon_social=self.form_razon_social.strip() or None,
                tipo_empresa=TipoEmpresa(self.form_tipo_empresa) if self.form_tipo_empresa else None,
                rfc=self.form_rfc.strip().upper() or None,
                direccion=self.form_direccion.strip() or None,
                codigo_postal=self.form_codigo_postal.strip() or None,
                telefono=self.form_telefono.strip() or None,
                email=self.form_email.strip() or None,
                pagina_web=self.form_pagina_web.strip() or None,
                estatus=EstatusEmpresa(self.form_estatus) if self.form_estatus else None,
                notas=self.form_notas.strip() or None
            )
            
            # Actualizar la empresa
            empresa_actualizada = await empresa_service.actualizar(self.empresa_seleccionada.id, update_data)
            
            if empresa_actualizada:
                # Cerrar modal y recargar lista
                self.cerrar_modal_editar()
                await self.cargar_empresas()
                
                self.mensaje_info = f"Empresa '{empresa_actualizada.nombre_comercial}' actualizada exitosamente"
                self.tipo_mensaje = "success"
            else:
                self.mensaje_info = "No se pudo actualizar la empresa"
                self.tipo_mensaje = "error"
            
        except Exception as e:
            self.mensaje_info = f"Error al actualizar empresa: {str(e)}"
            self.tipo_mensaje = "error"
    
    async def cambiar_estatus_empresa(self, empresa_id: int, nuevo_estatus: EstatusEmpresa):
        """Cambiar estatus de una empresa"""
        try:
            resultado = await empresa_service.cambiar_estatus(empresa_id, nuevo_estatus)
            
            if resultado:
                await self.cargar_empresas()
                self.mensaje_info = f"Estatus cambiado a {nuevo_estatus.value}"
                self.tipo_mensaje = "success"
            else:
                self.mensaje_info = "No se pudo cambiar el estatus"
                self.tipo_mensaje = "error"
                
        except Exception as e:
            self.mensaje_info = f"Error al cambiar estatus: {str(e)}"
            self.tipo_mensaje = "error"
    
    # ========================
    # OPERACIONES DE MODALES
    # ========================
    def abrir_modal_crear(self):
        """Abrir modal para crear nueva empresa"""
        self.limpiar_formulario()
        self.mostrar_modal_crear = True
    
    def cerrar_modal_crear(self):
        """Cerrar modal de crear empresa"""
        self.mostrar_modal_crear = False
        self.limpiar_formulario()
    
    async def abrir_modal_detalle(self, empresa_id: int):
        """Abrir modal con detalles de la empresa"""
        try:
            self.empresa_seleccionada = await empresa_service.obtener_por_id(empresa_id)
            if self.empresa_seleccionada:
                self.mostrar_modal_detalle = True
            else:
                self.mensaje_info = "No se pudo cargar la información de la empresa"
                self.tipo_mensaje = "error"
        except Exception as e:
            self.mensaje_info = f"Error al cargar empresa: {str(e)}"
            self.tipo_mensaje = "error"
    
    def cerrar_modal_detalle(self):
        """Cerrar modal de detalles"""
        self.mostrar_modal_detalle = False
        self.empresa_seleccionada = None
    
    async def abrir_modal_editar(self, empresa_id: int):
        """Abrir modal para editar empresa"""
        try:
            empresa = await empresa_service.obtener_por_id(empresa_id)
            if empresa:
                # Cargar datos en el formulario
                self.form_nombre_comercial = empresa.nombre_comercial
                self.form_razon_social = empresa.razon_social
                self.form_tipo_empresa = str(empresa.tipo_empresa)
                self.form_rfc = empresa.rfc
                self.form_direccion = empresa.direccion or ""
                self.form_codigo_postal = empresa.codigo_postal or ""
                self.form_telefono = empresa.telefono or ""
                self.form_email = empresa.email or ""
                self.form_pagina_web = empresa.pagina_web or ""
                self.form_estatus = str(empresa.estatus)
                self.form_notas = empresa.notas or ""
                
                self.empresa_seleccionada = empresa
                self.mostrar_modal_editar = True
            else:
                self.mensaje_info = "No se pudo cargar la empresa para editar"
                self.tipo_mensaje = "error"
        except Exception as e:
            self.mensaje_info = f"Error al cargar empresa: {str(e)}"
            self.tipo_mensaje = "error"
    
    def cerrar_modal_editar(self):
        """Cerrar modal de editar empresa"""
        self.mostrar_modal_editar = False
        self.empresa_seleccionada = None
        self.limpiar_formulario()
    
    # ========================
    # OPERACIONES DE FILTROS
    # ========================
    async def aplicar_filtros(self):
        """Aplicar filtros de búsqueda"""
        await self.cargar_empresas()
    
    async def limpiar_filtros(self):
        """Limpiar todos los filtros"""
        self.filtro_tipo = ""
        self.filtro_estatus = ""
        self.filtro_busqueda = ""
        self.incluir_inactivas = False
        await self.cargar_empresas()
    
    # ========================
    # UTILIDADES
    # ========================
    def limpiar_formulario(self):
        """Limpiar campos del formulario"""
        self.form_nombre_comercial = ""
        self.form_razon_social = ""
        self.form_tipo_empresa = TipoEmpresa.NOMINA.value
        self.form_rfc = ""
        self.form_direccion = ""
        self.form_codigo_postal = ""
        self.form_telefono = ""
        self.form_email = ""
        self.form_pagina_web = ""
        self.form_estatus = EstatusEmpresa.ACTIVO.value
        self.form_notas = ""
    
    def limpiar_mensajes(self):
        """Limpiar mensajes informativos"""
        self.mensaje_info = ""
        self.tipo_mensaje = "info"