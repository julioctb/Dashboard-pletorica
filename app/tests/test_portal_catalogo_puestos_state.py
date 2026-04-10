"""Tests para /portal/empresa/categorias."""

import asyncio
from decimal import Decimal
from types import SimpleNamespace

from app.presentation.pages.portal.empresa_categorias import state as state_module
from app.presentation.pages.portal.empresa_categorias.state import (
    EmpresaCategoriasState,
    FILTRO_TODOS,
)


async def _drain(async_gen) -> list:
    eventos = []
    async for item in async_gen:
        eventos.append(item)
    return eventos


class _DummyEmpresaCategoriasState:
    _fetch_catalogo = EmpresaCategoriasState._fetch_catalogo
    _serializar_tipo = staticmethod(EmpresaCategoriasState._serializar_tipo)
    _serializar_categoria = EmpresaCategoriasState._serializar_categoria
    _formatear_moneda_catalogo = staticmethod(EmpresaCategoriasState._formatear_moneda_catalogo)
    _parse_salario = staticmethod(EmpresaCategoriasState._parse_salario)
    _buscar_categoria_local = EmpresaCategoriasState._buscar_categoria_local
    _tipos_select_options = EmpresaCategoriasState._tipos_select_options
    _limpiar_form_categoria = EmpresaCategoriasState._limpiar_form_categoria
    _validar_form_categoria = EmpresaCategoriasState._validar_form_categoria
    guardar_categoria = EmpresaCategoriasState.__dict__["guardar_categoria"].fn
    crear_tipo_servicio = EmpresaCategoriasState.__dict__["crear_tipo_servicio"].fn
    editar_categoria_puesto = EmpresaCategoriasState.__dict__["editar_categoria_puesto"].fn

    def __init__(self):
        self.id_empresa_actual = 77
        self.loading = False
        self.saving = False
        self.es_admin_empresa = True
        self.puede_acceder_rrhh = True
        self.tipos_servicio_catalogo = []
        self.categorias_catalogo = []
        self.busqueda_categoria = ""
        self.filtro_estatus_categoria = FILTRO_TODOS
        self.creando_tipo_servicio = False
        self.form_nombre_tipo = ""
        self.error_form_nombre_tipo = ""
        self.modal_categoria_abierto = False
        self.categoria_editando_id = 0
        self.categoria_editando_contratos_count = 0
        self.categoria_editando_puede_desactivar = False
        self.form_tipo_servicio_id = ""
        self.form_nombre_categoria = ""
        self.form_clave_categoria = ""
        self.form_salario_base_categoria = ""
        self.error_form_tipo_servicio_id = ""
        self.error_form_nombre_categoria = ""
        self.error_form_clave_categoria = ""
        self.error_form_salario_base_categoria = ""

    def crear_toast(self, mensaje: str, tipo: str = "info", **_kwargs):
        return {"tipo": tipo, "mensaje": mensaje}

    def manejar_error_con_toast(self, error: Exception, contexto: str = ""):
        return {"tipo": "error", "mensaje": f"{contexto}:{error}"}

    def _computed(self, nombre: str):
        return EmpresaCategoriasState.__dict__[nombre].fget(self)

    @property
    def total_tipos(self):
        return self._computed("total_tipos")

    @property
    def total_activas(self):
        return self._computed("total_activas")

    @property
    def total_inactivas(self):
        return self._computed("total_inactivas")

    @property
    def tipos_servicio_select_options(self):
        return self._computed("tipos_servicio_select_options")

    @property
    def tiene_filtros_activos(self):
        return self._computed("tiene_filtros_activos")

    @property
    def tipos_servicio_con_categorias(self):
        return self._computed("tipos_servicio_con_categorias")

    @property
    def mostrar_empty_state_principal(self):
        return self._computed("mostrar_empty_state_principal")

    @property
    def mostrar_empty_state_filtros(self):
        return self._computed("mostrar_empty_state_filtros")

    @property
    def puede_guardar_categoria(self):
        return self._computed("puede_guardar_categoria")


class _FakeTipoServicioService:
    def __init__(self):
        self.creados: list[tuple[int, str]] = []

    async def obtener_portal_empresa(self, empresa_id: int, incluir_inactivas: bool = False):
        assert empresa_id == 77
        assert incluir_inactivas is False
        return [
            SimpleNamespace(id=1, nombre="jardineria"),
            SimpleNamespace(id=2, nombre="limpieza"),
        ]

    async def crear_portal_empresa(self, empresa_id: int, *, nombre: str, descripcion=None):
        self.creados.append((empresa_id, nombre))
        return SimpleNamespace(id=3, nombre=nombre)


