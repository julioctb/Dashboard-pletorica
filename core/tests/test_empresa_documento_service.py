"""Tests unitarios para `EmpresaDocumentoService`."""

from __future__ import annotations

import asyncio
import sys
import types
from datetime import datetime, timedelta, timezone
from enum import Enum
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from core.core.exceptions import BusinessRuleError


class _BootstrapDBManager:
    def get_client(self):
        return object()


class _EntidadArchivo(str, Enum):
    EMPRESA = "EMPRESA"


class _TipoArchivo(str, Enum):
    DOCUMENTO = "DOCUMENTO"


class _EmpresaDocumento(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: int | None = None
    empresa_id: int
    anio: int
    tipo_documento: str
    requisito_id: int | None = None
    archivo_id: int | None = None
    nombre_archivo: str | None = None
    version: int = 1
    es_vigente: bool = True
    subido_por: str | None = None
    fecha_creacion: datetime | None = None
    fecha_actualizacion: datetime | None = None


class _EmpresaDocumentoCreate(BaseModel):
    empresa_id: int
    anio: int
    tipo_documento: str
    requisito_id: int | None = None
    subido_por: str | None = None


class _EmpresaDocumentoResumen(BaseModel):
    empresa_id: int
    anio: int
    numero: int
    tipo_documento: str
    requisito_id: int | None = None
    tipo_documento_label: str
    ayuda: str = ""
    obligatorio: bool = True
    es_anual: bool = True
    es_personalizado: bool = False
    estatus: str = "Pendiente"
    subido: bool = False
    archivo_id: int | None = None
    nombre_archivo: str = ""
    version: int = 0
    anio_documento: int | None = None
    origen_documento_texto: str = ""
    fecha_creacion: datetime | None = None


class _EmpresaDocumentoShareLink(BaseModel):
    id: int | None = None
    empresa_id: int
    anio: int
    token_hash: str
    expires_at: datetime
    created_by: str | None = None
    revoked_at: datetime | None = None
    revoked_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class _EmpresaDocumentoRequisito(BaseModel):
    id: int | None = None
    empresa_id: int
    codigo: str
    nombre: str
    ayuda: str | None = None
    es_obligatorio: bool = False
    es_anual: bool = True
    orden: int = 100
    activo: bool = True
    fecha_creacion: datetime | None = None
    fecha_actualizacion: datetime | None = None


class _EmpresaDocumentoRequisitoCreate(BaseModel):
    empresa_id: int
    nombre: str
    ayuda: str | None = None
    es_obligatorio: bool = False
    es_anual: bool = True


class _ArchivoResponse:
    def __init__(self, archivo_id: int):
        self.archivo = types.SimpleNamespace(id=archivo_id)


class _ArchivoServiceStub:
    async def subir_archivo(self, **_kwargs):
        return _ArchivoResponse(archivo_id=77)


class _EmpresaServiceStub:
    async def obtener_por_id(self, empresa_id: int):
        return types.SimpleNamespace(
            id=empresa_id,
            nombre_comercial="Proveedor Demo",
            razon_social="Proveedor Demo SA de CV",
            rfc="DEM010101ABC",
            codigo_corto="DEM",
        )


class FakeResponse:
    def __init__(self, data=None):
        self.data = data


class FakeQuery:
    def __init__(self, supabase, table_name: str):
        self._supabase = supabase
        self._table_name = table_name
        self._action = None
        self._payload = None
        self._filters = []
        self._limit = None
        self._orders = []

    def select(self, *_fields):
        self._action = "select"
        return self

    def update(self, payload):
        self._action = "update"
        self._payload = payload
        return self

    def insert(self, payload):
        self._action = "insert"
        self._payload = payload
        return self

    def eq(self, field, value):
        self._filters.append(("eq", field, value))
        return self

    def is_(self, field, value):
        self._filters.append(("is", field, value))
        return self

    def gt(self, field, value):
        self._filters.append(("gt", field, value))
        return self

    def lte(self, field, value):
        self._filters.append(("lte", field, value))
        return self

    def order(self, field, desc=False):
        self._orders.append((field, desc))
        return self

    def limit(self, value):
        self._limit = value
        return self

    def execute(self):
        self._supabase.executed.append(
            {
                "table": self._table_name,
                "action": self._action,
                "payload": self._payload,
                "filters": list(self._filters),
                "limit": self._limit,
                "orders": list(self._orders),
            }
        )
        if not self._supabase.results:
            raise AssertionError("No hay respuestas configuradas para execute()")
        result = self._supabase.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class FakeSupabase:
    def __init__(self, results):
        self.results = list(results)
        self.executed = []

    def table(self, table_name: str):
        return FakeQuery(self, table_name)


_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "domain"
    / "services"
    / "empresa_documento_service.py"
)
_SPEC = spec_from_file_location("test_empresa_documento_service_module", _MODULE_PATH)
_MOD = module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader

