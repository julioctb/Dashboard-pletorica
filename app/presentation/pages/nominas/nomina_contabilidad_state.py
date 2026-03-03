"""
Estado de Reflex para la vista de Contabilidad en el módulo de Nóminas.

Gestiona: recepción de períodos de RRHH, captura de bonos,
ejecución del cálculo fiscal, cierre de períodos y detalle por empleado.

Acceso: es_contabilidad | es_admin_empresa
"""
import logging
from decimal import Decimal
from typing import Optional

import reflex as rx

from app.presentation.pages.nominas.base_state import NominaBaseState
from app.services.nomina_periodo_service import nomina_periodo_service
from app.services.nomina_calculo_service import nomina_calculo_service
from app.services.dispersion_service import dispersion_service
from app.database import db_manager

logger = logging.getLogger(__name__)

# Bonos capturables por Contabilidad (origen_captura = CONTABILIDAD)
CONCEPTOS_CONTABILIDAD = [
    {'label': 'Bono de productividad', 'value': 'BONO_PRODUCTIVIDAD'},
    {'label': 'Bono de puntualidad',   'value': 'BONO_PUNTUALIDAD'},
    {'label': 'Bono de asistencia',    'value': 'BONO_ASISTENCIA'},
]

# Estatus en los que Contabilidad puede actuar
_ESTATUS_CONTABILIDAD = (
    'ENVIADO_A_CONTABILIDAD',
    'EN_PROCESO_CONTABILIDAD',
    'CALCULADO',
    'CERRADO',
)