class _FakeCategoriaPuestoService:
    def __init__(self):
        self.creadas: list[dict] = []
        self.actualizadas: list[dict] = []

    async def obtener_por_tipo_servicio(self, tipo_servicio_id: int, incluir_inactivas: bool = False):
        assert incluir_inactivas is True
        if tipo_servicio_id == 1:
            return [
                SimpleNamespace(
                    id=11,
                    tipo_servicio_id=1,
                    clave="JARA",
                    nombre="jardinero a",
                    salario_base_mensual=Decimal("10000"),
                    estatus="ACTIVO",
                ),
                SimpleNamespace(
                    id=12,
                    tipo_servicio_id=1,
                    clave="SUP",
                    nombre="supervisor",
                    salario_base_mensual=Decimal("12000"),
                    estatus="INACTIVO",
                ),
            ]
        return [
            SimpleNamespace(
                id=21,
                tipo_servicio_id=2,
                clave="LIMA",
                nombre="auxiliar de limpieza",
                salario_base_mensual=Decimal("8000"),
                estatus="ACTIVO",
            ),
        ]

    async def contar_contratos_por_categorias(self, categoria_ids: list[int]):
        assert sorted(categoria_ids) == [11, 12, 21]
        return {11: 2, 12: 0, 21: 1}

    async def contar_contratos_por_categoria(self, categoria_id: int):
        return {11: 2, 12: 0, 21: 1}.get(categoria_id, 0)

    async def puede_desactivar_portal_empresa(self, categoria_id: int, empresa_id: int):
        assert empresa_id == 77
        return categoria_id != 11

    async def crear_portal_empresa(self, empresa_id: int, **payload):
        self.creadas.append({"empresa_id": empresa_id, **payload})
        return SimpleNamespace(id=99, **payload)

    async def actualizar_portal_empresa(self, categoria_id: int, empresa_id: int, **payload):
        self.actualizadas.append(
            {"categoria_id": categoria_id, "empresa_id": empresa_id, **payload}
        )
        return SimpleNamespace(id=categoria_id, **payload)

    async def activar_portal_empresa(self, categoria_id: int, empresa_id: int):
        return SimpleNamespace(id=categoria_id, estatus="ACTIVO")


def test_fetch_catalogo_agrupa_y_serializa(monkeypatch):
    dummy = _DummyEmpresaCategoriasState()

    monkeypatch.setattr(state_module, "tipo_servicio_service", _FakeTipoServicioService())
    monkeypatch.setattr(state_module, "categoria_puesto_service", _FakeCategoriaPuestoService())

    asyncio.run(dummy._fetch_catalogo())

    assert dummy.total_tipos == 2
    assert dummy.total_activas == 2
    assert dummy.total_inactivas == 1
    assert dummy.mostrar_empty_state_principal is False

    grupos = dummy.tipos_servicio_con_categorias
    assert [grupo["nombre_display"] for grupo in grupos] == ["Jardineria", "Limpieza"]
    assert grupos[0]["total_categorias"] == 2
    assert grupos[0]["categorias"][0]["clave_display"] == "JARA"
    assert grupos[0]["categorias"][0]["contratos_label"] == "2 contrato(s)"


def test_filtros_aplican_sobre_grupos(monkeypatch):
    dummy = _DummyEmpresaCategoriasState()

    monkeypatch.setattr(state_module, "tipo_servicio_service", _FakeTipoServicioService())
    monkeypatch.setattr(state_module, "categoria_puesto_service", _FakeCategoriaPuestoService())

    asyncio.run(dummy._fetch_catalogo())
    dummy.busqueda_categoria = "super"

    grupos = dummy.tipos_servicio_con_categorias
    assert len(grupos) == 1
    assert grupos[0]["categorias"][0]["nombre_display"] == "Supervisor"

    dummy.busqueda_categoria = ""
    dummy.filtro_estatus_categoria = "INACTIVO"
    grupos = dummy.tipos_servicio_con_categorias
    assert len(grupos) == 1
    assert grupos[0]["categorias"][0]["estatus"] == "INACTIVO"


def test_guardar_categoria_crea_y_cierra_modal(monkeypatch):
    dummy = _DummyEmpresaCategoriasState()
    fake_tipos = _FakeTipoServicioService()
    fake_categorias = _FakeCategoriaPuestoService()

    monkeypatch.setattr(state_module, "tipo_servicio_service", fake_tipos)
    monkeypatch.setattr(state_module, "categoria_puesto_service", fake_categorias)

    dummy.modal_categoria_abierto = True
    dummy.form_tipo_servicio_id = "1"
    dummy.form_nombre_categoria = "Jardinero C"
    dummy.form_clave_categoria = ""
    dummy.form_salario_base_categoria = "9500"

    asyncio.run(_drain(dummy.guardar_categoria()))

    assert fake_categorias.creadas == [
        {
            "empresa_id": 77,
            "tipo_servicio_id": 1,
            "nombre": "Jardinero C",
            "clave": "",
            "salario_base_mensual": Decimal("9500"),
        }
    ]
    assert dummy.modal_categoria_abierto is False
    assert dummy.form_nombre_categoria == ""


def test_crear_tipo_servicio_inline_refresca_catalogo(monkeypatch):
    dummy = _DummyEmpresaCategoriasState()
    fake_tipos = _FakeTipoServicioService()
    fake_categorias = _FakeCategoriaPuestoService()

    monkeypatch.setattr(state_module, "tipo_servicio_service", fake_tipos)
    monkeypatch.setattr(state_module, "categoria_puesto_service", fake_categorias)

    dummy.form_nombre_tipo = "Seguridad"

    asyncio.run(_drain(dummy.crear_tipo_servicio()))

    assert fake_tipos.creados == [(77, "Seguridad")]
    assert dummy.creando_tipo_servicio is False
    assert dummy.error_form_nombre_tipo == ""