_original_app_database = sys.modules.get("core.database")
_original_app_entities = sys.modules.get("core.domain.models")
_original_archivo = sys.modules.get("core.domain.models.archivo")
_original_empresa_doc = sys.modules.get("core.domain.models.empresa_documento")
_original_app_services = sys.modules.get("core.domain.services")
_original_archivo_service = sys.modules.get("core.domain.services.archivo_service")
_original_empresa_service = sys.modules.get("core.domain.services.empresa_service")

_app_database_stub = types.ModuleType("core.database")
_app_database_stub.db_manager = _BootstrapDBManager()
_app_entities_stub = types.ModuleType("core.domain.models")
_app_entities_stub.__path__ = []
_app_services_stub = types.ModuleType("core.domain.services")
_app_services_stub.__path__ = []
_archivo_stub = types.ModuleType("core.domain.models.archivo")
_archivo_stub.EntidadArchivo = _EntidadArchivo
_archivo_stub.TipoArchivo = _TipoArchivo
_empresa_doc_stub = types.ModuleType("core.domain.models.empresa_documento")
_empresa_doc_stub.EmpresaDocumento = _EmpresaDocumento
_empresa_doc_stub.EmpresaDocumentoCreate = _EmpresaDocumentoCreate
_empresa_doc_stub.EmpresaDocumentoResumen = _EmpresaDocumentoResumen
_empresa_doc_stub.EmpresaDocumentoRequisito = _EmpresaDocumentoRequisito
_empresa_doc_stub.EmpresaDocumentoRequisitoCreate = _EmpresaDocumentoRequisitoCreate
_empresa_doc_stub.EmpresaDocumentoShareLink = _EmpresaDocumentoShareLink
_archivo_service_stub = types.ModuleType("core.domain.services.archivo_service")
_archivo_service_stub.archivo_service = _ArchivoServiceStub()
_empresa_service_stub = types.ModuleType("core.domain.services.empresa_service")
_empresa_service_stub.empresa_service = _EmpresaServiceStub()

sys.modules["core.database"] = _app_database_stub
sys.modules["core.domain.models"] = _app_entities_stub
sys.modules["core.domain.services"] = _app_services_stub
sys.modules["core.domain.models.archivo"] = _archivo_stub
sys.modules["core.domain.models.empresa_documento"] = _empresa_doc_stub
sys.modules["core.domain.services.archivo_service"] = _archivo_service_stub
sys.modules["core.domain.services.empresa_service"] = _empresa_service_stub

try:
    _SPEC.loader.exec_module(_MOD)
finally:
    if _original_app_database is not None:
        sys.modules["core.database"] = _original_app_database
    else:
        sys.modules.pop("core.database", None)
    if _original_app_entities is not None:
        sys.modules["core.domain.models"] = _original_app_entities
    else:
        sys.modules.pop("core.domain.models", None)
    if _original_app_services is not None:
        sys.modules["core.domain.services"] = _original_app_services
    else:
        sys.modules.pop("core.domain.services", None)
    if _original_archivo is not None:
        sys.modules["core.domain.models.archivo"] = _original_archivo
    else:
        sys.modules.pop("core.domain.models.archivo", None)
    if _original_empresa_doc is not None:
        sys.modules["core.domain.models.empresa_documento"] = _original_empresa_doc
    else:
        sys.modules.pop("core.domain.models.empresa_documento", None)
    if _original_archivo_service is not None:
        sys.modules["core.domain.services.archivo_service"] = _original_archivo_service
    else:
        sys.modules.pop("core.domain.services.archivo_service", None)
    if _original_empresa_service is not None:
        sys.modules["core.domain.services.empresa_service"] = _original_empresa_service
    else:
        sys.modules.pop("core.domain.services.empresa_service", None)

EmpresaDocumentoService = _MOD.EmpresaDocumentoService


def _run(coro):
    return asyncio.run(coro)


def _service_with_results(*results):
    service = EmpresaDocumentoService()
    fake_supabase = FakeSupabase(results)
    service.supabase = fake_supabase
    return service, fake_supabase


