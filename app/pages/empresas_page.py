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
    
    # Lista de empresas
    empresas: List[EmpresaResumen] = []
    empresa_seleccionada: Empresa = None
    
    # Filtros
    filtro_tipo: str = ""
    filtro_estatus: str = ""
    filtro_busqueda: str = ""
    incluir_inactivas: bool = False
    
    # Estado de la UI
    loading: bool = False
    mostrar_modal_crear: bool = False
    mostrar_modal_editar: bool = False
    mostrar_modal_detalle: bool = False
    mensaje_info: str = ""
    tipo_mensaje: str = "info"  # info, success, error
    
    # Formulario de nueva empresa
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
    
    async def cargar_empresas(self):
        """Cargar la lista de empresas"""
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
                direccion=self.form_direccion.strip() if self.form_direccion else None,
                codigo_postal=self.form_codigo_postal.strip() if self.form_codigo_postal else None,
                telefono=self.form_telefono.strip() if self.form_telefono else None,
                email=self.form_email.strip() if self.form_email else None,
                pagina_web=self.form_pagina_web.strip() if self.form_pagina_web else None,
                estatus=EstatusEmpresa(self.form_estatus),
                notas=self.form_notas.strip() if self.form_notas else None
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
                nombre_comercial=self.form_nombre_comercial.strip() if self.form_nombre_comercial else None,
                razon_social=self.form_razon_social.strip() if self.form_razon_social else None,
                tipo_empresa=TipoEmpresa(self.form_tipo_empresa) if self.form_tipo_empresa else None,
                rfc=self.form_rfc.strip().upper() if self.form_rfc else None,
                direccion=self.form_direccion.strip() if self.form_direccion else None,
                codigo_postal=self.form_codigo_postal.strip() if self.form_codigo_postal else None,
                telefono=self.form_telefono.strip() if self.form_telefono else None,
                email=self.form_email.strip() if self.form_email else None,
                pagina_web=self.form_pagina_web.strip() if self.form_pagina_web else None,
                estatus=EstatusEmpresa(self.form_estatus) if self.form_estatus else None,
                notas=self.form_notas.strip() if self.form_notas else None
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

def empresa_card(empresa: EmpresaResumen) -> rx.Component:
    """Componente de tarjeta para mostrar información de una empresa"""
    return rx.card(
        rx.vstack(
            # Header de la tarjeta
            rx.hstack(
                rx.vstack(
                    rx.text(empresa.nombre_comercial, size="4", weight="bold"),
                    rx.text(f"ID: {empresa.id}", size="2", color="var(--gray-9)"),
                    align="start",
                    spacing="1"
                ),
                rx.spacer(),
                rx.badge(
                    empresa.tipo_empresa,
                    color_scheme=rx.cond(
                        empresa.tipo_empresa == TipoEmpresa.NOMINA,
                        "blue",
                        "green"
                    )
                ),
                width="100%",
                align="center"
            ),
            
            # Información de contacto
            rx.hstack(
                rx.icon("phone", size=16, color="var(--gray-9)"),
                rx.text(
                    empresa.contacto_principal,
                    size="2",
                    color="var(--gray-9)"
                ),
                spacing="2",
                align="center"
            ),
            
            # Footer con estatus y acciones
            rx.hstack(
                rx.badge(
                    empresa.estatus,
                    color_scheme=rx.cond(
                        empresa.estatus == EstatusEmpresa.ACTIVO,
                        "green",
                        rx.cond(
                            empresa.estatus == EstatusEmpresa.SUSPENDIDO,
                            "yellow",
                            "red"
                        )
                    )
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.icon("eye", size=14),
                        size="1",
                        variant="soft",
                        on_click=lambda: EmpresasState.abrir_modal_detalle(empresa.id)
                    ),
                    rx.button(
                        rx.icon("edit", size=14),
                        size="1",
                        variant="soft",
                        on_click=lambda: EmpresasState.abrir_modal_editar(empresa.id)
                    ),
                    spacing="1"
                ),
                width="100%",
                align="center"
            ),
            
            spacing="3",
            align="start"
        ),
        width="100%",
        max_width="400px",
        _hover={"cursor": "pointer", "bg": "var(--gray-2)"}
    )

