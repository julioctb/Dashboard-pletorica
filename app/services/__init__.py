"""
Services - Business logic layer
All services in one place for easy discovery
"""
from .empresa_service import EmpresaService, empresa_service

__all__ = [
    'EmpresaService',
    'empresa_service',
]
