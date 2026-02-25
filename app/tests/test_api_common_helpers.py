"""Tests unitarios para helpers de respuestas/errores API v1."""

import logging
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from app.core.exceptions import (
    BusinessRuleError,
    DatabaseError,
    DuplicateError,
    NotFoundError,
    ValidationError,
)


class HTTPException(Exception):
    """Stub minimo de fastapi.HTTPException para tests sin dependencia instalada."""

    def __init__(self, status_code: int, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


# Stub de modulo fastapi antes de cargar app.api.v1.common.errors
fastapi_stub = types.ModuleType("fastapi")
fastapi_stub.HTTPException = HTTPException
sys.modules.setdefault("fastapi", fastapi_stub)

_COMMON_DIR = Path(__file__).resolve().parents[1] / "api" / "v1" / "common"


class _SimpleAPIResponse:
    @classmethod
    def __class_getitem__(cls, _item):
        return cls

    def __init__(self, success: bool, data=None, total: int = 0, message=None):
        self.success = success
        self.data = data
        self.total = total
        self.message = message


class _SimpleAPIListResponse(_SimpleAPIResponse):
    pass


# Stub de paquetes para evitar import de app.api.main (requiere FastAPI real)
app_api_stub = types.ModuleType("app.api")
app_api_v1_stub = types.ModuleType("app.api.v1")
app_api_v1_schemas_stub = types.ModuleType("app.api.v1.schemas")
app_api_v1_schemas_stub.APIResponse = _SimpleAPIResponse
app_api_v1_schemas_stub.APIListResponse = _SimpleAPIListResponse
sys.modules.setdefault("app.api", app_api_stub)
sys.modules.setdefault("app.api.v1", app_api_v1_stub)
sys.modules["app.api.v1.schemas"] = app_api_v1_schemas_stub

_RESP_SPEC = spec_from_file_location("test_api_common_responses", _COMMON_DIR / "responses.py")
_RESP_MOD = module_from_spec(_RESP_SPEC)
assert _RESP_SPEC and _RESP_SPEC.loader
_RESP_SPEC.loader.exec_module(_RESP_MOD)

_ERR_SPEC = spec_from_file_location("test_api_common_errors", _COMMON_DIR / "errors.py")
_ERR_MOD = module_from_spec(_ERR_SPEC)
assert _ERR_SPEC and _ERR_SPEC.loader
_ERR_SPEC.loader.exec_module(_ERR_MOD)

ok = _RESP_MOD.ok
ok_list = _RESP_MOD.ok_list
raise_http_from_exc = _ERR_MOD.raise_http_from_exc


class TestApiResponseHelpers:
    """Tests para builders de respuesta."""

    def test_ok_builds_api_response(self):
        response = ok({"id": 1}, total=1, message="OK")
        assert response.success is True
        assert response.data == {"id": 1}
        assert response.total == 1
        assert response.message == "OK"

    def test_ok_list_builds_api_list_response_and_infers_total(self):
        response = ok_list([1, 2, 3])
        assert response.success is True
        assert response.data == [1, 2, 3]
        assert response.total == 3

    def test_ok_list_uses_explicit_total(self):
        response = ok_list([1, 2], total=10)
        assert response.total == 10


class TestApiErrorHelpers:
    """Tests para traduccion de errores a HTTPException."""

    def setup_method(self):
        self.logger = logging.getLogger("test.api.common.errors")

    def test_pass_through_http_exception(self):
        exc = HTTPException(status_code=401, detail="Token invalido")
        with pytest.raises(HTTPException) as raised:
            raise_http_from_exc(exc, self.logger, "auth")
        assert raised.value.status_code == 401
        assert raised.value.detail == "Token invalido"

    @pytest.mark.parametrize(
        ("exc", "status"),
        [
            (NotFoundError("No encontrado"), 404),
            (ValidationError("Datos invalidos"), 400),
            (DuplicateError("Duplicado"), 400),
            (BusinessRuleError("Regla de negocio"), 400),
        ],
    )
    def test_maps_domain_errors_to_http(self, exc, status):
        with pytest.raises(HTTPException) as raised:
            raise_http_from_exc(exc, self.logger, "contexto")
        assert raised.value.status_code == status
        assert str(exc) in str(raised.value.detail)

    def test_database_error_maps_to_500_generic_message(self):
        with pytest.raises(HTTPException) as raised:
            raise_http_from_exc(DatabaseError("DB down"), self.logger, "db")
        assert raised.value.status_code == 500
        assert raised.value.detail == "Error de base de datos"

    def test_unexpected_error_maps_to_500(self):
        with pytest.raises(HTTPException) as raised:
            raise_http_from_exc(RuntimeError("boom"), self.logger, "runtime")
        assert raised.value.status_code == 500
        assert raised.value.detail == "Error interno del servidor"