def test_subir_documento_crea_version_1_para_anio_especifico():
    service, fake = _service_with_results(
        FakeResponse(data=[{"id": 1}]),
        FakeResponse(data=[]),
        FakeResponse(
            data=[
                {
                    "id": 10,
                    "empresa_id": 25,
                    "anio": 2026,
                    "tipo_documento": "CONSTANCIA_SITUACION_FISCAL",
                    "archivo_id": 77,
                    "nombre_archivo": "sat.pdf",
                    "version": 1,
                    "es_vigente": True,
                }
            ]
        ),
    )

    created = _run(
        service.subir_documento(
            _EmpresaDocumentoCreate(
                empresa_id=25,
                anio=2026,
                tipo_documento="CONSTANCIA_SITUACION_FISCAL",
            ),
            b"pdf",
            "sat.pdf",
            "application/pdf",
        )
    )

    assert created.version == 1
    insert_call = fake.executed[-1]
    assert insert_call["payload"]["anio"] == 2026
    assert insert_call["payload"]["version"] == 1


def test_subir_documento_incrementa_version_en_mismo_anio_y_tipo():
    service, fake = _service_with_results(
        FakeResponse(data=[{"id": 1}]),
        FakeResponse(data=[{"version": 3}]),
        FakeResponse(
            data=[
                {
                    "id": 11,
                    "empresa_id": 25,
                    "anio": 2026,
                    "tipo_documento": "OPINION_CUMPLIMIENTO_SAT",
                    "archivo_id": 77,
                    "nombre_archivo": "opinion.pdf",
                    "version": 4,
                    "es_vigente": True,
                }
            ]
        ),
    )

    created = _run(
        service.subir_documento(
            _EmpresaDocumentoCreate(
                empresa_id=25,
                anio=2026,
                tipo_documento="OPINION_CUMPLIMIENTO_SAT",
            ),
            b"pdf",
            "opinion.pdf",
            "application/pdf",
        )
    )

    assert created.version == 4
    assert fake.executed[-1]["payload"]["version"] == 4


def test_subir_documento_a_otro_anio_no_toca_filtros_del_anio_previo():
    service, fake = _service_with_results(
        FakeResponse(data=[{"id": 1}]),
        FakeResponse(data=[{"version": 2}]),
        FakeResponse(
            data=[
                {
                    "id": 12,
                    "empresa_id": 25,
                    "anio": 2027,
                    "tipo_documento": "DECLARACION_ANUAL",
                    "archivo_id": 77,
                    "nombre_archivo": "anual.pdf",
                    "version": 3,
                    "es_vigente": True,
                }
            ]
        ),
    )

    _run(
        service.subir_documento(
            _EmpresaDocumentoCreate(
                empresa_id=25,
                anio=2027,
                tipo_documento="DECLARACION_ANUAL",
            ),
            b"pdf",
            "anual.pdf",
            "application/pdf",
        )
    )

    filtros_update = fake.executed[0]["filters"]
    filtros_select = fake.executed[1]["filters"]
    assert ("eq", "anio", 2027) in filtros_update
    assert ("eq", "anio", 2027) in filtros_select
    assert ("eq", "anio", 2026) not in filtros_update


def test_documento_persistente_actualiza_vigencia_sin_limitarse_al_anio():
    service, fake = _service_with_results(
        FakeResponse(data=[{"id": 1}]),
        FakeResponse(data=[{"version": 1}]),
        FakeResponse(
            data=[
                {
                    "id": 13,
                    "empresa_id": 25,
                    "anio": 2026,
                    "tipo_documento": "ACTA_CONSTITUTIVA",
                    "archivo_id": 77,
                    "nombre_archivo": "acta.pdf",
                    "version": 2,
                    "es_vigente": True,
                }
            ]
        ),
    )

    _run(
        service.subir_documento(
            _EmpresaDocumentoCreate(
                empresa_id=25,
                anio=2026,
                tipo_documento="ACTA_CONSTITUTIVA",
            ),
            b"pdf",
            "acta.pdf",
            "application/pdf",
        )
    )

    filtros_update = fake.executed[0]["filters"]
    filtros_select = fake.executed[1]["filters"]
    assert ("eq", "anio", 2026) not in filtros_update
    assert ("eq", "anio", 2026) not in filtros_select


def test_checklist_renderiza_labels_dinamicos_para_documentos_fiscales():
    service, _ = _service_with_results(FakeResponse(data=[]), FakeResponse(data=[]))

    expediente = _run(service.obtener_expediente_empresa(empresa_id=10, anio=2026))
    labels = {
        item["tipo_documento"]: item["tipo_documento_label"]
        for item in expediente["documentos"]
    }

    assert labels["DECLARACION_ANUAL"].endswith("2025")
    assert labels["ACUSE_DECLARACION_ANUAL"].endswith("2025")
    assert labels["DECLARACION_MENSUAL"].endswith("2026")
    assert labels["ACUSE_DECLARACION_MENSUAL"].endswith("2026")


