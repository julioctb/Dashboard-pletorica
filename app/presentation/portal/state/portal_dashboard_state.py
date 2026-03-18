"""
Substate del dashboard del portal.

Separado de PortalState para no cargar vars pesadas (list[dict])
en todas las paginas del portal — solo se serializa cuando se
visita /portal.
"""

import logging
from datetime import date, timedelta

import reflex as rx

from app.core.text_utils import capitalizar_palabras
from app.presentation.portal.state.portal_state import PortalState

logger = logging.getLogger(__name__)


class PortalDashboardState(PortalState):
    """State exclusivo del dashboard del portal."""

    # Metric footers
    empleados_en_onboarding: int = 0
    contratos_por_vencer: int = 0

    # Widget: Cobertura por contrato
    cobertura_por_contrato: list[dict] = []

    # Widget: Nomina
    nomina_periodo_actual: dict = {}

    # Widget: Entregables
    entregables_del_mes: list[dict] = []
    entregables_completados: int = 0
    entregables_total: int = 0

    # Widget: Ausencias
    top_ausencias_empleados: list[dict] = []
    top_tipos_ausencia: list[dict] = []
    total_faltas_mes: int = 0

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def porcentaje_cobertura(self) -> int:
        """Porcentaje global de cobertura de plazas."""
        total = self.total_plazas_ocupadas + self.total_plazas_vacantes
        if total == 0:
            return 0
        return int((self.total_plazas_ocupadas / total) * 100)

    @rx.var
    def nomina_estatus(self) -> str:
        return self.nomina_periodo_actual.get("estatus", "")

    @rx.var
    def nomina_periodo_label(self) -> str:
        return self.nomina_periodo_actual.get("periodo_label", "")

    @rx.var
    def tiene_nomina_activa(self) -> bool:
        return bool(self.nomina_periodo_actual)

    @rx.var
    def tiene_entregables(self) -> bool:
        return len(self.entregables_del_mes) > 0

    @rx.var
    def tiene_ausencias(self) -> bool:
        return self.total_faltas_mes > 0

    @rx.var
    def tiene_cobertura(self) -> bool:
        return len(self.cobertura_por_contrato) > 0

    # ========================
    # DATA FETCH
    # ========================
    async def _fetch_dashboard_widgets(self):
        """Carga datos de los widgets del dashboard."""
        if not self.id_empresa_actual or self.es_empleado_portal:
            return

        import asyncio
        from app.services import (
            onboarding_service,
            contrato_service,
            contrato_categoria_service,
            plaza_service,
            nomina_periodo_service,
            entregable_service,
            asistencia_service,
        )

        async def fetch_onboarding():
            try:
                conteos = await onboarding_service.obtener_conteos_pipeline(
                    empresa_id=self.id_empresa_actual,
                )
                self.empleados_en_onboarding = sum(conteos.values())
            except Exception as e:
                logger.debug("Error cargando onboarding: %s", e)
                self.empleados_en_onboarding = 0

        async def fetch_contratos_por_vencer():
            try:
                contratos = await contrato_service.obtener_por_empresa(
                    self.id_empresa_actual, incluir_inactivos=False,
                )
                hoy = date.today()
                limite = hoy + timedelta(days=30)
                self.contratos_por_vencer = sum(
                    1 for c in contratos
                    if getattr(c, "fecha_fin", None)
                    and hoy <= getattr(c, "fecha_fin") <= limite
                )
            except Exception as e:
                logger.debug("Error cargando contratos por vencer: %s", e)
                self.contratos_por_vencer = 0

        async def fetch_cobertura():
            try:
                # 1. Contratos activos con plazas (para la lista de contratos)
                resumen_contratos = await plaza_service.obtener_resumen_contratos_con_plazas(
                    empresa_id=self.id_empresa_actual,
                    solo_activos=True,
                )
                if not resumen_contratos:
                    self.cobertura_por_contrato = []
                    return

                # 2. Plazas agrupadas por (contrato, categoria) — da ocupadas reales
                resumen_cats = await plaza_service.obtener_resumen_categorias_con_plazas(
                    empresa_id=self.id_empresa_actual,
                )

                # 3. Min/max contractuales por categoria
                contrato_ids = [r["contrato_id"] for r in resumen_contratos]
                cc_por_contrato: dict[int, list] = {cid: [] for cid in contrato_ids}
                for cid in contrato_ids:
                    try:
                        cats = await contrato_categoria_service.obtener_resumen_de_contrato(cid)
                        cc_por_contrato[cid] = cats
                    except Exception:
                        pass

                # Index: (contrato_id, categoria_puesto_id) -> ocupadas
                ocupadas_index: dict[tuple, int] = {}
                for cat in resumen_cats:
                    key = (cat.get("contrato_id"), cat.get("categoria_puesto_id"))
                    ocupadas_index[key] = cat.get("plazas_ocupadas", 0)

                # 4. Construir estructura nested
                resultado = []
                for rc in resumen_contratos:
                    cid = rc["contrato_id"]
                    categorias = []
                    for cc in cc_por_contrato.get(cid, []):
                        cat_id = getattr(cc, "categoria_puesto_id", None)
                        nombre_raw = getattr(cc, "categoria_nombre", "Sin categoria")
                        categorias.append({
                            "nombre": capitalizar_palabras(nombre_raw),
                            "min": getattr(cc, "cantidad_minima", 0),
                            "max": getattr(cc, "cantidad_maxima", 0),
                            "ocupadas": ocupadas_index.get((cid, cat_id), 0),
                        })
                    resultado.append({
                        "contrato_numero": rc.get("contrato_codigo", ""),
                        "categorias": categorias,
                    })
                self.cobertura_por_contrato = resultado
            except Exception as e:
                logger.debug("Error cargando cobertura: %s", e)
                self.cobertura_por_contrato = []

        async def fetch_nomina():
            if not self.gestion_nomina_activa_empresa:
                self.nomina_periodo_actual = {}
                return
            try:
                periodos = await nomina_periodo_service.listar_periodos(
                    empresa_id=self.id_empresa_actual,
                    estatuses=[
                        "BORRADOR",
                        "EN_PREPARACION_RRHH",
                        "ENVIADO_A_CONTABILIDAD",
                        "EN_PROCESO_CONTABILIDAD",
                        "CALCULADO",
                    ],
                )
                if periodos:
                    p = periodos[0]
                    fi = p.get("fecha_inicio", "")
                    ff = p.get("fecha_fin", "")
                    self.nomina_periodo_actual = {
                        "periodo_label": f"{fi} - {ff}",
                        "estatus": p.get("estatus", ""),
                        "tipo_periodo": p.get("tipo_periodo", ""),
                    }
                else:
                    self.nomina_periodo_actual = {}
            except Exception as e:
                logger.debug("Error cargando nomina: %s", e)
                self.nomina_periodo_actual = {}

        async def fetch_entregables():
            try:
                entregables = await entregable_service.obtener_por_empresa(
                    empresa_id=self.id_empresa_actual,
                    limite=10,
                )
                self.entregables_del_mes = [
                    {
                        "nombre": getattr(e, "nombre", ""),
                        "estatus": getattr(e, "estatus", ""),
                        "contrato_codigo": getattr(e, "contrato_codigo", ""),
                        "fecha_limite": str(getattr(e, "fecha_limite", "")),
                    }
                    for e in entregables
                ]
                self.entregables_completados = sum(
                    1 for e in entregables if getattr(e, "estatus", "") in ("APROBADO", "PAGADO")
                )
                self.entregables_total = len(entregables)
            except Exception as e:
                logger.debug("Error cargando entregables: %s", e)
                self.entregables_del_mes = []

        async def fetch_ausencias():
            try:
                hoy = date.today()
                inicio_mes = hoy.replace(day=1)
                resumen = await asistencia_service.obtener_resumen_incidencias_mes(
                    empresa_id=self.id_empresa_actual,
                    fecha_inicio=inicio_mes,
                    fecha_fin=hoy,
                )
                self.top_ausencias_empleados = resumen.get("por_empleado", [])
                self.top_tipos_ausencia = resumen.get("por_tipo", [])
                self.total_faltas_mes = resumen.get("total_faltas", 0)
            except Exception as e:
                logger.debug("Error cargando ausencias: %s", e)

        await asyncio.gather(
            fetch_onboarding(),
            fetch_contratos_por_vencer(),
            fetch_cobertura(),
            fetch_nomina(),
            fetch_entregables(),
            fetch_ausencias(),
        )

    # ========================
    # MOUNT
    # ========================
    async def on_mount_dashboard(self):
        """Montaje del dashboard: auth + metricas + widgets."""
        async for _ in self._montar_pagina_portal(
            self._fetch_metricas,
            self._fetch_dashboard_widgets,
        ):
            yield
