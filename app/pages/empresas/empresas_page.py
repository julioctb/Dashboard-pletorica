import reflex as rx
from app.pages.empresas.empresas_state import EmpresasState
from app.components.business.empresa_card import empresa_card
from app.components.ui.cards import empty_state_card
from app.database.models import TipoEmpresa, EstatusEmpresa

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
                                    rx.badge(str(EmpresasState.empresa_seleccionada.tipo_empresa)),
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
            EmpresasState.loading == False,
            rx.cond(
                EmpresasState.empresas.length() > 0,
                rx.vstack(
                    rx.text(
                        f"Total: {EmpresasState.empresas.length()} empresas", 
                        size="2", 
                        color="var(--gray-9)"
                    ),
                    rx.grid(
                        rx.foreach(
                            EmpresasState.empresas,
                            lambda empresa: empresa_card(
                                empresa=empresa,
                                on_view=EmpresasState.abrir_modal_detalle,
                                on_edit=EmpresasState.abrir_modal_editar
                            )
                        ),
                        columns="3",
                        spacing="4",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),
                empty_state_card(
                    title="No se encontraron empresas",
                    description="Intente ajustar los filtros o crear una nueva empresa",
                    icon="building-2"
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