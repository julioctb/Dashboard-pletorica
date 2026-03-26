"""Middleware de la API."""
from core.api.middleware.auth import AuthMiddleware

__all__ = ["AuthMiddleware"]