def test_completitud_excluye_repse_en_v1():
    service, _ = _service_with_results(
        FakeResponse(
            data=[
                {
                    "id": 50,
                    "empresa_id": 10,
                    "anio": 2026,
                    "tipo_documento": "REPSE",
                    "archivo_id": 77,
                    "nombre_archivo": "repse.pdf",
                    "version": 1,
                    "es_vigente": True,
                }
            ]
        ),
        FakeResponse(
            data=[]
        )
    )

    expediente = _run(service.obtener_expediente_empresa(empresa_id=10, anio=2026))

    assert expediente["documentos_requeridos"] == 19
    assert expediente["documentos_subidos_requeridos"] == 0
    assert expediente["porcentaje_completitud"] == 0


def test_documento_persistente_se_reutiliza_desde_anio_previo():
    service, _ = _service_with_results(
        FakeResponse(
            data=[
                {
                    "id": 70,
                    "empresa_id": 10,
                    "anio": 2024,
                    "tipo_documento": "IDENTIFICACION_OFICIAL",
                    "archivo_id": 77,
                    "nombre_archivo": "ine.pdf",
                    "version": 1,
                    "es_vigente": True,
                }
            ]
        ),
        FakeResponse(data=[]),
    )

    expediente = _run(service.obtener_expediente_empresa(empresa_id=10, anio=2026))
    identificacion = next(
        item for item in expediente["documentos"]
        if item["tipo_documento"] == "IDENTIFICACION_OFICIAL"
    )

    assert identificacion["subido"] is True
    assert identificacion["anio_documento"] == 2024
    assert identificacion["origen_documento_texto"] == "Vigente desde 2024"


def test_documento_persistente_prioriza_version_vigente_mas_reciente():
    service, _ = _service_with_results(
        FakeResponse(
            data=[
                {
                    "id": 70,
                    "empresa_id": 10,
                    "anio": 2024,
                    "tipo_documento": "IDENTIFICACION_OFICIAL",
                    "archivo_id": 77,
                    "nombre_archivo": "ine-2024.pdf",
                    "version": 1,
                    "es_vigente": True,
                },
                {
                    "id": 71,
                    "empresa_id": 10,
                    "anio": 2026,
                    "tipo_documento": "IDENTIFICACION_OFICIAL",
                    "archivo_id": 88,
                    "nombre_archivo": "ine-2026.pdf",
                    "version": 2,
                    "es_vigente": True,
                },
            ]
        ),
        FakeResponse(data=[]),
    )

    expediente = _run(service.obtener_expediente_empresa(empresa_id=10, anio=2026))
    identificacion = next(
        item for item in expediente["documentos"]
        if item["tipo_documento"] == "IDENTIFICACION_OFICIAL"
    )

    assert identificacion["subido"] is True
    assert identificacion["anio_documento"] == 2026
    assert identificacion["nombre_archivo"] == "ine-2026.pdf"
    assert identificacion["origen_documento_texto"] == ""


def test_documento_anual_no_se_reutiliza_desde_anio_previo():
    service, _ = _service_with_results(
        FakeResponse(
            data=[
                {
                    "id": 72,
                    "empresa_id": 10,
                    "anio": 2025,
                    "tipo_documento": "CONSTANCIA_SITUACION_FISCAL",
                    "archivo_id": 77,
                    "nombre_archivo": "csf-2025.pdf",
                    "version": 1,
                    "es_vigente": True,
                }
            ]
        ),
        FakeResponse(data=[]),
    )

    expediente = _run(service.obtener_expediente_empresa(empresa_id=10, anio=2026))
    constancia = next(
        item for item in expediente["documentos"]
        if item["tipo_documento"] == "CONSTANCIA_SITUACION_FISCAL"
    )

    assert constancia["subido"] is False
    assert constancia["anio_documento"] is None
    assert constancia["estatus"] == "Pendiente"


