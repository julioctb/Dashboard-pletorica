# app/pages/empresas/empresas_state.py
# VERSIÓN CORREGIDA - Compatible con el nuevo servicio

import reflex as rx
from typing import List, Optional
from app.services.empresa_service import empresa_service
from app.database.models.empresa_models import (
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
    empresa_seleccionada: Optional[Empresa] = None
    
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
    
    # Setters para formulario
    def set_form_nombre_comercial(self, value: str):
        self.form_nombre_comercial = value
    
    def set_form_razon_social(self, value: str):
        self.form_razon_social = value
    
    def set_form_tipo_empresa(self, value: str):
        self.form_tipo_empresa = value
    
    def set_form_rfc(self, value: str):
        self.form_rfc = value.upper()
    
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
    # INICIALIZACIÓN Y CARGA
    # ========================
    async def cargar_empresas(self):
        """Carga la lista de empresas aplicando filtros"""
        try:
            self.loading = True
            self.mensaje_info = ""
            
            # Obtener todas las empresas
            empresas_completas = await empresa_service.obtener_todas(
                incluir_inactivas=self.incluir_inactivas
            )
            
            # Convertir a resumen manualmente
            self.empresas = []
            for empresa in empresas_completas:
                # Aplicar filtros
                if self.filtro_tipo and empresa.tipo_empresa != self.filtro_tipo:
                    continue
                
                if self.filtro_estatus and empresa.estatus != self.filtro_estatus:
                    continue
                
                if self.filtro_busqueda:
                    busqueda = self.filtro_busqueda.lower()
                    if busqueda not in empresa.nombre_comercial.lower() and \
                       busqueda not in empresa.razon_social.lower():
                        continue
                
                # Crear resumen
                resumen = EmpresaResumen(
                    id=empresa.id,
                    nombre_comercial=empresa.nombre_comercial,
                    tipo_empresa=empresa.tipo_empresa,
                    estatus=empresa.estatus,
                    contacto_principal=empresa.email or empresa.telefono or "Sin contacto",
                    fecha_creacion=empresa.fecha_creacion
                )
                self.empresas.append(resumen)
            
            if not self.empresas:
                self.mensaje_info = "No se encontraron empresas con los filtros aplicados"
                self.tipo_mensaje = "info"
            else:
                self.mensaje_info = f"Se encontraron {len(self.empresas)} empresas"
                self.tipo_mensaje = "info"
            
        except Exception as e:
            self.mensaje_info = f"Error al cargar empresas: {str(e)}"
            self.tipo_mensaje = "error"
            self.empresas = []
        finally:
            self.loading = False
    
    async def aplicar_filtros(self):
        """Aplica los filtros seleccionados"""
        await self.cargar_empresas()
    
    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.filtro_tipo = ""
        self.filtro_estatus = ""
        self.filtro_busqueda = ""
        self.incluir_inactivas = False
    
    # ========================
    # OPERACIONES CRUD
    # ========================
    async def crear_empresa(self):
        """Crea una nueva empresa"""
        try:
            self.loading = True
            self.mensaje_info = ""
            
            # Validaciones básicas
            if not self.form_nombre_comercial:
                self.mensaje_info = "El nombre comercial es requerido"
                self.tipo_mensaje = "error"
                return
            
            if not self.form_razon_social:
                self.mensaje_info = "La razón social es requerida"
                self.tipo_mensaje = "error"
                return
            
            if not self.form_rfc or len(self.form_rfc) < 12:
                self.mensaje_info = "El RFC es requerido (mínimo 12 caracteres)"
                self.tipo_mensaje = "error"
                return
            
            # Crear objeto para enviar
            nueva_empresa = EmpresaCreate(
                nombre_comercial=self.form_nombre_comercial,
                razon_social=self.form_razon_social,
                tipo_empresa=TipoEmpresa(self.form_tipo_empresa),
                rfc=self.form_rfc.upper(),
                direccion=self.form_direccion or None,
                codigo_postal=self.form_codigo_postal or None,
                telefono=self.form_telefono or None,
                email=self.form_email or None,
                pagina_web=self.form_pagina_web or None,
                estatus=EstatusEmpresa(self.form_estatus),
                notas=self.form_notas or None
            )
            
            # Llamar al servicio
            empresa_creada = await empresa_service.crear(nueva_empresa)
            
            if empresa_creada:
                self.mensaje_info = f"Empresa '{empresa_creada.nombre_comercial}' creada exitosamente"
                self.tipo_mensaje = "success"
                self.mostrar_modal_crear = False
                self.limpiar_formulario()
                await self.cargar_empresas()
            else:
                self.mensaje_info = "No se pudo crear la empresa"
                self.tipo_mensaje = "error"
                
        except Exception as e:
            self.mensaje_info = f"Error al crear empresa: {str(e)}"
            self.tipo_mensaje = "error"
        finally:
            self.loading = False
    
    async def actualizar_empresa(self):
        """Actualiza la empresa seleccionada"""
        try:
            if not self.empresa_seleccionada:
                self.mensaje_info = "No hay empresa seleccionada"
                self.tipo_mensaje = "error"
                return
            
            self.loading = True
            self.mensaje_info = ""
            
            # Crear objeto de actualización
            datos_actualizacion = EmpresaUpdate(
                nombre_comercial=self.form_nombre_comercial,
                razon_social=self.form_razon_social,
                tipo_empresa=TipoEmpresa(self.form_tipo_empresa),
                rfc=self.form_rfc.upper(),
                direccion=self.form_direccion or None,
                codigo_postal=self.form_codigo_postal or None,
                telefono=self.form_telefono or None,
                email=self.form_email or None,
                pagina_web=self.form_pagina_web or None,
                estatus=EstatusEmpresa(self.form_estatus),
                notas=self.form_notas or None
            )
            
            # Llamar al servicio
            empresa_actualizada = await empresa_service.actualizar(
                self.empresa_seleccionada.id, 
                datos_actualizacion
            )
            
            if empresa_actualizada:
                self.mensaje_info = f"Empresa '{empresa_actualizada.nombre_comercial}' actualizada"
                self.tipo_mensaje = "success"
                self.mostrar_modal_editar = False
                await self.cargar_empresas()
            else:
                self.mensaje_info = "No se pudo actualizar la empresa"
                self.tipo_mensaje = "error"
                
        except Exception as e:
            self.mensaje_info = f"Error al actualizar: {str(e)}"
            self.tipo_mensaje = "error"
        finally:
            self.loading = False
    
    async def ver_detalle_empresa(self, empresa_id: int):
        """Carga el detalle de una empresa"""
        try:
            self.loading = True
            
            # Obtener empresa completa
            self.empresa_seleccionada = await empresa_service.obtener_por_id(empresa_id)
            
            if self.empresa_seleccionada:
                self.mostrar_modal_detalle = True
            else:
                self.mensaje_info = "No se pudo cargar la empresa"
                self.tipo_mensaje = "error"
                
        except Exception as e:
            self.mensaje_info = f"Error al cargar detalle: {str(e)}"
            self.tipo_mensaje = "error"
        finally:
            self.loading = False
    
    async def editar_empresa(self, empresa_id: int):
        """Prepara el formulario para editar una empresa"""
        try:
            self.loading = True
            
            # Obtener empresa
            self.empresa_seleccionada = await empresa_service.obtener_por_id(empresa_id)
            
            if self.empresa_seleccionada:
                # Cargar datos en el formulario
                self.form_nombre_comercial = self.empresa_seleccionada.nombre_comercial
                self.form_razon_social = self.empresa_seleccionada.razon_social
                self.form_tipo_empresa = self.empresa_seleccionada.tipo_empresa.value
                self.form_rfc = self.empresa_seleccionada.rfc
                self.form_direccion = self.empresa_seleccionada.direccion or ""
                self.form_codigo_postal = self.empresa_seleccionada.codigo_postal or ""
                self.form_telefono = self.empresa_seleccionada.telefono or ""
                self.form_email = self.empresa_seleccionada.email or ""
                self.form_pagina_web = self.empresa_seleccionada.pagina_web or ""
                self.form_estatus = self.empresa_seleccionada.estatus.value
                self.form_notas = self.empresa_seleccionada.notas or ""
                
                self.mostrar_modal_editar = True
            else:
                self.mensaje_info = "No se pudo cargar la empresa"
                self.tipo_mensaje = "error"
                
        except Exception as e:
            self.mensaje_info = f"Error al cargar empresa: {str(e)}"
            self.tipo_mensaje = "error"
        finally:
            self.loading = False
    
    # ========================
    # UTILIDADES
    # ========================
    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
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
    
    def cerrar_modal_crear(self):
        """Cierra el modal de crear y limpia el formulario"""
        self.mostrar_modal_crear = False
        self.limpiar_formulario()
    
    def cerrar_modal_editar(self):
        """Cierra el modal de editar"""
        self.mostrar_modal_editar = False
        self.empresa_seleccionada = None
        self.limpiar_formulario()
    
    def cerrar_modal_detalle(self):
        """Cierra el modal de detalle"""
        self.mostrar_modal_detalle = False
        self.empresa_seleccionada = None