"""
State base del portal de cliente.

Hereda de AuthState y agrega verificacion de rol client,
acceso a la empresa activa, y carga de metricas del dashboard.
"""
import reflex as rx
import logging

from app.presentation.components.shared.auth_state import AuthState
from app.services import empresa_service, empleado_service, contrato_service
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class PortalState(AuthState):
    """
    State base para todas las paginas del portal de cliente.

    Proporciona:
    - Verificacion de rol client en on_mount
    - Redireccion a backoffice si es admin
    - Acceso rapido a empresa_id del usuario
    - Metricas del dashboard
    """

    # ========================
    # DATOS DE LA EMPRESA
    # ========================
    datos_empresa: dict = {}

    # ========================
    # METRICAS DEL DASHBOARD
    # ========================
    total_empleados: int = 0
    total_contratos: int = 0
    total_plazas_ocupadas: int = 0
    total_plazas_vacantes: int = 0
    tiene_contratos_con_personal: bool = False
    metricas_cargadas: bool = False

    # ========================
    # MONTAJE DEL PORTAL
    # ========================
    async def on_mount_portal(self):
        """
        Verificar que es usuario client y tiene empresa asignada.
        Llamar en on_mount de cada pagina del portal.
        """
        resultado = await self.verificar_y_redirigir()
        if resultado:
            return resultado

        # Si es admin, redirigir al backoffice
        if self.es_admin:
            return rx.redirect("/")

        # Si no tiene empresa asignada (empleados se vinculan por user_id, no user_companies)
        if not self.es_empleado_portal and not self.id_empresa_actual:
            return rx.toast.error(
                "No tienes una empresa asignada. Contacta al administrador.",
                position="top-center",
            )

        await self._cargar_contexto_portal_empresa()

    @staticmethod
    def _contrato_tiene_personal(contrato) -> bool:
        """Normaliza la bandera `tiene_personal` para modelos y dicts."""
        if isinstance(contrato, dict):
            return bool(contrato.get("tiene_personal"))
        return bool(getattr(contrato, "tiene_personal", False))

    async def _obtener_contratos_activos_empresa(self) -> list:
        """Obtiene contratos activos de la empresa actual."""
        if not self.id_empresa_actual:
            return []
        return await contrato_service.obtener_por_empresa(
            self.id_empresa_actual,
            incluir_inactivos=False,
        )

    async def _cargar_contexto_portal_empresa(self):
        """Carga señales mínimas que usa la navegación del portal."""
        self.total_contratos = 0
        self.tiene_contratos_con_personal = False

        if self.es_empleado_portal or not self.id_empresa_actual:
            return

        try:
            contratos = await self._obtener_contratos_activos_empresa()
            self.total_contratos = len(contratos)
            self.tiene_contratos_con_personal = any(
                self._contrato_tiene_personal(contrato)
                for contrato in contratos
            )
        except Exception as e:
            logger.error("Error cargando contexto del portal: %s", e)
            self.total_contratos = 0
            self.tiene_contratos_con_personal = False

    async def cambiar_empresa_portal(self, empresa_id_str: str):
        """
        Cambia la empresa activa desde el selector del sidebar.

        El select entrega string; se convierte a int y luego delega al
        metodo heredado de AuthState. Al final redirige a la ruta actual
        para re-ejecutar on_mount y recargar datos de la nueva empresa.
        """
        if not empresa_id_str:
            return

        try:
            empresa_id = int(empresa_id_str)
        except (TypeError, ValueError):
            return rx.toast.error("ID de empresa invalido")

        if empresa_id == self.id_empresa_actual:
            return

        resultado = await self.cambiar_empresa(empresa_id)

        # Si el cambio no ocurrio, propagar el resultado actual (ej. acceso denegado).
        if self.id_empresa_actual != empresa_id:
            return resultado

        try:
            from app.services import user_service

            user_id = self.obtener_uuid_usuario_actual()
            if user_id:
                await user_service.cambiar_empresa_principal(user_id, empresa_id)
        except Exception as e:
            logger.warning(f"No se pudo persistir cambio de empresa: {e}")

        ruta_actual = self.router.route_id or "/portal"
        if resultado:
            return [resultado, rx.redirect(ruta_actual)]
        return rx.redirect(ruta_actual)

    async def _montar_pagina_portal(self, *operaciones):
        """
        _montar_pagina con verificacion de portal (auth + rol + empresa).

        Verifica auth y rol primero. Si falla, redirige.
        Si pasa, delega a _montar_pagina para skeleton + fetch.

        Uso:
            async def on_mount(self):
                async for _ in self._montar_pagina_portal(
                    self._fetch_datos,
                ):
                    yield
        """
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return

        async for _ in self._montar_pagina(*operaciones):
            yield

    async def on_mount_dashboard(self):
        """Montaje del dashboard: verificar auth + cargar metricas."""
        async for _ in self._montar_pagina_portal(self._fetch_metricas):
            yield

    # ========================
    # CARGA DE DATOS
    # ========================
    async def cargar_datos_empresa(self):
        """Carga los datos completos de la empresa activa."""
        if not self.id_empresa_actual:
            return
        try:
            empresa = await empresa_service.obtener_por_id(self.id_empresa_actual)
            datos = empresa.model_dump(mode='json')
            if empresa.prima_riesgo is not None:
                datos["prima_riesgo"] = f"{empresa.get_prima_riesgo_porcentaje()}%"
            self.datos_empresa = datos
        except Exception as e:
            logger.error(f"Error cargando datos de empresa: {e}")
            self.datos_empresa = {}

    async def _fetch_metricas(self):
        """Carga metricas rapidas para el dashboard (sin manejo de loading)."""
        if not self.id_empresa_actual:
            self.total_empleados = 0
            self.total_contratos = 0
            self.total_plazas_ocupadas = 0
            self.total_plazas_vacantes = 0
            self.tiene_contratos_con_personal = False
            return

        try:
            # Empleados activos
            self.total_empleados = await empleado_service.contar(
                empresa_id=self.id_empresa_actual,
                estatus="ACTIVO",
            )

            # Contratos activos
            contratos = await self._obtener_contratos_activos_empresa()
            self.total_contratos = len(contratos)
            self.tiene_contratos_con_personal = any(
                self._contrato_tiene_personal(contrato)
                for contrato in contratos
            )

            # Plazas: sumar de todos los contratos
            from app.services import plaza_service
            ocupadas = 0
            vacantes = 0
            for contrato in contratos:
                try:
                    resumen = await plaza_service.calcular_totales_contrato(contrato.id)
                    ocupadas += resumen.plazas_ocupadas
                    vacantes += resumen.plazas_vacantes
                except Exception as e:
                    logger.debug(
                        "Error calculando métricas de plazas para contrato %s: %s",
                        contrato.id,
                        e,
                    )
            self.total_plazas_ocupadas = ocupadas
            self.total_plazas_vacantes = vacantes

            self.metricas_cargadas = True
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando metricas: {e}", "error")
        except Exception as e:
            logger.error(f"Error cargando metricas del portal: {e}")

    # ========================
    # PROPIEDADES DE CONVENIENCIA
    # ========================
    @rx.var
    def empresa_id(self) -> int:
        """ID de la empresa del usuario (shortcut)."""
        return self.id_empresa_actual

    @rx.var
    def es_usuario_empresa_portal(self) -> bool:
        """Usuario portal vinculado a una empresa distinta al autoservicio."""
        return bool(self.id_empresa_actual) and not self.es_empleado_portal

    @rx.var
    def mostrar_seccion_contrato(self) -> bool:
        return self.es_usuario_empresa_portal

    @rx.var
    def mostrar_seccion_entregables(self) -> bool:
        return self.es_usuario_empresa_portal and (
            self.es_operaciones or self.es_contabilidad or self.es_admin_empresa
        )

    @rx.var
    def mostrar_seccion_rrhh(self) -> bool:
        return self.es_usuario_empresa_portal and self.tiene_contratos_con_personal and (
            self.puede_gestionar_personal
            or self.puede_registrar_personal
            or self.es_operaciones
        )

    @rx.var
    def mostrar_seccion_nominas(self) -> bool:
        return self.es_usuario_empresa_portal and self.puede_acceder_nomina

    @rx.var
    def mostrar_seccion_empresa(self) -> bool:
        return self.es_usuario_empresa_portal

    @rx.var
    def mostrar_seccion_autoservicio(self) -> bool:
        return self.es_empleado_portal

    @rx.var
    def ruta_contrato_principal(self) -> str:
        return "/portal/contratos"

    @rx.var
    def ruta_entregables_principal(self) -> str:
        return "/portal/entregables"

    @rx.var
    def ruta_rrhh_principal(self) -> str:
        if not self.mostrar_seccion_rrhh:
            return "/portal"
        if self.puede_gestionar_personal:
            return "/portal/empleados"
        if self.puede_registrar_personal:
            return "/portal/onboarding"
        if self.es_operaciones:
            return "/portal/asistencias"
        return "/portal"

    @rx.var
    def ruta_nominas_principal(self) -> str:
        return "/portal/nominas"

    @rx.var
    def ruta_empresa_principal(self) -> str:
        return "/portal/mi-empresa"

    @rx.var
    def ruta_autoservicio_principal(self) -> str:
        return "/portal/mis-datos"

    @rx.var
    def total_plazas(self) -> int:
        return self.total_plazas_ocupadas + self.total_plazas_vacantes
