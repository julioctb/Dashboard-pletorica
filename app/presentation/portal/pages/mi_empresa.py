"""
Pagina Mi Empresa del portal de cliente.

Muestra los datos de la empresa del usuario.
Datos generales: solo lectura.
Datos de contacto: editables por el cliente.
"""
import reflex as rx

from app.presentation.portal.state.portal_state import PortalState
from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Colors, Typography, Spacing
from app.presentation.components.ui import form_input, form_row, boton_guardar, boton_cancelar
from app.presentation.pages.empresas.empresas_validators import (
    validar_telefono,
    validar_email,
    validar_codigo_postal,
)
from app.entities import EmpresaUpdate
from app.services import empresa_service


# =============================================================================
# STATE
# =============================================================================

class MiEmpresaState(PortalState):
    """State para la pagina Mi Empresa."""

    # Edicion de contacto
    editando_contacto: bool = False
    saving_contacto: bool = False
    form_telefono: str = ""
    form_email: str = ""
    form_pagina_web: str = ""
    form_direccion: str = ""
    form_codigo_postal: str = ""

    # Errores de validacion
    error_telefono: str = ""
    error_email: str = ""
    error_codigo_postal: str = ""

    async def on_mount_mi_empresa(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.es_admin_empresa:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self.cargar_datos_empresa):
            yield

    # --- Setters ---
    def set_form_telefono(self, value: str):
        self.form_telefono = value

    def set_form_email(self, value: str):
        self.form_email = value

    def set_form_pagina_web(self, value: str):
        self.form_pagina_web = value

    def set_form_direccion(self, value: str):
        self.form_direccion = value

    def set_form_codigo_postal(self, value: str):
        self.form_codigo_postal = value

    # --- Validacion on_blur ---
    def validar_campo_telefono(self, _value: str = ""):
        self.error_telefono = validar_telefono(self.form_telefono)

    def validar_campo_email(self, _value: str = ""):
        self.error_email = validar_email(self.form_email)

    def validar_campo_codigo_postal(self, _value: str = ""):
        self.error_codigo_postal = validar_codigo_postal(self.form_codigo_postal)

    def _validar_contacto(self) -> bool:
        """Ejecuta todas las validaciones y retorna True si hay errores."""
        self.error_telefono = validar_telefono(self.form_telefono)
        self.error_email = validar_email(self.form_email)
        self.error_codigo_postal = validar_codigo_postal(self.form_codigo_postal)
        return bool(self.error_telefono or self.error_email or self.error_codigo_postal)

    def _limpiar_errores_contacto(self):
        self.error_telefono = ""
        self.error_email = ""
        self.error_codigo_postal = ""

    # --- Acciones de contacto ---
    def abrir_edicion_contacto(self):
        """Puebla el formulario con datos actuales y activa modo edicion."""
        datos = self.datos_empresa
        self.form_telefono = datos.get("telefono") or ""
        self.form_email = datos.get("email") or ""
        self.form_pagina_web = datos.get("pagina_web") or ""
        self.form_direccion = datos.get("direccion") or ""
        self.form_codigo_postal = datos.get("codigo_postal") or ""
        self._limpiar_errores_contacto()
        self.editando_contacto = True

    def cancelar_edicion_contacto(self):
        """Cancela la edicion y limpia el formulario."""
        self.editando_contacto = False
        self._limpiar_errores_contacto()

    async def guardar_contacto(self):
        """Guarda los datos de contacto editados."""
        if self._validar_contacto():
            return

        self.saving_contacto = True
        try:
            update = EmpresaUpdate(
                telefono=self.form_telefono or None,
                email=self.form_email or None,
                pagina_web=self.form_pagina_web or None,
                direccion=self.form_direccion or None,
                codigo_postal=self.form_codigo_postal or None,
            )
            await empresa_service.actualizar(self.id_empresa_actual, update)
            await self.cargar_datos_empresa()
            self.editando_contacto = False
            self._limpiar_errores_contacto()
            return rx.toast.success("Datos de contacto actualizados", position="top-center")
        except Exception as e:
            return self.manejar_error_con_toast(e, "al guardar contacto")
        finally:
            self.saving_contacto = False


# =============================================================================
# COMPONENTES
# =============================================================================

def _campo_info(label: str, valor: rx.Var, icono: str = "") -> rx.Component:
    """Campo de informacion en modo solo lectura."""
    return rx.vstack(
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing="0.05em",
        ),
        rx.cond(
            valor,
            rx.text(
                valor,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                "No disponible",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
                font_style="italic",
            ),
        ),
        spacing="1",
        width="100%",
    )



