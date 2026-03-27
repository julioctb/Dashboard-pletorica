"""
State base del portal de cliente.

Hereda de AuthState y agrega verificacion de rol client,
acceso a la empresa activa, y carga de metricas del dashboard.
"""
import reflex as rx
import logging

from app.presentation.components.shared.auth_state import AuthState
from app.modules.application import empresa_service, contrato_service
from app.modules.empleados.application import empleado_service
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
    total_empleados_dashboard: int = 0
    total_contratos: int = 0
    total_plazas_ocupadas: int = 0
    total_plazas_vacantes: int = 0
    plazas_minimas: int = 0
    plazas_maximas: int = 0
    tiene_contratos_con_personal: bool = False
    primer_contrato_con_personal_id: int = 0
    gestion_nomina_activa_empresa: bool = False
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
            return self.crear_toast(
                "No tienes una empresa asignada. Contacta al administrador.",
                "error",
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
        self.primer_contrato_con_personal_id = 0
        self.gestion_nomina_activa_empresa = False

        if self.es_empleado_portal or not self.id_empresa_actual:
            return

        try:
            empresa = await empresa_service.obtener_por_id(self.id_empresa_actual)
            self.gestion_nomina_activa_empresa = bool(
                getattr(empresa, "gestion_nomina_activa", False)
            )
            contratos = await self._obtener_contratos_activos_empresa()
            self.total_contratos = len(contratos)
            contratos_con_personal = [
                contrato
                for contrato in contratos
                if self._contrato_tiene_personal(contrato)
            ]
            self.tiene_contratos_con_personal = bool(contratos_con_personal)
            if contratos_con_personal:
                primer_contrato = contratos_con_personal[0]
                if isinstance(primer_contrato, dict):
                    self.primer_contrato_con_personal_id = int(
                        primer_contrato.get("id") or 0
                    )
                else:
                    self.primer_contrato_con_personal_id = int(
                        getattr(primer_contrato, "id", 0) or 0
                    )
        except Exception as e:
            logger.error("Error cargando contexto del portal: %s", e)
            self.total_contratos = 0
            self.tiene_contratos_con_personal = False
            self.primer_contrato_con_personal_id = 0
            self.gestion_nomina_activa_empresa = False

    async def cambiar_empresa_portal(self, empresa_id_str: str):
        """
        Cambia la empresa activa desde el selector del sidebar.

        El select entrega string; se convierte a int y luego delega al
        metodo heredado de AuthState. El shell del portal se remonta cuando
        cambia `id_empresa_actual`, por lo que la página visible vuelve a
        ejecutar su `on_mount` sin tener que redirigir a la misma ruta.
        """
        if not empresa_id_str:
            return

        try:
            empresa_id = int(empresa_id_str)
        except (TypeError, ValueError):
            return self.crear_toast("ID de empresa invalido", "error")

        if empresa_id == self.id_empresa_actual:
            return

        resultado = await self.cambiar_empresa(empresa_id)

        # Si el cambio no ocurrio, propagar el resultado actual (ej. acceso denegado).
        if self.id_empresa_actual != empresa_id:
            return resultado

        await self._cargar_contexto_portal_empresa()

        try:
            from app.modules.application import user_service

            user_id = self.obtener_uuid_usuario_actual()
            if user_id:
                await user_service.cambiar_empresa_principal(user_id, empresa_id)
        except Exception as e:
            logger.warning(f"No se pudo persistir cambio de empresa: {e}")

        return resultado

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
            self.total_empleados_dashboard = 0
            self.total_contratos = 0
            self.total_plazas_ocupadas = 0
            self.total_plazas_vacantes = 0
            self.plazas_minimas = 0
            self.plazas_maximas = 0
            self.tiene_contratos_con_personal = False
            self.primer_contrato_con_personal_id = 0
            return

        try:
            # Empleados activos
            self.total_empleados_dashboard = await empleado_service.contar(
                empresa_id=self.id_empresa_actual,
                estatus="ACTIVO",
            )

            # Contratos activos
            contratos = await self._obtener_contratos_activos_empresa()
            self.total_contratos = len(contratos)
            contratos_con_personal = [
                contrato
                for contrato in contratos
                if self._contrato_tiene_personal(contrato)
            ]
            self.tiene_contratos_con_personal = bool(contratos_con_personal)
            if contratos_con_personal:
                primer_contrato = contratos_con_personal[0]
                if isinstance(primer_contrato, dict):
                    self.primer_contrato_con_personal_id = int(
                        primer_contrato.get("id") or 0
                    )
                else:
                    self.primer_contrato_con_personal_id = int(
                        getattr(primer_contrato, "id", 0) or 0
                    )
            else:
                self.primer_contrato_con_personal_id = 0

            # Plazas: batch via resumen de contratos (sin N+1)
            from app.modules.application import plaza_service
            resumen_contratos = await plaza_service.obtener_resumen_contratos_con_plazas(
                empresa_id=self.id_empresa_actual,
                solo_activos=True,
            )
            self.total_plazas_ocupadas = sum(r.get("plazas_ocupadas", 0) for r in resumen_contratos)
            self.total_plazas_vacantes = sum(r.get("plazas_vacantes", 0) for r in resumen_contratos)
            self.plazas_minimas = sum(r.get("cantidad_plazas_minima", 0) for r in resumen_contratos)
            self.plazas_maximas = sum(r.get("cantidad_plazas_maxima", 0) for r in resumen_contratos)

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
    def mostrar_seccion_plazas_portal(self) -> bool:
        return self.es_usuario_empresa_portal and self.tiene_contratos_con_personal and (
            self.puede_gestionar_personal
            or self.puede_registrar_personal
        )

    @rx.var
    def mostrar_seccion_nominas(self) -> bool:
        return (
            self.es_usuario_empresa_portal
            and self.puede_acceder_rrhh
            and self.gestion_nomina_activa_empresa
        )

    @rx.var
    def mostrar_seccion_contabilidad(self) -> bool:
        return (
            self.es_usuario_empresa_portal
            and self.puede_acceder_nomina_contabilidad
            and self.gestion_nomina_activa_empresa
        )

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
    def ruta_plazas_principal(self) -> str:
        contrato_id = int(self.primer_contrato_con_personal_id or 0)
        if contrato_id > 0:
            return f"/portal/contratos/{contrato_id}/plazas"
        return "/portal/contratos"

    @rx.var
    def ruta_entregables_principal(self) -> str:
        return "/portal/entregables"

    @rx.var
    def ruta_rrhh_principal(self) -> str:
        if not self.mostrar_seccion_rrhh:
            return "/portal"
        if self.puede_gestionar_personal or self.puede_registrar_personal:
            return "/portal/empleados"
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

    async def redirigir_a_portal_plazas(self):
        """Envía la entrada global de plazas al primer contrato con personal."""
        resultado = await self.on_mount_portal()
        if resultado:
            return resultado

        puede_ver_plazas = (
            self.es_usuario_empresa_portal
            and self.tiene_contratos_con_personal
            and (self.puede_gestionar_personal or self.puede_registrar_personal)
        )
        if not puede_ver_plazas:
            return rx.redirect("/portal/contratos", replace=True)
        return rx.redirect(self.ruta_plazas_principal, replace=True)
