"""Tests del state compartido del portal para incapacidades."""

import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

from core.core.enums import (
    EstatusEmpleado,
    EstatusIncapacidad,
    OrigenIncapacidad,
    TipoIncapacidad,
)
from core.core.exceptions import BusinessRuleError
from core.domain.models.incapacidad import IncapacidadResumen
from core.presentation.pages.portal.incapacidades import state as incapacidad_state_module


async def _drain(async_gen) -> list:
    eventos = []
    async for item in async_gen:
        eventos.append(item)
    return eventos


def _make_employee(
    *,
    empleado_id: int,
    nombre: str,
    clave: str,
    uuid: str,
    estatus: str = EstatusEmpleado.ACTIVO.value,
):
    return SimpleNamespace(
        id=empleado_id,
        nombre_completo=nombre,
        clave=clave,
        uuid=uuid,
        estatus=estatus,
    )


class _BaseDummyIncapacidadState:
    _reset_form = incapacidad_state_module.IncapacidadState._reset_form
    _limpiar_selector_empleado_modal = (
        incapacidad_state_module.IncapacidadState._limpiar_selector_empleado_modal
    )
    _filtrar_incapacidades_empresa = (
        incapacidad_state_module.IncapacidadState._filtrar_incapacidades_empresa
    )
    _normalizar_pagina_incapacidades = (
        incapacidad_state_module.IncapacidadState._normalizar_pagina_incapacidades
    )
    _cargar_catalogo_empleados_modal = (
        incapacidad_state_module.IncapacidadState._cargar_catalogo_empleados_modal
    )

    def __init__(self):
        self.incapacidades_empleado = []
        self.cargando_incapacidades = False
        self.error_incapacidades = ""
        self.incapacidades_empresa = []
        self.error_incapacidades_empresa = ""
        self.conteos_empresa = {"activas": 0, "vencidas": 0, "total": 0}
        self.filtro_estatus_empresa = incapacidad_state_module.FILTRO_TODOS
        self.pagina_incapacidades_actual = 1
        self.filtro_busqueda = ""

        self.modal_abierto = False
        self.modal_modo_global = False
        self.cargando_empleados_modal = False
        self.error_empleados_modal = ""
        self.busqueda_empleado_modal = ""
        self.empleados_catalogo_modal = []
        self.empleado_seleccionado_modal_id = ""
        self.contexto_empleado_resumen = ""
        self.contexto_empleado_error = ""

        self.empleado_contexto_id = 0
        self.empleado_contexto_uuid = ""
        self.empleado_contexto_clave = ""
        self.empleado_contexto_nombre = ""
        self.form_plaza_id = 0
        self.form_contrato_id = 0
        self.form_origen = OrigenIncapacidad.FORMAL.value
        self.form_tipo = TipoIncapacidad.ENF_GENERAL.value
        self.form_fecha_inicio = ""
        self.form_fecha_fin_estimada = ""
        self.form_folio_imss = ""
        self.form_dias_certificado = ""
        self.form_porcentaje_pago = "100.00"
        self.form_requiere_cobertura = False
        self.form_notas = ""
        self.form_error = ""
        self.saving = False
        self.loading = False
        self.id_empresa_actual = 52

        self.recargas: list[int] = []
        self.recargas_empresa = 0
        self.recargas_conteos = 0

    def _serializar_resumen(self, resumen):
        return incapacidad_state_module.IncapacidadState._serializar_resumen.__func__(
            incapacidad_state_module.IncapacidadState,
            resumen,
        )

    def _serializar_empleado_catalogo(self, empleado):
        return incapacidad_state_module.IncapacidadState._serializar_empleado_catalogo.__func__(
            incapacidad_state_module.IncapacidadState,
            empleado,
        )

    def _normalizar_nombre_empleado_catalogo(self, empleado):
        return incapacidad_state_module.IncapacidadState._normalizar_nombre_empleado_catalogo(
            empleado
        )

    def _construir_resumen_contexto(self, contexto: dict) -> str:
        return incapacidad_state_module.IncapacidadState._construir_resumen_contexto(contexto)

    def obtener_uuid_usuario_actual(self):
        return UUID("00000000-0000-0000-0000-000000000777")

    async def _cargar_incapacidades_empleado(self, empleado_id: int):
        self.recargas.append(empleado_id)
        self.incapacidades_empleado = [{"id": 501, "empleado_id": empleado_id}]
        self.error_incapacidades = ""

    async def _cargar_incapacidades_empresa(self):
        self.recargas_empresa += 1

    async def _cargar_conteos_empresa(self):
        self.recargas_conteos += 1

    def cerrar_modal_registro(self):
        return incapacidad_state_module.IncapacidadState.cerrar_modal_registro.fn(self)


