"""Paquete principal de la aplicacion Reflex."""

from typing import Any

__all__ = ["app"]


class _LazyAppProxy:
    """Lazy proxy that resolves the Reflex app only when accessed."""

    _instance: Any = None

    def _resolve(self):
        if self._instance is None:
            from app.app import app as reflex_app

            self._instance = reflex_app
        return self._instance

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)


app = _LazyAppProxy()
