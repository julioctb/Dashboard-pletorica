"""Tests para la página /portal/plazas."""

import asyncio
from types import SimpleNamespace

from app.presentation.pages.portal.plazas import state as plazas_state_module
from app.presentation.pages.portal.plazas.state import FILTRO_TODOS, PlazasListadoState


async def _drain(async_gen) -> list:
    eventos = []
    async for item in async_gen:
        eventos.append(item)
    return eventos


class _DummyPlazasListadoState:
    cargar_contratos = PlazasListadoState.cargar_contratos
    seleccionar_contrato = PlazasListadoState.seleccionar_contrato
    ir_a_plazas_contrato = PlazasListadoState.ir_a_plazas_contrato
    _cargar_contexto_fiscal_empresa = PlazasListadoState._cargar_contexto_fiscal_empresa
    _cargar_tipos_servicio_catalogo_rapido = (
        PlazasListadoState._cargar_tipos_servicio_catalogo_rapido
    )
    _normalizar_selector_contrato = staticmethod(
        PlazasListadoState._normalizar_selector_contrato
    )
    _resolver_color_cobertura = staticmethod(PlazasListadoState._resolver_color_cobertura)
    _resolver_scheme_cobertura = staticmethod(PlazasListadoState._resolver_scheme_cobertura)
    _resolver_color_cobertura_metrica = classmethod(
        lambda cls, porcentaje: PlazasListadoState._resolver_color_cobertura_metrica(
            porcentaje
        )
    )
    _conteos_plazas_por_categoria = staticmethod(
        PlazasListadoState._conteos_plazas_por_categoria
    )
    _serializar_contrato_resumen = PlazasListadoState._serializar_contrato_resumen
    _serializar_filas_contrato = PlazasListadoState._serializar_filas_contrato
    _sumar_costos = PlazasListadoState._sumar_costos
    _parse_decimal_seguro = staticmethod(PlazasListadoState._parse_decimal_seguro)
    _pluralizar = staticmethod(PlazasListadoState._pluralizar)
    _formatear_moneda_operativa = staticmethod(
        PlazasListadoState._formatear_moneda_operativa
    )
    _coerce_tipo_sueldo = staticmethod(PlazasListadoState._coerce_tipo_sueldo)
    _fecha_calculo_fiscal = PlazasListadoState._fecha_calculo_fiscal
    _contexto_fiscal_actual = PlazasListadoState._contexto_fiscal_actual
    _salario_minimo_diario_decimal = PlazasListadoState._salario_minimo_diario_decimal
    _salario_minimo_mensual_decimal = PlazasListadoState._salario_minimo_mensual_decimal
    _prima_riesgo_decimal = PlazasListadoState._prima_riesgo_decimal
    _factor_integracion_actual = PlazasListadoState._factor_integracion_actual
    _calcular_snapshot_desde_bruto = PlazasListadoState._calcular_snapshot_desde_bruto
    _resolver_bruto_desde_neto = PlazasListadoState._resolver_bruto_desde_neto
    _calcular_snapshot_categoria = PlazasListadoState._calcular_snapshot_categoria
    DEFAULT_PRIMA_RIESGO = PlazasListadoState.DEFAULT_PRIMA_RIESGO
    DEFAULT_PRIMA_RIESGO_LABEL = PlazasListadoState.DEFAULT_PRIMA_RIESGO_LABEL
    DIAS_MES_FISCAL = PlazasListadoState.DIAS_MES_FISCAL

    def __init__(self):
        self.id_empresa_actual = 19
        self.nombre_empresa_actual = "Mantiser"
        self.mostrar_seccion_plazas_portal = True
        self._is_loading = False
        self._contratos_resumen = []
        self._filas_categoria = []
        self.contrato_seleccionado = FILTRO_TODOS
        self.empresa_prima_riesgo = ""
        self.empresa_tiene_nivel_riesgo_configurado = False
        self.empresa_nombre_fiscal = ""
        self.tipos_servicio_catalogo_rapido = []
        self.saving = False

    async def on_mount_portal(self):
        return None

    def _computed(self, nombre: str):
        return PlazasListadoState.__dict__[nombre].fget(self)

    @property
    def contratos_visibles(self):
        return self._computed("contratos_visibles")

    @property
    def filas_categoria_visibles(self):
        return self._computed("filas_categoria_visibles")

    @property
    def tiene_contratos_activos(self):
        return self._computed("tiene_contratos_activos")

    @property
    def tiene_filas_categoria(self):
        return self._computed("tiene_filas_categoria")

    @property
    def plazas_configuradas(self):
        return self._computed("plazas_configuradas")

    @property
    def plazas_ocupadas(self):
        return self._computed("plazas_ocupadas")

    @property
    def cobertura_pct(self):
        return self._computed("cobertura_pct")

    @property
    def cobertura_texto(self):
        return self._computed("cobertura_texto")

    @property
    def cobertura_color_metrica(self):
        return self._computed("cobertura_color_metrica")

    @property
    def cobertura_color_chip_global(self):
        return self._computed("cobertura_color_chip_global")

    @property
    def cobertura_width(self):
        return self._computed("cobertura_width")

    @property
    def presupuesto_mensual(self):
        return self._computed("presupuesto_mensual")

    @property
    def costo_real_mensual(self):
        return self._computed("costo_real_mensual")

    @property
    def presupuesto_mensual_fmt(self):
        return self._computed("presupuesto_mensual_fmt")

    @property
    def costo_real_mensual_fmt(self):
        return self._computed("costo_real_mensual_fmt")

    @property
    def descripcion_metrica_plazas(self):
        return self._computed("descripcion_metrica_plazas")

    @property
    def plazas_sin_sede(self):
        return self._computed("plazas_sin_sede")

    @property
    def categorias_sin_sede(self):
        return self._computed("categorias_sin_sede")

    @property
    def chips_contrato(self):
        return self._computed("chips_contrato")

    @property
    def mostrar_callout_sin_sede(self):
        return self._computed("mostrar_callout_sin_sede")

    @property
    def mensaje_callout_sin_sede(self):
        return self._computed("mensaje_callout_sin_sede")

    @property
    def puede_editar_configuracion(self):
        return self._computed("puede_editar_configuracion")

    @property
    def ruta_editar_configuracion(self):
        return self._computed("ruta_editar_configuracion")

    @property
    def caption_tabla(self):
        return self._computed("caption_tabla")