class _DummyStateConCargaReal(_BaseDummyIncapacidadState):
    _cargar_incapacidades_empleado = (
        incapacidad_state_module.IncapacidadState._cargar_incapacidades_empleado
    )


class _FakePortalIncapacidadService:
    def __init__(self):
        self.registros = []
        self.listados = []
        self.listados_empresa = []
        self.conteos_solicitados = []
        self.contextos = []
        self.error = None
        self.error_contexto = None
        self.listado_resultado = []
        self.listado_empresa_resultado = []
        self.conteos_resultado = {"activas": 0, "vencidas": 0, "total": 0}
        self.contexto_resultado = {}

    async def registrar_incapacidad(self, data):
        if self.error is not None:
            raise self.error
        self.registros.append(data)
        return None

    async def listar_por_empleado(self, empleado_id: int):
        self.listados.append(empleado_id)
        return list(self.listado_resultado)

    async def listar_por_empresa(self, empresa_id: int):
        self.listados_empresa.append(empresa_id)
        return list(self.listado_empresa_resultado)

    async def obtener_conteos(self, empresa_id: int):
        self.conteos_solicitados.append(empresa_id)
        return dict(self.conteos_resultado)

    async def obtener_contexto_operativo_empleado(self, empleado_id: int, **kwargs):
        self.contextos.append((empleado_id, kwargs))
        if self.error_contexto is not None:
            raise self.error_contexto
        return dict(self.contexto_resultado)


class _FakeEmpleadoService:
    def __init__(self):
        self.busquedas = []
        self.listados_empresa = []
        self.buscar_resultado = []
        self.por_empresa_resultado = []

    async def buscar(self, termino: str, **kwargs):
        self.busquedas.append((termino, kwargs))
        return list(self.buscar_resultado)

    async def obtener_por_empresa(self, empresa_id: int, **kwargs):
        self.listados_empresa.append((empresa_id, kwargs))
        return list(self.por_empresa_resultado)


def test_abrir_modal_registro_desde_ficha_resetea_formulario_y_contexto():
    dummy = _BaseDummyIncapacidadState()
    dummy.form_notas = "nota previa"
    dummy.form_origen = OrigenIncapacidad.POR_ACUERDO.value

    incapacidad_state_module.IncapacidadState.abrir_modal_registro.fn(
        dummy,
        14,
        "ana perez",
    )

    assert dummy.modal_abierto is True
    assert dummy.modal_modo_global is False
    assert dummy.empleado_contexto_id == 14
    assert dummy.empleado_contexto_nombre == "Ana Perez"
    assert dummy.form_plaza_id == 0
    assert dummy.form_contrato_id == 0
    assert dummy.form_origen == OrigenIncapacidad.FORMAL.value
    assert dummy.form_notas == ""


def test_abrir_modal_registro_desde_plaza_conserva_plaza_y_contrato():
    dummy = _BaseDummyIncapacidadState()

    incapacidad_state_module.IncapacidadState.abrir_modal_registro.fn(
        dummy,
        14,
        "ana perez",
        31,
        410,
    )

    assert dummy.modal_abierto is True
    assert dummy.form_plaza_id == 31
    assert dummy.form_contrato_id == 410


def test_abrir_modal_registro_global_carga_catalogo_de_empleados_activos(monkeypatch):
    dummy = _BaseDummyIncapacidadState()
    fake_empleado_service = _FakeEmpleadoService()
    fake_empleado_service.por_empresa_resultado = [
        _make_employee(
            empleado_id=7,
            nombre="ANA PEREZ",
            clave="EMP-007",
            uuid="00000000-0000-0000-0000-000000000007",
        )
    ]

    monkeypatch.setattr(
        incapacidad_state_module,
        "empleado_service",
        fake_empleado_service,
    )

    asyncio.run(_drain(incapacidad_state_module.IncapacidadState.abrir_modal_registro_global.fn(dummy)))

    assert dummy.modal_abierto is True
    assert dummy.modal_modo_global is True
    assert dummy.cargando_empleados_modal is False
    assert len(dummy.empleados_catalogo_modal) == 1
    assert dummy.empleados_catalogo_modal[0]["label"] == "EMP-007 · Ana Perez"
    assert fake_empleado_service.listados_empresa == [
        (
            52,
            {
                "incluir_inactivos": False,
                "limite": incapacidad_state_module.CATALOGO_EMPLEADOS_MODAL_LIMITE,
                "offset": 0,
            },
        )
    ]