def filtros_component() -> rx.Component:
    """Componente de filtros para las empresas"""
    return rx.card(
        rx.vstack(
            rx.text("Filtros de Búsqueda", size="3", weight="bold"),
            
            rx.hstack(
                # Búsqueda general
                rx.input(
                    placeholder="Buscar por nombre comercial...",
                    value=EmpresasState.filtro_busqueda,
                    on_change=EmpresasState.set_filtro_busqueda,
                    size="2"
                ),
                
                # Filtro por tipo
                rx.select(
                    [tipo.value for tipo in TipoEmpresa],
                    placeholder="Tipo de empresa",
                    value=EmpresasState.filtro_tipo,
                    on_change=EmpresasState.set_filtro_tipo,
                    size="2"
                ),
                
                # Filtro por estatus
                rx.select(
                    [estatus.value for estatus in EstatusEmpresa],
                    placeholder="Estatus",
                    value=EmpresasState.filtro_estatus,
                    on_change=EmpresasState.set_filtro_estatus,
                    size="2"
                ),
                
                # Checkbox para incluir inactivas
                rx.checkbox(
                    "Incluir inactivas",
                    checked=EmpresasState.incluir_inactivas,
                    on_change=EmpresasState.set_incluir_inactivas
                ),
                
                spacing="2",
                wrap="wrap"
            ),
            
            rx.hstack(
                rx.button(
                    "Aplicar Filtros",
                    on_click=EmpresasState.aplicar_filtros,
                    size="2"
                ),
                rx.button(
                    "Limpiar",
                    on_click=EmpresasState.limpiar_filtros,
                    variant="soft",
                    size="2"
                ),
                spacing="2"
            ),
            
            spacing="3"
        ),
        width="100%"
    )

def modal_crear_empresa() -> rx.Component:
    """Modal para crear nueva empresa"""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("plus", size=16),
                "Nueva Empresa",
                size="2"
            )
        ),
        rx.dialog.content(
            rx.dialog.title("Crear Nueva Empresa"),
            rx.dialog.description("Ingrese la información de la nueva empresa"),
            
            rx.vstack(
                # Información básica
                rx.text("Información Básica", weight="bold", size="3"),
                rx.input(
                    placeholder="Nombre comercial *",
                    value=EmpresasState.form_nombre_comercial,
                    on_change=EmpresasState.set_form_nombre_comercial,
                    size="2",
                    width="100%"
                ),
                
                rx.input(
                    placeholder="Razón social *",
                    value=EmpresasState.form_razon_social,
                    on_change=EmpresasState.set_form_razon_social,
                    size="2",
                    width="100%"
                ),
                
                rx.hstack(
                    rx.select(
                        [tipo.value for tipo in TipoEmpresa],
                        placeholder="Tipo de empresa *",
                        value=EmpresasState.form_tipo_empresa,
                        on_change=EmpresasState.set_form_tipo_empresa,
                        size="2"
                    ),
                    rx.input(
                        placeholder="RFC *",
                        value=EmpresasState.form_rfc,
                        on_change=EmpresasState.set_form_rfc,
                        size="2"
                    ),
                    spacing="2"
                ),
                
                # Información de contacto
                rx.text("Información de Contacto", weight="bold", size="3"),
                rx.input(
                    placeholder="Dirección",
                    value=EmpresasState.form_direccion,
                    on_change=EmpresasState.set_form_direccion,
                    size="2",
                    width="100%"
                ),
                
                rx.hstack(
                    rx.input(
                        placeholder="Código Postal",
                        value=EmpresasState.form_codigo_postal,
                        on_change=EmpresasState.set_form_codigo_postal,
                        size="2"
                    ),
                    rx.input(
                        placeholder="Teléfono",
                        value=EmpresasState.form_telefono,
                        on_change=EmpresasState.set_form_telefono,
                        size="2"
                    ),
                    spacing="2"
                ),
                
                rx.hstack(
                    rx.input(
                        placeholder="Email",
                        value=EmpresasState.form_email,
                        on_change=EmpresasState.set_form_email,
                        size="2"
                    ),
                    rx.input(
                        placeholder="Página web",
                        value=EmpresasState.form_pagina_web,
                        on_change=EmpresasState.set_form_pagina_web,
                        size="2"
                    ),
                    spacing="2"
                ),
                
                # Control y notas
                rx.text("Control", weight="bold", size="3"),
                rx.select(
                    [estatus.value for estatus in EstatusEmpresa],
                    placeholder="Estatus",
                    value=EmpresasState.form_estatus,
                    on_change=EmpresasState.set_form_estatus,
                    size="2",
                    width="100%"
                ),
                
                rx.text_area(
                    placeholder="Notas adicionales",
                    value=EmpresasState.form_notas,
                    on_change=EmpresasState.set_form_notas,
                    size="2",
                    width="100%"
                ),
                
                spacing="3",
                width="100%"
            ),
            
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        size="2"
                    )
                ),
                rx.button(
                    "Crear Empresa",
                    on_click=EmpresasState.crear_empresa,
                    size="2"
                ),
                spacing="2",
                justify="end"
            ),
            
            max_width="600px",
            spacing="4"
        ),
        open=EmpresasState.mostrar_modal_crear,
        on_open_change=EmpresasState.set_mostrar_modal_crear
    )