def test_expediente_incluye_documentos_personalizados_por_empresa():
    service, _ = _service_with_results(
        FakeResponse(
            data=[
                {
                    "id": 81,
                    "empresa_id": 10,
                    "anio": 2026,
                    "tipo_documento": "DOCUMENTO_ADICIONAL",
                    "requisito_id": 5,
                    "archivo_id": 77,
                    "nombre_archivo": "reforma.pdf",
                    "version": 1,
                    "es_vigente": True,
                }
            ]
        ),
        FakeResponse(
            data=[
                {
                    "id": 5,
                    "empresa_id": 10,
                    "codigo": "DOC_10_100_ACTA_REFORMA",
                    "nombre": "Acta constitutiva - reforma 2021",
                    "ayuda": "Adjuntar protocolo y sello notarial.",
                    "es_obligatorio": True,
                    "es_anual": False,
                    "orden": 100,
                    "activo": True,
                }
            ]
        ),
    )

    expediente = _run(service.obtener_expediente_empresa(empresa_id=10, anio=2026))
    personalizado = next(
        item for item in expediente["documentos"]
        if item["requisito_id"] == 5
    )

    assert personalizado["tipo_documento"] == "DOCUMENTO_ADICIONAL"
    assert personalizado["tipo_documento_label"] == "Acta constitutiva - reforma 2021"
    assert personalizado["subido"] is True
    assert personalizado["es_personalizado"] is True


def test_documento_personalizado_anual_no_se_reutiliza_fuera_del_anio():
    service, _ = _service_with_results(
        FakeResponse(
            data=[
                {
                    "id": 82,
                    "empresa_id": 10,
                    "anio": 2025,
                    "tipo_documento": "DOCUMENTO_ADICIONAL",
                    "requisito_id": 6,
                    "archivo_id": 90,
                    "nombre_archivo": "constancia-anual-2025.pdf",
                    "version": 1,
                    "es_vigente": True,
                }
            ]
        ),
        FakeResponse(
            data=[
                {
                    "id": 6,
                    "empresa_id": 10,
                    "codigo": "DOC_10_101_CONSTANCIA_ANUAL",
                    "nombre": "Constancia anual de cumplimiento",
                    "ayuda": "Documento renovable por ejercicio.",
                    "es_obligatorio": True,
                    "es_anual": True,
                    "orden": 101,
                    "activo": True,
                }
            ]
        ),
    )

    expediente = _run(service.obtener_expediente_empresa(empresa_id=10, anio=2026))
    personalizado = next(
        item for item in expediente["documentos"]
        if item["requisito_id"] == 6
    )

    assert personalizado["subido"] is False
    assert personalizado["anio_documento"] is None
    assert personalizado["estatus"] == "Pendiente"


def test_generar_share_link_guarda_hash_y_retorna_path_publico():
    service, fake = _service_with_results(
        FakeResponse(data=[]),
        FakeResponse(
            data=[
                {
                    "id": 99,
                    "empresa_id": 10,
                    "anio": 2026,
                    "token_hash": "x" * 64,
                    "expires_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
                    "created_by": "user-1",
                }
            ]
        ),
    )

    result = _run(
        service.generar_share_link(
            empresa_id=10,
            anio=2026,
            expires_at=datetime.now(timezone.utc) + timedelta(days=3),
            created_by="user-1",
        )
    )

    assert result["share_path"].startswith("/share/empresa-documentacion/")
    insert_payload = fake.executed[-1]["payload"]
    assert insert_payload["token_hash"] != result["share_token"]
    assert len(insert_payload["token_hash"]) == 64


def test_resolver_share_token_valido_retorna_empresa_y_expediente():
    service, _ = _service_with_results()
    share = _EmpresaDocumentoShareLink(
        id=1,
        empresa_id=10,
        anio=2026,
        token_hash="hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    service.supabase = FakeSupabase(
        [
            FakeResponse(data=[share.model_dump(mode="json")]),
        ]
    )

    async def _fake_expediente(_empresa_id, _anio):
        return {
            "empresa_id": 10,
            "anio": 2026,
            "documentos": [],
            "documentos_requeridos": 19,
            "documentos_subidos_requeridos": 2,
            "porcentaje_completitud": 11,
        }

    service.obtener_expediente_empresa = _fake_expediente

    result = _run(service.resolver_share_token("token-demo"))

    assert result["empresa"]["nombre_comercial"] == "Proveedor Demo"
    assert result["anio"] == 2026
    assert result["porcentaje_completitud"] == 11


def test_resolver_share_token_expirado_falla():
    service, _ = _service_with_results()
    share = _EmpresaDocumentoShareLink(
        id=1,
        empresa_id=10,
        anio=2026,
        token_hash="hash",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    service.supabase = FakeSupabase(
        [
            FakeResponse(data=[share.model_dump(mode="json")]),
        ]
    )

    try:
        _run(service.resolver_share_token("token-expirado"))
    except BusinessRuleError as exc:
        assert "expirado" in str(exc).lower()
    else:
        raise AssertionError("Se esperaba BusinessRuleError para un token expirado")
