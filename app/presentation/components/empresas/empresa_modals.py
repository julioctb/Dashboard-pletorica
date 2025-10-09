import reflex as rx
from app.presentation.pages.empresas.empresas_state import EmpresasState
from app.entities import TipoEmpresa, EstatusEmpresa

def modal_crear_empresa() -> rx.Component:
    """Modal para crear nueva empresa"""
    return rx.dialog.root(

        rx.dialog.content(
            rx.dialog.title("Crear Nueva Empresa"),
            rx.dialog.description("Ingrese la información de la nueva empresa"),

            rx.vstack(
                # Información básica
                rx.text("Información Básica", weight="bold", size="3"),

                # Nombre comercial con validación
                rx.vstack(
                    rx.input(
                        placeholder="Nombre comercial *",
                        value=EmpresasState.form_nombre_comercial,
                        on_change=EmpresasState.set_form_nombre_comercial,
                        on_blur=EmpresasState.validar_nombre_comercial_campo,
                        size="2",
                        width="100%"
                    ),
                    rx.cond(
                        EmpresasState.error_nombre_comercial != "",
                        rx.text(
                            EmpresasState.error_nombre_comercial,
                            color="red",
                            size="1"
                        )
                    ),
                    spacing="1",
                    width="100%"
                ),

                # Razón social con validación
                rx.vstack(
                    rx.input(
                        placeholder="Razón social *",
                        value=EmpresasState.form_razon_social,
                        on_change=EmpresasState.set_form_razon_social,
                        on_blur=EmpresasState.validar_razon_social_campo,
                        size="2",
                        width="100%"
                    ),
                    rx.cond(
                        EmpresasState.error_razon_social != "",
                        rx.text(
                            EmpresasState.error_razon_social,
                            color="red",
                            size="1"
                        )
                    ),
                    spacing="1",
                    width="100%"
                ),

                # Tipo de empresa y RFC
                rx.hstack(
                    rx.select(
                        [tipo.value for tipo in TipoEmpresa],
                        placeholder="Tipo de empresa *",
                        value=EmpresasState.form_tipo_empresa,
                        on_change=EmpresasState.set_form_tipo_empresa,
                        size="2"
                    ),
                    rx.vstack(
                        rx.input(
                            placeholder="RFC *",
                            value=EmpresasState.form_rfc,
                            on_change=EmpresasState.set_form_rfc,
                            on_blur=EmpresasState.validar_rfc_campo,
                            size="2"
                        ),
                        rx.cond(
                            EmpresasState.error_rfc != "",
                            rx.text(
                                EmpresasState.error_rfc,
                                color="red",
                                size="1"
                            )
                        ),
                        spacing="1",
                        width="100%"
                    ),
                    spacing="2",
                    width="100%"
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

                # Código postal y teléfono con validación
                rx.hstack(
                    rx.vstack(
                        rx.input(
                            placeholder="Código Postal",
                            value=EmpresasState.form_codigo_postal,
                            on_change=EmpresasState.set_form_codigo_postal,
                            on_blur=EmpresasState.validar_codigo_postal_campo,
                            size="2"
                        ),
                        rx.cond(
                            EmpresasState.error_codigo_postal != "",
                            rx.text(
                                EmpresasState.error_codigo_postal,
                                color="red",
                                size="1"
                            )
                        ),
                        spacing="2"
                       
                    ),
                    rx.vstack(
                        rx.input(
                            placeholder="Teléfono",
                            value=EmpresasState.form_telefono,
                            on_change=EmpresasState.set_form_telefono,
                            on_blur=EmpresasState.validar_telefono_campo,
                            size="2"
                        ),
                        rx.cond(
                            EmpresasState.error_telefono != "",
                            rx.text(
                                EmpresasState.error_telefono,
                                color="red",
                                size="1"
                            )
                        ),
                        spacing="2",
                        
                    ),
                    spacing="2",
                    
                ),

                # Email y página web con validación
                rx.hstack(
                    rx.vstack(
                        rx.input(
                            placeholder="Email",
                            value=EmpresasState.form_email,
                            on_change=EmpresasState.set_form_email,
                            on_blur=EmpresasState.validar_email_campo,
                            size="2"
                        ),
                        rx.cond(
                            EmpresasState.error_email != "",
                            rx.text(
                                EmpresasState.error_email,
                                color="red",
                                size="1"
                            )
                        ),
                        spacing="2",
                        
                    ),
                    rx.input(
                        placeholder="Página web",
                        value=EmpresasState.form_pagina_web,
                        on_change=EmpresasState.set_form_pagina_web,
                        size="2"
                    ),
                    spacing="2",
                    
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
            rx.spacer(),

            # Mostrar mensaje de error si existe
            rx.cond(
                EmpresasState.mensaje_info != "",
                rx.callout(
                    EmpresasState.mensaje_info,
                    icon=rx.cond(
                        EmpresasState.tipo_mensaje == "error",
                        "triangle-alert",
                        "info"
                    ),
                    color_scheme=rx.cond(
                        EmpresasState.tipo_mensaje == "error",
                        "red",
                        "blue"
                    ),
                    size="2",
                    width="100%"
                )
            ),
            

            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        size="2",
                        on_click=EmpresasState.limpiar_mensajes
                    )
                ),
                rx.button(
                    "Crear Empresa",
                    on_click=EmpresasState.crear_empresa,
                    disabled=EmpresasState.tiene_errores_formulario,
                    size="2"
                ),
                spacing="4",
                justify="end"
            ),
            
            max_width="600px",
            spacing="6"
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

                # Nombre comercial con validación
                rx.vstack(
                    rx.input(
                        placeholder="Nombre comercial *",
                        value=EmpresasState.form_nombre_comercial,
                        on_change=EmpresasState.set_form_nombre_comercial,
                        on_blur=EmpresasState.validar_nombre_comercial_campo,
                        size="2",
                        width="100%"
                    ),
                    rx.cond(
                        EmpresasState.error_nombre_comercial != "",
                        rx.text(
                            EmpresasState.error_nombre_comercial,
                            color="red",
                            size="1"
                        )
                    ),
                    spacing="1",
                    width="100%"
                ),

                # Razón social con validación
                rx.vstack(
                    rx.input(
                        placeholder="Razón social *",
                        value=EmpresasState.form_razon_social,
                        on_change=EmpresasState.set_form_razon_social,
                        on_blur=EmpresasState.validar_razon_social_campo,
                        size="2",
                        width="100%"
                    ),
                    rx.cond(
                        EmpresasState.error_razon_social != "",
                        rx.text(
                            EmpresasState.error_razon_social,
                            color="red",
                            size="1"
                        )
                    ),
                    spacing="1",
                    width="100%"
                ),

                # Tipo de empresa y RFC
                rx.hstack(
                    rx.select(
                        [tipo.value for tipo in TipoEmpresa],
                        placeholder="Tipo de empresa *",
                        value=EmpresasState.form_tipo_empresa,
                        on_change=EmpresasState.set_form_tipo_empresa,
                        size="2"
                    ),
                    rx.vstack(
                        rx.input(
                            placeholder="RFC *",
                            value=EmpresasState.form_rfc,
                            on_change=EmpresasState.set_form_rfc,
                            on_blur=EmpresasState.validar_rfc_campo,
                            size="2"
                        ),
                        rx.cond(
                            EmpresasState.error_rfc != "",
                            rx.text(
                                EmpresasState.error_rfc,
                                color="red",
                                size="1"
                            )
                        ),
                        spacing="1",
                        width="100%"
                    ),
                    spacing="2",
                    width="100%"
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

                # Código postal y teléfono con validación
                rx.hstack(
                    rx.vstack(
                        rx.input(
                            placeholder="Código Postal",
                            value=EmpresasState.form_codigo_postal,
                            on_change=EmpresasState.set_form_codigo_postal,
                            on_blur=EmpresasState.validar_codigo_postal_campo,
                            size="2"
                        ),
                        rx.cond(
                            EmpresasState.error_codigo_postal != "",
                            rx.text(
                                EmpresasState.error_codigo_postal,
                                color="red",
                                size="1"
                            )
                        ),
                        spacing="2"
                    ),
                    rx.vstack(
                        rx.input(
                            placeholder="Teléfono",
                            value=EmpresasState.form_telefono,
                            on_change=EmpresasState.set_form_telefono,
                            on_blur=EmpresasState.validar_telefono_campo,
                            size="2"
                        ),
                        rx.cond(
                            EmpresasState.error_telefono != "",
                            rx.text(
                                EmpresasState.error_telefono,
                                color="red",
                                size="1"
                            )
                        ),
                        spacing="2"
                    ),
                    spacing="2"
                ),

                # Email y página web con validación
                rx.hstack(
                    rx.vstack(
                        rx.input(
                            placeholder="Email",
                            value=EmpresasState.form_email,
                            on_change=EmpresasState.set_form_email,
                            on_blur=EmpresasState.validar_email_campo,
                            size="2"
                        ),
                        rx.cond(
                            EmpresasState.error_email != "",
                            rx.text(
                                EmpresasState.error_email,
                                color="red",
                                size="1"
                            )
                        ),
                        spacing="2"
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
            rx.spacer(),

            # Mostrar mensaje de error si existe
            rx.cond(
                EmpresasState.mensaje_info != "",
                rx.callout(
                    EmpresasState.mensaje_info,
                    icon=rx.cond(
                        EmpresasState.tipo_mensaje == "error",
                        "triangle-alert",
                        "info"
                    ),
                    color_scheme=rx.cond(
                        EmpresasState.tipo_mensaje == "error",
                        "red",
                        "blue"
                    ),
                    size="2",
                    width="100%"
                )
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
                    disabled=EmpresasState.tiene_errores_formulario,
                    size="2"
                ),
                spacing="4",
                justify="end"
            ),

            max_width="600px",
            spacing="6"
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
                                    rx.badge(EmpresasState.empresa_seleccionada.tipo_empresa.to_string()),
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
                            ),
                            width="100%"
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
                            ),
                           width="100%" 
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
