"""Tests para la vista portal de plazas por contrato."""

import asyncio
from datetime import date
from decimal import Decimal

from app.presentation.pages.portal.contrato_plazas.state import ContratoPlazasState
from app.presentation.pages.portal.mis_empleados.state import MisEmpleadosState
from app.presentation.pages.portal.state.portal_state import PortalState
from app.presentation.theme import Colors
from app.domain.enums import TipoSueldo


class _DummyPortalPlazasNavState:
    mostrar_plazas = PortalState.mostrar_plazas
    mostrar_seccion_plazas_portal = PortalState.mostrar_seccion_plazas_portal
    ruta_plazas_principal = PortalState.ruta_plazas_principal
    redirigir_a_portal_plazas = PortalState.redirigir_a_portal_plazas

    def __init__(self):
        self.es_usuario_empresa_portal = True
        self.tiene_contratos_con_personal = True
        self.puede_gestionar_personal = True
        self.puede_registrar_personal = False
        self.es_empleado_portal = False
        self.primer_contrato_con_personal_id = 15

    async def on_mount_portal(self):
        return None


class _DummyContratoPlazasState:
    DEFAULT_PRIMA_RIESGO = ContratoPlazasState.DEFAULT_PRIMA_RIESGO
    DEFAULT_PRIMA_RIESGO_LABEL = ContratoPlazasState.DEFAULT_PRIMA_RIESGO_LABEL
    DIAS_MES_FISCAL = ContratoPlazasState.DIAS_MES_FISCAL
    _ruta_actual = ContratoPlazasState._ruta_actual
    _obtener_codigo_contrato_ruta = ContratoPlazasState._obtener_codigo_contrato_ruta
    _formatear_moneda_operativa = staticmethod(ContratoPlazasState._formatear_moneda_operativa)
    _costos_categoria_por_id = ContratoPlazasState._costos_categoria_por_id
    _descripcion_servicio_actual = ContratoPlazasState._descripcion_servicio_actual
    _vigencia_contrato_actual = ContratoPlazasState._vigencia_contrato_actual
    _decimal_a_texto_input = staticmethod(ContratoPlazasState._decimal_a_texto_input)
    _coerce_tipo_sueldo = staticmethod(ContratoPlazasState._coerce_tipo_sueldo)
    _resumen_plazas_actuales = ContratoPlazasState._resumen_plazas_actuales
    _construir_contrato_plaza_contexto = ContratoPlazasState._construir_contrato_plaza_contexto
    _tipo_sueldo_form_actual = ContratoPlazasState._tipo_sueldo_form_actual
    _toggle_sueldo_actual = ContratoPlazasState._toggle_sueldo_actual
    _contexto_fiscal_actual = ContratoPlazasState._contexto_fiscal_actual
    _salario_minimo_diario_decimal = ContratoPlazasState._salario_minimo_diario_decimal
    _salario_minimo_mensual_decimal = ContratoPlazasState._salario_minimo_mensual_decimal
    _prima_riesgo_decimal = ContratoPlazasState._prima_riesgo_decimal
    _factor_integracion_actual = ContratoPlazasState._factor_integracion_actual
    _calcular_snapshot_desde_bruto = ContratoPlazasState._calcular_snapshot_desde_bruto
    _resolver_bruto_desde_neto = ContratoPlazasState._resolver_bruto_desde_neto
    _calcular_snapshot_categoria = ContratoPlazasState._calcular_snapshot_categoria
    _buscar_categoria_detalle = ContratoPlazasState._buscar_categoria_detalle
    _parse_decimal_seguro = staticmethod(MisEmpleadosState._parse_decimal_seguro)
    _clave_contrato = staticmethod(MisEmpleadosState._clave_contrato)
    _pluralizar = staticmethod(MisEmpleadosState._pluralizar)
    _texto_resumen_cantidad = MisEmpleadosState._texto_resumen_cantidad
    _texto_resumen_plazas_sedes = MisEmpleadosState._texto_resumen_plazas_sedes
    _opciones_categoria_masiva_contrato = MisEmpleadosState._opciones_categoria_masiva_contrato

    def _fecha_calculo_fiscal(self):
        return date(2026, 4, 9)

    def __init__(self):
        self.router_data = {
            "pathname": "/portal/contratos/[codigo_contrato]/plazas",
            "asPath": "/portal/contratos/man-jar-26002/plazas",
        }
        self.contrato_actual_portal = {
            "id": 44,
            "codigo": "man-jar-26002",
            "estatus": "ACTIVO",
            "descripcion_objeto": "servicio de jardineria",
            "descripcion_objeto_display": "Servicio de jardinería",
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-12-31",
            "nombre_servicio_fmt": "Jardinería",
        }
        self.contrato_expandido_plaza_id = 44
        self.plazas_contrato_expandido = [
            {
                "id": 1,
                "numero_plaza": 1,
                "categoria_puesto_id": 3,
                "categoria_nombre": "jardinero b",
                "sede_id": 7,
                "sede_codigo": "cam-sal",
                "sede_nombre": "salud",
                "empleado_id": 90,
                "empleado_nombre": "alejandra moreno diaz",
                "empleado_uuid": "emp-1",
                "estatus": "OCUPADA",
                "estatus_plaza": "OCUPADA",
                "salario_mensual": "8000",
            },
            {
                "id": 2,
                "numero_plaza": 2,
                "categoria_puesto_id": 3,
                "categoria_nombre": "jardinero b",
                "sede_id": 7,
                "sede_codigo": "cam-sal",
                "sede_nombre": "salud",
                "empleado_id": 0,
                "empleado_nombre": "",
                "empleado_uuid": "",
                "estatus": "VACANTE",
                "estatus_plaza": "VACANTE",
                "salario_mensual": "8000",
            },
            {
                "id": 3,
                "numero_plaza": 3,
                "categoria_puesto_id": 4,
                "categoria_nombre": "podador",
                "sede_id": 0,
                "sede_codigo": "",
                "sede_nombre": "",
                "empleado_id": 0,
                "empleado_nombre": "",
                "empleado_uuid": "",
                "estatus": "VACANTE",
                "estatus_plaza": "SIN_SEDE",
                "salario_mensual": "7000",
            },
        ]
        self.plazas_pagina_actual = [
            {**self.plazas_contrato_expandido[0], "seleccionada": True},
            {**self.plazas_contrato_expandido[1], "seleccionada": False},
            {**self.plazas_contrato_expandido[2], "seleccionada": True},
        ]
        self.seleccion_plazas_por_contrato = {"44": [1, 3]}
        self.sedes_masivas_por_contrato = {"44": "7"}
        self.categorias_masivas_por_contrato = {"44": "3"}
        self.opciones_categorias_masivas_por_contrato = {
            "44": [{"value": "3", "label": "Jardinero B (1 disp.)"}]
        }
        self.toggle_vista_sueldo = TipoSueldo.BRUTO.value
        self.categoria_desglose_abierto_id = 0
        self.modal_categoria_abierto = False
        self.categoria_editando_id = 0
        self.form_nombre_categoria = ""
        self.form_tipo_sueldo = TipoSueldo.BRUTO.value
        self.form_sueldo_base = ""
        self.error_form_nombre_categoria = ""
        self.error_form_sueldo_base = ""
        self.empresa_prima_riesgo = ""
        self.empresa_tiene_nivel_riesgo_configurado = False
        self.empresa_nombre_fiscal = "Pletorica"

        snapshot_podador = self._calcular_snapshot_categoria(
            Decimal("6500"),
            TipoSueldo.NETO.value,
        )
        self.categorias_detalle_contrato = [
            {
                "id": 301,
                "categoria_puesto_id": 3,
                "categoria_clave": "JARB",
                "nombre": "Jardinero B",
                "categoria_nombre": "Jardinero B",
                "cantidad_minima": 1,
                "cantidad_maxima": 2,
                "costo_unitario": "8000",
                "sueldo_base": "8000",
                "tipo_sueldo": "BRUTO",
                "costo_unitario_fmt": "$8,000.00",
            },
            {
                "id": 302,
                "categoria_puesto_id": 4,
                "categoria_clave": "PODA",
                "nombre": "Podador",
                "categoria_nombre": "Podador",
                "cantidad_minima": 1,
                "cantidad_maxima": 1,
                "costo_unitario": str(snapshot_podador["sueldo_bruto"]),
                "sueldo_base": "6500",
                "tipo_sueldo": "NETO",
                "costo_unitario_fmt": self._formatear_moneda_operativa(
                    Decimal(str(snapshot_podador["sueldo_bruto"]))
                ),
            },
        ]
        self.contrato_plaza_activo = {}
        self.seleccion_todas_plazas_visibles_actual = False
        self.tab_activa = "plazas"
        self.plaza_busqueda = ""
        self.plaza_filtro_categoria = "all"
        self.plaza_filtro_estado = "all"
        self.pagina_plaza_actual = 1
        self.total_paginas_plaza_actual = 1
        self.plaza_total_filtradas = 3
        self.saving = False

    def _computed(self, nombre: str):
        return ContratoPlazasState.__dict__[nombre].fget(self)

    @property
    def contrato_plaza_contexto(self):
        return self._computed("contrato_plaza_contexto")

    @property
    def breadcrumb_items(self):
        return self._computed("breadcrumb_items")

    @property
    def codigo_contrato_actual(self):
        return self._computed("codigo_contrato_actual")

    @property
    def descripcion_contrato_actual(self):
        return self._computed("descripcion_contrato_actual")

    @property
    def subtitulo_contrato_actual(self):
        return self._computed("subtitulo_contrato_actual")

    @property
    def vigencia_contrato_actual(self):
        return self._computed("vigencia_contrato_actual")

    @property
    def estatus_contrato_actual(self):
        return self._computed("estatus_contrato_actual")

    @property
    def contrato_solo_consulta(self):
        return self._computed("contrato_solo_consulta")

    @property
    def total_plazas_contrato_actual(self):
        return self._computed("total_plazas_contrato_actual")

    @property
    def plazas_ocupadas_contrato_actual(self):
        return self._computed("plazas_ocupadas_contrato_actual")

    @property
    def plazas_vacantes_contrato_actual(self):
        return self._computed("plazas_vacantes_contrato_actual")

    @property
    def plazas_sin_sede_contrato_actual(self):
        return self._computed("plazas_sin_sede_contrato_actual")

    @property
    def cobertura_pct_contrato_actual(self):
        return self._computed("cobertura_pct_contrato_actual")

    @property
    def color_metrica_ocupadas(self):
        return self._computed("color_metrica_ocupadas")

    @property
    def color_metrica_vacantes(self):
        return self._computed("color_metrica_vacantes")

    @property
    def descripcion_metrica_ocupadas(self):
        return self._computed("descripcion_metrica_ocupadas")

    @property
    def descripcion_metrica_vacantes(self):
        return self._computed("descripcion_metrica_vacantes")

    @property
    def costo_presupuestado_contrato_actual(self):
        return self._computed("costo_presupuestado_contrato_actual")

    @property
    def costo_actual_contrato_actual(self):
        return self._computed("costo_actual_contrato_actual")

    @property
    def costo_presupuestado_contrato_actual_fmt(self):
        return self._computed("costo_presupuestado_contrato_actual_fmt")

    @property
    def costo_actual_contrato_actual_fmt(self):
        return self._computed("costo_actual_contrato_actual_fmt")

    @property
    def mostrar_costo_actual_contrato(self):
        return self._computed("mostrar_costo_actual_contrato")

    @property
    def descripcion_metrica_costo(self):
        return self._computed("descripcion_metrica_costo")

    @property
    def mensaje_callout_sin_sede(self):
        return self._computed("mensaje_callout_sin_sede")

    @property
    def categorias_tabla_resumen(self):
        return self._computed("categorias_tabla_resumen")

    @property
    def tiene_categorias_detalle_contrato(self):
        return self._computed("tiene_categorias_detalle_contrato")

    @property
    def total_categorias_detalle_contrato(self):
        return self._computed("total_categorias_detalle_contrato")

    @property
    def total_plazas_categorias_contrato(self):
        return self._computed("total_plazas_categorias_contrato")

    @property
    def costo_presupuestado_categorias_total(self):
        return self._computed("costo_presupuestado_categorias_total")

    @property
    def costo_presupuestado_categorias_total_fmt(self):
        return self._computed("costo_presupuestado_categorias_total_fmt")

    @property
    def caption_tabla_categorias(self):
        return self._computed("caption_tabla_categorias")

    @property
    def form_snapshot_categoria(self):
        return self._computed("form_snapshot_categoria")

    @property
    def form_bruto_preview(self):
        return self._computed("form_bruto_preview")

    @property
    def form_neto_preview(self):
        return self._computed("form_neto_preview")

    @property
    def form_bruto_preview_fmt(self):
        return self._computed("form_bruto_preview_fmt")

    @property
    def form_neto_preview_fmt(self):
        return self._computed("form_neto_preview_fmt")

    @property
    def form_es_menor_salario_minimo(self):
        return self._computed("form_es_menor_salario_minimo")

    @property
    def salario_minimo_diario_vigente(self):
        return self._computed("salario_minimo_diario_vigente")

    @property
    def salario_minimo_mensual_vigente(self):
        return self._computed("salario_minimo_mensual_vigente")

    @property
    def salario_minimo_diario_vigente_fmt(self):
        return self._computed("salario_minimo_diario_vigente_fmt")

    @property
    def salario_minimo_mensual_vigente_fmt(self):
        return self._computed("salario_minimo_mensual_vigente_fmt")

    @property
    def anio_actual(self):
        return self._computed("anio_actual")

    @property
    def mostrar_callout_nivel_riesgo(self):
        return self._computed("mostrar_callout_nivel_riesgo")

    @property
    def empresa_tiene_nivel_riesgo(self):
        return self._computed("empresa_tiene_nivel_riesgo")

    @property
    def prima_riesgo_activa_label(self):
        return self._computed("prima_riesgo_activa_label")

    @property
    def plazas_tabla_rows(self):
        return self._computed("plazas_tabla_rows")


