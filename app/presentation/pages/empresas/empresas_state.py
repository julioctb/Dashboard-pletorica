import reflex as rx
from app.presentation.components.shared.base_state import BaseState
from typing import List
from app.services import empresa_service

from app.entities import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
    TipoEmpresa,
    EstatusEmpresa
)

from .empresas_validators import (
    validar_nombre_comercial,
    validar_razon_social,
    validar_rfc,
    validar_email,
    validar_codigo_postal,
    validar_telefono
)

class EmpresasState(BaseState):
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
    mostrar_modal_empresa: bool = False  # Modal unificado crear/editar
    modo_modal_empresa: str = ""  # "crear" | "editar" | ""
    mostrar_modal_detalle: bool = False
    
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
    # ERRORES DE VALIDACIÓN DEL FORMULARIO
    # ========================
    error_nombre_comercial: str = ""
    error_razon_social: str = ""
    error_rfc: str = ""
    error_email: str = ""
    error_codigo_postal: str = ""
    error_telefono: str = ""

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

    def set_mostrar_modal_empresa(self, value: bool):
        self.mostrar_modal_empresa = value

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

                # Filtro de estatus: si hay filtro específico, usarlo; si no, aplicar incluir_inactivas
                if self.filtro_estatus:
                    self.empresas = [e for e in self.empresas if e.estatus.value == self.filtro_estatus]
                elif not self.incluir_inactivas:
                    # Solo filtrar activos si NO hay filtro de estatus específico
                    self.empresas = [e for e in self.empresas if e.estatus == EstatusEmpresa.ACTIVO]

            self.mostrar_mensaje(f"Se encontraron {len(self.empresas)} empresas", "info")

        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar empresas: {str(e)}", "error")
            self.empresas = []
        finally:
            self.loading = False
    
    async def crear_empresa(self):
        """Crear una nueva empresa"""
        try:
            # Crear objeto EmpresaCreate (validaciones ya hechas en formulario)
            nueva_empresa = EmpresaCreate(
                nombre_comercial=self.form_nombre_comercial.strip().upper(),
                razon_social=self.form_razon_social.strip().upper(),
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
                self.cerrar_modal_empresa()
                await self.cargar_empresas()

                # Mostrar toast de éxito (modal ya cerrado)
                return rx.toast.success(
                    f"Empresa '{empresa_creada.nombre_comercial}' creada exitosamente",
                    position="top-center",
                    duration=4000
                )
            else:
                # Error al crear (mostrar en modal)
                self.mostrar_mensaje(
                    "No se pudo crear la empresa. Verifique que el RFC no esté duplicado",
                    "error"
                )
                return  # NO cerrar modal

        except ValueError as e:
            # Errores de backend (RFC duplicado, etc.)
            self.mostrar_mensaje(str(e), "error")
            return  # NO cerrar modal

        except Exception as e:
            # Errores inesperados
            self.mostrar_mensaje(f"Error al crear empresa: {str(e)}", "error")
            return  # NO cerrar modal
    
    async def actualizar_empresa(self):
        """Actualizar empresa existente"""
        try:
            if not self.empresa_seleccionada:
                return

            # Crear objeto EmpresaUpdate (validaciones ya hechas en formulario)
            update_data = EmpresaUpdate(
                nombre_comercial=self.form_nombre_comercial.strip().upper() or None,
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
                self.cerrar_modal_empresa()
                await self.cargar_empresas()

                # Mostrar toast de éxito (modal ya cerrado)
                return rx.toast.success(
                    f"Empresa '{empresa_actualizada.nombre_comercial}' actualizada exitosamente",
                    position="top-center",
                    duration=4000
                )
            else:
                # Error al actualizar (mostrar en modal)
                self.mostrar_mensaje("No se pudo actualizar la empresa", "error")
                return  # NO cerrar modal

        except Exception as e:
            # Errores inesperados
            self.mostrar_mensaje(f"Error al actualizar empresa: {str(e)}", "error")
            return  # NO cerrar modal
    
    async def cambiar_estatus_empresa(self, empresa_id: int, nuevo_estatus: EstatusEmpresa):
        """Cambiar estatus de una empresa"""
        try:
            resultado = await empresa_service.cambiar_estatus(empresa_id, nuevo_estatus)

            if resultado:
                await self.cargar_empresas()
                self.mostrar_mensaje(f"Estatus cambiado a {nuevo_estatus.value}", "success")
            else:
                self.mostrar_mensaje("No se pudo cambiar el estatus", "error")

        except Exception as e:
            self.mostrar_mensaje(f"Error al cambiar estatus: {str(e)}", "error")
    
    # ========================
    # OPERACIONES DE MODALES
    # ========================
    def abrir_modal_crear(self):
        """Abrir modal unificado en modo crear"""
        self.limpiar_formulario()
        self.limpiar_mensajes()
        self.modo_modal_empresa = "crear"
        self.mostrar_modal_empresa = True

    async def abrir_modal_editar(self, empresa_id: int):
        """Abrir modal unificado en modo editar"""
        try:
            self.limpiar_mensajes()
            self.mostrar_modal_detalle = False  # Cerrar modal de detalle si está abierto
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
                self.modo_modal_empresa = "editar"
                self.mostrar_modal_empresa = True
            else:
                self.mostrar_mensaje("No se pudo cargar la empresa para editar", "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar empresa: {str(e)}", "error")

    def cerrar_modal_empresa(self):
        """Cerrar modal unificado (crear/editar)"""
        self.mostrar_modal_empresa = False
        self.modo_modal_empresa = ""
        self.empresa_seleccionada = None
        self.limpiar_formulario()
        self.limpiar_mensajes()

    async def abrir_modal_detalle(self, empresa_id: int):
        """Abrir modal con detalles de la empresa"""
        try:
            self.empresa_seleccionada = await empresa_service.obtener_por_id(empresa_id)
            if self.empresa_seleccionada:
                self.mostrar_modal_detalle = True
            else:
                self.mostrar_mensaje("No se pudo cargar la información de la empresa", "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar empresa: {str(e)}", "error")

    def cerrar_modal_detalle(self):
        """Cerrar modal de detalles"""
        self.mostrar_modal_detalle = False
        self.empresa_seleccionada = None
    
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
    # VALIDACIONES EN TIEMPO REAL
    # ========================
    def validar_nombre_comercial_campo(self):
        """Validar nombre comercial en tiempo real"""
        self.error_nombre_comercial = validar_nombre_comercial(self.form_nombre_comercial)

    def validar_razon_social_campo(self):
        """Validar razón social en tiempo real"""
        self.error_razon_social = validar_razon_social(self.form_razon_social)

    def validar_rfc_campo(self):
        """Validar RFC en tiempo real"""
        self.error_rfc = validar_rfc(self.form_rfc)

    def validar_email_campo(self):
        """Validar email en tiempo real"""
        self.error_email = validar_email(self.form_email)

    def validar_codigo_postal_campo(self):
        """Validar código postal en tiempo real"""
        self.error_codigo_postal = validar_codigo_postal(self.form_codigo_postal)

    def validar_telefono_campo(self):
        """Validar teléfono en tiempo real"""
        self.error_telefono = validar_telefono(self.form_telefono)

    @rx.var
    def tiene_errores_formulario(self) -> bool:
        """Verifica si hay errores de validación en el formulario"""
        return bool(
            self.error_nombre_comercial or
            self.error_razon_social or
            self.error_rfc or
            self.error_email or
            self.error_codigo_postal or
            self.error_telefono
        )

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
        # Limpiar errores de validación
        self.limpiar_errores_validacion()

    def limpiar_errores_validacion(self):
        """Limpiar todos los errores de validación del formulario"""
        self.error_nombre_comercial = ""
        self.error_razon_social = ""
        self.error_rfc = ""
        self.error_email = ""
        self.error_codigo_postal = ""
        self.error_telefono = ""