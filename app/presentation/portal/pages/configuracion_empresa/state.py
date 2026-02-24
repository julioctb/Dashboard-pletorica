"""
State para la pagina Configuracion Operativa de empresa en el portal.

Parametros de dias de pago y bloqueo bancario.
"""
import reflex as rx
import logging

from app.presentation.portal.state.portal_state import PortalState
from app.services.configuracion_operativa_service import configuracion_operativa_service
from app.entities.configuracion_operativa_empresa import ConfiguracionOperativaEmpresaUpdate
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class ConfiguracionEmpresaState(PortalState):
    """State de configuracion operativa de la empresa."""

    # ========================
    # DATOS ORIGINALES
    # ========================
    config: dict = {}
    config_cargada: bool = False

    # ========================
    # FORM FIELDS
    # ========================
    form_dias_bloqueo: int = 3
    form_dia_pago_1q: int = 15
    form_dia_pago_2q: int = 0

    # ========================
    # SETTERS
    # ========================
    def set_form_dias_bloqueo(self, value: str):
        try:
            self.form_dias_bloqueo = int(value)
        except (ValueError, TypeError):
            pass

    def set_form_dia_pago_1q(self, value: str):
        try:
            self.form_dia_pago_1q = int(value)
        except (ValueError, TypeError):
            pass

    def set_form_dia_pago_2q(self, value: str):
        try:
            self.form_dia_pago_2q = int(value)
        except (ValueError, TypeError):
            pass

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def tiene_cambios(self) -> bool:
        """Compara form fields con config original."""
        if not self.config_cargada:
            return False
        return (
            self.form_dias_bloqueo != self.config.get("dias_bloqueo_cuenta_antes_pago", 3)
            or self.form_dia_pago_1q != self.config.get("dia_pago_primera_quincena", 15)
            or self.form_dia_pago_2q != self.config.get("dia_pago_segunda_quincena", 0)
        )

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_configuracion_empresa(self):
        async for _ in self._montar_pagina_portal(self._fetch_configuracion):
            yield

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_configuracion(self):
        """Carga la configuracion operativa de la empresa."""
        if not self.id_empresa_actual:
            return

        try:
            config = await configuracion_operativa_service.obtener_o_crear_default(
                self.id_empresa_actual
            )
            self.config = config.model_dump(mode='json')
            self.config_cargada = True

            # Pre-llenar form fields
            self.form_dias_bloqueo = config.dias_bloqueo_cuenta_antes_pago
            self.form_dia_pago_1q = config.dia_pago_primera_quincena
            self.form_dia_pago_2q = config.dia_pago_segunda_quincena

        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando configuracion: {e}", "error")
            self.config = {}
            self.config_cargada = False
        except Exception as e:
            logger.error(f"Error cargando config operativa: {e}")
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")

    # ========================
    # GUARDAR
    # ========================
    async def guardar_configuracion(self):
        """Guarda la configuracion operativa."""
        self.saving = True
        try:
            datos = ConfiguracionOperativaEmpresaUpdate(
                dias_bloqueo_cuenta_antes_pago=self.form_dias_bloqueo,
                dia_pago_primera_quincena=self.form_dia_pago_1q,
                dia_pago_segunda_quincena=self.form_dia_pago_2q,
            )

            config = await configuracion_operativa_service.crear_o_actualizar(
                self.id_empresa_actual, datos
            )
            self.config = config.model_dump(mode='json')

            return rx.toast.success("Configuracion guardada")

        except DatabaseError as e:
            return rx.toast.error(f"Error guardando: {e}")
        except Exception as e:
            return self.manejar_error_con_toast(e, "guardando configuracion")
        finally:
            self.saving = False