def test_ruta_plazas_principal_usa_primer_contrato_con_personal():
    dummy = _DummyPortalPlazasNavState()

    assert dummy.ruta_plazas_principal.fget(dummy) == "/portal/plazas"


def test_redirigir_a_portal_plazas_envia_a_contrato_contextual():
    dummy = _DummyPortalPlazasNavState()

    evento = asyncio.run(dummy.redirigir_a_portal_plazas.fn(dummy))

    assert evento is not None


def test_obtener_codigo_contrato_ruta_toma_segmento_dinamico():
    dummy = _DummyContratoPlazasState()

    assert dummy._obtener_codigo_contrato_ruta() == "MAN-JAR-26002"


def test_contrato_plaza_contexto_construye_resumen_costos_y_subtitulo():
    dummy = _DummyContratoPlazasState()

    contexto = dummy.contrato_plaza_contexto
    costo_podador = dummy._parse_decimal_seguro(
        dummy.categorias_detalle_contrato[1]["costo_unitario"]
    )
    costo_presupuestado = dummy._formatear_moneda_operativa(
        Decimal("16000") + costo_podador
    )

    assert contexto["contrato_id"] == 44
    assert contexto["contrato_codigo"] == "MAN-JAR-26002"
    assert contexto["total_plazas"] == 3
    assert contexto["plazas_ocupadas"] == 1
    assert contexto["plazas_vacantes"] == 2
    assert contexto["plazas_sin_sede"] == 1
    assert contexto["seleccion_count"] == 2
    assert contexto["cobertura_pct"] == 33
    assert contexto["costo_presupuestado_fmt"] == costo_presupuestado
    assert contexto["costo_actual_fmt"] == "$8,000.00"
    assert contexto["subtitulo"] == "Servicio de Jardineria · Mar - Dic 2026"


