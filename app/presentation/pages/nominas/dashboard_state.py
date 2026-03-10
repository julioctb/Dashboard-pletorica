"""
Estado del dashboard de nóminas.

Separa dos bloques:
- resumen operativo del periodo actual calculado por política de nómina
- comparativo financiero del periodo seleccionado dentro del año filtrado
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

import reflex as rx

from app.database import db_manager
from app.presentation.pages.nominas.base_state import NominaBaseState
from app.services.configuracion_operativa_service import configuracion_operativa_service
from app.services.nomina_periodo_service import nomina_periodo_service

logger = logging.getLogger(__name__)


class NominaDashboardState(NominaBaseState):
    """Estado del dashboard ejecutivo de nóminas."""

    periodo_seleccionado_id: str = ""
    filtro_anio: str = str(date.today().year)
    filtro_contrato_nomina_id: str = ""

    periodos_catalogo: list[dict] = []
    contratos_nomina_opciones: list[dict] = []
    resumen_operativo_actual: dict = {}

    resumen_periodo: dict = {}
    desglose_isr: float = 0.0
    desglose_imss: float = 0.0
    top_empleados: list[dict] = []
    empleados_con_incidencias: list[dict] = []
    periodo_anterior: dict = {}

    @staticmethod
    def _serializar_periodo_catalogo(periodo: dict) -> dict:
        return {
            **dict(periodo or {}),
            "id": str((periodo or {}).get("id", "") or ""),
        }

    def _periodos_filtrados(self, anio: Optional[str] = None) -> list[dict]:
        valor_anio = str(anio or self.filtro_anio or date.today().year)
        periodos = self.periodos_catalogo
        if self.filtro_contrato_nomina_id:
            periodos = [
                periodo
                for periodo in periodos
                if str(periodo.get("contrato_id", "") or "") == self.filtro_contrato_nomina_id
            ]
        return [
            periodo
            for periodo in periodos
            if str(periodo.get("fecha_inicio", "") or "").startswith(valor_anio)
        ]

    def _resolver_periodo_previo(self, periodo_actual: dict) -> dict:
        fecha_inicio_actual = str(periodo_actual.get("fecha_inicio", "") or "")
        periodicidad_actual = str(periodo_actual.get("periodicidad", "") or "")
        periodo_id = str(periodo_actual.get("id", "") or "")

        for periodo in self.periodos_catalogo:
            if str(periodo.get("id", "") or "") == periodo_id:
                continue
            if self.filtro_contrato_nomina_id and (
                str(periodo.get("contrato_id", "") or "") != self.filtro_contrato_nomina_id
            ):
                continue
            if str(periodo.get("periodicidad", "") or "") != periodicidad_actual:
                continue
            if str(periodo.get("fecha_inicio", "") or "") >= fecha_inicio_actual:
                continue
            return periodo
        return {}

    def _limpiar_resumen_financiero(self):
        self.periodo_seleccionado_id = ""
        self.resumen_periodo = {}
        self.desglose_isr = 0.0
        self.desglose_imss = 0.0
        self.top_empleados = []
        self.empleados_con_incidencias = []
        self.periodo_anterior = {}

    @rx.var
    def anios_disponibles(self) -> list[dict]:
        anios = {str(date.today().year)}
        periodos = self.periodos_catalogo
        if self.filtro_contrato_nomina_id:
            periodos = [
                periodo
                for periodo in periodos
                if str(periodo.get("contrato_id", "") or "") == self.filtro_contrato_nomina_id
            ]
        for periodo in periodos:
            fecha_inicio = str(periodo.get("fecha_inicio", "") or "")
            if len(fecha_inicio) >= 4:
                anios.add(fecha_inicio[:4])
        return [{"value": anio, "label": anio} for anio in sorted(anios, reverse=True)]

    @rx.var
    def periodos_disponibles(self) -> list[dict]:
        return self._periodos_filtrados(self.filtro_anio)

    @rx.var
    def tiene_periodos_disponibles(self) -> bool:
        return len(self.periodos_disponibles) > 0

    @rx.var
    def tiene_contratos_nomina(self) -> bool:
        return len(self.contratos_nomina_opciones) > 0

    @rx.var
    def tiene_resumen_operativo(self) -> bool:
        return bool(self.resumen_operativo_actual)

    @rx.var
    def warning_resumen_operativo(self) -> str:
        return str(self.resumen_operativo_actual.get("warning", "") or "")

    @rx.var
    def metricas_contrato_disponibles(self) -> bool:
        return self.warning_resumen_operativo == ""

    @rx.var
    def valor_activos_card(self) -> str:
        if not self.metricas_contrato_disponibles:
            return "Sin configurar"
        return f"{self.activos} / {self.total_plazas}"

    @rx.var
    def valor_inasistencias_card(self) -> str:
        if not self.metricas_contrato_disponibles:
            return "Sin configurar"
        return str(self.inasistencias)

    @rx.var
    def valor_incapacidades_card(self) -> str:
        if not self.metricas_contrato_disponibles:
            return "Sin configurar"
        return str(self.incapacidades)

    @rx.var
    def total_plazas(self) -> int:
        return int(self.resumen_operativo_actual.get("total_plazas") or 0)

    @rx.var
    def activos(self) -> int:
        return int(self.resumen_operativo_actual.get("activos") or 0)

    @rx.var
    def inasistencias(self) -> int:
        return int(self.resumen_operativo_actual.get("inasistencias") or 0)

    @rx.var
    def incapacidades(self) -> int:
        return int(self.resumen_operativo_actual.get("incapacidades") or 0)

    @rx.var
    def periodo_actual_titulo(self) -> str:
        return str(self.resumen_operativo_actual.get("periodo_actual_titulo") or "Sin dato")

    @rx.var
    def periodo_actual_rango(self) -> str:
        return str(self.resumen_operativo_actual.get("periodo_actual_rango") or "Sin dato")

    @rx.var
    def total_bruto(self) -> float:
        return float(self.resumen_periodo.get("total_percepciones") or 0)

    @rx.var
    def total_neto_kpi(self) -> float:
        return float(self.resumen_periodo.get("total_neto") or 0)

    @rx.var
    def total_retenciones_isr(self) -> float:
        return self.desglose_isr

    @rx.var
    def total_cuotas_imss(self) -> float:
        return self.desglose_imss

    @rx.var
    def total_empleados_kpi(self) -> int:
        return int(self.resumen_periodo.get("total_empleados") or len(self.top_empleados) or 0)

    @rx.var
    def neto_anterior(self) -> float:
        return float(self.periodo_anterior.get("total_neto") or 0)

    @rx.var
    def variacion_neto_monto(self) -> float:
        return round(self.total_neto_kpi - self.neto_anterior, 2)

    @rx.var
    def variacion_neto_pct(self) -> float:
        if self.neto_anterior == 0:
            return 0.0
        return round((self.total_neto_kpi - self.neto_anterior) / self.neto_anterior * 100, 1)

    @rx.var
    def variacion_es_aumento(self) -> bool:
        return self.variacion_neto_monto > 0

    @rx.var
    def tiene_comparativo(self) -> bool:
        return bool(self.periodo_anterior)

    @rx.var
    def tiene_resumen(self) -> bool:
        return bool(self.resumen_periodo)

    @rx.var
    def tiene_top_empleados(self) -> bool:
        return len(self.top_empleados) > 0

    @rx.var
    def tiene_incidencias(self) -> bool:
        return len(self.empleados_con_incidencias) > 0

    @rx.var
    def periodo_nombre_actual(self) -> str:
        return str(self.resumen_periodo.get("nombre") or "")

    @rx.var
    def periodo_estatus_actual(self) -> str:
        return str(self.resumen_periodo.get("estatus") or "")

    async def on_mount_dashboard(self):
        resultado = await self.validar_contexto_nomina()
        if resultado:
            yield resultado
            return
        await self._cargar_dashboard()

    async def cambiar_filtro_anio(self, valor: str):
        self.filtro_anio = valor or str(date.today().year)
        await self._seleccionar_periodo_por_filtro()

    async def cambiar_filtro_contrato_nomina(self, valor: str):
        self.filtro_contrato_nomina_id = valor or ""
        self.loading = True
        try:
            await self._cargar_resumen_operativo()
            await self._seleccionar_periodo_por_filtro(usar_loading=False)
        finally:
            self.loading = False

    async def seleccionar_periodo(self, periodo_id: str):
        if not periodo_id:
            self._limpiar_resumen_financiero()
            return

        self.periodo_seleccionado_id = periodo_id
        await self._cargar_datos_periodo(int(periodo_id))

    async def _cargar_dashboard(self):
        self.loading = True
        try:
            await self._cargar_contratos_nomina()
            periodos = await nomina_periodo_service.listar_periodos(self.id_empresa_actual)
            self.periodos_catalogo = [
                self._serializar_periodo_catalogo(periodo)
                for periodo in periodos
            ]
            await self._cargar_resumen_operativo()
            await self._seleccionar_periodo_por_filtro(usar_loading=False)
        except Exception as e:
            self.manejar_error(e, "cargar dashboard de nóminas")
        finally:
            self.loading = False

    async def _seleccionar_periodo_por_filtro(self, *, usar_loading: bool = True):
        periodos_disponibles = self._periodos_filtrados(self.filtro_anio)
        if not periodos_disponibles:
            self._limpiar_resumen_financiero()
            return

        periodo_actual = next(
            (
                periodo
                for periodo in periodos_disponibles
                if str(periodo.get("id", "") or "") == self.periodo_seleccionado_id
            ),
            None,
        )
        if periodo_actual is None:
            periodo_actual = periodos_disponibles[0]

        self.periodo_seleccionado_id = str(periodo_actual.get("id", "") or "")
        await self._cargar_datos_periodo(
            int(self.periodo_seleccionado_id),
            usar_loading=usar_loading,
        )

    async def _cargar_datos_periodo(self, periodo_id: int, *, usar_loading: bool = True):
        if usar_loading:
            self.loading = True
        try:
            periodo = await nomina_periodo_service.obtener_periodo(periodo_id)
            self.resumen_periodo = dict(periodo or {})

            empleados_periodo = await nomina_periodo_service.obtener_empleados_periodo(periodo_id)
            self.resumen_periodo["total_empleados"] = len(empleados_periodo)

            await self._cargar_desglose_conceptos(periodo_id)

            self.top_empleados = sorted(
                empleados_periodo,
                key=lambda item: float(item.get("total_neto") or 0),
                reverse=True,
            )[:5]
            self.empleados_con_incidencias = sorted(
                [
                    item
                    for item in empleados_periodo
                    if float(item.get("total_deducciones") or 0) > 0
                ],
                key=lambda item: float(item.get("total_deducciones") or 0),
                reverse=True,
            )[:10]
            self.periodo_anterior = self._resolver_periodo_previo(self.resumen_periodo)
        except Exception as e:
            self.manejar_error(e, "cargar datos del período")
            self._limpiar_resumen_financiero()
        finally:
            if usar_loading:
                self.loading = False

    async def _cargar_contratos_nomina(self):
        contratos = await configuracion_operativa_service.listar_contratos_nomina_disponibles(
            self.id_empresa_actual
        )
        self.contratos_nomina_opciones = contratos
        opciones_validas = {
            str(opcion.get("value") or "")
            for opcion in contratos
        }
        if self.filtro_contrato_nomina_id in opciones_validas:
            return

        config = await configuracion_operativa_service.obtener_por_empresa(
            self.id_empresa_actual
        )
        contrato_configurado = str(getattr(config, "contrato_nomina_id", "") or "")
        if contrato_configurado and contrato_configurado in opciones_validas:
            self.filtro_contrato_nomina_id = contrato_configurado
        elif contratos:
            self.filtro_contrato_nomina_id = str(contratos[0].get("value") or "")
        else:
            self.filtro_contrato_nomina_id = ""

    async def _cargar_resumen_operativo(self):
        contrato_id = int(self.filtro_contrato_nomina_id) if self.filtro_contrato_nomina_id else None
        self.resumen_operativo_actual = (
            await nomina_periodo_service.obtener_resumen_operativo_actual(
                self.id_empresa_actual,
                contrato_id=contrato_id,
            )
        )

    async def _cargar_desglose_conceptos(self, periodo_id: int) -> None:
        """Suma ISR e IMSS filtrando movimientos por clave de concepto."""
        try:
            supabase = db_manager.get_client()
            res_ids = (
                supabase.table("nominas_empleado")
                .select("id")
                .eq("periodo_id", periodo_id)
                .execute()
            )
            ids = [r["id"] for r in (res_ids.data or [])]
            if not ids:
                self.desglose_isr = 0.0
                self.desglose_imss = 0.0
                return

            res_mov = (
                supabase.table("nomina_movimientos")
                .select("monto, conceptos_nomina(clave)")
                .in_("nomina_empleado_id", ids)
                .eq("tipo", "DEDUCCION")
                .execute()
            )
            isr = 0.0
            imss = 0.0
            for mov in (res_mov.data or []):
                clave = ""
                concepto = mov.get("conceptos_nomina")
                if isinstance(concepto, dict):
                    clave = str(concepto.get("clave") or "").upper()
                monto = float(mov.get("monto") or 0)
                if "ISR" in clave:
                    isr += monto
                elif "IMSS" in clave:
                    imss += monto
            self.desglose_isr = round(isr, 2)
            self.desglose_imss = round(imss, 2)
        except Exception as e:
            logger.warning(
                "No se pudo cargar desglose de conceptos para periodo %s: %s",
                periodo_id,
                e,
            )
            self.desglose_isr = 0.0
            self.desglose_imss = 0.0
