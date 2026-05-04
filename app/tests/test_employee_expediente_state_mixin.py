"""Tests puntuales para el mixin de expediente documental del portal."""

import asyncio

from app.domain.enums import TipoDocumentoEmpleado
import app.presentation.components.shared.employee_expediente_state_mixin as expediente_module
from app.presentation.components.shared.employee_expediente_state_mixin import (
    EmployeeExpedienteStateMixin,
)


class _FakeDoc:
    def __init__(self, payload: dict):
        self._payload = payload

    def model_dump(self, mode: str = "json") -> dict:
        assert mode == "json"
        return dict(self._payload)


class _FakeUploadFile:
    filename = "ine.pdf"
    content_type = "application/pdf"

    async def read(self) -> bytes:
        return b"pdf"


class _DummyExpedienteState(EmployeeExpedienteStateMixin):
    def __init__(self):
        self.empleado = {"id": 88}
        self.saving = False
        self._reset_expediente_documental_state()
        self.reloads: list[int] = []

    def obtener_uuid_usuario_actual(self) -> str:
        return "00000000-0000-0000-0000-000000000123"

    def manejar_error_con_toast(self, exc, action: str):
        raise AssertionError(f"No se esperaba error {action}: {exc}")

    async def _cargar_documentos_expediente(self, empleado_id: int) -> None:
        self.reloads.append(empleado_id)


def _primer_tipo(*, obligatorio: bool) -> TipoDocumentoEmpleado:
    return next(tipo for tipo in TipoDocumentoEmpleado if bool(tipo.es_obligatorio) is obligatorio)


def test_cargar_documentos_expediente_reconstruye_checklist_y_metricas(monkeypatch):
    required_type = _primer_tipo(obligatorio=True)
    optional_type = _primer_tipo(obligatorio=False)

    class _FakeDocumentoService:
        async def obtener_documentos_empleado(self, empleado_id: int, solo_vigentes: bool):
            assert empleado_id == 88
            assert solo_vigentes is True
            return [
                _FakeDoc(
                    {
                        "id": 1,
                        "archivo_id": 10,
                        "tipo_documento": required_type.value,
                        "estatus": "APROBADO",
                        "version": 2,
                        "nombre_archivo": "ine.pdf",
                    }
                ),
                _FakeDoc(
                    {
                        "id": 2,
                        "archivo_id": 11,
                        "tipo_documento": optional_type.value,
                        "estatus": "PENDIENTE_REVISION",
                        "version": 1,
                        "nombre_archivo": "constancia.pdf",
                    }
                ),
            ]

    monkeypatch.setattr(expediente_module, "empleado_documento_service", _FakeDocumentoService())

    dummy = _DummyExpedienteState()
    dummy._cargar_documentos_expediente = EmployeeExpedienteStateMixin._cargar_documentos_expediente.__get__(
        dummy,
        _DummyExpedienteState,
    )

    asyncio.run(dummy._cargar_documentos_expediente(88))

    assert dummy.total_requeridos >= 1
    assert dummy.total_aprobados == 1
    assert dummy.total_rechazados == 0
    assert dummy.total_pendientes == dummy.total_requeridos - 1
    assert any(doc["tipo_documento"] == required_type.value for doc in dummy.documentos_obligatorios)
    assert any(doc["tipo_documento"] == optional_type.value for doc in dummy.documentos_opcionales)


def test_handle_upload_documento_autoaprueba_y_recarga(monkeypatch):
    required_type = _primer_tipo(obligatorio=True)
    captured: dict = {}

    class _FakeDocumentoService:
        async def subir_documento(self, *, datos, contenido, nombre_archivo, tipo_mime, auto_aprobar):
            captured["empleado_id"] = datos.empleado_id
            captured["tipo_documento"] = datos.tipo_documento
            captured["subido_por"] = datos.subido_por
            captured["contenido"] = contenido
            captured["nombre_archivo"] = nombre_archivo
            captured["tipo_mime"] = tipo_mime
            captured["auto_aprobar"] = auto_aprobar

    monkeypatch.setattr(expediente_module, "empleado_documento_service", _FakeDocumentoService())

    dummy = _DummyExpedienteState()
    dummy.tipo_documento_subiendo = required_type.value

    asyncio.run(dummy.handle_upload_documento([_FakeUploadFile()]))

    assert captured["empleado_id"] == 88
    assert captured["tipo_documento"] == required_type.value
    assert str(captured["subido_por"]) == "00000000-0000-0000-0000-000000000123"
    assert captured["contenido"] == b"pdf"
    assert captured["nombre_archivo"] == "ine.pdf"
    assert captured["tipo_mime"] == "application/pdf"
    assert captured["auto_aprobar"] is True
    assert dummy.reloads == [88]
    assert dummy.mostrar_modal_subir is False


def test_aprobar_documento_recarga_checklist(monkeypatch):
    captured: dict = {}

    class _FakeDocumentoService:
        async def aprobar_documento(self, *, documento_id: int, revisado_por: str):
            captured["documento_id"] = documento_id
            captured["revisado_por"] = revisado_por

    monkeypatch.setattr(expediente_module, "empleado_documento_service", _FakeDocumentoService())

    dummy = _DummyExpedienteState()

    asyncio.run(dummy.aprobar_documento({"id": 55}))

    assert captured["documento_id"] == 55
    assert captured["revisado_por"] == "00000000-0000-0000-0000-000000000123"
    assert dummy.reloads == [88]


def test_confirmar_rechazo_valida_observacion_minima():
    dummy = _DummyExpedienteState()
    dummy.documento_rechazando_id = 44
    dummy.form_observacion_rechazo = "no"

    asyncio.run(dummy.confirmar_rechazo())

    assert dummy.error_observacion == "La observación debe tener al menos 5 caracteres"