def test_breadcrumb_y_metricas_respetan_contexto_total_contrato():
    dummy = _DummyContratoPlazasState()

    assert dummy.breadcrumb_items == [
        {"texto": "Plazas", "href": "/portal/plazas"},
        {"texto": "MAN-JAR-26002", "href": ""},
    ]
    assert dummy.descripcion_contrato_actual == "Servicio de Jardineria"
    assert dummy.vigencia_contrato_actual == "Mar - Dic 2026"
    assert dummy.total_plazas_contrato_actual == 3
    assert dummy.plazas_ocupadas_contrato_actual == 1
    assert dummy.plazas_vacantes_contrato_actual == 2
    assert dummy.plazas_sin_sede_contrato_actual == 1
    assert dummy.cobertura_pct_contrato_actual == 33
    assert dummy.color_metrica_ocupadas == Colors.WARNING
    assert dummy.color_metrica_vacantes == Colors.WARNING
    assert dummy.descripcion_metrica_ocupadas == "33% cobertura"
    assert dummy.descripcion_metrica_vacantes == "Requiere atención"
    assert dummy.descripcion_metrica_costo == "$8,000.00 actual"
    assert dummy.mensaje_callout_sin_sede == "1 plaza sin sede asignada — requiere configuración"


def test_filas_tabla_muestran_sueldo_sede_y_cta_contextual():
    dummy = _DummyContratoPlazasState()

    filas = dummy.plazas_tabla_rows

    assert filas[0]["categoria_nombre_ui"] == "Jardinero B"
    assert filas[0]["sueldo_categoria_fmt"] == "$8,000.00"
    assert filas[0]["sede_display_tabla"] == "CAM-SAL – Salud"
    assert filas[0]["empleado_href"] == "/portal/empleados/emp-1"
    assert filas[0]["cta_texto"] == "Acciones"
    assert filas[0]["mostrar_menu_acciones"] is True
    assert filas[1]["cta_texto"] == "Asignar"
    assert filas[2]["tiene_sede"] is False
    assert filas[2]["sede_display_tabla"] == ""
    assert filas[2]["cta_texto"] == "Asignar sede"