class _FakePlazaService:
    async def obtener_resumen_contratos_con_plazas(self, empresa_id: int, solo_activos: bool = False):
        assert empresa_id == 19
        assert solo_activos is True
        return [
            {
                "contrato_id": 10,
                "contrato_codigo": "man-jar-26002",
                "contrato_estatus": "ACTIVO",
                "tipo_servicio_nombre": "jardineria",
                "total_plazas": 5,
                "plazas_ocupadas": 4,
                "plazas_vacantes": 1,
                "plazas_suspendidas": 0,
            },
            {
                "contrato_id": 11,
                "contrato_codigo": "man-lim-26001",
                "contrato_estatus": "ACTIVO",
                "tipo_servicio_nombre": "limpieza",
                "total_plazas": 2,
                "plazas_ocupadas": 0,
                "plazas_vacantes": 2,
                "plazas_suspendidas": 0,
            },
        ]

    async def obtener_resumen_de_contrato(self, contrato_id: int):
        if contrato_id == 10:
            return [
                SimpleNamespace(categoria_puesto_id=101, estatus="OCUPADA", sede_id=7),
                SimpleNamespace(categoria_puesto_id=101, estatus="OCUPADA", sede_id=7),
                SimpleNamespace(categoria_puesto_id=101, estatus="VACANTE", sede_id=None),
                SimpleNamespace(categoria_puesto_id=102, estatus="OCUPADA", sede_id=7),
                SimpleNamespace(categoria_puesto_id=102, estatus="OCUPADA", sede_id=7),
            ]
        return [
            SimpleNamespace(categoria_puesto_id=201, estatus="VACANTE", sede_id=3),
            SimpleNamespace(categoria_puesto_id=201, estatus="VACANTE", sede_id=3),
        ]


class _FakeContratoCategoriaService:
    async def obtener_resumen_de_contrato(self, contrato_id: int):
        if contrato_id == 10:
            return [
                SimpleNamespace(
                    id=1001,
                    categoria_puesto_id=101,
                    nombre="jardinero b",
                    categoria_nombre="jardinero b",
                    cantidad_minima=2,
                    cantidad_maxima=3,
                    sueldo_base="12000",
                    tipo_sueldo="BRUTO",
                    costo_unitario="12000",
                    costo_contractual=None,
                ),
                SimpleNamespace(
                    id=1002,
                    categoria_puesto_id=102,
                    nombre="podador",
                    categoria_nombre="podador",
                    cantidad_minima=1,
                    cantidad_maxima=2,
                    sueldo_base="12000",
                    tipo_sueldo="BRUTO",
                    costo_unitario="12000",
                    costo_contractual=None,
                ),
            ]
        return [
            SimpleNamespace(
                id=1003,
                categoria_puesto_id=201,
                nombre="auxiliar de limpieza",
                categoria_nombre="auxiliar de limpieza",
                cantidad_minima=1,
                cantidad_maxima=2,
                sueldo_base="5000",
                tipo_sueldo="BRUTO",
                costo_unitario="5000",
                costo_contractual=None,
            ),
        ]


