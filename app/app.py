"""Legacy entrypoint compatibility shim for ``from app.app import app``."""

from core.app import app

__all__ = ["app"]
