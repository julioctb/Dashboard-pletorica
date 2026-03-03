"""
Utilidades compartidas de navegación y permisos para el módulo de Nóminas.
"""
import reflex as rx

from app.presentation.components.shared.auth_state import AuthState


class NominaBaseState(AuthState):
    """Base compartida para nómina en backoffice y portal."""

    @rx.var
    def nomina_base_path(self) -> str:
        ruta = self.router.route_id or ""
        if ruta.startswith("/portal/nominas"):
            return "/portal/nominas"
        return "/nominas"

    @rx.var
    def nomina_preparacion_path(self) -> str:
        return self.nomina_base_path + "/preparacion"

    @rx.var
    def nomina_calculo_path(self) -> str:
        return self.nomina_base_path + "/calculo"

    @rx.var
    def nomina_detalle_path(self) -> str:
        return self.nomina_base_path + "/empleado-detalle"

    @rx.var
    def nomina_dashboard_path(self) -> str:
        return self.nomina_base_path + "/dashboard"

    @rx.var
    def nomina_conciliacion_path(self) -> str:
        return self.nomina_base_path + "/conciliacion"

    @rx.var
    def nomina_no_access_path(self) -> str:
        ruta = self.router.route_id or ""
        if ruta.startswith("/portal/nominas"):
            return "/portal"
        return "/admin"