def _datos_empresa() -> rx.Component:
    """Vista de datos de la empresa."""
    datos = MiEmpresaState.datos_empresa

    return rx.cond(
        MiEmpresaState.loading,
        rx.center(rx.spinner(size="3"), padding="12"),
        rx.cond(
            datos,
            rx.vstack(
                # Datos generales
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("building-2", size=18, color=Colors.PORTAL_PRIMARY),
                            rx.text(
                                "Datos Generales",
                                font_size=Typography.SIZE_SM,
                                font_weight=Typography.WEIGHT_BOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.separator(),
                        rx.grid(
                            _campo_info("Nombre Comercial", datos["nombre_comercial"]),
                            _campo_info("Razon Social", datos["razon_social"]),
                            _campo_info("RFC", datos["rfc"]),
                            _campo_info("Codigo Corto", datos["codigo_corto"]),
                            _campo_info("Estatus", datos["estatus"]),
                            columns=rx.breakpoints(initial="1", sm="2"),
                            spacing="4",
                            width="100%",
                        ),
                        # Datos laborales (solo si hay registro patronal o prima de riesgo)
                        rx.cond(
                            datos["registro_patronal"] | datos["prima_riesgo"],
                            rx.vstack(
                                rx.separator(),
                                rx.grid(
                                    _campo_info("Registro Patronal", datos["registro_patronal"]),
                                    _campo_info("Prima de Riesgo", datos["prima_riesgo"]),
                                    columns=rx.breakpoints(initial="1", sm="2"),
                                    spacing="4",
                                    width="100%",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    width="100%",
                ),
                # Contacto (editable)
                _seccion_contacto(),
                spacing="4",
                width="100%",
            ),
            rx.center(
                rx.text("No se encontraron datos de la empresa", color=Colors.TEXT_SECONDARY),
                padding="12",
            ),
        ),
    )


# =============================================================================
# SECCION CONTACTO (editable)
# =============================================================================

def _contacto_vista() -> rx.Component:
    """Vista de solo lectura de los datos de contacto."""
    datos = MiEmpresaState.datos_empresa
    return rx.grid(
        _campo_info("Telefono", datos["telefono"]),
        _campo_info("Email", datos["email"]),
        _campo_info("Pagina Web", datos["pagina_web"]),
        _campo_info("Direccion", datos["direccion"]),
        _campo_info("Codigo Postal", datos["codigo_postal"]),
        columns=rx.breakpoints(initial="1", sm="2"),
        spacing="4",
        width="100%",
    )


def _contacto_formulario() -> rx.Component:
    """Formulario de edicion de datos de contacto."""
    return rx.vstack(
        form_row(
            form_input(
                label="Telefono",
                placeholder="Ej: 2221234567",
                hint="10 digitos",
                value=MiEmpresaState.form_telefono,
                on_change=MiEmpresaState.set_form_telefono,
                on_blur=MiEmpresaState.validar_campo_telefono,
                error=MiEmpresaState.error_telefono,
                max_length=15,
            ),
            form_input(
                label="Email",
                placeholder="Ej: contacto@empresa.com",
                value=MiEmpresaState.form_email,
                on_change=MiEmpresaState.set_form_email,
                on_blur=MiEmpresaState.validar_campo_email,
                error=MiEmpresaState.error_email,
                max_length=100,
            ),
        ),
        form_row(
            form_input(
                label="Pagina Web",
                placeholder="Ej: www.empresa.com",
                value=MiEmpresaState.form_pagina_web,
                on_change=MiEmpresaState.set_form_pagina_web,
                max_length=100,
            ),
            form_input(
                label="Codigo Postal",
                placeholder="Ej: 72000",
                hint="5 digitos",
                value=MiEmpresaState.form_codigo_postal,
                on_change=MiEmpresaState.set_form_codigo_postal,
                on_blur=MiEmpresaState.validar_campo_codigo_postal,
                error=MiEmpresaState.error_codigo_postal,
                max_length=5,
            ),
        ),
        form_input(
            label="Direccion",
            placeholder="Ej: Av. Reforma 123, Col. Centro",
            value=MiEmpresaState.form_direccion,
            on_change=MiEmpresaState.set_form_direccion,
            max_length=200,
        ),
        # Botones
        rx.hstack(
            boton_cancelar(
                on_click=MiEmpresaState.cancelar_edicion_contacto,
                disabled=MiEmpresaState.saving_contacto,
            ),
            boton_guardar(
                texto="Guardar",
                texto_guardando="Guardando...",
                on_click=MiEmpresaState.guardar_contacto,
                saving=MiEmpresaState.saving_contacto,
                color_scheme="teal",
            ),
            spacing="2",
            justify="end",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def _seccion_contacto() -> rx.Component:
    """Seccion de contacto con modo vista/edicion."""
    return rx.card(
        rx.vstack(
            # Header con boton editar
            rx.hstack(
                rx.hstack(
                    rx.icon("phone", size=18, color=Colors.PORTAL_PRIMARY),
                    rx.text(
                        "Contacto",
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.cond(
                    ~MiEmpresaState.editando_contacto,
                    rx.button(
                        rx.icon("pencil", size=14),
                        "Editar",
                        variant="ghost",
                        size="1",
                        color_scheme="teal",
                        on_click=MiEmpresaState.abrir_edicion_contacto,
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.separator(),
            # Contenido: vista o formulario
            rx.cond(
                MiEmpresaState.editando_contacto,
                _contacto_formulario(),
                _contacto_vista(),
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
    )


# =============================================================================
# SELECTOR DE EMPRESA (multiples empresas)
# =============================================================================

def _empresa_selector() -> rx.Component:
    """Selector de empresa si el usuario tiene multiples asignadas."""
    return rx.cond(
        MiEmpresaState.tiene_multiples_empresas,
        rx.card(
            rx.hstack(
                rx.icon("repeat", size=16, color=Colors.TEXT_SECONDARY),
                rx.text(
                    "Tienes acceso a multiples empresas. Selecciona cual deseas ver:",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            variant="surface",
        ),
        rx.fragment(),
    )


# =============================================================================
# PAGINA
# =============================================================================

def mi_empresa_page() -> rx.Component:
    """Pagina de datos de la empresa (solo lectura)."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Mi Empresa",
                subtitulo="Datos generales de la empresa",
                icono="building-2",
            ),
            content=rx.vstack(
                _empresa_selector(),
                _datos_empresa(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MiEmpresaState.on_mount_mi_empresa,
    )