def test_set_empleado_seleccionado_modal_id_resuelve_contexto_laboral(monkeypatch):
    dummy = _BaseDummyIncapacidadState()
    dummy.modal_modo_global = True
    dummy.empleados_catalogo_modal = [
        {
            "id": 14,
            "uuid": "00000000-0000-0000-0000-000000000014",
            "clave": "EMP-014",
            "nombre": "Ana Perez",
            "label": "EMP-014 · Ana Perez",
        }
    ]
    fake_service = _FakePortalIncapacidadService()
    fake_service.contexto_resultado = {
        "plaza_id": 31,
        "contrato_id": 410,
        "categoria_nombre": "SUPERVISORA",
        "sede_nombre": "CAMPUS CENTRO",
    }

    monkeypatch.setattr(
        incapacidad_state_module,
        "incapacidad_service",
        fake_service,
    )

    asyncio.run(
        _drain(
            incapacidad_state_module.IncapacidadState.set_empleado_seleccionado_modal_id.fn(
                dummy,
                "14",
            )
        )
    )

    assert dummy.empleado_contexto_id == 14
    assert dummy.empleado_contexto_uuid == "00000000-0000-0000-0000-000000000014"
    assert dummy.empleado_contexto_clave == "EMP-014"
    assert dummy.form_plaza_id == 31
    assert dummy.form_contrato_id == 410
    assert dummy.contexto_empleado_resumen == "Supervisora · Campus Centro · Contrato #410 · Plaza #31"
    assert dummy.contexto_empleado_error == ""
    assert fake_service.contextos == [(14, {})]


def test_guardar_incapacidad_construye_payload_y_refresca_lista_contextual(monkeypatch):
    dummy = _BaseDummyIncapacidadState()
    dummy.modal_abierto = True
    dummy.empleado_contexto_id = 99
    dummy.form_plaza_id = 15
    dummy.form_contrato_id = 55
    dummy.form_origen = OrigenIncapacidad.POR_ACUERDO.value
    dummy.form_tipo = TipoIncapacidad.ACUERDO.value
    dummy.form_fecha_inicio = "2030-03-10"
    dummy.form_fecha_fin_estimada = "2030-03-12"
    dummy.form_porcentaje_pago = "65.50"
    dummy.form_requiere_cobertura = True
    dummy.form_notas = "Acuerdo temporal"
    fake_service = _FakePortalIncapacidadService()

    monkeypatch.setattr(
        incapacidad_state_module,
        "incapacidad_service",
        fake_service,
    )

    asyncio.run(_drain(incapacidad_state_module.IncapacidadState.guardar_incapacidad.fn(dummy)))

    assert len(fake_service.registros) == 1
    payload = fake_service.registros[0]
    assert payload.empleado_id == 99
    assert payload.plaza_id == 15
    assert payload.contrato_id == 55
    assert payload.empresa_id == 52
    assert payload.origen == OrigenIncapacidad.POR_ACUERDO
    assert payload.tipo == TipoIncapacidad.ACUERDO
    assert payload.fecha_inicio == date(2030, 3, 10)
    assert payload.fecha_fin_estimada == date(2030, 3, 12)
    assert payload.porcentaje_pago == Decimal("65.50")
    assert payload.requiere_cobertura is True
    assert payload.registrado_por == UUID("00000000-0000-0000-0000-000000000777")
    assert dummy.modal_abierto is False
    assert dummy.recargas == [99]
    assert dummy.recargas_empresa == 0
    assert dummy.recargas_conteos == 0
    assert dummy.saving is False


def test_guardar_incapacidad_global_refresca_listado_y_conteos(monkeypatch):
    dummy = _BaseDummyIncapacidadState()
    dummy.modal_abierto = True
    dummy.modal_modo_global = True
    dummy.empleado_contexto_id = 99
    dummy.form_plaza_id = 15
    dummy.form_contrato_id = 55
    dummy.form_fecha_inicio = "2030-03-10"
    dummy.form_fecha_fin_estimada = "2030-03-12"
    dummy.form_folio_imss = "IMSS-009"
    fake_service = _FakePortalIncapacidadService()

    monkeypatch.setattr(
        incapacidad_state_module,
        "incapacidad_service",
        fake_service,
    )

    asyncio.run(_drain(incapacidad_state_module.IncapacidadState.guardar_incapacidad.fn(dummy)))

    assert len(fake_service.registros) == 1
    assert dummy.modal_abierto is False
    assert dummy.recargas == []
    assert dummy.recargas_empresa == 1
    assert dummy.recargas_conteos == 1


