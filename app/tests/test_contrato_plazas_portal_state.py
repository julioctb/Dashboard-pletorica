"""Tests para la vista portal de plazas por contrato."""

import asyncio

from app.presentation.pages.portal.contrato_plazas.state import ContratoPlazasState
from app.presentation.pages.portal.mis_empleados.state import MisEmpleadosState
from app.presentation.pages.portal.state.portal_state import PortalState


class _DummyPortalPlazasNavState:
    mostrar_seccion_plazas_portal = PortalState.mostrar_seccion_plazas_portal
    ruta_plazas_principal = PortalState.ruta_plazas_principal
    redirigir_a_portal_plazas = PortalState.redirigir_a_portal_plazas

    def __init__(self):
        self.es_usuario_empresa_portal = True
        self.tiene_contratos_con_personal = True
        self.puede_gestionar_personal = True
        self.puede_registrar_personal = False
        self.primer_contrato_con_personal_id = 15

    async def on_mount_portal(self):
        return None


class _DummyContratoPlazasState:
    _ruta_actual = ContratoPlazasState._ruta_actual
    _obtener_contrato_id_ruta = ContratoPlazasState._obtener_contrato_id_ruta
    _resumen_plazas_actuales = ContratoPlazasState._resumen_plazas_actuales
    _construir_contrato_plaza_contexto = ContratoPlazasState._construir_contrato_plaza_contexto
    _clave_contrato = staticmethod(MisEmpleadosState._clave_contrato)
    _pluralizar = staticmethod(MisEmpleadosState._pluralizar)
    _texto_resumen_cantidad = MisEmpleadosState._texto_resumen_cantidad
    _texto_resumen_plazas_sedes = MisEmpleadosState._texto_resumen_plazas_sedes
    _opciones_categoria_masiva_contrato = MisEmpleadosState._opciones_categoria_masiva_contrato
    contrato_plaza_contexto = ContratoPlazasState.contrato_plaza_contexto

    def __init__(self):
        self.router_data = {
            "pathname": "/portal/contratos/[id]/plazas",
            "asPath": "/portal/contratos/44/plazas",
        }
        self.contrato_actual_portal = {
            "id": 44,
            "codigo": "CT-044",
            "estatus": "ACTIVO",
            "descripcion_objeto_display": "Servicio de prueba",
            "nombre_servicio_fmt": "Limpieza",
        }
        self.contrato_expandido_plaza_id = 44
        self.plazas_contrato_expandido = [
            {"id": 1, "estatus": "OCUPADA", "sede_id": 7},
            {"id": 2, "estatus": "VACANTE", "sede_id": 7},
            {"id": 3, "estatus": "VACANTE", "sede_id": 0},
        ]
        self.seleccion_plazas_por_contrato = {"44": [1, 3]}
        self.sedes_masivas_por_contrato = {"44": "7"}
        self.categorias_masivas_por_contrato = {"44": "3"}
        self.opciones_categorias_masivas_por_contrato = {
            "44": [{"value": "3", "label": "Auxiliar (2 disp.)"}]
        }
        self.contrato_plaza_activo = {}
        self.seleccion_todas_plazas_visibles_actual = False


def test_ruta_plazas_principal_usa_primer_contrato_con_personal():
    dummy = _DummyPortalPlazasNavState()

    assert dummy.ruta_plazas_principal.fget(dummy) == "/portal/plazas"


def test_redirigir_a_portal_plazas_envia_a_contrato_contextual():
    dummy = _DummyPortalPlazasNavState()

    evento = asyncio.run(dummy.redirigir_a_portal_plazas.fn(dummy))

    assert evento is not None


def test_obtener_contrato_id_ruta_toma_segmento_dinamico():
    dummy = _DummyContratoPlazasState()

    assert dummy._obtener_contrato_id_ruta() == 44


def test_contrato_plaza_contexto_construye_resumen_desde_plazas_cargadas():
    dummy = _DummyContratoPlazasState()

    contexto = dummy._construir_contrato_plaza_contexto()

    assert contexto["contrato_id"] == 44
    assert contexto["contrato_codigo"] == "CT-044"
    assert contexto["total_plazas"] == 3
    assert contexto["plazas_ocupadas"] == 1
    assert contexto["plazas_vacantes"] == 2
    assert contexto["plazas_sin_sede"] == 1
    assert contexto["seleccion_count"] == 2
