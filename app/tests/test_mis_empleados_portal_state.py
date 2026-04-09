"""Tests puntuales para MisEmpleadosState."""

import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import reflex as rx

from app.domain.enums import EstatusPlaza, TipoJornadaPlaza
from app.domain.models.plaza import PlazaResumen
from app.presentation.pages.portal.mis_empleados import state as mis_empleados_state_module
from app.presentation.pages.portal.mis_empleados.state import (
    ACCION_PLAZA_ASIGNAR_CATEGORIA,
    ACCION_PLAZA_ASIGNAR_EMPLEADO,
    ACCION_PLAZA_ASIGNAR_SEDE,
    ACCION_PLAZA_ACTUALIZAR_SALARIO,
    ACCION_PLAZA_CAMBIAR_CATEGORIA,
    ACCION_PLAZA_LIBERAR,
    ACCION_PLAZA_REACTIVAR,
    ACCION_PLAZA_REASIGNAR_CATEGORIA,
    ACCION_PLAZA_REASIGNAR_PLAZA,
    ACCION_PLAZA_REASIGNAR_SEDE,
    MisEmpleadosState,
)


async def _drain(async_gen) -> list:
    eventos = []
    async for item in async_gen:
        eventos.append(item)
    return eventos


class _DummyMisEmpleadosState:
    _normalizar_nombre_visual = staticmethod(MisEmpleadosState._normalizar_nombre_visual)
    _normalizar_sede_visual = staticmethod(MisEmpleadosState._normalizar_sede_visual)
    _estatus_visual_plaza = staticmethod(MisEmpleadosState._estatus_visual_plaza)
    _resolver_acciones_plaza = staticmethod(MisEmpleadosState._resolver_acciones_plaza)
    _placeholder_acciones_plaza = staticmethod(MisEmpleadosState._placeholder_acciones_plaza)
    _serializar_plaza_portal = MisEmpleadosState._serializar_plaza_portal

    def __init__(self):
        self.puede_acceder_rrhh = True
        self.puede_registrar_personal = False
        self.es_institucion = False
        self.empleados = []


class _DummyContratoPlazaState:
    _clave_contrato = staticmethod(MisEmpleadosState._clave_contrato)
    _normalizar_nombre_visual = staticmethod(MisEmpleadosState._normalizar_nombre_visual)
    _opciones_categoria_masiva_contrato = MisEmpleadosState._opciones_categoria_masiva_contrato
    _cargar_opciones_categoria_masiva = MisEmpleadosState._cargar_opciones_categoria_masiva
    _reset_filtros_internos_plaza = MisEmpleadosState._reset_filtros_internos_plaza
    _reset_contexto_plazas_ui = MisEmpleadosState._reset_contexto_plazas_ui
    _listar_contratos_plaza_filtrados = MisEmpleadosState._listar_contratos_plaza_filtrados
    _resolver_contrato_plaza_seleccionado = (
        MisEmpleadosState._resolver_contrato_plaza_seleccionado
    )
    _asegurar_contrato_plaza_seleccionado = (
        MisEmpleadosState._asegurar_contrato_plaza_seleccionado
    )
    _sincronizar_seleccion_contrato_actual = MisEmpleadosState._sincronizar_seleccion_contrato_actual

    def __init__(self):
        self.plazas_por_contrato = []
        self.filtro_estatus_plaza = "all"
        self.contrato_expandido_plaza_id = 0
        self.plazas_contrato_expandido = []
        self.seleccion_plazas_por_contrato = {}
        self.sedes_masivas_por_contrato = {}
        self.categorias_masivas_por_contrato = {}
        self.opciones_categorias_masivas_por_contrato = {}
        self.cargando_plazas_contrato_actual = False
        self.contrato_accion_masiva_activo = ""
        self.pagina_plaza_actual = 1
        self.plaza_por_pagina = 20
        self.plaza_busqueda = ""
        self.plaza_filtro_categoria = "all"
        self.plaza_filtro_sede = "all"
        self.plaza_filtro_estado = "all"
        self.cargas = []

    @property
    def total_paginas_plaza_actual(self):
        return 1

    @property
    def plazas_pagina_actual(self):
        return list(self.plazas_contrato_expandido)

    async def _cargar_pagina_plazas_contrato(self, contrato_id: int, pagina: int = 1):
        self.cargas.append((contrato_id, pagina))
        self.contrato_expandido_plaza_id = int(contrato_id or 0)
        self.plazas_contrato_expandido = [{"id": 100 + int(contrato_id or 0)}]
        self.pagina_plaza_actual = pagina


