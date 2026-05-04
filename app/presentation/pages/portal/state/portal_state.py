"""
State base del portal de cliente.

Hereda de AuthState y agrega verificacion de rol client,
acceso a la empresa activa, y carga de metricas del dashboard.
"""
import logging

import reflex as rx

from app.core.exceptions import DatabaseError
from app.core.text_utils import normalizar_mayusculas
from app.domain.enums import EstatusContrato
from app.modules.application import contrato_service, empresa_service, plaza_service
from app.modules.empleados.application import empleado_service
from app.presentation.components.shared.auth_state import AuthState

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
    tiene_contratos_configurados: bool = False
    tiene_contratos_con_personal: bool = False
    tiene_plazas_configuradas: bool = False
    tiene_empleados_asignados: bool = False
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
        await self._sincronizar_contexto_portal_global()

    def _copiar_contexto_portal_desde(self, origen: "PortalState") -> None:
        """Replica al estado global solo las señales que consume la navegación."""
        for campo in (
            "total_contratos",
            "tiene_contratos_configurados",
            "tiene_contratos_con_personal",
            "tiene_plazas_configuradas",
            "tiene_empleados_asignados",
            "primer_contrato_con_personal_id",
            "gestion_nomina_activa_empresa",
            "metricas_cargadas",
        ):
            setattr(self, campo, getattr(origen, campo))

    async def _sincronizar_contexto_portal_global(self) -> None:
        """Sincroniza el `PortalState` global sin disparar una recarga tardía del sidebar."""
        try:
            portal_state = await self.get_state(PortalState)
        except Exception:
            return
        if portal_state is self:
            return
        portal_state._copiar_contexto_portal_desde(self)

    @staticmethod
    def _contrato_tiene_personal(contrato) -> bool:
        """Normaliza la bandera `tiene_personal` para modelos y dicts."""
        if isinstance(contrato, dict):
            return bool(contrato.get("tiene_personal"))
        return bool(getattr(contrato, "tiene_personal", False))

    @staticmethod
    def _contrato_estatus(contrato) -> str:
        """Normaliza el estatus del contrato para modelos y dicts."""
        if isinstance(contrato, dict):
            return str(contrato.get("estatus") or "").strip().upper()
        return str(getattr(contrato, "estatus", "") or "").strip().upper()

    async def _obtener_contratos_activos_empresa(self) -> list:
        """Obtiene contratos activos de la empresa actual."""
        if not self.id_empresa_actual:
            return []
        return await contrato_service.obtener_por_empresa(
            self.id_empresa_actual,
            incluir_inactivos=False,
        )

    async def _obtener_contratos_contexto_empresa(self) -> list:
        """Obtiene contratos del contexto portal para progressive disclosure."""
        if not self.id_empresa_actual:
            return []
        return await contrato_service.obtener_por_empresa(
            self.id_empresa_actual,
            incluir_inactivos=True,
        )

    async def _cargar_contexto_portal_empresa(self):
        """Carga señales mínimas que usa la navegación del portal."""
        self.total_contratos = 0
        self.tiene_contratos_configurados = False
        self.tiene_contratos_con_personal = False
        self.tiene_plazas_configuradas = False
        self.tiene_empleados_asignados = False
        self.primer_contrato_con_personal_id = 0
        self.gestion_nomina_activa_empresa = False

        if self.es_empleado_portal or not self.id_empresa_actual:
            return

        try:
            empresa = await empresa_service.obtener_por_id(self.id_empresa_actual)
            self.gestion_nomina_activa_empresa = bool(
                getattr(empresa, "gestion_nomina_activa", False)
            )
            contratos = await self._obtener_contratos_contexto_empresa()
            contratos_configurados = [
                contrato
                for contrato in contratos
                if self._contrato_estatus(contrato) != EstatusContrato.BORRADOR.value
            ]
            self.total_contratos = len(contratos_configurados)
            self.tiene_contratos_configurados = bool(contratos_configurados)
            contratos_con_personal = [
                contrato
                for contrato in contratos_configurados
                if self._contrato_tiene_personal(contrato)
            ]
            self.tiene_contratos_con_personal = bool(contratos_con_personal)
            self.tiene_plazas_configuradas = await plaza_service.tiene_plazas_configuradas(
                self.id_empresa_actual
            )
            self.tiene_empleados_asignados = bool(
                await plaza_service.obtener_empleados_asignados(self.id_empresa_actual)
            )
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
            self.tiene_contratos_configurados = False
            self.tiene_contratos_con_personal = False
            self.tiene_plazas_configuradas = False
            self.tiene_empleados_asignados = False
            self.primer_contrato_con_personal_id = 0
            self.gestion_nomina_activa_empresa = False

    async def refrescar_sidebar(self):
        """
        Recalcula los triggers del sidebar.

        Cuando se invoca desde un estado hijo del portal, sincroniza el
        `PortalState` global que consume el layout.
        """
        await self._cargar_contexto_portal_empresa()
        portal_state = self
        try:
            portal_state = await self.get_state(PortalState)
        except Exception:
            portal_state = self
        if portal_state is self:
            return
        portal_state._copiar_contexto_portal_desde(self)

    async def cambiar_empresa_portal(self, empresa_id_str: str):
        """
        Cambia la empresa activa desde el selector del sidebar.

        El select entrega string; se convierte a int y luego delega al
        metodo heredado de AuthState. Al terminar, se dispara un
        `rx.redirect(ruta_actual, replace=True)` para que la página visible
        vuelva a ejecutar su `on_mount` con el nuevo contexto. Antes esto se
        lograba remontando el shell vía `key=id_empresa_actual`, pero eso
        causaba doble mount en la hidratación inicial.
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

        ruta_actual = self._ruta_actual_portal()
        eventos: list = [resultado] if resultado is not None else []
        if ruta_actual:
            eventos.append(rx.redirect(ruta_actual, replace=True))
        return eventos or None

    def _ruta_actual_portal(self) -> str:
        """Devuelve la ruta actual del portal (sin querystring)."""
        try:
            path = str(getattr(getattr(self.router, "url", None), "path", "") or "").strip()
        except Exception:
            path = ""
        if not path:
            router_data = self.router_data or {}
            path = str(
                router_data.get("asPath")
                or router_data.get("pathname")
                or "",
            ).strip()
        path = path.split("?", maxsplit=1)[0]
        return path or "/portal"

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
            self.tiene_contratos_configurados = False
            self.tiene_contratos_con_personal = False
            self.tiene_plazas_configuradas = False
            self.tiene_empleados_asignados = False
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
    def mostrar_herramientas(self) -> bool:
        """Trigger 0.1: solo admin_empresa."""
        return self.es_usuario_empresa_portal and self.es_admin_empresa

    @rx.var
    def mostrar_entregables(self) -> bool:
        """Trigger 1: existe al menos un contrato configurado."""
        return self.es_usuario_empresa_portal and self.tiene_contratos_configurados and (
            self.es_operaciones or self.es_contabilidad or self.es_admin_empresa
        )

    @rx.var
    def mostrar_plazas(self) -> bool:
        """Trigger 2: existe al menos un contrato configurado con personal."""
        return self.es_usuario_empresa_portal and self.tiene_contratos_con_personal and (
            self.puede_gestionar_personal
            or self.puede_registrar_personal
        )

    @rx.var
    def mostrar_personal(self) -> bool:
        """Trigger 3: existe al menos una plaza con sueldo y sede."""
        return self.es_usuario_empresa_portal and self.tiene_plazas_configuradas and (
            self.puede_gestionar_personal
            or self.puede_registrar_personal
            or self.es_operaciones
        )

    @rx.var
    def mostrar_nomina(self) -> bool:
        """Trigger 4: existe al menos un empleado asignado a una plaza."""
        return (
            self.es_usuario_empresa_portal
            and self.tiene_empleados_asignados
            and self.gestion_nomina_activa_empresa
            and (
                self.puede_acceder_rrhh
                or self.puede_acceder_nomina_contabilidad
            )
        )

    @rx.var
    def mostrar_seccion_contrato(self) -> bool:
        return self.es_usuario_empresa_portal

    @rx.var
    def mostrar_seccion_entregables(self) -> bool:
        return self.mostrar_entregables

    @rx.var
    def mostrar_seccion_rrhh(self) -> bool:
        return self.mostrar_personal

    @rx.var
    def mostrar_seccion_plazas_portal(self) -> bool:
        return self.mostrar_plazas

    @rx.var
    def mostrar_seccion_nominas(self) -> bool:
        return (
            self.es_usuario_empresa_portal
            and self.tiene_empleados_asignados
            and self.puede_acceder_rrhh
            and self.gestion_nomina_activa_empresa
        )

    @rx.var
    def mostrar_seccion_contabilidad(self) -> bool:
        return (
            self.es_usuario_empresa_portal
            and self.tiene_empleados_asignados
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

    @staticmethod
    def construir_ruta_plazas_contrato(codigo_contrato: str | int) -> str:
        codigo = normalizar_mayusculas(str(codigo_contrato or ""))
        return f"/portal/contratos/{codigo}/plazas" if codigo else "/portal/contratos"

    @rx.var
    def ruta_plazas_principal(self) -> str:
        return self.ruta_contrato_principal

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
        """Redirige la ruta legacy de plazas al módulo de contratos."""
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
