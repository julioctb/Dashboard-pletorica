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

from app.modules.nomina.domain.enums import TipoPeriodoNomina
from app.core.text_utils import formatear_moneda
from app.presentation.pages.backoffice.nominas.base_state import NominaBaseState
from app.modules.nomina.application import contrato_categoria_service
from app.modules.nomina.application import configuracion_operativa_service
from app.modules.nomina.application import nomina_periodo_service
from app.modules.application import presentation_bridge_service

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
    categorias_contrato_catalogo: list[dict] = []
    empleados_periodo_catalogo: list[dict] = []
    movimientos_periodo: dict = {}
    permisos_periodo: int = 0
    top_empleados: list[dict] = []
    empleados_con_incidencias: list[dict] = []
    periodo_anterior: dict = {}

    @staticmethod
    def _serializar_periodo_catalogo(periodo: dict) -> dict:
        return {
            **dict(periodo or {}),
            "id": str((periodo or {}).get("id", "") or ""),
        }

    def _periodos_ordinarios_catalogo(self) -> list[dict]:
        return [
            periodo
            for periodo in self.periodos_catalogo
            if str(periodo.get("tipo_periodo") or TipoPeriodoNomina.ORDINARIA.value)
            == TipoPeriodoNomina.ORDINARIA.value
        ]

    def _periodos_filtrados(self, anio: Optional[str] = None) -> list[dict]:
        valor_anio = str(anio or self.filtro_anio or date.today().year)
        periodos = self._periodos_ordinarios_catalogo()
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

        for periodo in self._periodos_ordinarios_catalogo():
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
        self.empleados_periodo_catalogo = []
        self.movimientos_periodo = {}
        self.permisos_periodo = 0
        self.top_empleados = []
        self.empleados_con_incidencias = []
        self.periodo_anterior = {}

    @rx.var
    def anios_disponibles(self) -> list[dict]:
        anios = {str(date.today().year)}
        periodos = self._periodos_ordinarios_catalogo()
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
    def contrato_activo_label(self) -> str:
        contrato_id = str(self.filtro_contrato_nomina_id or "")
        if not contrato_id:
            return "Sin contrato seleccionado"
        for contrato in self.contratos_nomina_opciones:
            if str(contrato.get("value") or "") == contrato_id:
                return str(contrato.get("label") or "Sin contrato seleccionado")
        return "Sin contrato seleccionado"

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
        return f"{self.activos_plantilla} / {self.total_plazas}"

    @rx.var
    def activos_plantilla(self) -> int:
        if self.tiene_resumen:
            return self.total_empleados_kpi
        return self.activos

    @rx.var
    def cobertura_plazas_pct(self) -> int:
        if self.total_plazas <= 0:
            return 0
        return round((self.activos_plantilla / self.total_plazas) * 100)

    @rx.var
    def cobertura_plazas_width(self) -> str:
        return f"{self.cobertura_plazas_pct}%"

    @rx.var
    def cobertura_plazas_hint(self) -> str:
        return f"{self.cobertura_plazas_pct}% cobertura"

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
    def total_neto_kpi_fmt(self) -> str:
        return formatear_moneda(f"{self.total_neto_kpi:.2f}")

    @rx.var
    def neto_a_dispersar_display(self) -> str:
        if self.periodo_estatus_actual == "BORRADOR" and self.total_neto_kpi <= 0:
            return "—"
        return self.total_neto_kpi_fmt

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
    def total_empleados_anterior(self) -> int:
        return int(self.periodo_anterior.get("total_empleados") or 0)

    @rx.var
    def delta_empleados(self) -> int:
        return self.total_empleados_kpi - self.total_empleados_anterior

    @rx.var
    def delta_empleados_label(self) -> str:
        delta = self.delta_empleados
        if delta == 0:
            return "Sin cambio"
        if delta > 0:
            return f"+{delta} vs anterior"
        return f"{delta} vs anterior"

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
    def delta_neto_label(self) -> str:
        delta = self.variacion_neto_monto
        if delta == 0:
            return "Sin cambio vs anterior"
        monto = formatear_moneda(f"{abs(delta):.2f}")
        prefijo = "+" if delta > 0 else "-"
        return f"{prefijo}{monto} vs anterior"

    @rx.var
    def referencia_periodo_anterior_label(self) -> str:
        nombre = str(self.periodo_anterior.get("nombre") or "").strip()
        if not nombre:
            return ""
        return f"Comparado contra {nombre}"

    @rx.var
    def categorias_plantilla(self) -> list[dict]:
        conteos: dict[int, int] = {}
        for empleado in self.empleados_periodo_catalogo:
            categoria_id = int(empleado.get("categoria_puesto_id") or 0)
            if categoria_id <= 0:
                continue
            conteos[categoria_id] = conteos.get(categoria_id, 0) + 1

        if self.categorias_contrato_catalogo:
            return [
                {
                    "id": categoria["id"],
                    "label": categoria["label"],
                    "valor": conteos.get(int(categoria["id"]), 0),
                }
                for categoria in self.categorias_contrato_catalogo
            ]

        agregados: dict[str, int] = {}
        for empleado in self.empleados_periodo_catalogo:
            nombre = str(empleado.get("categoria_nombre") or "").strip() or "Sin categoría"
            agregados[nombre] = agregados.get(nombre, 0) + 1
        return [
            {"id": nombre, "label": nombre, "valor": total}
            for nombre, total in agregados.items()
        ]

    @rx.var
    def total_transferencia_empleados(self) -> int:
        return len(
            [
                emp
                for emp in self.empleados_periodo_catalogo
                if str(emp.get("clabe_destino") or "").strip()
                or str(emp.get("banco_destino") or "").strip()
            ]
        )

    @rx.var
    def monto_transferencia_total(self) -> float:
        return round(
            sum(
                float(emp.get("total_neto") or 0)
                for emp in self.empleados_periodo_catalogo
                if str(emp.get("clabe_destino") or "").strip()
                or str(emp.get("banco_destino") or "").strip()
            ),
            2,
        )

    @rx.var
    def monto_transferencia_total_fmt(self) -> str:
        return formatear_moneda(f"{self.monto_transferencia_total:.2f}")

    @rx.var
    def total_efectivo_empleados(self) -> int:
        return max(self.total_empleados_kpi - self.total_transferencia_empleados, 0)

    @rx.var
    def monto_efectivo_total(self) -> float:
        return round(
            sum(
                float(emp.get("total_neto") or 0)
                for emp in self.empleados_periodo_catalogo
                if not (
                    str(emp.get("clabe_destino") or "").strip()
                    or str(emp.get("banco_destino") or "").strip()
                )
            ),
            2,
        )

    @rx.var
    def monto_efectivo_total_fmt(self) -> str:
        return formatear_moneda(f"{self.monto_efectivo_total:.2f}")

    @rx.var
    def altas_periodo(self) -> int:
        return int(self.movimientos_periodo.get("altas") or 0)

    @rx.var
    def bajas_periodo(self) -> int:
        return int(self.movimientos_periodo.get("bajas") or 0)

    @rx.var
    def total_movimientos_periodo(self) -> int:
        return int(self.movimientos_periodo.get("total") or 0)

    @rx.var
    def hint_movimientos_periodo(self) -> str:
        return f"{self.altas_periodo} altas · {self.bajas_periodo} bajas"

    @rx.var
    def total_faltas_periodo(self) -> int:
        return int(
            sum(int(emp.get("dias_faltas") or 0) for emp in self.empleados_periodo_catalogo)
        )

    @rx.var
    def empleados_con_faltas_periodo(self) -> int:
        return len(
            [
                emp
                for emp in self.empleados_periodo_catalogo
                if int(emp.get("dias_faltas") or 0) > 0
            ]
        )

    @rx.var
    def hint_faltas_periodo(self) -> str:
        empleados = self.empleados_con_faltas_periodo
        if empleados <= 0:
            return ""
        return f"{empleados} empleado(s)"

    @rx.var
    def total_incapacidades_dias(self) -> int:
        return int(
            sum(
                int(emp.get("dias_incapacidad") or 0)
                for emp in self.empleados_periodo_catalogo
            )
        )

    @rx.var
    def empleados_con_incapacidades_periodo(self) -> int:
        return len(
            [
                emp
                for emp in self.empleados_periodo_catalogo
                if int(emp.get("dias_incapacidad") or 0) > 0
            ]
        )

    @rx.var
    def hint_incapacidades_periodo(self) -> str:
        empleados = self.empleados_con_incapacidades_periodo
        dias = self.total_incapacidades_dias
        if empleados <= 0 or dias <= 0:
            return ""
        sufijo = "s" if empleados != 1 else ""
        return f"{empleados} empleado{sufijo} · {dias} día(s)"

    @rx.var
    def total_horas_extra_periodo(self) -> float:
        return round(
            sum(
                float(emp.get("horas_extra_dobles") or 0)
                + float(emp.get("horas_extra_triples") or 0)
                for emp in self.empleados_periodo_catalogo
            ),
            2,
        )

    @rx.var
    def empleados_con_horas_extra_periodo(self) -> int:
        return len(
            [
                emp
                for emp in self.empleados_periodo_catalogo
                if (
                    float(emp.get("horas_extra_dobles") or 0)
                    + float(emp.get("horas_extra_triples") or 0)
                ) > 0
            ]
        )

    @rx.var
    def hint_horas_extra_periodo(self) -> str:
        empleados = self.empleados_con_horas_extra_periodo
        if empleados <= 0:
            return ""
        return f"{empleados} empleado(s)"

    @rx.var
    def total_permisos_periodo(self) -> int:
        return int(self.permisos_periodo or 0)

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

    @rx.var
    def periodo_actual_header_label(self) -> str:
        return str(self.resumen_periodo.get("nombre") or "Sin período seleccionado")

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

    async def seleccionar_periodo(self, periodo_id: object):
        periodo_id_str = str(periodo_id or "").strip()
        if not periodo_id_str:
            self._limpiar_resumen_financiero()
            return

        self.periodo_seleccionado_id = periodo_id_str
        await self._cargar_datos_periodo(int(periodo_id_str))

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
            self.empleados_periodo_catalogo = empleados_periodo
            self.resumen_periodo["total_empleados"] = len(empleados_periodo)
            self.movimientos_periodo = await nomina_periodo_service.obtener_movimientos_periodo(
                self.id_empresa_actual,
                contrato_id=periodo.get("contrato_id"),
                fecha_inicio=str(periodo.get("fecha_inicio") or ""),
                fecha_fin=str(periodo.get("fecha_fin") or ""),
            )
            self.permisos_periodo = await nomina_periodo_service.contar_permisos_periodo(
                self.id_empresa_actual,
                contrato_id=periodo.get("contrato_id"),
                fecha_inicio=str(periodo.get("fecha_inicio") or ""),
                fecha_fin=str(periodo.get("fecha_fin") or ""),
            )

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
        await self._cargar_categorias_contrato(contrato_id)

    async def _cargar_categorias_contrato(self, contrato_id: Optional[int]) -> None:
        if contrato_id is None:
            self.categorias_contrato_catalogo = []
            return
        try:
            categorias = await contrato_categoria_service.obtener_resumen_de_contrato(
                int(contrato_id)
            )
            self.categorias_contrato_catalogo = [
                {
                    "id": str(categoria.categoria_puesto_id),
                    "label": str(categoria.categoria_nombre or "Sin categoría"),
                }
                for categoria in categorias
            ]
        except Exception as e:
            logger.warning(
                "No se pudieron cargar categorías del contrato %s: %s",
                contrato_id,
                e,
            )
            self.categorias_contrato_catalogo = []

    async def _cargar_desglose_conceptos(self, periodo_id: int) -> None:
        """Suma ISR e IMSS filtrando movimientos por clave de concepto."""
        try:
            ids = await presentation_bridge_service.fetch_nomina_empleado_ids(periodo_id)
            if not ids:
                self.desglose_isr = 0.0
                self.desglose_imss = 0.0
                return

            isr = 0.0
            imss = 0.0
            movimientos = await presentation_bridge_service.fetch_deducciones_movimientos(ids)
            for mov in movimientos:
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