class _DummySalarioPlazaState:
    _parse_decimal_seguro = staticmethod(MisEmpleadosState._parse_decimal_seguro)

    def __init__(self):
        self.plaza_salario_seleccionada = {}
        self.form_salario_plaza = ""
        self.error_salario_plaza = ""
        self.salario_base_categoria_plaza_referencia = ""
        self.mostrar_modal_salario_plaza = True
        self.saving = False
        self.recargas = 0
        self.errores = []

    async def _fetch_empleados(self):
        self.recargas += 1

    def validar_salario_plaza_campo(self):
        return MisEmpleadosState.validar_salario_plaza_campo.fn(self)

    def cerrar_modal_salario_plaza(self):
        return MisEmpleadosState.cerrar_modal_salario_plaza.fn(self)

    def manejar_error_con_toast(self, error, contexto):
        self.errores.append((contexto, str(error)))
        return None


def _contrato_resumen(
    contrato_id: int,
    *,
    ocupadas: int,
    vacantes: int,
) -> dict:
    return {
        "contrato_id": contrato_id,
        "contrato_codigo": f"CT-{contrato_id:02d}",
        "tipo_servicio_nombre": "Servicio",
        "resumen_plazas": f"{ocupadas + vacantes} plazas · 1 sede",
        "plazas_ocupadas": ocupadas,
        "plazas_vacantes": vacantes,
        "plazas_suspendidas": 0,
        "total_plazas": ocupadas + vacantes,
    }


def test_serializar_plaza_portal_preserva_empleado_uuid():
    dummy = _DummyMisEmpleadosState()
    plaza = PlazaResumen(
        id=11,
        contrato_id=4,
        sede_id=3,
        categoria_puesto_id=7,
        numero_plaza=18,
        codigo="PLA-018",
        empleado_id=99,
        fecha_inicio=date(2030, 1, 1),
        salario_mensual=Decimal("12000.00"),
        tipo_jornada=TipoJornadaPlaza.COMPLETA,
        factor_jornada=Decimal("1.0"),
        estatus=EstatusPlaza.OCUPADA,
        contrato_codigo="CT-04",
        categoria_nombre="AUXILIAR",
        sede_codigo="CU",
        sede_nombre="CAMPUS UNIVERSITARIO",
        empleado_nombre="ANA PEREZ",
        empleado_uuid="00000000-0000-0000-0000-000000000099",
    )

    resultado = dummy._serializar_plaza_portal(plaza)

    assert resultado["empleado_uuid"] == "00000000-0000-0000-0000-000000000099"
    assert resultado["empleado_nombre"] == "Ana Perez"


def test_ver_perfil_plaza_prioriza_uuid_presente_en_payload():
    dummy = _DummyMisEmpleadosState()
    evento = MisEmpleadosState.ver_perfil_plaza.fn(
        dummy,
        {
            "id": 11,
            "empleado_id": 99,
            "empleado_uuid": "00000000-0000-0000-0000-000000000099",
        },
    )

    assert isinstance(evento, rx.event.EventSpec)
    assert "/portal/empleados/00000000-0000-0000-0000-000000000099" in str(evento)


