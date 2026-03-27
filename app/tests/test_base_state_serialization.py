"""Tests unitarios para helpers serializables de BaseState."""

import asyncio
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "presentation"
    / "components"
    / "shared"
    / "base_state.py"
)
_SPEC = spec_from_file_location("test_base_state_module", _MODULE_PATH)
_MOD = module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_original_app_core_config = sys.modules.get("app.core.config")
_app_core_config_stub = types.ModuleType("app.core.config")


class _StubConfig:
    DEBUG = False


_app_core_config_stub.Config = _StubConfig
sys.modules["app.core.config"] = _app_core_config_stub
try:
    _SPEC.loader.exec_module(_MOD)
finally:
    if _original_app_core_config is not None:
        sys.modules["app.core.config"] = _original_app_core_config
    else:
        sys.modules.pop("app.core.config", None)

BaseState = _MOD.BaseState


class _FakeModel:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self, *, mode="json"):  # noqa: ARG002 - compat con BaseState
        return dict(self._payload)


class _DummyState:
    serializar_item_state = staticmethod(BaseState.serializar_item_state)
    serializar_lista_state = BaseState.serializar_lista_state

    def __init__(self):
        self.errors = []

    def manejar_error(self, error, contexto):
        self.errors.append((type(error).__name__, contexto, str(error)))


def test_serializar_item_state_convierte_modelos():
    data = BaseState.serializar_item_state(_FakeModel({"id": 1, "nombre": "ACME"}))
    assert data == {"id": 1, "nombre": "ACME"}


def test_serializar_lista_state_aplica_transformador():
    dummy = _DummyState()
    data = BaseState.serializar_lista_state.fn(
        dummy,
        [_FakeModel({"id": 1}), _FakeModel({"id": 2})],
        transformar=lambda item: {"id": item.model_dump()["id"], "ok": True},
    )
    assert data == [{"id": 1, "ok": True}, {"id": 2, "ok": True}]


def test_cargar_y_asignar_lista_retorna_vacio_y_reporta_error():
    dummy = _DummyState()

    async def _run():
        async def _loader():
            raise RuntimeError("boom")

        return await BaseState.cargar_y_asignar_lista.fn(
            dummy,
            "items",
            _loader,
            contexto_error="cargando items",
        )

    assert asyncio.run(_run()) == []
    assert dummy.errors == [("RuntimeError", "cargando items", "boom")]
