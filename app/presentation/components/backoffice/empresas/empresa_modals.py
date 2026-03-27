import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_select, form_textarea
from app.presentation.components.ui.feedback import feedback_callout
from app.presentation.components.ui.modals import modal_formulario, modal_detalle
from app.presentation.pages.backoffice.empresas.empresas_state import EmpresasState
from app.domain.models import TipoEmpresa, EstatusEmpresa


def modal_empresa() -> rx.Component:
    """Modal unificado para crear o editar empresa"""
    return modal_formulario(
        open=EmpresasState.mostrar_modal_empresa,
        titulo=rx.cond(
            EmpresasState.modo_modal_empresa == "crear",
            "Crear Nueva Empresa",
            "Editar Empresa",
        ),
        descripcion=rx.cond(
            EmpresasState.modo_modal_empresa == "crear",
            "Ingrese la información de la nueva empresa",
            "Modifique la información de la empresa",
        ),
        icono="building",
        on_guardar=rx.cond(
            EmpresasState.modo_modal_empresa == "crear",
            EmpresasState.crear_empresa,
            EmpresasState.actualizar_empresa,
        ),
        on_cancelar=EmpresasState.cerrar_modal_empresa,
        puede_guardar=~EmpresasState.tiene_errores_formulario,
        loading=EmpresasState.saving,
        texto_guardar=rx.cond(
            EmpresasState.modo_modal_empresa == "crear",
            "Crear Empresa",
            "Guardar Cambios",
        ),
        texto_guardando=rx.cond(
            EmpresasState.modo_modal_empresa == "crear",
            "Creando...",
            "Guardando...",
        ),
        scroll_body=True,
        max_width="600px",
        contenido=rx.vstack(
            # Mensaje de error/info
            rx.cond(
                EmpresasState.mensaje_info != "",
                feedback_callout(
                    EmpresasState.mensaje_info,
                    EmpresasState.tipo_mensaje,
                ),
            ),

            # ============================================
            # SECCIÓN 1: INFORMACIÓN BÁSICA
            # ============================================
            rx.vstack(
                rx.text("Información Básica", weight="bold", size="3"),

                form_input(
                    label="Nombre comercial",
                    required=True,
                    placeholder="Ej: ACME Corp",
                    value=EmpresasState.form_nombre_comercial,
                    on_change=EmpresasState.set_form_nombre_comercial,
                    on_blur=EmpresasState.validar_nombre_comercial_campo,
                    error=EmpresasState.error_nombre_comercial,
                ),

                form_input(
                    label="Razon social",
                    required=True,
                    placeholder="Ej: ACME Corporation SA de CV",
                    value=EmpresasState.form_razon_social,
                    on_change=EmpresasState.set_form_razon_social,
                    on_blur=EmpresasState.validar_razon_social_campo,
                    error=EmpresasState.error_razon_social,
                ),

                form_input(
                    label="RFC",
                    required=True,
                    placeholder="Ej: ACM010101ABC",
                    value=EmpresasState.form_rfc,
                    on_change=EmpresasState.set_form_rfc,
                    on_blur=EmpresasState.validar_rfc_campo,
                    error=EmpresasState.error_rfc,
                ),

                rx.hstack(
                    form_select(
                        label="Tipo de empresa",
                        required=True,
                        placeholder="Seleccione tipo",
                        value=EmpresasState.form_tipo_empresa,
                        on_change=EmpresasState.set_form_tipo_empresa,
                        options=[{"label": tipo.value, "value": tipo.value} for tipo in TipoEmpresa],
                    ),
                    rx.box(width="100%"),  # Spacer
                    spacing="2",
                    width="100%",
                ),

                spacing="2",
                width="100%",
            ),

            # ============================================
            # SECCIÓN 2: DATOS IMSS
            # ============================================
            rx.vstack(
                rx.text("Datos IMSS", weight="bold", size="3"),

                rx.hstack(
                    form_input(
                        label="Registro patronal",
                        placeholder="Ej: Y1234567101",
                        value=EmpresasState.form_registro_patronal,
                        on_change=EmpresasState.set_form_registro_patronal,
                        on_blur=EmpresasState.validar_registro_patronal_campo,
                        error=EmpresasState.error_registro_patronal,
                    ),
                    form_input(
                        label="Prima de riesgo (%)",
                        placeholder="Ej: 2.598",
                        value=EmpresasState.form_prima_riesgo,
                        on_change=EmpresasState.set_form_prima_riesgo,
                        on_blur=EmpresasState.validar_prima_riesgo_campo,
                        error=EmpresasState.error_prima_riesgo,
                    ),
                    spacing="2",
                    width="100%",
                ),

                spacing="2",
                width="100%",
            ),

            # ============================================
            # SECCIÓN 3: INFORMACIÓN DE CONTACTO
            # ============================================
            rx.vstack(
                rx.text("Información de Contacto", weight="bold", size="3"),

                form_input(
                    label="Direccion",
                    placeholder="Ej: Av. Reforma 123, Col. Centro",
                    value=EmpresasState.form_direccion,
                    on_change=EmpresasState.set_form_direccion,
                ),

                rx.hstack(
                    form_input(
                        label="Codigo postal",
                        placeholder="Ej: 72000",
                        value=EmpresasState.form_codigo_postal,
                        on_change=EmpresasState.set_form_codigo_postal,
                        on_blur=EmpresasState.validar_codigo_postal_campo,
                        error=EmpresasState.error_codigo_postal,
                    ),
                    form_input(
                        label="Telefono",
                        placeholder="Ej: 2221234567",
                        value=EmpresasState.form_telefono,
                        on_change=EmpresasState.set_form_telefono,
                        on_blur=EmpresasState.validar_telefono_campo,
                        error=EmpresasState.error_telefono,
                    ),
                    spacing="2",
                    width="100%",
                ),

                rx.hstack(
                    form_input(
                        label="Email",
                        placeholder="Ej: contacto@empresa.com",
                        value=EmpresasState.form_email,
                        on_change=EmpresasState.set_form_email,
                        on_blur=EmpresasState.validar_email_campo,
                        error=EmpresasState.error_email,
                    ),
                    form_input(
                        label="Pagina web",
                        placeholder="Ej: www.empresa.com",
                        value=EmpresasState.form_pagina_web,
                        on_change=EmpresasState.set_form_pagina_web,
                    ),
                    spacing="2",
                    width="100%",
                ),

                spacing="2",
                width="100%",
            ),

            # ============================================
            # SECCIÓN 4: CONTROL Y NOTAS
            # ============================================
            rx.vstack(
                rx.text("Control", weight="bold", size="3"),

                rx.hstack(
                    form_select(
                        label="Estatus",
                        placeholder="Seleccione estatus",
                        value=EmpresasState.form_estatus,
                        on_change=EmpresasState.set_form_estatus,
                        options=[{"label": estatus.value, "value": estatus.value} for estatus in EstatusEmpresa],
                    ),
                    rx.box(width="100%"),  # Spacer
                    spacing="2",
                    width="100%",
                ),
                rx.hstack(
                    rx.switch(
                        checked=EmpresasState.form_gestion_nomina_activa,
                        on_change=EmpresasState.set_form_gestion_nomina_activa,
                    ),
                    rx.vstack(
                        rx.text("Gestion de nomina activa", weight="medium", size="2"),
                        rx.text(
                            "Habilita configuracion operativa y acceso al modulo de nominas para la empresa.",
                            size="1",
                            color="gray",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    spacing="3",
                    align="center",
                    width="100%",
                ),

                form_textarea(
                    label="Notas",
                    placeholder="Ej: Informacion adicional...",
                    value=EmpresasState.form_notas,
                    on_change=EmpresasState.set_form_notas,
                    rows="4",
                ),

                spacing="2",
                width="100%",
            ),

            spacing="8",
            width="100%",
        ),
    )


def modal_detalle_empresa() -> rx.Component:
    """Modal para mostrar detalles completos de la empresa"""
    return modal_detalle(
        open=EmpresasState.mostrar_modal_detalle,
        titulo="Detalles de la Empresa",
        on_cerrar=EmpresasState.cerrar_modal_detalle,
        boton_accion=rx.button(
            "Editar",
            on_click=lambda: EmpresasState.abrir_modal_editar(EmpresasState.empresa_seleccionada.id),
            size="2",
        ),
        max_width="500px",
        contenido=rx.cond(
            EmpresasState.empresa_seleccionada,
            rx.vstack(
                # Información principal
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.text("Información General", weight="bold", size="4"),
                            rx.spacer(),
                            rx.badge(
                                EmpresasState.empresa_seleccionada.codigo_corto,
                                color_scheme="blue",
                                size="2",
                                variant="solid",
                            ),
                            align="center",
                            width="100%",
                        ),
                        rx.grid(
                            rx.vstack(
                                rx.text("Nombre Comercial:", weight="bold", size="2"),
                                rx.text(EmpresasState.empresa_seleccionada.nombre_comercial, size="2"),
                                align="start",
                            ),
                            rx.vstack(
                                rx.text("Razón Social:", weight="bold", size="2"),
                                rx.text(EmpresasState.empresa_seleccionada.razon_social, size="2"),
                                align="start",
                            ),
                            rx.vstack(
                                rx.text("RFC:", weight="bold", size="2"),
                                rx.text(EmpresasState.empresa_seleccionada.rfc, size="2"),
                                align="start",
                            ),
                            rx.vstack(
                                rx.text("Tipo:", weight="bold", size="2"),
                                rx.badge(EmpresasState.empresa_seleccionada.tipo_empresa.to_string()),
                                align="start",
                            ),
                            rx.vstack(
                                rx.text("Nomina:", weight="bold", size="2"),
                                rx.badge(
                                    rx.cond(
                                        EmpresasState.empresa_seleccionada.gestion_nomina_activa,
                                        "ACTIVA",
                                        "INACTIVA",
                                    ),
                                    color_scheme=rx.cond(
                                        EmpresasState.empresa_seleccionada.gestion_nomina_activa,
                                        "blue",
                                        "gray",
                                    ),
                                ),
                                align="start",
                            ),
                            columns="2",
                            spacing="4",
                        ),
                        spacing="3",
                    ),
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
                                    spacing="2",
                                ),
                            ),
                            rx.cond(
                                EmpresasState.empresa_seleccionada.telefono,
                                rx.hstack(
                                    rx.icon("phone", size=16),
                                    rx.text(EmpresasState.empresa_seleccionada.telefono, size="2"),
                                    spacing="2",
                                ),
                            ),
                            rx.cond(
                                EmpresasState.empresa_seleccionada.email,
                                rx.hstack(
                                    rx.icon("mail", size=16),
                                    rx.text(EmpresasState.empresa_seleccionada.email, size="2"),
                                    spacing="2",
                                ),
                            ),
                            spacing="2",
                        ),
                        width="100%",
                    ),
                ),

                # Notas
                rx.cond(
                    EmpresasState.empresa_seleccionada.notas,
                    rx.card(
                        rx.vstack(
                            rx.text("Notas", weight="bold", size="4"),
                            rx.text(EmpresasState.empresa_seleccionada.notas, size="2"),
                            spacing="2",
                        ),
                        width="100%",
                    ),
                ),

                spacing="4",
                width="100%",
            ),
        ),
    )