def test_ver_ficha_empleado_fallback_por_id_no_usa_ruta_legacy():
    dummy = _DummyMisEmpleadosState()
    evento = MisEmpleadosState.ver_ficha_empleado.fn(
        dummy,
        {
            "id": 77,
            "uuid": "",
        },
    )

    assert isinstance(evento, rx.event.EventSpec)
    assert "/portal/empleados/77" in str(evento)
    assert "/expediente" not in str(evento)


def test_resolver_contrato_plaza_autoselecciona_primer_visible_con_pill():
    dummy = _DummyContratoPlazaState()
    dummy.plazas_por_contrato = [
        _contrato_resumen(1, ocupadas=0, vacantes=3),
        _contrato_resumen(2, ocupadas=4, vacantes=0),
    ]
    dummy.filtro_estatus_plaza = EstatusPlaza.OCUPADA.value
    dummy.contrato_expandido_plaza_id = 1

    contrato_id = dummy._resolver_contrato_plaza_seleccionado(autoselect_if_empty=True)

    assert contrato_id == 2


def test_asegurar_contrato_plaza_autoselecciona_y_carga_primer_contrato_visible():
    dummy = _DummyContratoPlazaState()
    dummy.plazas_por_contrato = [
        _contrato_resumen(3, ocupadas=2, vacantes=1),
        _contrato_resumen(4, ocupadas=1, vacantes=2),
    ]

    asyncio.run(
        dummy._asegurar_contrato_plaza_seleccionado(
            autoselect_if_empty=True,
        )
    )

    assert dummy.cargas == [(3, 1)]
    assert dummy.contrato_expandido_plaza_id == 3


def test_asegurar_contrato_plaza_no_recarga_si_actual_sigue_valido():
    dummy = _DummyContratoPlazaState()
    dummy.plazas_por_contrato = [
        _contrato_resumen(5, ocupadas=2, vacantes=1),
        _contrato_resumen(6, ocupadas=1, vacantes=2),
    ]
    dummy.contrato_expandido_plaza_id = 6
    dummy.plazas_contrato_expandido = [{"id": 601}]

    asyncio.run(
        dummy._asegurar_contrato_plaza_seleccionado(
            preferred_contract_id=6,
            autoselect_if_empty=True,
        )
    )

    assert dummy.cargas == []
    assert dummy.contrato_expandido_plaza_id == 6


def test_opciones_categoria_masiva_por_contrato_regresan_las_del_contrato_activo():
    dummy = _DummyContratoPlazaState()
    dummy.opciones_categorias_masivas_por_contrato = {
        "6": [{"value": "10", "label": "Auxiliar (2 disp.)"}],
        "8": [{"value": "20", "label": "Supervisor (1 disp.)"}],
    }

    opciones = dummy._opciones_categoria_masiva_contrato(6)

    assert opciones == [{"value": "10", "label": "Auxiliar (2 disp.)"}]


def test_cargar_opciones_categoria_masiva_incluye_categorias_sin_disponibles(monkeypatch):
    dummy = _DummyContratoPlazaState()

    async def _fake_resumen(_contrato_id: int):
        return [
            SimpleNamespace(
                categoria_puesto_id=10,
                cantidad_maxima=1,
                categoria_nombre="SUPERVISOR",
            ),
            SimpleNamespace(
                categoria_puesto_id=20,
                cantidad_maxima=2,
                categoria_nombre="AUXILIAR",
            ),
        ]

    async def _fake_conteos(_contrato_id: int, _fecha_referencia=None):
        return {10: 1, 20: 1}

    monkeypatch.setattr(
        mis_empleados_state_module.contrato_categoria_service,
        "obtener_resumen_de_contrato",
        _fake_resumen,
    )
    monkeypatch.setattr(
        mis_empleados_state_module.plaza_service,
        "obtener_cantidad_esperada_por_categoria",
        _fake_conteos,
    )

    asyncio.run(dummy._cargar_opciones_categoria_masiva(6))

    assert dummy.opciones_categorias_masivas_por_contrato["6"] == [
        {"value": "10", "label": "Supervisor (0 disp.)"},
        {"value": "20", "label": "Auxiliar (1 disp.)"},
    ]


