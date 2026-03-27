"""
Capa API REST (FastAPI).

Proporciona endpoints HTTP para integracion con aplicaciones externas (Flutter).
Se monta sobre Reflex usando api_transformer.
"""
from app.api.main import api_app

__all__ = ["api_app"]
