"""
Estado del dashboard ejecutivo de nóminas.

Muestra KPIs, comparativos y tablas de resumen para un período seleccionado.
Acceso: es_rrhh | es_contabilidad | es_admin_empresa
"""
import logging
from typing import Optional

import reflex as rx

from app.presentation.pages.nominas.base_state import NominaBaseState
from app.database import db_manager
from app.services.nomina_periodo_service import nomina_periodo_service

logger = logging.getLogger(__name__)


class NominaDashboardState(NominaBaseState):
    """Estado del dashboard ejecutivo de nóminas."""

    # Período seleccionado (string para rx.select)
    periodo_seleccionado_id: str = ""

    # Catálogo de períodos de la empresa
    periodos_disponibles: list[dict] = []

    # Datos del período seleccionado
    resumen_periodo: dict = {}
    desglose_isr: float = 0.0
    desglose_imss: float = 0.0

    # Top 5 empleados por neto y empleados con deducciones
    top_empleados: list[dict] = []
    empleados_con_incidencias: list[dict] = []

    # Comparativo con período anterior
    periodo_anterior: dict = {}

    # =========================================================================
    # COMPUTED VARS — KPIs
    # =========================================================================

    @rx.var
    def total_bruto(self) -> float:
        return float(self.resumen_periodo.get('total_percepciones') or 0)

    @rx.var
    def total_neto_kpi(self) -> float:
        return float(self.resumen_periodo.get('total_neto') or 0)

    @rx.var
    def total_retenciones_isr(self) -> float:
        return self.desglose_isr

    @rx.var
    def total_cuotas_imss(self) -> float:
        return self.desglose_imss

    @rx.var
    def total_empleados_kpi(self) -> int:
        return int(
            self.resumen_periodo.get('total_empleados')
            or len(self.top_empleados)
            or 0
        )

    # =========================================================================
    # COMPUTED VARS — Comparativo
    # =========================================================================

    @rx.var
    def neto_anterior(self) -> float:
        return float(self.periodo_anterior.get('total_neto') or 0)

    @rx.var
    def variacion_neto_monto(self) -> float:
        return round(self.total_neto_kpi - self.neto_anterior, 2)

    @rx.var
    def variacion_neto_pct(self) -> float:
        """Variación porcentual. Positivo = aumento de costos."""
        if self.neto_anterior == 0:
            return 0.0
        return round(
            (self.total_neto_kpi - self.neto_anterior) / self.neto_anterior * 100, 1
        )

    @rx.var
    def variacion_es_aumento(self) -> bool:
        """True si el neto aumentó respecto al período anterior."""
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
        return self.resumen_periodo.get('nombre', '')

    @rx.var
    def periodo_estatus_actual(self) -> str:
        return self.resumen_periodo.get('estatus', '')

    # =========================================================================
    # MONTAJE
    # =========================================================================

    async def on_mount_dashboard(self):
        """Carga la lista de períodos y selecciona el más reciente."""
        if self.requiere_login and not self.esta_autenticado:
            yield rx.redirect("/login")
            return
        if not self.puede_acceder_nomina:
            yield rx.redirect(self.nomina_no_access_path)
            return
        if not self.id_empresa_actual:
            return
        await self._cargar_periodos_disponibles()

    # =========================================================================
    # HANDLERS
    # =========================================================================

    async def seleccionar_periodo(self, periodo_id: str):
        """Carga KPIs del período seleccionado."""
        self.periodo_seleccionado_id = periodo_id
        if periodo_id:
            await self._cargar_datos_periodo(int(periodo_id))

    # =========================================================================
    # CARGA DE DATOS
    # =========================================================================

    async def _cargar_periodos_disponibles(self):
        self.loading = True
        try:
            supabase = db_manager.get_client()
            result = (
                supabase.table('periodos_nomina')
                .select('id, nombre, estatus, fecha_inicio, fecha_fin')
                .eq('empresa_id', self.id_empresa_actual)
                .order('fecha_inicio', desc=True)
                .execute()
            )
            # Convertir IDs a str para rx.select
            self.periodos_disponibles = [
                {**p, 'id': str(p['id'])} for p in (result.data or [])
            ]
            # Auto-seleccionar el más reciente si no hay selección
            if self.periodos_disponibles and not self.periodo_seleccionado_id:
                primer_id = self.periodos_disponibles[0]['id']
                self.periodo_seleccionado_id = primer_id
                await self._cargar_datos_periodo(int(primer_id))
        except Exception as e:
            self.manejar_error(e, "cargar períodos disponibles")
        finally:
            self.loading = False

    async def _cargar_datos_periodo(self, periodo_id: int):
        self.loading = True
        try:
            supabase = db_manager.get_client()

            # 1. Período actual con totales
            res = (
                supabase.table('periodos_nomina')
                .select('*')
                .eq('id', periodo_id)
                .limit(1)
                .execute()
            )
            self.resumen_periodo = (res.data or [{}])[0]

            empleados_periodo = await nomina_periodo_service.obtener_empleados_periodo(periodo_id)
            self.resumen_periodo['total_empleados'] = len(empleados_periodo)

            # 2. Desglose ISR e IMSS
            await self._cargar_desglose_conceptos(periodo_id, supabase)

            # 3. Top 5 empleados por neto
            self.top_empleados = sorted(
                empleados_periodo,
                key=lambda item: float(item.get('total_neto') or 0),
                reverse=True,
            )[:5]

            # 4. Empleados con deducciones significativas (incidencias)
            self.empleados_con_incidencias = sorted(
                [
                    item for item in empleados_periodo
                    if float(item.get('total_deducciones') or 0) > 0
                ],
                key=lambda item: float(item.get('total_deducciones') or 0),
                reverse=True,
            )[:10]

            # 5. Período anterior para comparativo
            fecha_inicio = self.resumen_periodo.get('fecha_inicio', '')
            empresa_id = self.resumen_periodo.get('empresa_id', self.id_empresa_actual)
            if fecha_inicio:
                res_ant = (
                    supabase.table('periodos_nomina')
                    .select(
                        'id, nombre, total_neto, total_percepciones, '
                        'total_deducciones, total_empleados'
                    )
                    .eq('empresa_id', empresa_id)
                    .lt('fecha_inicio', fecha_inicio)
                    .order('fecha_inicio', desc=True)
                    .limit(1)
                    .execute()
                )
                self.periodo_anterior = (res_ant.data or [{}])[0]
            else:
                self.periodo_anterior = {}

        except Exception as e:
            self.manejar_error(e, "cargar datos del período")
        finally:
            self.loading = False

    async def _cargar_desglose_conceptos(self, periodo_id: int, supabase) -> None:
        """Suma ISR e IMSS filtrando movimientos por clave de concepto."""
        try:
            # IDs de nominas_empleado del período
            res_ids = (
                supabase.table('nominas_empleado')
                .select('id')
                .eq('periodo_id', periodo_id)
                .execute()
            )
            ids = [r['id'] for r in (res_ids.data or [])]
            if not ids:
                self.desglose_isr = 0.0
                self.desglose_imss = 0.0
                return

            res_mov = (
                supabase.table('nomina_movimientos')
                .select('monto, conceptos_nomina(clave)')
                .in_('nomina_empleado_id', ids)
                .eq('tipo', 'DEDUCCION')
                .execute()
            )
            isr = 0.0
            imss = 0.0
            for mov in (res_mov.data or []):
                clave = ''
                cn = mov.get('conceptos_nomina')
                if isinstance(cn, dict):
                    clave = (cn.get('clave') or '').upper()
                monto = float(mov.get('monto') or 0)
                if 'ISR' in clave:
                    isr += monto
                elif 'IMSS' in clave:
                    imss += monto
            self.desglose_isr = round(isr, 2)
            self.desglose_imss = round(imss, 2)
        except Exception as e:
            logger.warning(f"No se pudo cargar desglose conceptos período {periodo_id}: {e}")
            self.desglose_isr = 0.0
            self.desglose_imss = 0.0
