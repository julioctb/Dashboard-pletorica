"""
State para la pagina de Bajas de Personal en el portal RRHH.
"""
import logging
from datetime import date
from typing import List

import reflex as rx

from app.presentation.portal.state.portal_state import PortalState
from app.services.baja_service import baja_service
from app.core.exceptions import BusinessRuleError

logger = logging.getLogger(__name__)


class BajasState(PortalState):
    """State del modulo de bajas de personal."""

    bajas: list[dict] = []
    alertas: list[dict] = []
    total_bajas: int = 0
    filtro_estatus: str = "ACTIVAS"

    baja_seleccionada: dict = {}
    mostrar_modal_accion: bool = False
    accion_actual: str = ""
    form_notas_cancelacion: str = ""

    @rx.var
    def bajas_filtradas(self) -> List[dict]:
        """Filtra bajas por busqueda de empleado o clave."""
        if not self.filtro_busqueda:
            return self.bajas

        termino = self.filtro_busqueda.lower()
        return [
            baja for baja in self.bajas
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
        if not value:
            return ""
        try:
            return date.fromisoformat(value).strftime("%d/%m/%Y")
        except ValueError:
            return value

    async def on_mount_bajas(self):
        """Carga bajas y alertas al montar la pagina."""
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.es_rrhh:
            yield rx.redirect("/portal")
            return
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
        """Marca baja como comunicada a BUAP."""
        self.saving = True
        try:
            await baja_service.comunicar_a_buap(baja["id"])
            await self._recargar_resumen()
            return rx.toast.success("Baja marcada como comunicada a BUAP")
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
        """Registra si BUAP solicito sustitucion."""
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