def test_resolver_acciones_plaza_sin_categoria_agrega_salario():
    acciones = MisEmpleadosState._resolver_acciones_plaza(
        {
            "estatus": EstatusPlaza.VACANTE.value,
            "categoria_puesto_id": 0,
            "sede_id": 0,
            "empleado_id": 0,
        }
    )

    assert [item["value"] for item in acciones] == [
        ACCION_PLAZA_ASIGNAR_CATEGORIA,
        ACCION_PLAZA_ACTUALIZAR_SALARIO,
    ]


def test_resolver_acciones_plaza_con_categoria_y_sin_sede():
    acciones = MisEmpleadosState._resolver_acciones_plaza(
        {
            "estatus": EstatusPlaza.VACANTE.value,
            "categoria_puesto_id": 7,
            "sede_id": 0,
            "empleado_id": 0,
        }
    )

    assert [item["value"] for item in acciones] == [
        ACCION_PLAZA_REASIGNAR_CATEGORIA,
        ACCION_PLAZA_ASIGNAR_SEDE,
        ACCION_PLAZA_ACTUALIZAR_SALARIO,
    ]


def test_resolver_acciones_plaza_vacante_con_sede_y_categoria():
    acciones = MisEmpleadosState._resolver_acciones_plaza(
        {
            "estatus": EstatusPlaza.VACANTE.value,
            "categoria_puesto_id": 7,
            "sede_id": 3,
            "empleado_id": 0,
        }
    )

    assert [item["value"] for item in acciones] == [
        ACCION_PLAZA_REASIGNAR_CATEGORIA,
        ACCION_PLAZA_REASIGNAR_SEDE,
        ACCION_PLAZA_ASIGNAR_EMPLEADO,
        ACCION_PLAZA_ACTUALIZAR_SALARIO,
    ]


def test_resolver_acciones_plaza_ocupada_exige_liberar_o_reasignar():
    acciones = MisEmpleadosState._resolver_acciones_plaza(
        {
            "estatus": EstatusPlaza.OCUPADA.value,
            "categoria_puesto_id": 7,
            "sede_id": 3,
            "empleado_id": 99,
        }
    )

    assert [item["value"] for item in acciones] == [
        ACCION_PLAZA_REASIGNAR_PLAZA,
        ACCION_PLAZA_LIBERAR,
        ACCION_PLAZA_CAMBIAR_CATEGORIA,
        ACCION_PLAZA_ACTUALIZAR_SALARIO,
    ]


def test_resolver_acciones_plaza_suspendida_solo_reactiva():
    acciones = MisEmpleadosState._resolver_acciones_plaza(
        {
            "estatus": EstatusPlaza.SUSPENDIDA.value,
            "categoria_puesto_id": 7,
            "sede_id": 3,
            "empleado_id": 0,
        }
    )

    assert [item["value"] for item in acciones] == [ACCION_PLAZA_REACTIVAR]


def test_label_accion_salario_plaza_depende_del_salario_actual():
    assert (
        MisEmpleadosState._label_accion_salario_plaza(
            {"salario_mensual": Decimal("0")},
        )
        == "Asignar salario"
    )
    assert (
        MisEmpleadosState._label_accion_salario_plaza(
            {"salario_mensual": Decimal("14500.00")},
        )
        == "Actualizar salario"
    )


def test_titulo_modal_salario_plaza_cambia_segun_salario_actual():
    dummy = _DummySalarioPlazaState()
    dummy.plaza_salario_seleccionada = {"salario_mensual": Decimal("0")}

    assert MisEmpleadosState.titulo_modal_salario_plaza.fget(dummy) == "Asignar salario"
    assert MisEmpleadosState.texto_guardar_salario_plaza.fget(dummy) == "Asignar salario"

    dummy.plaza_salario_seleccionada = {"salario_mensual": Decimal("18000.00")}

    assert MisEmpleadosState.titulo_modal_salario_plaza.fget(dummy) == "Actualizar salario"
    assert MisEmpleadosState.texto_guardar_salario_plaza.fget(dummy) == "Guardar salario"


