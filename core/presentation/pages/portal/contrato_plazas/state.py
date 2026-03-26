"""State de plazas por contrato en portal."""

from __future__ import annotations

import logging

import reflex as rx

from core.core.enums import EstatusPlaza
from core.core.exceptions import BusinessRuleError, NotFoundError
from core.presentation.pages.backoffice.contratos.contrato_presentacion import (
    enriquecer_contrato_presentacion,
)
from core.presentation.pages.portal.mis_empleados.state import (
    MisEmpleadosState,
    VISTA_PERSONAL_PLAZA,
)
from core.domain.services import contrato_service

logger = logging.getLogger(__name__)


class ContratoPlazasState(MisEmpleadosState):
    """Vista portal de plazas ligada a un contrato especifico."""

    contrato_actual_portal: dict = {}

    def _ruta_actual(self) -> str:
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

        return path.split("?", maxsplit=1)[0]

    def _obtener_contrato_id_ruta(self) -> int:
        raw_contrato_id = ""

        try:
            raw = getattr(self, "id", None)
            if raw is not None and callable(raw) is False:
                raw_contrato_id = str(raw).strip()
        except Exception:
            raw_contrato_id = ""

        if not raw_contrato_id:
            router_data = self.router_data or {}
            posibles_ids = [
                (router_data.get("query", {}) or {}).get("id", ""),
                (router_data.get("params", {}) or {}).get("id", ""),
                (router_data.get("path_params", {}) or {}).get("id", ""),
                (router_data.get("kwargs", {}) or {}).get("id", ""),
                (router_data.get("query", {}) or {}).get("contrato_id", ""),
                (router_data.get("params", {}) or {}).get("contrato_id", ""),
                (router_data.get("path_params", {}) or {}).get("contrato_id", ""),
                (router_data.get("kwargs", {}) or {}).get("contrato_id", ""),
            ]
            for raw_id in posibles_ids:
                raw_contrato_id = str(raw_id or "").strip()
                if raw_contrato_id:
                    break

        if not raw_contrato_id:
            path = self._ruta_actual()
            partes = [segmento for segmento in path.strip("/").split("/") if segmento]
            if (
                len(partes) >= 4
                and partes[0] == "portal"
                and partes[1] == "contratos"
                and partes[3] == "plazas"
            ):
                raw_contrato_id = str(partes[2] or "").strip()

        try:
            return int(raw_contrato_id)
        except (TypeError, ValueError):
            return 0

    async def _cargar_contrato_actual_portal(self, contrato_id: int) -> None:
        contrato = await contrato_service.obtener_por_id(contrato_id)
        contrato_empresa_id = int(getattr(contrato, "empresa_id", 0) or 0)
        if not self.id_empresa_actual or contrato_empresa_id != int(self.id_empresa_actual):
            raise BusinessRuleError("Solo puedes consultar plazas de contratos de la empresa activa")
        if not bool(getattr(contrato, "tiene_personal", False)):
            raise BusinessRuleError("Este contrato no tiene plazas configurables en portal")
        self.contrato_actual_portal = enriquecer_contrato_presentacion(contrato)

    async def on_mount_contrato_plazas(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return

        if not self.mostrar_seccion_plazas_portal:
            yield rx.redirect("/portal")
            return

        contrato_id = self._obtener_contrato_id_ruta()
        if contrato_id <= 0:
            yield rx.redirect("/portal/contratos")
            return

        try:
            await self._cargar_contrato_actual_portal(contrato_id)
        except NotFoundError:
            yield rx.toast.error("Contrato no encontrado")
            yield rx.redirect("/portal/contratos")
            return
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
            yield rx.redirect("/portal/contratos")
            return
        except Exception as e:
            logger.error("Error cargando contrato portal %s: %s", contrato_id, e)
            yield rx.toast.error("No se pudo abrir la sección de plazas")
            yield rx.redirect("/portal/contratos")
            return

        self.vista_personal = VISTA_PERSONAL_PLAZA
        self.filtro_contrato_id = str(contrato_id)
        self.contrato_expandido_plaza_id = contrato_id
        self._reset_filtros_internos_plaza()

        async for _ in self._montar_pagina(self._fetch_empleados):
            yield

    def _resumen_plazas_actuales(self) -> dict[str, int]:
        plazas = list(self.plazas_contrato_expandido or [])
        total_plazas = len(plazas)
        plazas_ocupadas = sum(
            1 for plaza in plazas
            if str(plaza.get("estatus", "") or "") == EstatusPlaza.OCUPADA.value
        )
        plazas_vacantes = sum(
            1 for plaza in plazas
            if str(plaza.get("estatus", "") or "") == EstatusPlaza.VACANTE.value
        )
        plazas_suspendidas = sum(
            1 for plaza in plazas
            if str(plaza.get("estatus", "") or "") == EstatusPlaza.SUSPENDIDA.value
        )
        total_sedes = len(
            {
                int(plaza.get("sede_id") or 0)
                for plaza in plazas
                if int(plaza.get("sede_id") or 0) > 0
            }
        )
        return {
            "total_plazas": total_plazas,
            "plazas_ocupadas": plazas_ocupadas,
            "plazas_vacantes": plazas_vacantes,
            "plazas_suspendidas": plazas_suspendidas,
            "total_sedes": total_sedes,
        }

    def _construir_contrato_plaza_contexto(self) -> dict:
        contrato = dict(self.contrato_actual_portal or {})
        contrato_id = int(contrato.get("id") or self.contrato_expandido_plaza_id or 0)
        if contrato_id <= 0:
            return {}

        activo = dict(self.contrato_plaza_activo or {})
        resumen = self._resumen_plazas_actuales()
        clave = self._clave_contrato(contrato_id)
        seleccion_ids = list(self.seleccion_plazas_por_contrato.get(clave, []) or [])

        total_plazas = int(activo.get("total_plazas") or resumen["total_plazas"])
        plazas_ocupadas = int(activo.get("plazas_ocupadas") or resumen["plazas_ocupadas"])
        plazas_vacantes = int(activo.get("plazas_vacantes") or resumen["plazas_vacantes"])
        plazas_suspendidas = int(
            activo.get("plazas_suspendidas") or resumen["plazas_suspendidas"]
        )
        total_sedes = int(activo.get("total_sedes") or resumen["total_sedes"])

        return {
            "contrato_id": contrato_id,
            "contrato_codigo": str(
                activo.get("contrato_codigo")
                or contrato.get("codigo")
                or "Sin contrato"
            ),
            "contrato_estatus": str(
                contrato.get("estatus")
                or activo.get("contrato_estatus")
                or ""
            ),
            "tipo_servicio_nombre": str(
                activo.get("tipo_servicio_nombre")
                or contrato.get("nombre_servicio_fmt")
                or ""
            ),
            "total_plazas": total_plazas,
            "plazas_ocupadas": plazas_ocupadas,
            "plazas_vacantes": plazas_vacantes,
            "plazas_suspendidas": plazas_suspendidas,
            "total_sedes": total_sedes,
            "tiene_plazas": total_plazas > 0,
            "resumen_plazas": self._texto_resumen_plazas_sedes(total_plazas, total_sedes),
            "seleccion_ids": seleccion_ids,
            "seleccion_count": len(seleccion_ids),
            "tiene_seleccion": len(seleccion_ids) > 0,
            "seleccion_label": self._texto_resumen_cantidad(
                len(seleccion_ids),
                "plaza seleccionada",
                "plazas seleccionadas",
            ),
            "seleccion_todas_visibles": self.seleccion_todas_plazas_visibles_actual,
            "sede_masiva_value": str(self.sedes_masivas_por_contrato.get(clave, "") or ""),
            "categoria_masiva_value": str(
                self.categorias_masivas_por_contrato.get(clave, "") or ""
            ),
            "opciones_categorias_masivas": self._opciones_categoria_masiva_contrato(clave),
            "mostrar_badge_suspendidas": plazas_suspendidas > 0,
        }

    @rx.var
    def contrato_plaza_contexto(self) -> dict:
        return self._construir_contrato_plaza_contexto()

    @rx.var
    def tiene_contrato_plaza_contexto(self) -> bool:
        return bool(self.contrato_plaza_contexto)

    @rx.var
    def breadcrumb_items(self) -> list[dict]:
        return [
            {"texto": "Portal", "href": "/portal"},
            {"texto": "Contratos", "href": "/portal/contratos"},
            {"texto": "Plazas", "href": ""},
        ]

    @rx.var
    def codigo_contrato_actual(self) -> str:
        return str(
            self.contrato_plaza_contexto.get("contrato_codigo")
            or self.contrato_actual_portal.get("codigo")
            or ""
        )

    @rx.var
    def descripcion_contrato_actual(self) -> str:
        return str(
            self.contrato_actual_portal.get("descripcion_objeto_display")
            or "Configuracion y operacion de plazas por contrato"
        )

    @rx.var
    def tipo_servicio_contrato_actual(self) -> str:
        return str(
            self.contrato_plaza_contexto.get("tipo_servicio_nombre")
            or self.contrato_actual_portal.get("nombre_servicio_fmt")
            or ""
        )

    @rx.var
    def estatus_contrato_actual(self) -> str:
        return str(
            self.contrato_plaza_contexto.get("contrato_estatus")
            or self.contrato_actual_portal.get("estatus")
            or ""
        )

    @rx.var
    def total_plazas_contrato_actual(self) -> int:
        return int(self.contrato_plaza_contexto.get("total_plazas") or 0)

    @rx.var
    def plazas_ocupadas_contrato_actual(self) -> int:
        return int(self.contrato_plaza_contexto.get("plazas_ocupadas") or 0)

    @rx.var
    def plazas_vacantes_contrato_actual(self) -> int:
        return int(self.contrato_plaza_contexto.get("plazas_vacantes") or 0)

    @rx.var
    def plazas_suspendidas_contrato_actual(self) -> int:
        return int(self.contrato_plaza_contexto.get("plazas_suspendidas") or 0)
