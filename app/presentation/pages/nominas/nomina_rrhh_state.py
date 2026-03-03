"""
Estado de Reflex para el módulo de Nóminas (vista RRHH).

Gestiona el ciclo de vida de períodos, poblado de empleados,
captura de descuentos y envío a Contabilidad.
"""
import logging
from datetime import date
from decimal import Decimal
from typing import Optional

import reflex as rx

from app.core.ui_helpers import FILTRO_TODOS
from app.presentation.pages.nominas.base_state import NominaBaseState
from app.services.nomina_periodo_service import nomina_periodo_service
from app.database import db_manager

logger = logging.getLogger(__name__)

# Conceptos capturables por RRHH (origin=RRHH, es_automatico=False)
CONCEPTOS_RRHH = [
    {'label': 'Descuento INFONAVIT', 'value': 'DESCUENTO_INFONAVIT'},
    {'label': 'Descuento FONACOT', 'value': 'DESCUENTO_FONACOT'},
    {'label': 'Préstamo empresa', 'value': 'PRESTAMO_EMPRESA'},
    {'label': 'Pensión alimenticia', 'value': 'PENSION_ALIMENTICIA'},
]

OPCIONES_PERIODICIDAD = [
    {'label': 'Quincenal', 'value': 'QUINCENAL'},
    {'label': 'Semanal', 'value': 'SEMANAL'},
    {'label': 'Mensual', 'value': 'MENSUAL'},
]


