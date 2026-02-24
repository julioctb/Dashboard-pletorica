"""
State base del portal de cliente.

Hereda de AuthState y agrega verificacion de rol client,
acceso a la empresa activa, y carga de metricas del dashboard.
"""
import reflex as rx
import logging
from typing import List, Optional

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
            return

        try:
            # Empleados activos
            self.total_empleados = await empleado_service.contar(
                empresa_id=self.id_empresa_actual,
                estatus="ACTIVO",
            )

            # Contratos activos
            contratos = await contrato_service.obtener_por_empresa(
                self.id_empresa_actual,
                incluir_inactivos=False,
            )
            self.total_contratos = len(contratos)

            # Plazas: sumar de todos los contratos
            from app.services import plaza_service
            ocupadas = 0
            vacantes = 0
            for contrato in contratos:
                try:
                    resumen = await plaza_service.calcular_totales_contrato(contrato.id)
                    ocupadas += resumen.plazas_ocupadas
                    vacantes += resumen.plazas_vacantes
                except Exception:
                    pass
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
    def total_plazas(self) -> int:
        return self.total_plazas_ocupadas + self.total_plazas_vacantes
