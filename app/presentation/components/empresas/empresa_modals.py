import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_select, form_textarea
from app.presentation.pages.empresas.empresas_state import EmpresasState
from app.entities import TipoEmpresa, EstatusEmpresa

def modal_empresa() -> rx.Component:
    """Modal unificado para crear o editar empresa"""
    return rx.dialog.root(
        rx.dialog.content(
            # Header: Título + Descripción (muy pegados)
            rx.dialog.title(
                rx.cond(
                    EmpresasState.modo_modal_empresa == "crear",
                    "Crear Nueva Empresa",
                    "Editar Empresa"
                )        
            ),

            rx.dialog.description(
                rx.cond(
                    EmpresasState.modo_modal_empresa == "crear",
                    "Ingrese la información de la nueva empresa",
                    "Modifique la información de la empresa"
                ),
                margin_bottom="20px"  # GRANDE espacio antes del formulario
            ),

            # Mensaje de error/info
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
                    width="100%",
                    role="alert",
                    aria_live="assertive"
                )
            ),

            # Formulario (con margen superior extra)
            rx.vstack(
                # ============================================
                # SECCIÓN 1: INFORMACIÓN BÁSICA
                # ============================================
                rx.vstack(
                    rx.text("Información Básica", weight="bold", size="3"),

                    form_input(
                        placeholder="Nombre comercial *",
                        value=EmpresasState.form_nombre_comercial,
                        on_change=EmpresasState.set_form_nombre_comercial,
                        on_blur=EmpresasState.validar_nombre_comercial_campo,
                        error=EmpresasState.error_nombre_comercial
                    ),

                    form_input(
                        placeholder="Razón social *",
                        value=EmpresasState.form_razon_social,
                        on_change=EmpresasState.set_form_razon_social,
                        on_blur=EmpresasState.validar_razon_social_campo,
                        error=EmpresasState.error_razon_social
                    ),

                    form_input(
                        placeholder="RFC *",
                        value=EmpresasState.form_rfc,
                        on_change=EmpresasState.set_form_rfc,
                        on_blur=EmpresasState.validar_rfc_campo,
                        error=EmpresasState.error_rfc
                    ),

                    rx.hstack(
                        form_select(
                            label="Tipo de empresa *",
                            options=[tipo.value for tipo in TipoEmpresa],
                            value=EmpresasState.form_tipo_empresa,
                            on_change=EmpresasState.set_form_tipo_empresa
                        ),
                        rx.box(width="100%"),  # Spacer
                        spacing="2",
                        width="100%"
                    ),

                    spacing="2",
                    width="100%"
                ),

                # ============================================
                # SECCIÓN 2: INFORMACIÓN DE CONTACTO
                # ============================================
                rx.vstack(
                    rx.text("Información de Contacto", weight="bold", size="3"),

                    form_input(
                        placeholder="Dirección",
                        value=EmpresasState.form_direccion,
                        on_change=EmpresasState.set_form_direccion
                    ),

                    rx.hstack(
                        form_input(
                            placeholder="Código Postal",
                            value=EmpresasState.form_codigo_postal,
                            on_change=EmpresasState.set_form_codigo_postal,
                            on_blur=EmpresasState.validar_codigo_postal_campo,
                            error=EmpresasState.error_codigo_postal
                        ),
                        form_input(
                            placeholder="Teléfono",
                            value=EmpresasState.form_telefono,
                            on_change=EmpresasState.set_form_telefono,
                            on_blur=EmpresasState.validar_telefono_campo,
                            error=EmpresasState.error_telefono
                        ),
                        spacing="2",
                        width="100%"
                    ),

                    rx.hstack(
                        form_input(
                            placeholder="Email",
                            value=EmpresasState.form_email,
                            on_change=EmpresasState.set_form_email,
                            on_blur=EmpresasState.validar_email_campo,
                            error=EmpresasState.error_email
                        ),
                        form_input(
                            placeholder="Página web",
                            value=EmpresasState.form_pagina_web,
                            on_change=EmpresasState.set_form_pagina_web
                        ),
                        spacing="2",
                        width="100%"
                    ),

                    spacing="2",
                    width="100%"
                ),

                # ============================================
                # SECCIÓN 3: CONTROL Y NOTAS
                # ============================================
                rx.vstack(
                    rx.text("Control", weight="bold", size="3"),

                    rx.hstack(
                        form_select(
                            label="Estatus",
                            options=[estatus.value for estatus in EstatusEmpresa],
                            value=EmpresasState.form_estatus,
                            on_change=EmpresasState.set_form_estatus,
                        ),
                        rx.box(width="100%"),  # Spacer
                        spacing="2",
                        width="100%"
                    ),

                    form_textarea(
                        label="Notas Adicionales",
                        placeholder="Información complementaria sobre la empresa...",
                        value=EmpresasState.form_notas,
                        on_change=EmpresasState.set_form_notas,
                        rows=4
                    ),

                    spacing="2",
                    width="100%"
                ),

                spacing="8",  # ~32px entre secciones (4x ratio vs spacing="2" interno)
                width="100%",
                margin_bottom="40px"  # Espacio GRANDE antes de los botones
            ),

            # Botones dinámicos
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        size="2",
                        on_click=EmpresasState.cerrar_modal_empresa
                    )
                ),
                rx.button(
                    # Texto dinámico del botón con loading state
                    rx.cond(
                        EmpresasState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.cond(
                                EmpresasState.modo_modal_empresa == "crear",
                                "Creando...",
                                "Guardando..."
                            ),
                            spacing="2"
                        ),
                        rx.cond(
                            EmpresasState.modo_modal_empresa == "crear",
                            "Crear Empresa",
                            "Guardar Cambios"
                        )
                    ),
                    # Función dinámica
                    on_click=rx.cond(
                        EmpresasState.modo_modal_empresa == "crear",
                        EmpresasState.crear_empresa,
                        EmpresasState.actualizar_empresa
                    ),
                    disabled=EmpresasState.tiene_errores_formulario | EmpresasState.saving,
                    loading=EmpresasState.saving,
                    size="2"
                ),
                spacing="4",
                justify="end"
            ),

            max_width="600px",
            spacing="7"  # Spacing GRANDE entre: header → formulario → botones
        ),
        open=EmpresasState.mostrar_modal_empresa,
        on_open_change=EmpresasState.set_mostrar_modal_empresa
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
