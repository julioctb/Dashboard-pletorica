"""
State para la configuracion operativa de la empresa en el portal.

Centraliza la politica de nomina por empresa:
- periodicidad semanal/quincenal/mensual
- reglas de pago segun la periodicidad
- bloqueo bancario previo a dispersion
"""
import logging

import reflex as rx

from core.core.enums import PeriodicidadNomina
from core.core.enums import ReglaCalculoQuincenal
from core.domain.models.configuracion_fiscal_empresa import ConfiguracionFiscalEmpresaUpdate
from core.domain.models.configuracion_operativa_empresa import ConfiguracionOperativaEmpresaUpdate
from core.presentation.pages.portal.state.portal_state import PortalState
from core.domain.services.configuracion_fiscal_service import configuracion_fiscal_service
from core.domain.services.configuracion_operativa_service import configuracion_operativa_service

logger = logging.getLogger(__name__)


_TIPOS_NOMINA_OPTIONS = [
    {"value": PeriodicidadNomina.QUINCENAL.value, "label": "Quincenal"},
    {"value": PeriodicidadNomina.SEMANAL.value, "label": "Semanal"},
    {"value": PeriodicidadNomina.MENSUAL.value, "label": "Mensual"},
]

_REGLAS_CALCULO_QUINCENAL_OPTIONS = [
    {"value": ReglaCalculoQuincenal.REAL.value, "label": "Real por dias"},
    {"value": ReglaCalculoQuincenal.MIXTA.value, "label": "Base fija quincenal"},
]

_DIAS_SEMANA_OPTIONS = [
    {"value": "1", "label": "Lunes"},
    {"value": "2", "label": "Martes"},
    {"value": "3", "label": "Miercoles"},
    {"value": "4", "label": "Jueves"},
    {"value": "5", "label": "Viernes"},
    {"value": "6", "label": "Sabado"},
    {"value": "7", "label": "Domingo"},
]


