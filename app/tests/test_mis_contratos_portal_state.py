"""Tests del listado de contratos en el portal."""

import asyncio

from app.core.ui_helpers import FILTRO_TODOS
from app.presentation.pages.portal import mis_contratos as mis_contratos_module


class _DummyMisContratosState:
    _fetch_contratos = mis_contratos_module.MisContratosState._fetch_contratos
    _enriquecer_contrato = mis_contratos_module.MisContratosState._enriquecer_contrato
    _calcular_pct_cobertura = staticmethod(
        mis_contratos_module.MisContratosState._calcular_pct_cobertura
    )
    puede_navegar_plazas_desde_contratos = (
        mis_contratos_module.MisContratosState.puede_navegar_plazas_desde_contratos
    )
    contrato_detalle_tiene_plazas = (
        mis_contratos_module.MisContratosState.contrato_detalle_tiene_plazas
    )
    ir_a_plazas_contrato = mis_contratos_module.MisContratosState.ir_a_plazas_contrato

    def __init__(self, filtro_estatus: str):
        self.id_empresa_actual = 26
        self.filtro_estatus_cto = filtro_estatus
        self.contratos = []
        self.total_contratos_lista = 0
        self.mensajes = []
        self.es_usuario_empresa_portal = True
        self.tiene_contratos_con_personal = True
        self.puede_gestionar_personal = True
        self.puede_registrar_personal = False
        self.contrato_detalle = {}

    def mostrar_mensaje(self, mensaje: str, tipo: str):
        self.mensajes.append((mensaje, tipo))

    @staticmethod
    def _contrato_tiene_personal(contrato) -> bool:
        return bool(contrato.get("tiene_personal"))


class _FakeContratoService:
    def __init__(self):
        self.calls = []

    async def obtener_por_empresa(self, empresa_id: int, incluir_inactivos: bool = False):
        self.calls.append((empresa_id, incluir_inactivos))
        return [
            {
                "id": 1,
                "codigo": "CTO-001",
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2026-02-01",
                "monto_minimo": "1000",
                "monto_maximo": "2000",
            }
        ]


def test_fetch_contratos_portal_incluye_vencidos_por_default(monkeypatch):
    dummy = _DummyMisContratosState(FILTRO_TODOS)
    fake_service = _FakeContratoService()

    monkeypatch.setattr(
        mis_contratos_module,
        "contrato_service",
        fake_service,
    )

    asyncio.run(dummy._fetch_contratos())

    assert fake_service.calls == [(26, True)]
    assert dummy.total_contratos_lista == 1
    assert dummy.contratos[0]["descripcion_objeto_display"] == "Sin objeto capturado"
    assert dummy.contratos[0]["fecha_fin_fmt"] == "01/02/2026"
    assert dummy.contratos[0]["vigencia_label"] == "VENCIDO"


def test_fetch_contratos_portal_siempre_incluye_inactivos(monkeypatch):
    """El filtro por estatus ahora se aplica solo en secciones en memoria;
    el query al servicio siempre trae todos los contratos para poder pintar
    borradores, activos e historial en la misma carga."""
    dummy = _DummyMisContratosState("ACTIVO")
    fake_service = _FakeContratoService()

    monkeypatch.setattr(
        mis_contratos_module,
        "contrato_service",
        fake_service,
    )

    asyncio.run(dummy._fetch_contratos())

    assert fake_service.calls == [(26, True)]
    assert dummy.total_contratos_lista == 1


def test_ir_a_plazas_contrato_redirige_a_ruta_contextual():
    dummy = _DummyMisContratosState(FILTRO_TODOS)

    evento = dummy.ir_a_plazas_contrato.fn(dummy, "man-jar-26002")

    assert "/portal/contratos/MAN-JAR-26002/plazas" in str(evento)


def test_contrato_detalle_tiene_plazas_respeta_permiso_y_bandera():
    dummy = _DummyMisContratosState(FILTRO_TODOS)
    dummy.contrato_detalle = {"id": 7, "tiene_personal": True}

    assert dummy.contrato_detalle_tiene_plazas.fget(dummy) is True

    dummy.contrato_detalle = {"id": 7, "tiene_personal": False}

    assert dummy.contrato_detalle_tiene_plazas.fget(dummy) is False
