# core/config/routes.py
from typing import Dict, List

class RouteConfig:
    # Rutas base para Backoffice
    BACKOFFICE_BASE = ""
    PORTAL_BASE = "/portal"
    
    # Rutas de Backoffice (sin prefijo)
    BACKOFFICE_ROUTES = {
        "nominas": "/nominas",
        "nominas_preparacion": "/nominas/preparacion",
        "asistencias": "/asistencias",
        "asistencias_registro": "/asistencias/registro",
        "empleados": "/empleados",
        "empleados_registro": "/empleados/registro",
        "departamentos": "/departamentos",
    }
    
    # Rutas de Portal (con prefijo)
    PORTAL_ROUTES = {
        "nominas": "/portal/nominas",
        "nominas_preparacion": "/portal/nominas/preparacion",
        "asistencias": "/portal/asistencias",
        "asistencias_registro": "/portal/asistencias/registro",
        "empleados": "/portal/empleados",
        "empleados_registro": "/portal/empleados/registro",
        "departamentos": "/portal/departamentos",
    }
    
    # Rutas completas para uso directo
    ALL_ROUTES = {
        **BACKOFFICE_ROUTES,
        **PORTAL_ROUTES
    }
    
    @classmethod
    def get_backoffice_route(cls, route_key: str) -> str:
        return cls.BACKOFFICE_ROUTES.get(route_key, "")
    
    @classmethod
    def get_portal_route(cls, route_key: str) -> str:
        return cls.PORTAL_ROUTES.get(route_key, "")
    
    @classmethod
    def get_route(cls, route_key: str, is_portal: bool = False) -> str:
        if is_portal:
            return cls.PORTAL_ROUTES.get(route_key, "")
        return cls.BACKOFFICE_ROUTES.get(route_key, "")
