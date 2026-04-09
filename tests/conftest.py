"""Global pytest config for deterministic offline test runs."""

from __future__ import annotations

import os
import socket
from typing import Any

import pytest


# Keep test imports stable even when the developer has no .env loaded.
OFFLINE_ENV_DEFAULTS = {
    "SUPABASE_URL": "http://localhost",
    "SUPABASE_KEY": "test-key",
    "SUPABASE_SERVICE_KEY": "test-service-key",
    "SKIP_AUTH": "true",
}
for env_key, env_value in OFFLINE_ENV_DEFAULTS.items():
    os.environ.setdefault(env_key, env_value)

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _normalize_host(address: Any) -> str:
    if isinstance(address, tuple) and address:
        host = address[0]
    else:
        host = address

    if isinstance(host, bytes):
        host = host.decode("utf-8", errors="ignore")

    return str(host or "")


def _allow_address(address: Any) -> bool:
    host = _normalize_host(address)
    return host in LOCAL_HOSTS or host.startswith("/")


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch: pytest.MonkeyPatch):
    """Block outbound internet calls while still allowing localhost sockets."""
    original_connect = socket.socket.connect
    original_create_connection = socket.create_connection

    def guarded_connect(sock: socket.socket, address):
        if not _allow_address(address):
            raise RuntimeError(
                f"Prueba offline: conexion externa bloqueada hacia '{_normalize_host(address)}'"
            )
        return original_connect(sock, address)

    def guarded_create_connection(address, *args, **kwargs):
        if not _allow_address(address):
            raise RuntimeError(
                f"Prueba offline: create_connection bloqueada hacia '{_normalize_host(address)}'"
            )
        return original_create_connection(address, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)
