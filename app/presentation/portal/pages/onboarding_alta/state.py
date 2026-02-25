"""
State para la pagina Alta de Empleados (Onboarding) del portal.
"""
import reflex as rx
from typing import List, Optional

from app.presentation.portal.state.portal_state import PortalState
from app.services.onboarding_service import onboarding_service
from app.services.curp_service import curp_service
from app.entities.onboarding import AltaEmpleadoBuap
from app.core.exceptions import (
    DatabaseError,
    BusinessRuleError,
    ValidationError,
)
from app.presentation.pages.empleados.empleados_validators import (
    validar_curp,
    validar_nombre,
    validar_apellido_paterno,
    validar_email,
)
from app.core.ui_options import OPCIONES_ESTATUS_ONBOARDING


class OnboardingAltaState(PortalState):
    """State para la lista y alta de empleados en onboarding."""

    # ========================
    # DATOS
    # ========================
    empleados_onboarding: List[dict] = []
    total_onboarding: int = 0

    # Filtros
    filtro_estatus_onboarding: str = ""

    # ========================
    # FORMULARIO ALTA
    # ========================
    mostrar_modal_alta: bool = False
    form_curp: str = ""
    form_nombre: str = ""
    form_apellido_paterno: str = ""
    form_apellido_materno: str = ""
    form_email: str = ""
    form_sede_id: str = ""

    # Validacion CURP realtime
    curp_validado: bool = False
    curp_mensaje: str = ""
    curp_es_valido: bool = False

    # ========================
    # ERRORES
    # ========================
    error_curp: str = ""
    error_nombre: str = ""
    error_apellido_paterno: str = ""
    error_email: str = ""

    # ========================
    # SETTERS
    # ========================
    def set_filtro_estatus_onboarding(self, value: str):
        self.filtro_estatus_onboarding = value

    def set_form_curp(self, value: str):
        self.form_curp = value.upper() if value else ""
        self.curp_validado = False
        self.curp_mensaje = ""
        self.curp_es_valido = False

    def set_form_nombre(self, value: str):
        self.form_nombre = value.upper() if value else ""

    def set_form_apellido_paterno(self, value: str):
        self.form_apellido_paterno = value.upper() if value else ""

    def set_form_apellido_materno(self, value: str):
        self.form_apellido_materno = value.upper() if value else ""

    def set_form_email(self, value: str):
        self.form_email = value.lower() if value else ""

    def set_form_sede_id(self, value: str):
        self.form_sede_id = value if value else ""

    # ========================
    # VALIDADORES ON_BLUR
    # ========================
    def validar_curp_blur(self):
        self.error_curp = validar_curp(self.form_curp)

    def validar_nombre_blur(self):
        self.error_nombre = validar_nombre(self.form_nombre)

    def validar_apellido_paterno_blur(self):
        self.error_apellido_paterno = validar_apellido_paterno(self.form_apellido_paterno)

    def validar_email_blur(self):
        if self.form_email:
            self.error_email = validar_email(self.form_email)
        else:
            self.error_email = ""

    # ========================
    # VALIDACION CURP REALTIME
    # ========================
    async def validar_curp_realtime(self):
        """Valida CURP contra BD (duplicados/restriccion)."""
        if len(self.form_curp) != 18:
            self.curp_validado = False
            self.curp_mensaje = ""
            self.curp_es_valido = False
            return

        # Validar formato primero
        error = validar_curp(self.form_curp)
        if error:
            self.curp_validado = True
            self.curp_mensaje = error
            self.curp_es_valido = False
            self.error_curp = error
            return

        try:
            resultado = await curp_service.validar_curp(self.form_curp)
            self.curp_validado = True

            if not resultado.formato_valido:
                self.curp_mensaje = resultado.mensaje
                self.curp_es_valido = False
                self.error_curp = resultado.mensaje
            elif resultado.duplicado:
                msg = f"CURP ya registrado: {resultado.empleado_nombre}"
                if resultado.is_restricted:
                    msg += " (RESTRINGIDO)"
                self.curp_mensaje = msg
                self.curp_es_valido = False
                self.error_curp = msg
            else:
                self.curp_mensaje = "CURP disponible"
                self.curp_es_valido = True
                self.error_curp = ""

        except Exception as e:
            self.curp_validado = True
            self.curp_mensaje = f"Error validando: {e}"
            self.curp_es_valido = False

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def empleados_onboarding_filtrados(self) -> List[dict]:
        """Filtra por estatus de onboarding."""
        if not self.filtro_estatus_onboarding or self.filtro_estatus_onboarding == "TODOS":
            return self.empleados_onboarding
        return [
            e for e in self.empleados_onboarding
            if e.get("estatus_onboarding") == self.filtro_estatus_onboarding
        ]

    @rx.var
    def opciones_estatus_onboarding(self) -> List[dict]:
        """Opciones para el filtro de estatus."""
        return OPCIONES_ESTATUS_ONBOARDING

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_onboarding_alta(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.puede_registrar_personal:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_empleados_onboarding):
            yield

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_empleados_onboarding(self):
        """Carga empleados en onboarding de la empresa."""
        if not self.id_empresa_actual:
            return

        try:
            empleados = await onboarding_service.obtener_empleados_onboarding(
                empresa_id=self.id_empresa_actual,
            )
            self.empleados_onboarding = empleados
            self.total_onboarding = len(empleados)
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando empleados: {e}", "error")
            self.empleados_onboarding = []
            self.total_onboarding = 0
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.empleados_onboarding = []
            self.total_onboarding = 0

    async def recargar_onboarding(self):
        """Recarga con skeleton."""
        async for _ in self._recargar_datos(self._fetch_empleados_onboarding):
            yield

    # ========================
    # ACCIONES DE MODAL
    # ========================
    def abrir_modal_alta(self):
        """Abre el modal para dar de alta un empleado."""
        self._limpiar_formulario()
        self.mostrar_modal_alta = True

    def cerrar_modal_alta(self):
        """Cierra el modal de alta."""
        self.mostrar_modal_alta = False
        self._limpiar_formulario()

    # ========================
    # REGISTRAR EMPLEADO
    # ========================
    async def registrar_empleado(self):
        """Registra un nuevo empleado en onboarding."""
        if not self._validar_formulario():
            return rx.toast.error("Por favor corrija los errores del formulario")

        self.saving = True
        try:
            datos = AltaEmpleadoBuap(
                empresa_id=self.id_empresa_actual,
                curp=self.form_curp,
                nombre=self.form_nombre,
                apellido_paterno=self.form_apellido_paterno,
                apellido_materno=self.form_apellido_materno or None,
                email=self.form_email or None,
                sede_id=int(self.form_sede_id) if self.form_sede_id else None,
            )

            # UUID del usuario actual (o placeholder si SKIP_AUTH)
            from uuid import UUID
            registrado_por = UUID('00000000-0000-0000-0000-000000000000')
            if self.usuario_actual:
                uid = self.usuario_actual.get('id')
                if uid:
                    registrado_por = UUID(str(uid))

            empleado = await onboarding_service.alta_empleado_buap(datos, registrado_por)

            self.cerrar_modal_alta()
            await self._fetch_empleados_onboarding()
            return rx.toast.success(
                f"Empleado {empleado.clave} registrado correctamente"
            )

        except BusinessRuleError as e:
            if "curp" in str(e).lower() or "CURP" in str(e):
                self.error_curp = str(e)
            return rx.toast.error(str(e))
        except ValidationError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "registrando empleado")
        finally:
            self.saving = False

    # ========================
    # METODOS PRIVADOS
    # ========================
    def _limpiar_formulario(self):
        """Limpia el formulario de alta."""
        self.form_curp = ""
        self.form_nombre = ""
        self.form_apellido_paterno = ""
        self.form_apellido_materno = ""
        self.form_email = ""
        self.form_sede_id = ""
        self.curp_validado = False
        self.curp_mensaje = ""
        self.curp_es_valido = False
        self._limpiar_errores()

    def _limpiar_errores(self):
        """Limpia errores de validacion."""
        self.error_curp = ""
        self.error_nombre = ""
        self.error_apellido_paterno = ""
        self.error_email = ""

    def _validar_formulario(self) -> bool:
        """Valida el formulario completo. Retorna True si es valido."""
        self._limpiar_errores()
        es_valido = True

        error = validar_curp(self.form_curp)
        if error:
            self.error_curp = error
            es_valido = False

        error = validar_nombre(self.form_nombre)
        if error:
            self.error_nombre = error
            es_valido = False

        error = validar_apellido_paterno(self.form_apellido_paterno)
        if error:
            self.error_apellido_paterno = error
            es_valido = False

        if self.form_email:
            error = validar_email(self.form_email)
            if error:
                self.error_email = error
                es_valido = False

        return es_valido
