"""Tests unitarios para el helper compartido de merges parciales."""

from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator


_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "services"
    / "shared"
    / "model_updates.py"
)
_SPEC = spec_from_file_location("test_model_updates_module", _MODULE_PATH)
_MOD = module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MOD)

merge_update_model = _MOD.merge_update_model


@dataclass
class _FakeEntity:
    nombre: str
    telefono: str | None = None
    activo: bool = True


class _FakeUpdate:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self, *, exclude_unset=False):  # noqa: ARG002 - firma compatible
        return dict(self._payload)


def test_merge_update_model_actualiza_campos_definidos():
    entity = _FakeEntity(nombre="ACME", telefono="5551234567", activo=True)

    updated = merge_update_model(
        entity,
        _FakeUpdate({"nombre": "ACME DOS", "activo": False}),
    )

    assert updated is entity
    assert entity.nombre == "ACME DOS"
    assert entity.activo is False
    assert entity.telefono == "5551234567"


def test_merge_update_model_ignora_none_en_updates_parciales():
    entity = _FakeEntity(nombre="ACME", telefono="5551234567", activo=True)

    merge_update_model(
        entity,
        _FakeUpdate({"nombre": "ACME DOS", "telefono": None}),
    )

    assert entity.nombre == "ACME DOS"
    assert entity.telefono == "5551234567"


class _FakePydanticEntity(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    minimo: int
    maximo: int

    @model_validator(mode="after")
    def validar_rango(self):
        if self.maximo < self.minimo:
            raise ValueError("maximo debe ser mayor o igual a minimo")
        return self


def test_merge_update_model_revalida_pydantic_en_un_solo_paso():
    entity = _FakePydanticEntity(minimo=4, maximo=10)
    update = _FakeUpdate({"minimo": 8, "maximo": 9})

    updated = merge_update_model(entity, update)

    assert updated is not entity
    assert updated.minimo == 8
    assert updated.maximo == 9
