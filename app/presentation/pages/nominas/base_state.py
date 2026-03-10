"""
Utilidades compartidas de navegación y permisos para el módulo de Nóminas.
"""
import reflex as rx

from app.presentation.components.shared.auth_state import AuthState
from app.services import empresa_service


class NominaBaseState(AuthState):
    """Base compartida para nómina en backoffice y portal."""

    async def validar_contexto_nomina(
        self,
        *,
        requiere_contabilidad: bool = False,
    ):
        """Valida login, rol, empresa activa y habilitación del módulo."""
        if self.requiere_login and not self.esta_autenticado:
            return rx.redirect("/login")

        if requiere_contabilidad:
            if not self.puede_acceder_nomina_contabilidad:
                return rx.redirect(self.nomina_no_access_path)
        elif not self.puede_acceder_nomina:
            return rx.redirect(self.nomina_no_access_path)

        if not self.id_empresa_actual:
            return self.crear_toast(
                "Selecciona una empresa para gestionar nóminas",
                "error",
            )

        try:
            empresa = await empresa_service.obtener_por_id(self.id_empresa_actual)
        except Exception:
            return rx.redirect(self.nomina_no_access_path)

        if not bool(getattr(empresa, "gestion_nomina_activa", False)):
            return rx.redirect(self.nomina_no_access_path)
        return None

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
