"""
State para la pagina de Bajas de Personal en el portal RRHH.
"""
import logging
from datetime import date
from typing import List

import reflex as rx

from core.core.text_utils import capitalizar_palabras, formatear_fecha
from core.modules.empleados.application import baja_service
from core.presentation.pages.portal.state.portal_state import PortalState
from core.core.exceptions import BusinessRuleError

logger = logging.getLogger(__name__)


class BajasState(PortalState):
    """State del modulo de bajas de personal."""

    bajas: list[dict] = []
    alertas: list[dict] = []
    total_bajas: int = 0
    filtro_estatus: str = "ACTIVAS"
    empleado_id_query: int = 0

    baja_seleccionada: dict = {}
    mostrar_modal_accion: bool = False
    accion_actual: str = ""
    form_notas_cancelacion: str = ""

    @rx.var
    def bajas_filtradas(self) -> List[dict]:
        """Filtra bajas por busqueda de empleado o clave."""
        bajas = self.bajas

        if self.empleado_id_query > 0:
            bajas = [
                baja for baja in bajas
                if int(baja.get("empleado_id") or 0) == self.empleado_id_query
            ]

        if not self.filtro_busqueda:
            return bajas

        termino = self.filtro_busqueda.lower()
        return [
            baja for baja in bajas
            if termino in (baja.get("empleado_nombre") or "").lower()
            or termino in (baja.get("empleado_clave") or "").lower()
            or termino in (baja.get("motivo") or "").lower()
        ]

    @rx.var
    def tiene_alertas(self) -> bool:
        return len(self.alertas) > 0

    @staticmethod
    def _calcular_badge_liquidacion(estatus: str, dias) -> str:
        """Calcula el valor del badge de liquidacion (Python puro, sin Vars)."""
        if estatus == "ENTREGADA":
            return "entregada"
        if dias is None:
            return "pendiente"
        try:
            dias_int = int(dias)
        except (TypeError, ValueError):
            return "pendiente"
        if dias_int < 0:
            return "vencida"
        if dias_int <= 5:
            return "proxima"
        return "pendiente"

    @staticmethod
    def _formatear_fecha_iso(value: str) -> str:
        """Formatea fecha ISO a DD/MM/AAAA para la UI."""
        return formatear_fecha(value, valor_vacio="")

    def _aplicar_query_inicial(self):
        query = self.router_data.get("query", {}) or {}
        empleado_id = query.get("empleado_id")
        estatus = str(query.get("estatus", "") or "").upper()

        try:
            self.empleado_id_query = int(empleado_id) if empleado_id else 0
        except (TypeError, ValueError):
            self.empleado_id_query = 0

        if estatus in {"ACTIVAS", "CERRADAS", "TODAS"}:
            self.filtro_estatus = estatus

    async def on_mount_bajas(self):
        """Carga bajas y alertas al montar la pagina."""
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.mostrar_seccion_rrhh or not self.puede_acceder_rrhh:
            yield rx.redirect("/portal")
            return
        self._aplicar_query_inicial()
        async for _ in self._montar_pagina(self._cargar_bajas, self._cargar_alertas):
            yield

    async def _cargar_bajas(self):
        """Carga bajas segun filtro."""
        if not self.id_empresa_actual:
            return
        try:
            solo_activas = self.filtro_estatus == "ACTIVAS"
            resumenes = await baja_service.obtener_bajas_empresa(
                empresa_id=self.id_empresa_actual,
                solo_activas=solo_activas,
            )
            bajas = []
            for resumen in resumenes:
                baja = resumen.model_dump(mode='json')
                baja["fecha_efectiva_fmt"] = self._formatear_fecha_iso(
                    str(baja.get("fecha_efectiva", ""))
                )
                baja["empleado_nombre_ui"] = capitalizar_palabras(
                    str(baja.get("empleado_nombre", "") or "")
                )
                baja["badge_liquidacion"] = self._calcular_badge_liquidacion(
                    baja.get("estatus_liquidacion", ""),
                    baja.get("dias_para_liquidar"),
                )
                bajas.append(baja)

            if self.filtro_estatus == "CERRADAS":
                bajas = [
                    baja for baja in bajas
                    if baja.get("estatus") in ("CERRADA", "CANCELADA")
                ]

            self.bajas = bajas
            self.total_bajas = len(bajas)
        except Exception as e:
            self.mostrar_mensaje(f"Error cargando bajas: {e}", "error")
            self.bajas = []
            self.total_bajas = 0

    async def _cargar_alertas(self):
        """Carga alertas de plazos pendientes."""
        if not self.id_empresa_actual:
            return
        try:
            self.alertas = await baja_service.obtener_alertas_pendientes(
                self.id_empresa_actual
            )
        except Exception as e:
            logger.error(f"Error cargando alertas: {e}")
            self.alertas = []

    async def cambiar_filtro(self, filtro: str):
        """Cambia filtro y recarga."""
        self.filtro_estatus = filtro
        await self._cargar_bajas()

    async def recargar_bajas(self):
        """Recarga bajas y alertas."""
        async for _ in self._recargar_datos(self._cargar_bajas, self._cargar_alertas):
            yield

    async def _recargar_resumen(self):
        """Sincroniza lista y alertas tras una mutación."""
        await self._cargar_bajas()
        await self._cargar_alertas()

    async def comunicar_baja(self, baja: dict):
        """Marca baja como comunicada al cliente."""
        self.saving = True
        try:
            await baja_service.comunicar_a_buap(baja["id"])
            await self._recargar_resumen()
            return rx.toast.success("Baja marcada como comunicada al cliente")
        except (BusinessRuleError, ValueError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "comunicando baja")
        finally:
            self.saving = False

    async def registrar_liquidacion(self, baja: dict):
        """Marca liquidacion como entregada."""
        self.saving = True
        try:
            await baja_service.registrar_liquidacion(baja["id"])
            await self._recargar_resumen()
            return rx.toast.success("Liquidacion registrada como entregada")
        except (BusinessRuleError, ValueError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "registrando liquidacion")
        finally:
            self.saving = False

    async def cerrar_baja(self, baja: dict):
        """Cierra el proceso de baja."""
        self.saving = True
        try:
            await baja_service.cerrar_baja(baja["id"])
            await self._recargar_resumen()
            return rx.toast.success("Proceso de baja cerrado")
        except (BusinessRuleError, ValueError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "cerrando baja")
        finally:
            self.saving = False

    async def cancelar_baja(self):
        """Cancela la baja y reactiva al empleado."""
        if not self.baja_seleccionada:
            return

        self.saving = True
        try:
            await baja_service.cancelar_baja(
                baja_id=self.baja_seleccionada["id"],
                notas=self.form_notas_cancelacion,
            )
            self.cerrar_modal_accion()
            await self._recargar_resumen()
            return rx.toast.success("Baja cancelada. Empleado reactivado.")
        except (BusinessRuleError, ValueError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "cancelando baja")
        finally:
            self.saving = False

    async def actualizar_sustitucion(self, baja: dict, requiere: bool):
        """Registra si el cliente solicitó sustitución."""
        try:
            await baja_service.actualizar_sustitucion(baja["id"], requiere)
            await self._cargar_bajas()
            msg = (
                "Sustitucion marcada como requerida"
                if requiere else "Marcado: no requiere sustitucion"
            )
            return rx.toast.success(msg)
        except Exception as e:
            return self.manejar_error_con_toast(e, "actualizando sustitucion")

    async def actualizar_sustitucion_valor(self, baja: dict, valor: str):
        """Mapea valor UI a bool y actualiza sustitucion."""
        if valor == "SI":
            return await self.actualizar_sustitucion(baja, True)
        if valor == "NO":
            return await self.actualizar_sustitucion(baja, False)
        return rx.toast.error("Valor de sustitucion invalido")

    def abrir_cancelacion(self, baja: dict):
        self.baja_seleccionada = baja
        self.form_notas_cancelacion = ""
        self.accion_actual = "cancelar"
        self.mostrar_modal_accion = True

    def cerrar_modal_accion(self):
        self.mostrar_modal_accion = False
        self.baja_seleccionada = {}
        self.accion_actual = ""
        self.form_notas_cancelacion = ""

    def set_form_notas_cancelacion(self, value: str):
        self.form_notas_cancelacion = value

    @rx.event
    def consultar_baja(self, baja: dict):
        if not isinstance(baja, dict):
            return

        empleado_id = int(baja.get("empleado_id") or 0)
        if empleado_id <= 0:
            return rx.redirect("/portal/bajas")

        return rx.redirect(
            f"/portal/bajas?empleado_id={empleado_id}&estatus={self.filtro_estatus}",
        )
