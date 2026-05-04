"""Tests para los triggers de progressive disclosure del sidebar portal."""

import asyncio
from types import SimpleNamespace

from app.presentation.pages.portal.state import portal_state as portal_state_module
from app.presentation.pages.portal.state.portal_state import PortalState


class _DummyPortalContextState:
    _cargar_contexto_portal_empresa = PortalState._cargar_contexto_portal_empresa
    _obtener_contratos_contexto_empresa = PortalState._obtener_contratos_contexto_empresa
    _contrato_tiene_personal = staticmethod(PortalState._contrato_tiene_personal)
    _contrato_estatus = staticmethod(PortalState._contrato_estatus)

    def __init__(self):
        self.es_empleado_portal = False
        self.id_empresa_actual = 27
        self.total_contratos = 0
        self.tiene_contratos_configurados = False
        self.tiene_contratos_con_personal = False
        self.tiene_plazas_configuradas = False
        self.tiene_empleados_asignados = False
        self.primer_contrato_con_personal_id = 0
        self.gestion_nomina_activa_empresa = False


class _DummyPortalSidebarState:
    mostrar_herramientas = PortalState.mostrar_herramientas
    mostrar_entregables = PortalState.mostrar_entregables
    mostrar_plazas = PortalState.mostrar_plazas
    mostrar_personal = PortalState.mostrar_personal
    mostrar_nomina = PortalState.mostrar_nomina
    mostrar_seccion_nominas = PortalState.mostrar_seccion_nominas
    mostrar_seccion_contabilidad = PortalState.mostrar_seccion_contabilidad

    def __init__(self):
        self.es_usuario_empresa_portal = True
        self.es_admin_empresa = True
        self.es_operaciones = True
        self.es_contabilidad = True
        self.puede_gestionar_personal = True
        self.puede_registrar_personal = True
        self.puede_acceder_rrhh = True
        self.puede_acceder_nomina_contabilidad = True
        self.gestion_nomina_activa_empresa = True
        self.tiene_contratos_configurados = False
        self.tiene_contratos_con_personal = False
        self.tiene_plazas_configuradas = False
        self.tiene_empleados_asignados = False


class _FakeContratoService:
    async def obtener_por_empresa(self, empresa_id: int, incluir_inactivos: bool = False):
        assert empresa_id == 27
        assert incluir_inactivos is True
        return [
            {"id": 31, "estatus": "SUSPENDIDO", "tiene_personal": True},
            {"id": 18, "estatus": "ACTIVO", "tiene_personal": False},
            {"id": 7, "estatus": "BORRADOR", "tiene_personal": True},
        ]


class _FakePlazaService:
    async def tiene_plazas_configuradas(self, empresa_id: int) -> bool:
        assert empresa_id == 27
        return True

    async def obtener_empleados_asignados(self, empresa_id: int) -> list[int]:
        assert empresa_id == 27
        return [801]


class _FakeEmpresaService:
    async def obtener_por_id(self, empresa_id: int):
        assert empresa_id == 27
        return SimpleNamespace(gestion_nomina_activa=True)


def test_cargar_contexto_portal_calcula_triggers_desde_servicios(monkeypatch):
    dummy = _DummyPortalContextState()

    monkeypatch.setattr(
        portal_state_module,
        "empresa_service",
        _FakeEmpresaService(),
    )
    monkeypatch.setattr(
        portal_state_module,
        "contrato_service",
        _FakeContratoService(),
    )
    monkeypatch.setattr(
        portal_state_module,
        "plaza_service",
        _FakePlazaService(),
    )

    asyncio.run(dummy._cargar_contexto_portal_empresa())

    assert dummy.total_contratos == 2
    assert dummy.tiene_contratos_configurados is True
    assert dummy.tiene_contratos_con_personal is True
    assert dummy.primer_contrato_con_personal_id == 31
    assert dummy.tiene_plazas_configuradas is True
    assert dummy.tiene_empleados_asignados is True
    assert dummy.gestion_nomina_activa_empresa is True


def test_sidebar_vars_siguen_el_desbloqueo_progresivo():
    dummy = _DummyPortalSidebarState()

    assert _DummyPortalSidebarState.mostrar_herramientas.fget(dummy) is True
    assert _DummyPortalSidebarState.mostrar_entregables.fget(dummy) is False
    assert _DummyPortalSidebarState.mostrar_plazas.fget(dummy) is False
    assert _DummyPortalSidebarState.mostrar_personal.fget(dummy) is False
    assert _DummyPortalSidebarState.mostrar_nomina.fget(dummy) is False

    dummy.tiene_contratos_configurados = True
    assert _DummyPortalSidebarState.mostrar_entregables.fget(dummy) is True

    dummy.tiene_contratos_con_personal = True
    assert _DummyPortalSidebarState.mostrar_plazas.fget(dummy) is True

    dummy.tiene_plazas_configuradas = True
    assert _DummyPortalSidebarState.mostrar_personal.fget(dummy) is True

    dummy.tiene_empleados_asignados = True
    assert _DummyPortalSidebarState.mostrar_nomina.fget(dummy) is True
    assert _DummyPortalSidebarState.mostrar_seccion_nominas.fget(dummy) is True
    assert _DummyPortalSidebarState.mostrar_seccion_contabilidad.fget(dummy) is True


def test_herramientas_permanece_oculta_para_usuarios_no_admin():
    dummy = _DummyPortalSidebarState()
    dummy.es_admin_empresa = False

    assert _DummyPortalSidebarState.mostrar_herramientas.fget(dummy) is False


def test_nomina_permanece_oculta_si_el_modulo_no_esta_activo():
    dummy = _DummyPortalSidebarState()
    dummy.tiene_contratos_configurados = True
    dummy.tiene_contratos_con_personal = True
    dummy.tiene_plazas_configuradas = True
    dummy.tiene_empleados_asignados = True
    dummy.gestion_nomina_activa_empresa = False

    assert _DummyPortalSidebarState.mostrar_nomina.fget(dummy) is False


def test_copiar_contexto_portal_desde_reutiliza_senales_para_sidebar():
    origen = _DummyPortalContextState()
    origen.total_contratos = 4
    origen.tiene_contratos_configurados = True
    origen.tiene_contratos_con_personal = True
    origen.tiene_plazas_configuradas = True
    origen.tiene_empleados_asignados = True
    origen.primer_contrato_con_personal_id = 31
    origen.gestion_nomina_activa_empresa = True
    origen.metricas_cargadas = True

    destino = _DummyPortalContextState()

    PortalState._copiar_contexto_portal_desde(destino, origen)

    assert destino.total_contratos == 4
    assert destino.tiene_contratos_configurados is True
    assert destino.tiene_contratos_con_personal is True
    assert destino.tiene_plazas_configuradas is True
    assert destino.tiene_empleados_asignados is True
    assert destino.primer_contrato_con_personal_id == 31
    assert destino.gestion_nomina_activa_empresa is True
    assert destino.metricas_cargadas is True