def test_confirmar_salario_plaza_rechaza_campo_vacio():
    dummy = _DummySalarioPlazaState()
    dummy.plaza_salario_seleccionada = {"id": 11, "salario_mensual": Decimal("12000.00")}

    asyncio.run(_drain(MisEmpleadosState.confirmar_salario_plaza.fn(dummy)))

    assert dummy.error_salario_plaza == "Capture un salario"
    assert dummy.recargas == 0
    assert dummy.mostrar_modal_salario_plaza is True
    assert dummy.saving is False


def test_confirmar_salario_plaza_rechaza_valor_invalido():
    dummy = _DummySalarioPlazaState()
    dummy.plaza_salario_seleccionada = {"id": 11, "salario_mensual": Decimal("12000.00")}
    dummy.form_salario_plaza = "abc"

    asyncio.run(_drain(MisEmpleadosState.confirmar_salario_plaza.fn(dummy)))

    assert dummy.error_salario_plaza == "El salario debe ser mayor a 0"
    assert dummy.recargas == 0
    assert dummy.mostrar_modal_salario_plaza is True
    assert dummy.saving is False


def test_confirmar_salario_plaza_rechaza_cero():
    dummy = _DummySalarioPlazaState()
    dummy.plaza_salario_seleccionada = {"id": 11, "salario_mensual": Decimal("12000.00")}
    dummy.form_salario_plaza = "0"

    asyncio.run(_drain(MisEmpleadosState.confirmar_salario_plaza.fn(dummy)))

    assert dummy.error_salario_plaza == "El salario debe ser mayor a 0"
    assert dummy.recargas == 0
    assert dummy.mostrar_modal_salario_plaza is True
    assert dummy.saving is False


def test_confirmar_salario_plaza_cierra_sin_mutar_si_no_hay_cambio(monkeypatch):
    dummy = _DummySalarioPlazaState()
    dummy.plaza_salario_seleccionada = {"id": 11, "salario_mensual": Decimal("12500.00")}
    dummy.form_salario_plaza = "$ 12,500.00"
    llamadas = []

    async def _fake_actualizar(*args, **kwargs):
        llamadas.append((args, kwargs))
        return None

    monkeypatch.setattr(
        mis_empleados_state_module.plaza_service,
        "actualizar",
        _fake_actualizar,
    )

    asyncio.run(_drain(MisEmpleadosState.confirmar_salario_plaza.fn(dummy)))

    assert llamadas == []
    assert dummy.mostrar_modal_salario_plaza is False
    assert dummy.recargas == 0
    assert dummy.saving is False


def test_confirmar_salario_plaza_actualiza_y_recarga(monkeypatch):
    dummy = _DummySalarioPlazaState()
    dummy.plaza_salario_seleccionada = {"id": 11, "salario_mensual": Decimal("12500.00")}
    dummy.form_salario_plaza = "$ 13,900.00"
    llamadas = []

    async def _fake_actualizar(plaza_id, payload):
        llamadas.append((plaza_id, payload))
        return SimpleNamespace(id=plaza_id, salario_mensual=payload.salario_mensual)

    monkeypatch.setattr(
        mis_empleados_state_module.plaza_service,
        "actualizar",
        _fake_actualizar,
    )

    asyncio.run(_drain(MisEmpleadosState.confirmar_salario_plaza.fn(dummy)))

    assert len(llamadas) == 1
    plaza_id, payload = llamadas[0]
    assert plaza_id == 11
    assert payload.salario_mensual == Decimal("13900.00")
    assert dummy.mostrar_modal_salario_plaza is False
    assert dummy.recargas == 1
    assert dummy.saving is False
