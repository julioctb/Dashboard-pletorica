"""Middleware de la API."""
from app.api.middleware.auth import AuthMiddleware

__all__ = ["AuthMiddleware"]