class NominaContabilidadState(NominaBaseState):
    """Estado para la estación de trabajo de Contabilidad en nóminas."""

    # =========================================================================
    # DATOS
    # =========================================================================
    periodos_pendientes: list[dict] = []
    periodo_actual: dict = {}
    empleados_periodo: list[dict] = []
    empleado_detalle: dict = {}
    movimientos_detalle: list[dict] = []

    # =========================================================================
    # UI — Modales / Dialogs
    # =========================================================================
    mostrar_modal_bono: bool = False
    empleado_bono: dict = {}
    form_concepto_bono_clave: str = ""
    form_monto_bono: str = ""
    form_notas_bono: str = ""
    error_monto_bono: str = ""

    mostrar_dialog_ejecutar: bool = False
    mostrar_dialog_cerrar: bool = False
    mostrar_dialog_devolver: bool = False

    # Indicador de cálculo en curso (separado de saving para UX)
    calculando: bool = False

    # Dispersión
    layouts_dispersion: list[dict] = []
    generando_layouts: bool = False

    # =========================================================================
    # COMPUTED VARS — Período
    # =========================================================================

    @rx.var
    def periodo_estatus(self) -> str:
        return self.periodo_actual.get('estatus', '')

    @rx.var
    def periodo_nombre(self) -> str:
        return self.periodo_actual.get('nombre', 'Período')

    @rx.var
    def periodo_es_enviado(self) -> bool:
        return self.periodo_actual.get('estatus') == 'ENVIADO_A_CONTABILIDAD'

    @rx.var
    def periodo_en_proceso(self) -> bool:
        return self.periodo_actual.get('estatus') == 'EN_PROCESO_CONTABILIDAD'

    @rx.var
    def periodo_calculado(self) -> bool:
        return self.periodo_actual.get('estatus') == 'CALCULADO'

    @rx.var
    def periodo_cerrado(self) -> bool:
        return self.periodo_actual.get('estatus') == 'CERRADO'

    @rx.var
    def puede_agregar_bonos(self) -> bool:
        return self.periodo_actual.get('estatus') == 'EN_PROCESO_CONTABILIDAD'

    @rx.var
    def puede_calcular(self) -> bool:
        return (
            self.periodo_actual.get('estatus') == 'EN_PROCESO_CONTABILIDAD'
            and len(self.empleados_periodo) > 0
        )

    @rx.var
    def puede_cerrar(self) -> bool:
        return self.periodo_actual.get('estatus') == 'CALCULADO'

    @rx.var
    def puede_devolver(self) -> bool:
        return self.periodo_actual.get('estatus') in (
            'EN_PROCESO_CONTABILIDAD', 'ENVIADO_A_CONTABILIDAD'
        )

    @rx.var
    def tiene_empleados(self) -> bool:
        return len(self.empleados_periodo) > 0

    @rx.var
    def tiene_periodos_pendientes(self) -> bool:
        return len(self.periodos_pendientes) > 0

    # =========================================================================
    # COMPUTED VARS — Totales del período
    # =========================================================================

    @rx.var
    def total_percepciones_periodo(self) -> float:
        return float(self.periodo_actual.get('total_percepciones') or 0)

    @rx.var
    def total_deducciones_periodo(self) -> float:
        return float(self.periodo_actual.get('total_deducciones') or 0)

    @rx.var
    def total_neto_periodo(self) -> float:
        return float(self.periodo_actual.get('total_neto') or 0)

    @rx.var
    def total_empleados_periodo(self) -> int:
        return int(
            self.periodo_actual.get('total_empleados')
            or len(self.empleados_periodo)
        )

    # =========================================================================
    # COMPUTED VARS — Detalle empleado
    # =========================================================================

    @rx.var
    def detalle_nombre_empleado(self) -> str:
        return self.empleado_detalle.get('nombre_empleado', '')

    @rx.var
    def detalle_clave_empleado(self) -> str:
        return self.empleado_detalle.get('clave_empleado', '')

    @rx.var
    def detalle_total_percepciones(self) -> float:
        return float(self.empleado_detalle.get('total_percepciones') or 0)

    @rx.var
    def detalle_total_deducciones(self) -> float:
        return float(self.empleado_detalle.get('total_deducciones') or 0)

    @rx.var
    def detalle_total_otros_pagos(self) -> float:
        return float(self.empleado_detalle.get('total_otros_pagos') or 0)

    @rx.var
    def detalle_total_neto(self) -> float:
        return float(self.empleado_detalle.get('total_neto') or 0)

    # Movimientos filtrados por tipo para la página de detalle
    @rx.var
    def movimientos_percepciones(self) -> list[dict]:
        return [m for m in self.movimientos_detalle if m.get('tipo') == 'PERCEPCION']

    @rx.var
    def movimientos_deducciones(self) -> list[dict]:
        return [m for m in self.movimientos_detalle if m.get('tipo') == 'DEDUCCION']

    @rx.var
    def movimientos_otros_pagos(self) -> list[dict]:
        return [m for m in self.movimientos_detalle if m.get('tipo') == 'OTRO_PAGO']

    # =========================================================================
    # COMPUTED VARS — Form / UI
    # =========================================================================

    @rx.var
    def nombre_empleado_bono(self) -> str:
        return self.empleado_bono.get('nombre_empleado', '')

    @rx.var
    def opciones_conceptos_contabilidad(self) -> list[dict]:
        return CONCEPTOS_CONTABILIDAD

    # =========================================================================
    # SETTERS EXPLÍCITOS
    # =========================================================================

    def set_form_concepto_bono_clave(self, v: str):
        self.form_concepto_bono_clave = v

    def set_form_monto_bono(self, v: str):
        self.form_monto_bono = v
        self.error_monto_bono = ""

    def set_form_notas_bono(self, v: str):
        self.form_notas_bono = v

    # =========================================================================
    # MONTAJE
    # =========================================================================

    async def on_mount_contabilidad(self):
        """Carga períodos en estatus relevantes para Contabilidad."""
        if self.requiere_login and not self.esta_autenticado:
            yield rx.redirect("/login")
            return
        if not self.es_contabilidad:
            yield rx.redirect(self.nomina_no_access_path)
            return
        if not self.id_empresa_actual:
            yield self.mostrar_mensaje(
                "Selecciona una empresa para gestionar nóminas", "error"
            )
            return
        await self._cargar_periodos_pendientes()

    async def on_mount_calculo(self):
        """Monta la vista de cálculo. Requiere periodo_actual en estado."""
        if self.requiere_login and not self.esta_autenticado:
            yield rx.redirect("/login")
            return
        if not self.es_contabilidad:
            yield rx.redirect(self.nomina_no_access_path)
            return
        if not self.periodo_actual:
            yield rx.redirect(self.nomina_base_path)
            return
        periodo_id = self.periodo_actual.get('id')
        if periodo_id:
            # Refrescar período y empleados
            self.periodo_actual = await nomina_periodo_service.obtener_periodo(periodo_id)
            await self._cargar_empleados(periodo_id)
            await self._cargar_layouts_existentes(periodo_id)

    async def on_mount_detalle(self):
        """Monta el detalle de un empleado. Requiere empleado_detalle en estado."""
        if self.requiere_login and not self.esta_autenticado:
            yield rx.redirect("/login")
            return
        if not self.es_contabilidad:
            yield rx.redirect(self.nomina_no_access_path)
            return
        if not self.empleado_detalle:
            yield rx.redirect(self.nomina_calculo_path)
            return
        nomina_id = self.empleado_detalle.get('id')
        if nomina_id:
            await self._cargar_movimientos(nomina_id)

    # =========================================================================
    # CARGA DE DATOS
    # =========================================================================

    async def _cargar_periodos_pendientes(self):
        self.loading = True
        try:
            supabase = db_manager.get_client()
            result = (
                supabase.table('periodos_nomina')
                .select('*')
                .eq('empresa_id', self.id_empresa_actual)
                .in_('estatus', list(_ESTATUS_CONTABILIDAD))
                .order('fecha_inicio', desc=True)
                .execute()
            )
            self.periodos_pendientes = result.data or []
        except Exception as e:
            self.manejar_error(e, "cargar períodos pendientes")
        finally:
            self.loading = False

    async def _cargar_empleados(self, periodo_id: int):
        self.loading = True
        try:
            self.empleados_periodo = await nomina_periodo_service.obtener_empleados_periodo(
                periodo_id
            )
        except Exception as e:
            self.manejar_error(e, "cargar empleados")
        finally:
            self.loading = False

    async def _cargar_movimientos(self, nomina_empleado_id: int):
        self.loading = True
        try:
            self.movimientos_detalle = await nomina_calculo_service.obtener_desglose(
                nomina_empleado_id
            )
        except Exception as e:
            self.manejar_error(e, "cargar desglose")
        finally:
            self.loading = False

    # =========================================================================
    # NAVEGACIÓN — Abrir período en vista Contabilidad
    # =========================================================================

    async def abrir_periodo_calculo(self, periodo: dict):
        """Navega a la vista de cálculo del período seleccionado."""
        self.periodo_actual = periodo
        await self._cargar_empleados(periodo['id'])
        yield rx.redirect(self.nomina_calculo_path)

    # =========================================================================
    # WORKFLOW — Recibir / Devolver
    # =========================================================================

    async def confirmar_recibir(self):
        """ENVIADO_A_CONTABILIDAD → EN_PROCESO_CONTABILIDAD."""
        periodo_id = self.periodo_actual.get('id')
        if not periodo_id:
            return
        self.saving = True
        try:
            resultado = await nomina_periodo_service.transicionar_estatus(
                periodo_id,
                'EN_PROCESO_CONTABILIDAD',
                str(self.usuario_actual.get('id', '') or ''),
            )
            self.periodo_actual = resultado
            await self._cargar_empleados(periodo_id)
            yield self.mostrar_mensaje(
                "Período recibido. Puedes agregar bonos y ejecutar el cálculo.", "success"
            )
        except Exception as e:
            self.manejar_error(e, "recibir período")
        finally:
            self.saving = False

    def abrir_dialog_devolver(self):
        self.mostrar_dialog_devolver = True

    def cerrar_dialog_devolver(self):
        self.mostrar_dialog_devolver = False

    async def devolver_a_rrhh(self):
        """Devuelve al estatus anterior para que RRHH corrija."""
        periodo_id = self.periodo_actual.get('id')
        if not periodo_id:
            return
        estatus_actual = self.periodo_actual.get('estatus')
        # EN_PROCESO → ENVIADO_A_CONTABILIDAD
        # ENVIADO_A_CONTABILIDAD → EN_PREPARACION_RRHH
        nuevo = (
            'ENVIADO_A_CONTABILIDAD'
            if estatus_actual == 'EN_PROCESO_CONTABILIDAD'
            else 'EN_PREPARACION_RRHH'
        )
        self.saving = True
        try:
            resultado = await nomina_periodo_service.transicionar_estatus(
                periodo_id,
                nuevo,
                str(self.usuario_actual.get('id', '') or ''),
            )
            self.periodo_actual = resultado
            self.mostrar_dialog_devolver = False
            yield self.mostrar_mensaje("Período devuelto a RRHH para correcciones.", "success")
            yield rx.redirect(self.nomina_base_path)
        except Exception as e:
            self.manejar_error(e, "devolver a RRHH")
        finally:
            self.saving = False

    # =========================================================================
    # WORKFLOW — Cálculo
    # =========================================================================

    def abrir_dialog_ejecutar(self):
        self.mostrar_dialog_ejecutar = True

    def cerrar_dialog_ejecutar(self):
        self.mostrar_dialog_ejecutar = False

    async def ejecutar_calculo(self):
        """Ejecuta el cálculo fiscal completo del período."""
        periodo_id = self.periodo_actual.get('id')
        if not periodo_id:
            return
        self.mostrar_dialog_ejecutar = False
        self.calculando = True
        try:
            resumen = await nomina_calculo_service.calcular_periodo(periodo_id)
            # Refrescar período y empleados con totales actualizados
            self.periodo_actual = await nomina_periodo_service.obtener_periodo(periodo_id)
            await self._cargar_empleados(periodo_id)
            errores = len(resumen.get('errores', []))
            if errores:
                yield self.mostrar_mensaje(
                    f"Cálculo completado con {errores} error(es). Revisa los detalles.", "warning"
                )
            else:
                yield self.mostrar_mensaje(
                    f"Cálculo exitoso: {resumen['empleados_calculados']} empleados procesados.",
                    "success",
                )
        except Exception as e:
            self.manejar_error(e, "ejecutar cálculo")
        finally:
            self.calculando = False

    # =========================================================================
    # WORKFLOW — Cierre
    # =========================================================================

    def abrir_dialog_cerrar(self):
        self.mostrar_dialog_cerrar = True

    def cerrar_dialog_cerrar(self):
        self.mostrar_dialog_cerrar = False

    async def cerrar_periodo(self):
        """CALCULADO → CERRADO. Acción irreversible."""
        periodo_id = self.periodo_actual.get('id')
        if not periodo_id:
            return
        self.saving = True
        try:
            resultado = await nomina_periodo_service.transicionar_estatus(
                periodo_id,
                'CERRADO',
                str(self.usuario_actual.get('id', '') or ''),
            )
            self.periodo_actual = resultado
            self.mostrar_dialog_cerrar = False
            yield self.mostrar_mensaje(
                "Período cerrado. Los datos son de solo lectura.", "success"
            )
        except Exception as e:
            self.manejar_error(e, "cerrar período")
        finally:
            self.saving = False

    # =========================================================================
    # BONOS (origen = CONTABILIDAD)
    # =========================================================================

    async def abrir_modal_bono(self, empleado: dict):
        self.empleado_bono = empleado
        self.form_concepto_bono_clave = ""
        self.form_monto_bono = ""
        self.form_notas_bono = ""
        self.error_monto_bono = ""
        self.mostrar_modal_bono = True

    def cerrar_modal_bono(self):
        self.mostrar_modal_bono = False
        self.empleado_bono = {}

    async def guardar_bono(self):
        if not self.form_concepto_bono_clave:
            yield self.mostrar_mensaje("Selecciona el tipo de bono", "error")
            return
        if not self.form_monto_bono.strip():
            self.error_monto_bono = "El monto es obligatorio"
            return
        try:
            monto = Decimal(self.form_monto_bono.replace(',', '').strip())
            if monto <= 0:
                self.error_monto_bono = "El monto debe ser mayor a 0"
                return
        except Exception:
            self.error_monto_bono = "Monto inválido (ej: 2500.00)"
            return

        nomina_empleado_id = self.empleado_bono.get('id')
        if not nomina_empleado_id:
            return

        self.saving = True
        try:
            concepto_id = await self._obtener_concepto_id(self.form_concepto_bono_clave)
            if not concepto_id:
                yield self.mostrar_mensaje("Concepto no encontrado en catálogo", "error")
                return

            supabase = db_manager.get_client()
            supabase.table('nomina_movimientos').insert({
                'nomina_empleado_id': nomina_empleado_id,
                'concepto_id': concepto_id,
                'tipo': 'PERCEPCION',
                'origen': 'CONTABILIDAD',
                'monto': float(monto),
                'monto_gravable': float(monto),
                'monto_exento': 0.0,
                'es_automatico': False,
                'notas': self.form_notas_bono.strip() or None,
            }).execute()

            self.form_concepto_bono_clave = ""
            self.form_monto_bono = ""
            self.form_notas_bono = ""
            self.mostrar_modal_bono = False
            yield self.mostrar_mensaje("Bono aplicado correctamente", "success")
        except Exception as e:
            self.manejar_error(e, "guardar bono")
        finally:
            self.saving = False

    # =========================================================================
    # DETALLE EMPLEADO
    # =========================================================================

    async def ver_detalle_empleado(self, empleado: dict):
        """Navega al detalle de movimientos del empleado."""
        self.empleado_detalle = empleado
        nomina_id = empleado.get('id')
        if nomina_id:
            await self._cargar_movimientos(nomina_id)
        yield rx.redirect(self.nomina_detalle_path)

    async def recalcular_empleado(self):
        """Recalcula la nómina del empleado individual (SISTEMA solamente)."""
        nomina_id = self.empleado_detalle.get('id')
        if not nomina_id:
            return
        self.saving = True
        try:
            await nomina_calculo_service.recalcular_empleado(nomina_id)
            await self._cargar_movimientos(nomina_id)
            # Actualizar fila en la tabla del período
            periodo_id = self.periodo_actual.get('id')
            if periodo_id:
                await self._cargar_empleados(periodo_id)
            yield self.mostrar_mensaje("Empleado recalculado correctamente", "success")
        except Exception as e:
            self.manejar_error(e, "recalcular empleado")
        finally:
            self.saving = False

    # =========================================================================
    # HELPERS
    # =========================================================================

    # =========================================================================
    # DISPERSIÓN BANCARIA
    # =========================================================================

    @rx.var
    def puede_dispersar(self) -> bool:
        return self.periodo_actual.get('estatus') in ('CALCULADO', 'CERRADO')

    @rx.var
    def tiene_layouts(self) -> bool:
        return len(self.layouts_dispersion) > 0

    async def generar_layouts_dispersion(self):
        """Genera los archivos bancarios para el período actual."""
        periodo_id = self.periodo_actual.get('id')
        if not periodo_id:
            return
        self.generando_layouts = True
        try:
            actor = str(self.usuario_actual.get('id', '') or '')
            resultados = await dispersion_service.generar_layouts(
                periodo_id,
                generado_por=actor or None,
            )
            self.layouts_dispersion = resultados
            exitosos = sum(1 for r in resultados if r.get('url_descarga'))
            if exitosos:
                yield self.mostrar_mensaje(
                    f"{exitosos} layout(s) generado(s) correctamente.", "success"
                )
            else:
                yield self.mostrar_mensaje(
                    "No se generaron layouts. Verifica la configuración de bancos.", "warning"
                )
        except Exception as e:
            self.manejar_error(e, "generar layouts de dispersión")
        finally:
            self.generando_layouts = False

    async def _cargar_layouts_existentes(self, periodo_id: int):
        """Carga layouts ya generados para el período."""
        try:
            self.layouts_dispersion = await dispersion_service.obtener_layouts_periodo(
                periodo_id
            )
        except Exception as e:
            logger.warning(f"No se pudieron cargar layouts del período {periodo_id}: {e}")

    async def descargar_layout(self, storage_path: str):
        """Abre la URL de descarga del layout en una nueva pestaña."""
        url = await dispersion_service.generar_url_descarga(storage_path)
        if url:
            yield rx.redirect(url, external=True)
        else:
            yield self.mostrar_mensaje("No se pudo generar la URL de descarga.", "error")

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
