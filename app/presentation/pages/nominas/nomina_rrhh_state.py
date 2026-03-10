"""
Estado de Reflex para el módulo de Nóminas (vista RRHH).

Gestiona el ciclo de vida de períodos, poblado de empleados,
captura de descuentos y envío a Contabilidad.
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import reflex as rx

from app.core.ui_helpers import FILTRO_TODOS, rango_paginacion
from app.core.text_utils import formatear_fecha, formatear_fecha_hora, formatear_moneda
from app.core.validation import limpiar_moneda
from app.entities.empleado_descuento_recurrente import DESCUENTOS_RECURRENTES_POR_CLAVE
from app.presentation.pages.nominas.base_state import NominaBaseState
from app.services.configuracion_operativa_service import configuracion_operativa_service
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
    filtro_busqueda_empleados: str = ""
    filtro_sede_empleados_preparacion: str = FILTRO_TODOS
    pagina_empleados_preparacion: int = 1
    por_pagina_empleados_preparacion: int = 20

    # Filtro de períodos
    filtro_anio_periodos: str = str(date.today().year)
    filtro_contrato_nomina_id: str = ""
    contratos_filtro_nomina_opciones: list[dict] = []

    # =========================================================================
    # FORMULARIO — Período
    # =========================================================================
    periodos_disponibles_catalogo: list[dict] = []
    contratos_nomina_opciones: list[dict] = []
    form_contrato_nomina_id: str = ""
    form_periodo_key: str = ""
    form_fecha_generacion_preview: str = ""
    form_generado_por_preview: str = ""
    form_fecha_pago: str = ""
    error_contrato_nomina: str = ""
    error_periodo: str = ""
    error_fecha_pago: str = ""

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
    def puede_abrir_preparacion(self) -> bool:
        return self.puede_acceder_rrhh

    @rx.var
    def puede_abrir_calculo(self) -> bool:
        return self.puede_acceder_nomina_contabilidad

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
    def tiene_periodos_filtrados(self) -> bool:
        return len(self.periodos_filtrados) > 0

    @rx.var
    def tiene_empleados(self) -> bool:
        return len(self.empleados_periodo) > 0

    @rx.var
    def opciones_sede_empleados_preparacion(self) -> list[dict]:
        sedes = sorted(
            {
                str(empleado.get("sede_nombre") or "").strip() or "Sin sede"
                for empleado in self.empleados_periodo
            }
        )
        return [{"value": FILTRO_TODOS, "label": "Todas las sedes"}] + [
            {"value": sede, "label": sede}
            for sede in sedes
        ]

    @rx.var
    def empleados_periodo_filtrados(self) -> list[dict]:
        empleados = self.empleados_periodo
        if self.filtro_sede_empleados_preparacion not in ("", FILTRO_TODOS):
            empleados = [
                empleado
                for empleado in empleados
                if (str(empleado.get("sede_nombre") or "").strip() or "Sin sede")
                == self.filtro_sede_empleados_preparacion
            ]
        termino = (self.filtro_busqueda_empleados or "").strip().lower()
        if not termino:
            return empleados
        return [
            empleado
            for empleado in empleados
            if termino in str(empleado.get("nombre_empleado", "") or "").lower()
            or termino in str(empleado.get("sede_nombre", "") or "").lower()
        ]

    @rx.var
    def tiene_empleados_filtrados(self) -> bool:
        return len(self.empleados_periodo_filtrados) > 0

    @rx.var
    def total_empleados_filtrados_preparacion(self) -> int:
        return len(self.empleados_periodo_filtrados)

    @rx.var
    def total_paginas_empleados_preparacion(self) -> int:
        return self.calcular_total_paginas(
            self.total_empleados_filtrados_preparacion,
            self.por_pagina_empleados_preparacion,
        )

    @rx.var
    def pagina_empleados_preparacion_actual(self) -> int:
        if self.pagina_empleados_preparacion < 1:
            return 1
        if self.pagina_empleados_preparacion > self.total_paginas_empleados_preparacion:
            return self.total_paginas_empleados_preparacion
        return self.pagina_empleados_preparacion

    @rx.var
    def empleados_periodo_paginados(self) -> list[dict]:
        inicio = (
            (self.pagina_empleados_preparacion_actual - 1)
            * self.por_pagina_empleados_preparacion
        )
        fin = inicio + self.por_pagina_empleados_preparacion
        return self.empleados_periodo_filtrados[inicio:fin]

    @rx.var
    def paginas_visibles_empleados_preparacion(self) -> list[int]:
        return rango_paginacion(
            self.pagina_empleados_preparacion_actual,
            self.total_paginas_empleados_preparacion,
            visible=5,
        )

    @rx.var
    def total_caption_empleados_preparacion(self) -> str:
        total_filtrado = len(self.empleados_periodo_filtrados)
        if total_filtrado <= 0:
            return "Sin empleados registrados"
        inicio = (
            (self.pagina_empleados_preparacion_actual - 1)
            * self.por_pagina_empleados_preparacion
        ) + 1
        fin = min(
            inicio + len(self.empleados_periodo_paginados) - 1,
            total_filtrado,
        )
        return f"Mostrando {inicio}-{fin} de {total_filtrado} empleado(s)"

    @rx.var
    def periodos_filtrados(self) -> list[dict]:
        periodos = self.periodos
        if self.filtro_contrato_nomina_id:
            periodos = [
                p for p in periodos
                if str(p.get("contrato_id", "") or "") == self.filtro_contrato_nomina_id
            ]
        if self.filtro_anio_periodos:
            periodos = [
                p for p in periodos
                if str(p.get("fecha_inicio", "") or "").startswith(self.filtro_anio_periodos)
            ]

        termino = (self.filtro_busqueda or "").strip().lower()
        if not termino:
            return periodos

        return [
            p
            for p in periodos
            if termino in str(p.get("nombre", "") or "").lower()
            or termino in str(p.get("creado_por_nombre", "") or "").lower()
        ]

    @rx.var
    def nombre_empleado_seleccionado(self) -> str:
        return self.empleado_seleccionado.get('nombre_empleado', '')

    @rx.var
    def opciones_conceptos_rrhh(self) -> list[dict]:
        conceptos_aplicados = {
            str(item.get("concepto_clave") or "").strip().upper()
            for item in self.descuentos_empleado
            if item.get("concepto_clave")
        }
        return [
            option
            for option in CONCEPTOS_RRHH
            if option["value"] not in conceptos_aplicados
        ]

    @rx.var
    def tiene_opciones_conceptos_rrhh(self) -> bool:
        return len(self.opciones_conceptos_rrhh) > 0

    @rx.var
    def puede_anadir_descuento(self) -> bool:
        return bool(
            self.puede_editar_descuentos
            and self.tiene_opciones_conceptos_rrhh
            and str(self.form_concepto_clave or "").strip()
            and str(self.form_monto_descuento or "").strip()
        )

    @rx.var
    def tiene_periodos_disponibles(self) -> bool:
        return len(self.periodos_disponibles_catalogo) > 0

    @rx.var
    def tiene_contratos_nomina(self) -> bool:
        return len(self.contratos_nomina_opciones) > 0

    @rx.var
    def puede_generar_periodo(self) -> bool:
        return bool(
            self.puede_acceder_rrhh
            and self.tiene_contratos_nomina
            and self.tiene_periodos_disponibles
            and str(self.form_contrato_nomina_id or "").strip()
            and str(self.form_periodo_key or "").strip()
            and str(self.form_fecha_pago or "").strip()
        )

    @rx.var
    def fecha_generacion_preview_fmt(self) -> str:
        return formatear_fecha_hora(
            self.form_fecha_generacion_preview,
            valor_vacio="Sin dato",
        )

    @rx.var
    def anios_disponibles_periodos(self) -> list[dict]:
        anios = {str(date.today().year)}
        periodos = self.periodos
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

        return [
            {"value": anio, "label": anio}
            for anio in sorted(anios, reverse=True)
        ]

    # =========================================================================
    # SETTERS EXPLÍCITOS
    # =========================================================================

    def set_form_contrato_nomina_id(self, v: str):
        self.form_contrato_nomina_id = v or ""
        self.error_contrato_nomina = ""
        self.limpiar_mensajes()

    def _obtener_periodo_disponible_por_key(self, periodo_key: str) -> Optional[dict]:
        for item in self.periodos_disponibles_catalogo:
            if item.get("key") == periodo_key:
                return item
        return None

    def set_form_periodo_key(self, v: str):
        self.form_periodo_key = v
        self.error_periodo = ""
        self.limpiar_mensajes()

        periodo = self._obtener_periodo_disponible_por_key(v)
        if periodo and periodo.get("fecha_pago_sugerida"):
            self.form_fecha_pago = str(periodo["fecha_pago_sugerida"])

    def set_form_fecha_pago(self, v: str):
        self.form_fecha_pago = v
        self.error_fecha_pago = ""
        self.limpiar_mensajes()

    def set_form_concepto_clave(self, v: str):
        self.form_concepto_clave = v

    def set_form_monto_descuento(self, v: str):
        self.form_monto_descuento = formatear_moneda(v) if v else ""
        self.error_monto = ""

    def set_form_notas_descuento(self, v: str):
        self.form_notas_descuento = v

    def set_filtro_anio_periodos(self, v: str):
        self.filtro_anio_periodos = v or str(date.today().year)

    def set_filtro_contrato_nomina_id(self, v: str):
        self.filtro_contrato_nomina_id = v or ""

    def set_filtro_busqueda_empleados(self, value: str):
        self.filtro_busqueda_empleados = value or ""
        self.pagina_empleados_preparacion = 1

    def set_filtro_sede_empleados_preparacion(self, value: str):
        self.filtro_sede_empleados_preparacion = value or FILTRO_TODOS
        self.pagina_empleados_preparacion = 1

    def ir_a_pagina_empleados_preparacion(self, pagina: int):
        self.pagina_empleados_preparacion = int(pagina) if pagina else 1
        self._ajustar_pagina_empleados_preparacion()

    def pagina_anterior_empleados_preparacion(self):
        self.ir_a_pagina_empleados_preparacion(
            self.pagina_empleados_preparacion_actual - 1
        )

    def pagina_siguiente_empleados_preparacion(self):
        self.ir_a_pagina_empleados_preparacion(
            self.pagina_empleados_preparacion_actual + 1
        )

    def cambiar_filtro_anio_periodos(self, v: str):
        valor = v or str(date.today().year)
        self.filtro_anio_periodos = valor
        from app.presentation.pages.nominas.dashboard_state import NominaDashboardState
        return NominaDashboardState.cambiar_filtro_anio(valor)

    def cambiar_filtro_contrato_nomina(self, v: str):
        valor = v or ""
        self.filtro_contrato_nomina_id = valor
        from app.presentation.pages.nominas.dashboard_state import NominaDashboardState
        return NominaDashboardState.cambiar_filtro_contrato_nomina(valor)

    @staticmethod
    def _serializar_periodo_ui(periodo: dict) -> dict:
        """Agrega campos legibles de fecha sin alterar los valores ISO crudos."""
        if hasattr(periodo, "model_dump"):
            data = periodo.model_dump(mode="json")
        else:
            data = dict(periodo or {})
        try:
            total_neto = float(data.get("total_neto") or 0)
        except (TypeError, ValueError):
            total_neto = 0.0
        data["fecha_inicio_fmt"] = formatear_fecha(data.get("fecha_inicio"))
        data["fecha_fin_fmt"] = formatear_fecha(data.get("fecha_fin"))
        data["fecha_pago_fmt"] = formatear_fecha(
            data.get("fecha_pago"),
            valor_vacio="Sin dato",
        )
        data["fecha_creacion_fmt"] = formatear_fecha_hora(
            data.get("fecha_creacion"),
            valor_vacio="Sin dato",
        )
        data["creado_por_nombre_fmt"] = (
            str(data.get("creado_por_nombre") or "").strip() or "Sin dato"
        )
        data["total_neto_fmt"] = formatear_moneda(f"{total_neto:.2f}")
        return data

    def _set_periodo_actual(self, periodo: dict):
        """Mantiene `periodo_actual` con campos visibles derivados."""
        self.periodo_actual = self._serializar_periodo_ui(periodo)

    # =========================================================================
    # MONTAJE
    # =========================================================================

    async def on_mount_periodos(self):
        """Monta la lista de períodos. Verifica acceso."""
        resultado = await self.validar_contexto_nomina()
        if resultado:
            yield resultado
            return
        await self._cargar_contratos_filtro_nomina()
        await self._cargar_periodos()

    async def on_mount_preparacion(self):
        """Monta la vista de preparación. Requiere periodo_actual en estado."""
        resultado = await self.validar_contexto_nomina()
        if resultado:
            yield resultado
            return
        self.filtro_busqueda_empleados = ""
        self.filtro_sede_empleados_preparacion = FILTRO_TODOS
        self.pagina_empleados_preparacion = 1
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
            periodos = await nomina_periodo_service.listar_periodos(self.id_empresa_actual)
            self.periodos = [self._serializar_periodo_ui(periodo) for periodo in periodos]
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
            self._ajustar_pagina_empleados_preparacion()
        except Exception as e:
            self.manejar_error(e, "cargar empleados del período")
        finally:
            self.loading = False

    async def _cargar_periodos_disponibles(self):
        try:
            self.periodos_disponibles_catalogo = (
                await nomina_periodo_service.listar_periodos_disponibles(self.id_empresa_actual)
            )
        except Exception as e:
            self.periodos_disponibles_catalogo = []
            self.manejar_error(e, "cargar periodos disponibles")

    async def _cargar_contratos_filtro_nomina(self):
        try:
            self.contratos_filtro_nomina_opciones = (
                await configuracion_operativa_service.listar_contratos_nomina_disponibles(
                    self.id_empresa_actual
                )
            )
            opciones_validas = {
                str(opcion.get("value") or "")
                for opcion in self.contratos_filtro_nomina_opciones
            }
            if self.filtro_contrato_nomina_id in opciones_validas:
                return

            config = await configuracion_operativa_service.obtener_por_empresa(
                self.id_empresa_actual
            )
            contrato_configurado = str(getattr(config, "contrato_nomina_id", "") or "")
            if contrato_configurado and contrato_configurado in opciones_validas:
                self.filtro_contrato_nomina_id = contrato_configurado
            elif self.contratos_filtro_nomina_opciones:
                self.filtro_contrato_nomina_id = str(
                    self.contratos_filtro_nomina_opciones[0].get("value") or ""
                )
            else:
                self.filtro_contrato_nomina_id = ""
        except Exception as e:
            self.contratos_filtro_nomina_opciones = []
            self.filtro_contrato_nomina_id = ""
            self.manejar_error(e, "cargar contratos filtro de nomina")

    async def _cargar_contratos_nomina(self):
        try:
            self.contratos_nomina_opciones = (
                await configuracion_operativa_service.listar_contratos_nomina_disponibles(
                    self.id_empresa_actual
                )
            )
            config = await configuracion_operativa_service.obtener_por_empresa(
                self.id_empresa_actual
            )
            contrato_configurado = str(getattr(config, "contrato_nomina_id", "") or "")
            opciones_validas = {
                str(opcion.get("value") or "")
                for opcion in self.contratos_nomina_opciones
            }
            if contrato_configurado and contrato_configurado in opciones_validas:
                self.form_contrato_nomina_id = contrato_configurado
            elif len(self.contratos_nomina_opciones) == 1:
                self.form_contrato_nomina_id = str(
                    self.contratos_nomina_opciones[0].get("value") or ""
                )
            else:
                self.form_contrato_nomina_id = ""
        except Exception as e:
            self.contratos_nomina_opciones = []
            self.form_contrato_nomina_id = ""
            self.manejar_error(e, "cargar contratos de nomina")

    def _prellenar_datos_generacion_periodo(self):
        self.form_fecha_generacion_preview = datetime.now().isoformat()
        self.form_generado_por_preview = (
            str(self.usuario_actual.get("nombre_completo", "") or "").strip() or "Sin dato"
        )

    # =========================================================================
    # CRUD PERÍODOS
    # =========================================================================

    async def abrir_modal_periodo(self):
        self.limpiar_mensajes()
        self._limpiar_form_periodo()
        self._prellenar_datos_generacion_periodo()
        await self._cargar_contratos_nomina()
        await self._cargar_periodos_disponibles()
        if not self.contratos_nomina_opciones:
            self.mostrar_mensaje(
                "No hay contratos activos con personal disponibles para generar nómina.",
                "warning",
            )
        elif not self.periodos_disponibles_catalogo:
            self.mostrar_mensaje(
                "No hay periodos disponibles para generar en el mes actual.",
                "warning",
            )
        self.mostrar_modal_periodo = True

    def cerrar_modal_periodo(self):
        self.mostrar_modal_periodo = False
        self._limpiar_form_periodo()

    def set_mostrar_modal_periodo(self, value: bool):
        self.mostrar_modal_periodo = value
        if value:
            self.limpiar_mensajes()
            return
        self._limpiar_form_periodo()

    def _limpiar_form_periodo(self):
        self.periodos_disponibles_catalogo = []
        self.contratos_nomina_opciones = []
        self.form_contrato_nomina_id = ""
        self.form_periodo_key = ""
        self.form_fecha_generacion_preview = ""
        self.form_generado_por_preview = ""
        self.form_fecha_pago = ""
        self.error_contrato_nomina = ""
        self.error_periodo = ""
        self.error_fecha_pago = ""
        self.limpiar_mensajes()

    def _validar_form_periodo(self) -> Optional[tuple[str, date]]:
        """Valida el formulario de alta de periodo calculado."""
        self.error_contrato_nomina = ""
        self.error_periodo = ""
        self.error_fecha_pago = ""
        self.limpiar_mensajes()

        if not self.form_contrato_nomina_id:
            self.error_contrato_nomina = "Selecciona un contrato base"
            self.mostrar_mensaje("Selecciona un contrato base de nómina.", "error")
            return None

        if not self.form_periodo_key:
            self.error_periodo = "Selecciona un periodo"
            self.mostrar_mensaje("Selecciona un periodo disponible.", "error")
            return None

        periodo = self._obtener_periodo_disponible_por_key(self.form_periodo_key)
        if not periodo:
            self.error_periodo = "El periodo seleccionado ya no está disponible"
            self.mostrar_mensaje("Recarga el catálogo y selecciona otro periodo.", "error")
            return None

        try:
            fecha_inicio = date.fromisoformat(str(periodo["fecha_inicio"]))
        except ValueError:
            self.error_periodo = "El periodo seleccionado no tiene fechas válidas"
            self.mostrar_mensaje("El periodo seleccionado es inválido.", "error")
            return None

        if not self.form_fecha_pago:
            self.error_fecha_pago = "La fecha de pago es obligatoria"
            self.mostrar_mensaje("Completa la fecha de pago.", "error")
            return None

        try:
            fecha_pago = date.fromisoformat(self.form_fecha_pago)
        except ValueError:
            self.error_fecha_pago = "La fecha de pago no es válida"
            self.mostrar_mensaje("Corrige la fecha de pago.", "error")
            return None

        if fecha_pago < fecha_inicio:
            self.error_fecha_pago = "La fecha de pago no puede ser anterior al inicio"
            self.mostrar_mensaje("Corrige la fecha de pago.", "error")
            return None

        return self.form_periodo_key, fecha_pago

    async def crear_periodo(self):
        """Crea período, pobla empleados y refresca la lista."""
        valores = self._validar_form_periodo()
        if not valores:
            return

        periodo_key, fecha_pago = valores
        contrato_id = int(self.form_contrato_nomina_id)

        self.saving = True
        try:
            periodo = await nomina_periodo_service.crear_periodo_configurado(
                empresa_id=self.id_empresa_actual,
                periodo_key=periodo_key,
                contrato_id=contrato_id,
                fecha_pago_override=fecha_pago,
                usuario_id=str(self.usuario_actual.get('id', '') or '') or None,
                usuario_nombre=self.form_generado_por_preview or None,
            )
            total_empleados = int(periodo.get('total_empleados_poblados') or 0)

            self.mostrar_modal_periodo = False
            self._limpiar_form_periodo()
            await self._cargar_periodos()

            if total_empleados > 0:
                yield rx.toast.success(
                    f"Nómina creada con {total_empleados} empleado(s) cargado(s)",
                    position="top-center",
                )
            else:
                yield rx.toast.success(
                    "Nómina creada. No se encontraron empleados activos para poblar.",
                    position="top-center",
                )

        except Exception as e:
            self.manejar_error(e, "crear período")
        finally:
            self.saving = False

    async def abrir_periodo(self, periodo: dict):
        """Navega a la vista de preparación del período seleccionado."""
        self._set_periodo_actual(periodo)
        self.filtro_busqueda_empleados = ""
        self.filtro_sede_empleados_preparacion = FILTRO_TODOS
        self.pagina_empleados_preparacion = 1
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
            self._set_periodo_actual(resultado)
            await self._cargar_empleados(periodo_id)
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

    async def abrir_dialog_envio_periodo(self, periodo: dict):
        """Prepara el estado desde la tabla y abre confirmación de envío."""
        self._set_periodo_actual(periodo)
        await self._cargar_empleados(periodo['id'])
        if not self.empleados_periodo:
            yield self.mostrar_mensaje(
                "El período no tiene empleados. Puebla el período primero.", "error"
            )
            return
        self.mostrar_dialog_envio = True

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
            self._set_periodo_actual(resultado)
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
                .select(
                    'id, monto, notas, concepto_id, es_automatico, '
                    'conceptos_nomina(nombre, clave)'
                )
                .eq('nomina_empleado_id', nomina_empleado_id)
                .eq('origen', 'RRHH')
                .execute()
            )
            items = []
            for r in (result.data or []):
                concepto = r.pop('conceptos_nomina', {}) or {}
                clave = str(concepto.get('clave') or '').strip().upper()
                meta = DESCUENTOS_RECURRENTES_POR_CLAVE.get(clave, {})
                r['concepto_clave'] = clave
                r['concepto_nombre'] = concepto.get('nombre', '') or meta.get('nombre', '')
                r['badge'] = meta.get('badge', 'RRH')
                r['color_scheme'] = meta.get('color_scheme', 'orange')
                monto = Decimal(str(r.get('monto') or 0))
                r['monto_fmt'] = formatear_moneda(f"{monto:.2f}")
                r['origen_label'] = (
                    'Perfil empleado'
                    if r.get('es_automatico')
                    else 'RRHH manual'
                )
                items.append(r)
            items.sort(
                key=lambda item: (
                    int(
                        DESCUENTOS_RECURRENTES_POR_CLAVE.get(
                            item.get("concepto_clave", ""),
                            {},
                        ).get("orden", 999)
                    ),
                    0 if item.get("es_automatico") else 1,
                )
            )
            self.descuentos_empleado = items
            if self.form_concepto_clave and all(
                option["value"] != self.form_concepto_clave
                for option in self.opciones_conceptos_rrhh
            ):
                self.form_concepto_clave = ""
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
            monto = Decimal(limpiar_moneda(self.form_monto_descuento))
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
            movimiento_existente = (
                supabase.table('nomina_movimientos')
                .select('id')
                .eq('nomina_empleado_id', nomina_empleado_id)
                .eq('concepto_id', concepto_id)
                .eq('origen', 'RRHH')
                .limit(1)
                .execute()
            )
            payload = {
                'monto': float(monto),
                'notas': self.form_notas_descuento.strip() or None,
                'es_automatico': False,
            }
            if movimiento_existente.data:
                supabase.table('nomina_movimientos').update(payload).eq(
                    'id',
                    movimiento_existente.data[0]['id'],
                ).execute()
            else:
                supabase.table('nomina_movimientos').insert({
                    'nomina_empleado_id': nomina_empleado_id,
                    'concepto_id': concepto_id,
                    'tipo': 'DEDUCCION',
                    'origen': 'RRHH',
                    'monto_gravable': 0.0,
                    'monto_exento': 0.0,
                    **payload,
                }).execute()

            self.form_concepto_clave = ""
            self.form_monto_descuento = ""
            self.form_notas_descuento = ""
            await self._cargar_descuentos_empleado(nomina_empleado_id)
            periodo_id = self.periodo_actual.get('id')
            if periodo_id:
                await self._cargar_empleados(periodo_id)
            yield self.mostrar_mensaje("Descuento añadido", "success")

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
            periodo_id = self.periodo_actual.get('id')
            if periodo_id:
                await self._cargar_empleados(periodo_id)
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

    def _ajustar_pagina_empleados_preparacion(self) -> None:
        total_paginas = self.calcular_total_paginas(
            self.total_empleados_filtrados_preparacion,
            self.por_pagina_empleados_preparacion,
        )
        if self.pagina_empleados_preparacion < 1:
            self.pagina_empleados_preparacion = 1
        elif self.pagina_empleados_preparacion > total_paginas:
            self.pagina_empleados_preparacion = total_paginas