def test_tabla_categorias_incluye_plazas_configuradas_actuales():
    dummy = _DummyContratoPlazasState()

    categorias = dummy.categorias_tabla_resumen

    assert len(categorias) == 2
    assert categorias[0]["categoria_nombre_ui"] == "Jardinero B"
    assert categorias[0]["plazas_configuradas"] == 2
    assert categorias[0]["es_ancla"] is True
    assert categorias[0]["mostrar_calculado"] is False
    assert categorias[1]["categoria_nombre_ui"] == "Podador"
    assert categorias[1]["plazas_configuradas"] == 1
    assert categorias[1]["es_ancla"] is False
    assert categorias[1]["mostrar_calculado"] is True
    assert categorias[1]["costo_empresa_fmt"].startswith("$")
    assert dummy.caption_tabla_categorias.startswith("2 categorías · 3 plazas")


def test_tabla_categorias_cambia_ancla_al_toggle_neto():
    dummy = _DummyContratoPlazasState()
    dummy.toggle_vista_sueldo = TipoSueldo.NETO.value

    categorias = dummy.categorias_tabla_resumen

    assert categorias[0]["es_ancla"] is False
    assert categorias[0]["mostrar_calculado"] is True
    assert categorias[1]["es_ancla"] is True
    assert categorias[1]["mostrar_calculado"] is False


def test_preview_formulario_categoria_y_warning_salario_minimo():
    dummy = _DummyContratoPlazasState()
    dummy.form_tipo_sueldo = TipoSueldo.NETO.value
    dummy.form_sueldo_base = "7000"

    assert dummy.form_bruto_preview > dummy.form_neto_preview
    assert dummy.form_bruto_preview_fmt.startswith("$")
    assert dummy.form_es_menor_salario_minimo is True


def test_callout_riesgo_y_referencia_salario_minimo_usan_fallback_configurable():
    dummy = _DummyContratoPlazasState()

    assert dummy.mostrar_callout_nivel_riesgo is True
    assert dummy.empresa_tiene_nivel_riesgo is False
    assert dummy.prima_riesgo_activa_label == "2.59840%"
    assert dummy.salario_minimo_mensual_vigente_fmt.startswith("$")
    assert dummy.anio_actual == 2026


def test_contrato_vencido_pasa_a_modo_solo_consulta():
    dummy = _DummyContratoPlazasState()
    dummy.contrato_actual_portal["estatus"] = "VENCIDO"

    assert dummy.contrato_solo_consulta is True
    assert dummy.plazas_tabla_rows[0]["cta_texto"] == "Consultar"