class _FakeEmpresaService:
    async def obtener_por_id(self, empresa_id: int):
        assert empresa_id == 19
        return SimpleNamespace(nombre_comercial="Mantiser", prima_riesgo=None)


def test_ir_a_plazas_contrato_redirige_con_codigo_canonico():
    dummy = _DummyPlazasListadoState()

    evento = dummy.ir_a_plazas_contrato.fn(dummy, "man-jar-26002")

    assert "/portal/contratos/MAN-JAR-26002/plazas" in str(evento)


def test_cargar_contratos_construye_metricas_y_filas(monkeypatch):
    dummy = _DummyPlazasListadoState()

    monkeypatch.setattr(plazas_state_module, "plaza_service", _FakePlazaService())
    monkeypatch.setattr(
        plazas_state_module,
        "contrato_categoria_service",
        _FakeContratoCategoriaService(),
    )
    monkeypatch.setattr(
        plazas_state_module,
        "empresa_service",
        _FakeEmpresaService(),
    )

    asyncio.run(_drain(PlazasListadoState.cargar_contratos.fn(dummy)))

    assert len(dummy._contratos_resumen) == 2
    assert dummy.plazas_configuradas == 7
    assert dummy.plazas_ocupadas == 4
    assert dummy.cobertura_pct == 57
    assert dummy.presupuesto_mensual_fmt == "$70,000.00"
    assert dummy.costo_real_mensual_fmt == "$48,000.00"

    assert len(dummy.chips_contrato) == 3
    assert dummy.chips_contrato[0]["selector_value"] == FILTRO_TODOS
    assert dummy.chips_contrato[1]["codigo_display"] == "MAN-JAR-26002"

    assert dummy.mostrar_callout_sin_sede is True
    assert dummy.mensaje_callout_sin_sede == (
        "1 plaza sin sede asignada en 1 categoría — requiere configuración"
    )

    assert len(dummy.filas_categoria_visibles) == 3

    jardinero = next(item for item in dummy.filas_categoria_visibles if item["id"] == 1001)
    limpieza = next(item for item in dummy.filas_categoria_visibles if item["id"] == 1003)

    assert jardinero["codigo_contrato"] == "MAN-JAR-26002"
    assert jardinero["nombre_categoria"] == "Jardinero B"
    assert jardinero["cobertura_texto"] == "2/3"
    assert jardinero["plazas_rango_texto"] == "Min 2 · Max 3"
    assert jardinero["mostrar_warning_salario_minimo"] is False

    assert limpieza["codigo_contrato"] == "MAN-LIM-26001"
    assert limpieza["mostrar_warning_salario_minimo"] is True
    assert dummy.caption_tabla == (
        "3 categorías en 2 contratos · 7 plazas totales · Presupuesto: $70,000.00/mes"
    )


def test_seleccionar_contrato_filtra_y_habilita_edicion(monkeypatch):
    dummy = _DummyPlazasListadoState()

    monkeypatch.setattr(plazas_state_module, "plaza_service", _FakePlazaService())
    monkeypatch.setattr(
        plazas_state_module,
        "contrato_categoria_service",
        _FakeContratoCategoriaService(),
    )
    monkeypatch.setattr(
        plazas_state_module,
        "empresa_service",
        _FakeEmpresaService(),
    )

    asyncio.run(_drain(PlazasListadoState.cargar_contratos.fn(dummy)))

    PlazasListadoState.seleccionar_contrato.fn(dummy, "man-jar-26002")

    assert len(dummy.contratos_visibles) == 1
    assert len(dummy.filas_categoria_visibles) == 2
    assert dummy.puede_editar_configuracion is True
    assert dummy.ruta_editar_configuracion == "/portal/contratos/MAN-JAR-26002/plazas"

    jardinero = next(item for item in dummy.filas_categoria_visibles if item["id"] == 1001)
    assert jardinero["categoria_puesto_id"] == 101
    assert jardinero["cobertura_color_scheme"] in {"green", "amber", "red"}
    assert dummy.caption_tabla == (
        "2 categorías en 1 contrato · 5 plazas totales · Presupuesto: $60,000.00/mes"
    )