def test_guardar_incapacidad_global_bloquea_si_no_hay_contexto_operable():
    dummy = _BaseDummyIncapacidadState()
    dummy.modal_abierto = True
    dummy.modal_modo_global = True
    dummy.empleado_contexto_id = 99
    dummy.form_fecha_inicio = "2030-03-10"
    dummy.contexto_empleado_error = "No se encontró contexto laboral vigente"

    asyncio.run(_drain(incapacidad_state_module.IncapacidadState.guardar_incapacidad.fn(dummy)))

    assert dummy.form_error == "No se encontró contexto laboral vigente"
    assert dummy.modal_abierto is True
    assert dummy.saving is False


def test_guardar_incapacidad_muestra_error_de_regla_de_negocio(monkeypatch):
    dummy = _BaseDummyIncapacidadState()
    dummy.modal_abierto = True
    dummy.empleado_contexto_id = 99
    dummy.form_fecha_inicio = "2030-03-10"
    dummy.form_fecha_fin_estimada = "2030-03-12"
    dummy.form_folio_imss = "IMSS-009"
    fake_service = _FakePortalIncapacidadService()
    fake_service.error = BusinessRuleError("Conflicto en 11/03/2030")

    monkeypatch.setattr(
        incapacidad_state_module,
        "incapacidad_service",
        fake_service,
    )

    asyncio.run(_drain(incapacidad_state_module.IncapacidadState.guardar_incapacidad.fn(dummy)))

    assert dummy.form_error == "Conflicto en 11/03/2030"
    assert dummy.modal_abierto is True
    assert dummy.saving is False


def test_cargar_por_empleado_serializa_resultados_del_servicio(monkeypatch):
    dummy = _DummyStateConCargaReal()
    fake_service = _FakePortalIncapacidadService()
    fake_service.listado_resultado = [
        IncapacidadResumen(
            id=88,
            empleado_id=14,
            empleado_uuid=UUID("00000000-0000-0000-0000-000000000014"),
            empleado_clave="EMP-014",
            empleado_nombre="ANA PEREZ",
            tipo=TipoIncapacidad.MATERNIDAD,
            origen=OrigenIncapacidad.FORMAL,
            fecha_inicio=date(2031, 1, 1),
            fecha_fin_estimada=date(2031, 1, 14),
            estatus=EstatusIncapacidad.ACTIVA,
            dias_certificados=14,
            total_certificados=1,
            requiere_cobertura=True,
            plaza_id=31,
            contrato_id=410,
            ultimo_folio_imss="FOL-014",
            plaza_categoria="SUPERVISORA",
            plaza_sede="CAMPUS CENTRO",
        )
    ]

    monkeypatch.setattr(
        incapacidad_state_module,
        "incapacidad_service",
        fake_service,
    )

    asyncio.run(_drain(incapacidad_state_module.IncapacidadState.cargar_por_empleado.fn(dummy, 14)))

    assert fake_service.listados == [14]
    assert dummy.error_incapacidades == ""
    assert dummy.cargando_incapacidades is False
    assert dummy.incapacidades_empleado == [
        {
            "id": 88,
            "empleado_id": 14,
            "empleado_uuid": "00000000-0000-0000-0000-000000000014",
            "empleado_clave": "EMP-014",
            "empleado_nombre": "Ana Perez",
            "tipo": "MATERNIDAD",
            "tipo_label": "Maternidad",
            "origen": "FORMAL",
            "origen_label": "Formal (IMSS)",
            "fecha_inicio": "2031-01-01",
            "fecha_inicio_fmt": "01/01/2031",
            "fecha_fin_estimada": "2031-01-14",
            "fecha_fin_estimada_fmt": "14/01/2031",
            "periodo_label": "01/01/2031 — 14/01/2031",
            "estatus": "ACTIVA",
            "estatus_label": "Activa",
            "dias_certificados": 14,
            "dias_certificados_label": "14 día(s)",
            "total_certificados": 1,
            "total_certificados_label": "1 certificado(s)",
            "ultimo_folio_imss": "FOL-014",
            "folio_imss_label": "FOL-014",
            "requiere_cobertura": True,
            "plaza_id": 31,
            "contrato_id": 410,
            "plaza_detalle": "Supervisora · Campus Centro",
        }
    ]
