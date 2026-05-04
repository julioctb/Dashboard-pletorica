"""Security regression tests for auth/profile hardening."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.domain.enums import RolPlataforma
from app.domain.models.user_profile import UserProfileCreate
from app.domain.services.user_auth_service import UserAuthService


def test_auth_metadata_excludes_role() -> None:
    datos = UserProfileCreate(
        email="institucion@example.com",
        password="password123",
        nombre_completo="Usuario Institucional",
        rol=RolPlataforma.INSTITUCION,
        telefono="5512345678",
        institucion_id=10,
    )

    metadata = datos.to_auth_metadata()

    assert "rol" not in metadata
    assert metadata["nombre_completo"] == "Usuario Institucional"
    assert metadata["telefono"] == "5512345678"


class _FakeAdminApi:
    def create_user(self, _payload: dict):
        return SimpleNamespace(user=SimpleNamespace(id=str(uuid4())))


class _FakeSupabaseAdmin:
    def __init__(self):
        self.auth = SimpleNamespace(admin=_FakeAdminApi())


class _FakeRoot:
    def __init__(self):
        self.supabase_admin = _FakeSupabaseAdmin()
        self.profile_updates: list[tuple[str, dict]] = []

    async def obtener_por_id(self, user_id):
        return SimpleNamespace(id=user_id)

    def _actualizar_profile_data(self, user_id, payload: dict):
        self.profile_updates.append((str(user_id), payload))

    async def asignar_empresa(self, **_kwargs):
        return None


def test_non_client_role_is_applied_via_backend_profile_update() -> None:
    root = _FakeRoot()
    service = UserAuthService(root)
    datos = UserProfileCreate(
        email="admin@example.com",
        password="password123",
        nombre_completo="Admin Seguro",
        rol=RolPlataforma.ADMIN,
    )

    asyncio.run(service.crear_usuario(datos))

    assert any(payload == {"rol": "admin"} for _, payload in root.profile_updates)