class ConfiguracionEmpresaState(PortalState):
    """State de configuracion operativa de la empresa."""

    config: dict = {}
    config_cargada: bool = False

    form_tipo_nomina: str = PeriodicidadNomina.QUINCENAL.value
    form_regla_calculo_quincenal: str = ReglaCalculoQuincenal.MIXTA.value
    form_dias_bloqueo: int = 3
    form_dia_pago_1q: int = 15
    form_dia_pago_2q: int = 0
    form_dia_pago_semanal: int = 5
    form_dia_pago_mensual: int = 0
    form_dias_aguinaldo: int = 15

    def set_form_tipo_nomina(self, value: str):
        self.form_tipo_nomina = value or PeriodicidadNomina.QUINCENAL.value

    def set_form_regla_calculo_quincenal(self, value: str):
        self.form_regla_calculo_quincenal = (
            value or ReglaCalculoQuincenal.MIXTA.value
        )

    def set_form_dias_bloqueo(self, value: str):
        self.set_int_attr("form_dias_bloqueo", value, 3)

    def set_form_dia_pago_1q(self, value: str):
        self.set_int_attr("form_dia_pago_1q", value, 15)

    def set_form_dia_pago_2q(self, value: str):
        self.set_int_attr("form_dia_pago_2q", value, 0)

    def set_form_dia_pago_semanal(self, value: str):
        self.set_int_attr("form_dia_pago_semanal", value, 5)

    def set_form_dia_pago_mensual(self, value: str):
        self.set_int_attr("form_dia_pago_mensual", value, 0)

    def set_form_dias_aguinaldo(self, value: str):
        self.set_int_attr("form_dias_aguinaldo", value, 15)

    @rx.var
    def tipos_nomina_options(self) -> list[dict]:
        return _TIPOS_NOMINA_OPTIONS

    @rx.var
    def reglas_calculo_quincenal_options(self) -> list[dict]:
        return _REGLAS_CALCULO_QUINCENAL_OPTIONS

    @rx.var
    def dias_semana_options(self) -> list[dict]:
        return _DIAS_SEMANA_OPTIONS

    @rx.var
    def puede_configurar_nomina(self) -> bool:
        return bool(self.gestion_nomina_activa_empresa)

    @rx.var
    def es_quincenal(self) -> bool:
        return self.form_tipo_nomina == PeriodicidadNomina.QUINCENAL.value

    @rx.var
    def es_semanal(self) -> bool:
        return self.form_tipo_nomina == PeriodicidadNomina.SEMANAL.value

    @rx.var
    def es_mensual(self) -> bool:
        return self.form_tipo_nomina == PeriodicidadNomina.MENSUAL.value

    @rx.var
    def tiene_cambios(self) -> bool:
        if not self.config_cargada:
            return False
        return any(
            (
                self.form_tipo_nomina != self.config.get("tipo_nomina", PeriodicidadNomina.QUINCENAL.value),
                self.form_regla_calculo_quincenal != self.config.get(
                    "regla_calculo_quincenal",
                    ReglaCalculoQuincenal.MIXTA.value,
                ),
                self.form_dias_bloqueo != self.config.get("dias_bloqueo_cuenta_antes_pago", 3),
                self.form_dia_pago_1q != self.config.get("dia_pago_primera_quincena", 15),
                self.form_dia_pago_2q != self.config.get("dia_pago_segunda_quincena", 0),
                self.form_dia_pago_semanal != self.config.get("dia_pago_semanal", 5),
                self.form_dia_pago_mensual != self.config.get("dia_pago_mensual", 0),
                self.form_dias_aguinaldo != self.config.get("dias_aguinaldo", 15),
            )
        )

    async def on_mount_configuracion_empresa(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.puede_configurar_empresa:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_configuracion):
            yield

    async def _fetch_configuracion(self):
        if not self.id_empresa_actual:
            return

        try:
            config = await configuracion_operativa_service.obtener_o_crear_default(
                self.id_empresa_actual
            )
            config_fiscal = await configuracion_fiscal_service.obtener_o_crear_default(
                self.id_empresa_actual
            )
            self.config = {
                **config.model_dump(mode="json"),
                **config_fiscal.model_dump(mode="json"),
            }
            self.config_cargada = True

            self.form_tipo_nomina = str(
                self.config.get("tipo_nomina", PeriodicidadNomina.QUINCENAL.value)
            )
            self.form_regla_calculo_quincenal = str(
                self.config.get(
                    "regla_calculo_quincenal",
                    ReglaCalculoQuincenal.MIXTA.value,
                )
            )
            self.form_dias_bloqueo = config.dias_bloqueo_cuenta_antes_pago
            self.form_dia_pago_1q = config.dia_pago_primera_quincena
            self.form_dia_pago_2q = config.dia_pago_segunda_quincena
            self.form_dia_pago_semanal = int(config.dia_pago_semanal or 5)
            self.form_dia_pago_mensual = int(config.dia_pago_mensual or 0)
            self.form_dias_aguinaldo = int(getattr(config_fiscal, "dias_aguinaldo", 15) or 15)
        except Exception as e:
            logger.error("Error cargando config operativa empresa: %s", e)
            self.config = {}
            self.config_cargada = False
            self.manejar_error(e, "cargando configuracion operativa")

    async def guardar_configuracion(self):
        if not self.puede_configurar_nomina:
            return rx.toast.warning(
                "Activa la gestion de nomina en la empresa antes de configurar la politica."
            )

        self.saving = True
        try:
            datos = ConfiguracionOperativaEmpresaUpdate(
                tipo_nomina=self.form_tipo_nomina,
                regla_calculo_quincenal=self.form_regla_calculo_quincenal,
                dias_bloqueo_cuenta_antes_pago=self.form_dias_bloqueo,
                dia_pago_primera_quincena=self.form_dia_pago_1q,
                dia_pago_segunda_quincena=self.form_dia_pago_2q,
                dia_pago_semanal=self.form_dia_pago_semanal,
                dia_pago_mensual=self.form_dia_pago_mensual,
            )

            config = await configuracion_operativa_service.crear_o_actualizar(
                self.id_empresa_actual,
                datos,
            )
            config_fiscal = await configuracion_fiscal_service.crear_o_actualizar(
                self.id_empresa_actual,
                ConfiguracionFiscalEmpresaUpdate(
                    dias_aguinaldo=self.form_dias_aguinaldo,
                ),
            )
            self.config = {
                **config.model_dump(mode="json"),
                **config_fiscal.model_dump(mode="json"),
            }
            self.config_cargada = True

            return rx.toast.success("Politica de nomina guardada")
        except Exception as e:
            return self.manejar_error_con_toast(e, "guardando configuracion de nomina")
        finally:
            self.saving = False