class NominaRRHHState(NominaBaseState):
    """Estado para gestión de nóminas por RRHH / Contabilidad."""

    # =========================================================================
    # DATOS
    # =========================================================================
    periodos: list[dict] = []
    periodo_actual: dict = {}
    empleados_periodo: list[dict] = []
    descuentos_empleado: list[dict] = []

    # =========================================================================
    # UI
    # =========================================================================
    mostrar_modal_periodo: bool = False
    mostrar_modal_descuento: bool = False
    mostrar_dialog_envio: bool = False
    mostrar_dialog_iniciar: bool = False
    empleado_seleccionado: dict = {}

    # Filtro de períodos
    filtro_estatus_periodos: str = FILTRO_TODOS

    # =========================================================================
    # FORMULARIO — Período
    # =========================================================================
    form_nombre: str = ""
    form_periodicidad: str = "QUINCENAL"
    form_fecha_inicio: str = ""
    form_fecha_fin: str = ""
    form_fecha_pago: str = ""
    error_nombre: str = ""

    # =========================================================================
    # FORMULARIO — Descuento
    # =========================================================================
    form_concepto_clave: str = ""
    form_monto_descuento: str = ""
    form_notas_descuento: str = ""
    error_monto: str = ""

    # =========================================================================
    # COMPUTED VARS
    # =========================================================================

    @rx.var
    def puede_acceder(self) -> bool:
        """RRHH, Contabilidad y Admin empresa pueden usar el módulo."""
        return self.puede_acceder_nomina

    @rx.var
    def periodo_estatus(self) -> str:
        return self.periodo_actual.get('estatus', '')

    @rx.var
    def periodo_es_borrador(self) -> bool:
        return self.periodo_actual.get('estatus') == 'BORRADOR'

    @rx.var
    def periodo_en_preparacion(self) -> bool:
        return self.periodo_actual.get('estatus') == 'EN_PREPARACION_RRHH'

    @rx.var
    def periodo_enviado(self) -> bool:
        return self.periodo_actual.get('estatus') in (
            'ENVIADO_A_CONTABILIDAD', 'EN_PROCESO_CONTABILIDAD', 'CALCULADO', 'CERRADO'
        )

    @rx.var
    def puede_editar_descuentos(self) -> bool:
        return self.periodo_actual.get('estatus') == 'EN_PREPARACION_RRHH'

    @rx.var
    def puede_enviar_a_contabilidad(self) -> bool:
        return (
            self.periodo_actual.get('estatus') == 'EN_PREPARACION_RRHH'
            and len(self.empleados_periodo) > 0
        )

    @rx.var
    def nombre_periodo_actual(self) -> str:
        return self.periodo_actual.get('nombre', 'Período')

    @rx.var
    def tiene_periodos(self) -> bool:
        return len(self.periodos) > 0

    @rx.var
    def tiene_empleados(self) -> bool:
        return len(self.empleados_periodo) > 0

    @rx.var
    def periodos_filtrados(self) -> list[dict]:
        if not self.filtro_estatus_periodos or self.filtro_estatus_periodos == FILTRO_TODOS:
            return self.periodos
        return [p for p in self.periodos if p.get('estatus') == self.filtro_estatus_periodos]

    @rx.var
    def nombre_empleado_seleccionado(self) -> str:
        return self.empleado_seleccionado.get('nombre_empleado', '')

    @rx.var
    def opciones_conceptos_rrhh(self) -> list[dict]:
        return CONCEPTOS_RRHH

    @rx.var
    def opciones_periodicidad(self) -> list[dict]:
        return OPCIONES_PERIODICIDAD

    # =========================================================================
    # SETTERS EXPLÍCITOS
    # =========================================================================

    def set_form_nombre(self, v: str):
        self.form_nombre = v
        self.error_nombre = ""

    def set_form_periodicidad(self, v: str):
        self.form_periodicidad = v

    def set_form_fecha_inicio(self, v: str):
        self.form_fecha_inicio = v

    def set_form_fecha_fin(self, v: str):
        self.form_fecha_fin = v

    def set_form_fecha_pago(self, v: str):
        self.form_fecha_pago = v

    def set_form_concepto_clave(self, v: str):
        self.form_concepto_clave = v

    def set_form_monto_descuento(self, v: str):
        self.form_monto_descuento = v
        self.error_monto = ""

    def set_form_notas_descuento(self, v: str):
        self.form_notas_descuento = v

    def set_filtro_estatus_periodos(self, v: str):
        self.filtro_estatus_periodos = v

    # =========================================================================
    # MONTAJE
    # =========================================================================

    async def on_mount_periodos(self):
        """Monta la lista de períodos. Verifica acceso."""
        if self.requiere_login and not self.esta_autenticado:
            yield rx.redirect("/login")
            return
        if not self.puede_acceder_nomina:
            yield rx.redirect(self.nomina_no_access_path)
            return
        if not self.id_empresa_actual:
            yield self.mostrar_mensaje(
                "Selecciona una empresa para gestionar nóminas", "error"
            )
            return
        await self._cargar_periodos()

    async def on_mount_preparacion(self):
        """Monta la vista de preparación. Requiere periodo_actual en estado."""
        if self.requiere_login and not self.esta_autenticado:
            yield rx.redirect("/login")
            return
        if not self.puede_acceder_nomina:
            yield rx.redirect(self.nomina_no_access_path)
            return
        if not self.periodo_actual:
            yield rx.redirect(self.nomina_base_path)
            return
        periodo_id = self.periodo_actual.get('id')
        if periodo_id:
            await self._cargar_empleados(periodo_id)

    # =========================================================================
    # CARGA DE DATOS
    # =========================================================================

    async def _cargar_periodos(self):
        self.loading = True
        try:
            self.periodos = await nomina_periodo_service.listar_periodos(
                self.id_empresa_actual
            )
        except Exception as e:
            self.manejar_error(e, "cargar períodos")
        finally:
            self.loading = False

    async def _cargar_empleados(self, periodo_id: int):
        self.loading = True
        try:
            self.empleados_periodo = await nomina_periodo_service.obtener_empleados_periodo(
                periodo_id
            )
        except Exception as e:
            self.manejar_error(e, "cargar empleados del período")
        finally:
            self.loading = False

    # =========================================================================
    # CRUD PERÍODOS
    # =========================================================================

    def abrir_modal_periodo(self):
        self._limpiar_form_periodo()
        self.mostrar_modal_periodo = True

    def cerrar_modal_periodo(self):
        self.mostrar_modal_periodo = False
        self._limpiar_form_periodo()

    def _limpiar_form_periodo(self):
        self.form_nombre = ""
        self.form_periodicidad = "QUINCENAL"
        self.form_fecha_inicio = ""
        self.form_fecha_fin = ""
        self.form_fecha_pago = ""
        self.error_nombre = ""

    async def crear_periodo(self):
        """Crea período, pobla empleados y refresca la lista."""
        if not self.form_nombre.strip():
            self.error_nombre = "El nombre es obligatorio"
            return
        if not self.form_fecha_inicio or not self.form_fecha_fin:
            yield self.mostrar_mensaje("Las fechas de inicio y fin son obligatorias", "error")
            return

        self.saving = True
        try:
            fecha_inicio = date.fromisoformat(self.form_fecha_inicio)
            fecha_fin = date.fromisoformat(self.form_fecha_fin)
            fecha_pago = (
                date.fromisoformat(self.form_fecha_pago)
                if self.form_fecha_pago else None
            )

            if fecha_fin < fecha_inicio:
                yield self.mostrar_mensaje("La fecha de fin debe ser posterior al inicio", "error")
                return

            periodo = await nomina_periodo_service.crear_periodo(
                empresa_id=self.id_empresa_actual,
                nombre=self.form_nombre.strip(),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                periodicidad=self.form_periodicidad,
                fecha_pago=fecha_pago,
            )
            await nomina_periodo_service.poblar_empleados(periodo['id'])

            self.mostrar_modal_periodo = False
            self._limpiar_form_periodo()
            yield self.mostrar_mensaje("Período creado y empleados cargados", "success")
            await self._cargar_periodos()

        except Exception as e:
            self.manejar_error(e, "crear período")
        finally:
            self.saving = False

    async def abrir_periodo(self, periodo: dict):
        """Navega a la vista de preparación del período seleccionado."""
        self.periodo_actual = periodo
        await self._cargar_empleados(periodo['id'])
        yield rx.redirect(self.nomina_preparacion_path)

    # =========================================================================
    # WORKFLOW DEL PERÍODO
    # =========================================================================

    def abrir_dialog_iniciar(self):
        self.mostrar_dialog_iniciar = True

    def cerrar_dialog_iniciar(self):
        self.mostrar_dialog_iniciar = False

    async def iniciar_preparacion(self):
        """BORRADOR → EN_PREPARACION_RRHH."""
        periodo_id = self.periodo_actual.get('id')
        if not periodo_id:
            return
        self.saving = True
        try:
            resultado = await nomina_periodo_service.transicionar_estatus(
                periodo_id,
                'EN_PREPARACION_RRHH',
                str(self.usuario_actual.get('id', '') or ''),
            )
            self.periodo_actual = resultado
            self.mostrar_dialog_iniciar = False
            yield self.mostrar_mensaje("Preparación de nómina iniciada", "success")
        except Exception as e:
            self.manejar_error(e, "iniciar preparación")
        finally:
            self.saving = False

    def abrir_dialog_envio(self):
        self.mostrar_dialog_envio = True

    def cerrar_dialog_envio(self):
        self.mostrar_dialog_envio = False

    async def enviar_a_contabilidad(self):
        """EN_PREPARACION_RRHH → ENVIADO_A_CONTABILIDAD."""
        periodo_id = self.periodo_actual.get('id')
        if not periodo_id:
            return
        if not self.empleados_periodo:
            yield self.mostrar_mensaje(
                "El período no tiene empleados. Puebla el período primero.", "error"
            )
            return
        self.saving = True
        try:
            resultado = await nomina_periodo_service.transicionar_estatus(
                periodo_id,
                'ENVIADO_A_CONTABILIDAD',
                str(self.usuario_actual.get('id', '') or ''),
            )
            self.periodo_actual = resultado
            self.mostrar_dialog_envio = False
            yield self.mostrar_mensaje(
                "Nómina enviada a Contabilidad. Ya no se puede modificar.", "success"
            )
        except Exception as e:
            self.manejar_error(e, "enviar a contabilidad")
        finally:
            self.saving = False

    # =========================================================================
    # DESCUENTOS MANUALES (origen = RRHH)
    # =========================================================================

    async def abrir_modal_descuento(self, empleado: dict):
        self.empleado_seleccionado = empleado
        self.form_concepto_clave = ""
        self.form_monto_descuento = ""
        self.form_notas_descuento = ""
        self.error_monto = ""
        await self._cargar_descuentos_empleado(empleado.get('id'))
        self.mostrar_modal_descuento = True

    def cerrar_modal_descuento(self):
        self.mostrar_modal_descuento = False
        self.empleado_seleccionado = {}
        self.descuentos_empleado = []

    async def _cargar_descuentos_empleado(self, nomina_empleado_id: int):
        try:
            supabase = db_manager.get_client()
            result = (
                supabase.table('nomina_movimientos')
                .select('id, monto, notas, concepto_id, conceptos_nomina(nombre)')
                .eq('nomina_empleado_id', nomina_empleado_id)
                .eq('origen', 'RRHH')
                .execute()
            )
            items = []
            for r in (result.data or []):
                concepto = r.pop('conceptos_nomina', {}) or {}
                r['concepto_nombre'] = concepto.get('nombre', '')
                items.append(r)
            self.descuentos_empleado = items
        except Exception as e:
            logger.error(f"Error cargando descuentos empleado: {e}")
            self.descuentos_empleado = []

    async def guardar_descuento(self):
        if not self.form_concepto_clave:
            yield self.mostrar_mensaje("Selecciona un concepto", "error")
            return
        if not self.form_monto_descuento.strip():
            self.error_monto = "El monto es obligatorio"
            return
        try:
            monto = Decimal(self.form_monto_descuento.replace(',', '').strip())
            if monto <= 0:
                self.error_monto = "El monto debe ser mayor a 0"
                return
        except Exception:
            self.error_monto = "Monto inválido (ej: 1500.00)"
            return

        nomina_empleado_id = self.empleado_seleccionado.get('id')
        if not nomina_empleado_id:
            return

        self.saving = True
        try:
            concepto_id = await self._obtener_concepto_id(self.form_concepto_clave)
            if not concepto_id:
                yield self.mostrar_mensaje("Concepto no encontrado en el catálogo", "error")
                return

            supabase = db_manager.get_client()
            supabase.table('nomina_movimientos').insert({
                'nomina_empleado_id': nomina_empleado_id,
                'concepto_id': concepto_id,
                'tipo': 'DEDUCCION',
                'origen': 'RRHH',
                'monto': float(monto),
                'monto_gravable': 0.0,
                'monto_exento': 0.0,
                'es_automatico': False,
                'notas': self.form_notas_descuento.strip() or None,
            }).execute()

            self.form_concepto_clave = ""
            self.form_monto_descuento = ""
            self.form_notas_descuento = ""
            await self._cargar_descuentos_empleado(nomina_empleado_id)
            yield self.mostrar_mensaje("Descuento aplicado", "success")

        except Exception as e:
            self.manejar_error(e, "guardar descuento")
        finally:
            self.saving = False

    async def eliminar_descuento(self, movimiento_id: int):
        try:
            supabase = db_manager.get_client()
            supabase.table('nomina_movimientos').delete().eq(
                'id', movimiento_id
            ).eq('origen', 'RRHH').execute()
            nomina_empleado_id = self.empleado_seleccionado.get('id')
            if nomina_empleado_id:
                await self._cargar_descuentos_empleado(nomina_empleado_id)
            yield self.mostrar_mensaje("Descuento eliminado", "success")
        except Exception as e:
            self.manejar_error(e, "eliminar descuento")

    async def _obtener_concepto_id(self, clave: str) -> Optional[int]:
        try:
            supabase = db_manager.get_client()
            result = (
                supabase.table('conceptos_nomina')
                .select('id')
                .eq('clave', clave)
                .execute()
            )
            return result.data[0]['id'] if result.data else None
        except Exception:
            return None