def modal_detalle_empresa() -> rx.Component:
    """Modal para mostrar detalles completos de la empresa"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                EmpresasState.empresa_seleccionada,
                rx.vstack(
                    rx.dialog.title("Detalles de la Empresa"),
                    
                    # Información principal
                    rx.card(
                        rx.vstack(
                            rx.text("Información General", weight="bold", size="4"),
                            rx.grid(
                                rx.vstack(
                                    rx.text("Nombre Comercial:", weight="bold", size="2"),
                                    rx.text(EmpresasState.empresa_seleccionada.nombre_comercial, size="2"),
                                    align="start"
                                ),
                                rx.vstack(
                                    rx.text("Razón Social:", weight="bold", size="2"),
                                    rx.text(EmpresasState.empresa_seleccionada.razon_social, size="2"),
                                    align="start"
                                ),
                                rx.vstack(
                                    rx.text("RFC:", weight="bold", size="2"),
                                    rx.text(EmpresasState.empresa_seleccionada.rfc, size="2"),
                                    align="start"
                                ),
                                rx.vstack(
                                    rx.text("Tipo:", weight="bold", size="2"),
                                    rx.badge(EmpresasState.empresa_seleccionada.tipo_empresa),
                                    align="start"
                                ),
                                columns="2",
                                spacing="4"
                            ),
                            spacing="3"
                        )
                    ),
                    
                    # Información de contacto
                    rx.cond(
                        EmpresasState.empresa_seleccionada.direccion | 
                        EmpresasState.empresa_seleccionada.telefono | 
                        EmpresasState.empresa_seleccionada.email,
                        rx.card(
                            rx.vstack(
                                rx.text("Información de Contacto", weight="bold", size="4"),
                                rx.cond(
                                    EmpresasState.empresa_seleccionada.direccion,
                                    rx.hstack(
                                        rx.icon("map-pin", size=16),
                                        rx.text(EmpresasState.empresa_seleccionada.direccion, size="2"),
                                        spacing="2"
                                    )
                                ),
                                rx.cond(
                                    EmpresasState.empresa_seleccionada.telefono,
                                    rx.hstack(
                                        rx.icon("phone", size=16),
                                        rx.text(EmpresasState.empresa_seleccionada.telefono, size="2"),
                                        spacing="2"
                                    )
                                ),
                                rx.cond(
                                    EmpresasState.empresa_seleccionada.email,
                                    rx.hstack(
                                        rx.icon("mail", size=16),
                                        rx.text(EmpresasState.empresa_seleccionada.email, size="2"),
                                        spacing="2"
                                    )
                                ),
                                spacing="2"
                            )
                        )
                    ),
                    
                    # Notas
                    rx.cond(
                        EmpresasState.empresa_seleccionada.notas,
                        rx.card(
                            rx.vstack(
                                rx.text("Notas", weight="bold", size="4"),
                                rx.text(EmpresasState.empresa_seleccionada.notas, size="2"),
                                spacing="2"
                            )
                        )
                    ),
                    
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cerrar", variant="soft", size="2")
                        ),
                        rx.button(
                            "Editar",
                            on_click=lambda: EmpresasState.abrir_modal_editar(EmpresasState.empresa_seleccionada.id),
                            size="2"
                        ),
                        spacing="2",
                        justify="end"
                    ),
                    
                    spacing="4",
                    width="100%"
                )
            ),
            max_width="500px"
        ),
        open=EmpresasState.mostrar_modal_detalle,
        on_open_change=EmpresasState.set_mostrar_modal_detalle
    )

def modal_editar_empresa() -> rx.Component:
    """Modal para editar empresa existente"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Editar Empresa"),
            rx.dialog.description("Modifique la información de la empresa"),
            
            rx.vstack(
                # Información básica
                rx.text("Información Básica", weight="bold", size="3"),
                rx.input(
                    placeholder="Nombre comercial *",
                    value=EmpresasState.form_nombre_comercial,
                    on_change=EmpresasState.set_form_nombre_comercial,
                    size="2",
                    width="100%"
                ),
                
                rx.input(
                    placeholder="Razón social *",
                    value=EmpresasState.form_razon_social,
                    on_change=EmpresasState.set_form_razon_social,
                    size="2",
                    width="100%"
                ),
                
                rx.hstack(
                    rx.select(
                        [tipo.value for tipo in TipoEmpresa],
                        placeholder="Tipo de empresa *",
                        value=EmpresasState.form_tipo_empresa,
                        on_change=EmpresasState.set_form_tipo_empresa,
                        size="2"
                    ),
                    rx.input(
                        placeholder="RFC *",
                        value=EmpresasState.form_rfc,
                        on_change=EmpresasState.set_form_rfc,
                        size="2"
                    ),
                    spacing="2"
                ),
                
                # Información de contacto
                rx.text("Información de Contacto", weight="bold", size="3"),
                rx.input(
                    placeholder="Dirección",
                    value=EmpresasState.form_direccion,
                    on_change=EmpresasState.set_form_direccion,
                    size="2",
                    width="100%"
                ),
                
                rx.hstack(
                    rx.input(
                        placeholder="Código Postal",
                        value=EmpresasState.form_codigo_postal,
                        on_change=EmpresasState.set_form_codigo_postal,
                        size="2"
                    ),
                    rx.input(
                        placeholder="Teléfono",
                        value=EmpresasState.form_telefono,
                        on_change=EmpresasState.set_form_telefono,
                        size="2"
                    ),
                    spacing="2"
                ),
                
                rx.hstack(
                    rx.input(
                        placeholder="Email",
                        value=EmpresasState.form_email,
                        on_change=EmpresasState.set_form_email,
                        size="2"
                    ),
                    rx.input(
                        placeholder="Página web",
                        value=EmpresasState.form_pagina_web,
                        on_change=EmpresasState.set_form_pagina_web,
                        size="2"
                    ),
                    spacing="2"
                ),
                
                # Control y notas
                rx.text("Control", weight="bold", size="3"),
                rx.select(
                    [estatus.value for estatus in EstatusEmpresa],
                    placeholder="Estatus",
                    value=EmpresasState.form_estatus,
                    on_change=EmpresasState.set_form_estatus,
                    size="2",
                    width="100%"
                ),
                
                rx.text_area(
                    placeholder="Notas adicionales",
                    value=EmpresasState.form_notas,
                    on_change=EmpresasState.set_form_notas,
                    size="2",
                    width="100%"
                ),
                
                spacing="3",
                width="100%"
            ),
            
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        size="2",
                        on_click=EmpresasState.cerrar_modal_editar
                    )
                ),
                rx.button(
                    "Guardar Cambios",
                    on_click=EmpresasState.actualizar_empresa,
                    size="2"
                ),
                spacing="2",
                justify="end"
            ),
            
            max_width="600px",
            spacing="4"
        ),
        open=EmpresasState.mostrar_modal_editar,
        on_open_change=EmpresasState.set_mostrar_modal_editar
    )

def empresas_page() -> rx.Component:
    """Página principal de gestión de empresas"""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.hstack(
                rx.icon("building-2", size=32, color="var(--blue-9)"),
                rx.vstack(
                    rx.text("Gestión de Empresas", size="6", weight="bold"),
                    rx.text("Administre las empresas del sistema", size="3", color="var(--gray-9)"),
                    align="start",
                    spacing="1"
                ),
                spacing="3",
                align="center"
            ),
            rx.spacer(),
            
            rx.hstack(
                modal_crear_empresa(),
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    "Actualizar",
                    on_click=EmpresasState.cargar_empresas,
                    variant="soft",
                    size="2"
                ),
                spacing="2"
            ),
            
            width="100%",
            align="center"
        ),
        
        # Mensaje informativo
        rx.cond(
            EmpresasState.mensaje_info,
        rx.callout(
            EmpresasState.mensaje_info,
            icon=rx.cond(
                EmpresasState.tipo_mensaje == "info",
                "info",
                rx.cond(
                    EmpresasState.tipo_mensaje == "success",
                    "check",
                    "alert-triangle"
                )
            ),
            color_scheme=rx.cond(
                EmpresasState.tipo_mensaje == "info",
                "blue",
                rx.cond(
                    EmpresasState.tipo_mensaje == "success",
                    "green",
                    "red"
                )
            ),
            size="2"
        )
        ),
        
        # Filtros
        filtros_component(),
        
        # Loading state
        rx.cond(
            EmpresasState.loading,
            rx.center(
                rx.spinner(size="3"),
                padding="4"
            )
        ),
        
        # Lista de empresas
        rx.cond(
            ~EmpresasState.loading,
            rx.cond(
                EmpresasState.empresas.length() > 0,
                rx.vstack(
                    rx.text(f"Total: {EmpresasState.empresas.length()} empresas", size="2", color="var(--gray-9)"),
                    rx.grid(
                        rx.foreach(
                            EmpresasState.empresas,
                            empresa_card
                        ),
                        columns="3",
                        spacing="4",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("building-2", size=48, color="var(--gray-6)"),
                        rx.text("No se encontraron empresas", size="4", color="var(--gray-9)"),
                        rx.text("Intente ajustar los filtros o crear una nueva empresa", size="2", color="var(--gray-7)"),
                        spacing="2",
                        align="center"
                    ),
                    padding="8"
                )
            )
        ),
        
        # Modales
        modal_detalle_empresa(),
        modal_editar_empresa(),
        
        spacing="4",
        width="100%",
        padding="4",
        on_mount=EmpresasState.cargar_empresas
    )