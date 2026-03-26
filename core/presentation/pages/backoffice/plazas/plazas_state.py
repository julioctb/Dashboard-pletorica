"""Estado de Reflex para el módulo de plazas bajo el modelo plazas-first."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

import reflex as rx

from core.core.exceptions import BusinessRuleError, DuplicateError
from core.core.ui_helpers import FILTRO_TODOS
from core.core.text_utils import formatear_fecha, formatear_moneda
from core.core.utils import normalize_date_input, parse_date_input
from core.domain.models import EstatusPlaza, PlazaUpdate, TipoJornadaPlaza
from core.presentation.components.shared.auth_state import AuthState
from core.domain.services import (
    categoria_puesto_service,
    contrato_service,
    plaza_service,
    sede_service,
    tipo_servicio_service,
)

PORTAL_PLAZAS_ROUTE = "/portal/plazas"
SIN_CATEGORIA_VALUE = "__SIN_CATEGORIA__"
MODO_ASIGNACION_SEDE_CATEGORIA = "sede_categoria"
MODO_ASIGNACION_SOLO_SEDE = "solo_sede"

FORM_DEFAULTS = {
    "codigo": "",
    "sede_id": "",
    "categoria_puesto_id": "",
    "fecha_inicio": "",
    "fecha_fin": "",
    "salario_mensual": "",
    "tipo_jornada": TipoJornadaPlaza.COMPLETA.value,
    "factor_jornada": "1.00",
    "estatus": EstatusPlaza.VACANTE.value,
    "notas": "",
    "cantidad": "1",
    "prefijo_codigo": "",
}


class PlazasState(AuthState):
    """State del módulo de plazas centrado en contrato y operación de plazas."""

    # =========================================================================
    # VISTA
    # =========================================================================
    view_mode: str = "table"

    # =========================================================================
    # DATOS
    # =========================================================================
    plazas: List[dict] = []
    plaza_seleccionada: Optional[dict] = None
    resumen_categorias: List[dict] = []
    resumen_contratos: List[dict] = []
    contratos_disponibles: List[dict] = []
    categorias_catalogo: List[dict] = []
    sedes_catalogo: List[dict] = []

    contrato_id: int = 0
    contrato_codigo: str = ""
    contrato_estatus: str = ""
    contrato_tipo_servicio_clave: str = ""
    contrato_tipo_servicio_nombre: str = ""
    contrato_seleccionado_id: str = ""
    categoria_filtro_id: str = FILTRO_TODOS

    total_plazas: int = 0
    plazas_vacantes: int = 0
    plazas_ocupadas: int = 0
    plazas_suspendidas: int = 0
    plazas_canceladas: int = 0
    plazas_categorizadas: int = 0
    plazas_sin_categoria: int = 0
    cantidad_plazas_minima: int = 0
    cantidad_plazas_maxima: int = 0
    plazas_desfase: int = 0

    # =========================================================================
    # UI
    # =========================================================================
    mostrar_modal_plaza: bool = False
    mostrar_modal_detalle: bool = False
    mostrar_modal_confirmar_cancelar: bool = False
    mostrar_modal_crear_lote: bool = False
    mostrar_modal_asignar_empleado: bool = False

    cargando_contratos: bool = False
    cargando_categorias: bool = False
    cargando_empleados: bool = False

    # =========================================================================
    # ASIGNACIÓN DE EMPLEADO
    # =========================================================================
    empleados_disponibles: List[dict] = []
    empleado_seleccionado_id: str = ""

    # =========================================================================
    # FILTROS
    # =========================================================================
    filtro_estatus: str = FILTRO_TODOS

    # =========================================================================
    # FORMULARIO
    # =========================================================================
    form_codigo: str = ""
    form_sede_id: str = ""
    form_categoria_puesto_id: str = ""
    form_fecha_inicio: str = ""
    form_fecha_fin: str = ""
    form_salario_mensual: str = ""
    form_tipo_jornada: str = TipoJornadaPlaza.COMPLETA.value
    form_factor_jornada: str = "1.00"
    form_estatus: str = EstatusPlaza.VACANTE.value
    form_notas: str = ""
    form_cantidad: str = "1"
    form_prefijo_codigo: str = ""
    modo_asignacion_lote: str = MODO_ASIGNACION_SEDE_CATEGORIA

    # =========================================================================
    # ERRORES
    # =========================================================================
    error_codigo: str = ""
    error_sede_id: str = ""
    error_categoria_puesto_id: str = ""
    error_fecha_inicio: str = ""
    error_salario_mensual: str = ""
    error_factor_jornada: str = ""
    error_cantidad: str = ""

    # =========================================================================
    # COMPUTED VARS
    # =========================================================================
    @rx.var
    def mostrar_vista_inicial(self) -> bool:
        return self.contrato_id == 0

    @rx.var
    def tiene_resumen(self) -> bool:
        if self.es_contexto_portal:
            return len(self.resumen_contratos) > 0
        return len(self.resumen_categorias) > 0

    @rx.var
    def es_contexto_portal(self) -> bool:
        ruta_actual = self.router.route_id or ""
        return ruta_actual.startswith("/portal/")

    @rx.var
    def plazas_base_path(self) -> str:
        return PORTAL_PLAZAS_ROUTE if self.es_contexto_portal else "/plazas"

    @rx.var
    def titulo_pagina(self) -> str:
        return "Plazas"

    @rx.var
    def subtitulo_inicio(self) -> str:
        if self.es_contexto_portal:
            return "Asignación de plazas"
        return "Operación de plazas por contrato"

    @rx.var
    def descripcion_selector_contrato(self) -> str:
        if self.es_contexto_portal:
            return "Seleccione un contrato vigente con personal para asignar y gestionar sus plazas"
        return "Seleccione un contrato con personal para revisar, completar y operar sus plazas"

    @rx.var
    def mensaje_sin_contratos_disponibles(self) -> str:
        if self.es_contexto_portal:
            return "No hay contratos activos con personal asignado."
        return (
            "No hay contratos disponibles con personal habilitado. "
            "Primero configure un contrato de servicios con plazas."
        )

    @rx.var
    def puede_operar_plazas_en_contexto(self) -> bool:
        if self.es_contexto_portal:
            return bool(self.id_empresa_actual) and self.puede_acceder_rrhh
        return bool(
            self.es_superadmin
            or self.es_institucion
            or self.puede_gestionar_personal
            or self.puede_registrar_personal
            or self.puede_operar_empleados
        )

    @rx.var
    def tiene_contexto(self) -> bool:
        return self.contrato_id > 0

    @rx.var
    def es_detalle_portal(self) -> bool:
        return self.es_contexto_portal and self.tiene_contexto

    @rx.var
    def vacantes_sin_categoria_disponibles(self) -> int:
        return len(
            [
                plaza
                for plaza in self.plazas
                if plaza.get("estatus") == EstatusPlaza.VACANTE.value
                and not plaza.get("categoria_puesto_id")
            ]
        )

    @rx.var
    def vacantes_sin_sede_con_categoria_disponibles(self) -> int:
        return len(
            [
                plaza
                for plaza in self.plazas
                if plaza.get("estatus") == EstatusPlaza.VACANTE.value
                and plaza.get("categoria_puesto_id")
                and not plaza.get("sede_id")
            ]
        )

    @rx.var
    def plazas_ocupadas_sin_sede_total(self) -> int:
        return len(
            [
                plaza
                for plaza in self.plazas
                if plaza.get("estatus") == EstatusPlaza.OCUPADA.value
                and not plaza.get("sede_id")
            ]
        )

    @rx.var
    def mostrar_tabs_asignacion_lote(self) -> bool:
        return (
            self.vacantes_sin_categoria_disponibles > 0
            and self.vacantes_sin_sede_con_categoria_disponibles > 0
        )

    @rx.var
    def es_modo_sede_categoria_lote(self) -> bool:
        return self.modo_asignacion_lote != MODO_ASIGNACION_SOLO_SEDE

    @rx.var
    def disponibles_asignacion_lote(self) -> int:
        if self.es_modo_sede_categoria_lote:
            return self.vacantes_sin_categoria_disponibles
        return self.vacantes_sin_sede_con_categoria_disponibles

    @rx.var
    def puede_asignar_lote(self) -> bool:
        return (
            self.puede_operar_plazas_en_contexto
            and self.tiene_contexto
            and (
                self.vacantes_sin_categoria_disponibles > 0
                or self.vacantes_sin_sede_con_categoria_disponibles > 0
            )
        )

    @rx.var
    def opciones_estatus(self) -> List[dict]:
        return [
            {"value": FILTRO_TODOS, "label": "Todos"},
            {"value": EstatusPlaza.VACANTE.value, "label": "Vacante"},
            {"value": EstatusPlaza.OCUPADA.value, "label": "Ocupada"},
            {"value": EstatusPlaza.SUSPENDIDA.value, "label": "Suspendida"},
            {"value": EstatusPlaza.CANCELADA.value, "label": "Cancelada"},
        ]

    @rx.var
    def opciones_estatus_form(self) -> List[dict]:
        return [
            {"value": EstatusPlaza.VACANTE.value, "label": "Vacante"},
            {"value": EstatusPlaza.SUSPENDIDA.value, "label": "Suspendida"},
            {"value": EstatusPlaza.CANCELADA.value, "label": "Cancelada"},
        ]

    @rx.var
    def opciones_contratos(self) -> List[dict]:
        opciones = []
        for contrato in self.contratos_disponibles:
            codigo = contrato.get("codigo", "")
            estatus = contrato.get("estatus", "")
            maximo = int(contrato.get("cantidad_plazas_maxima") or 0)
            opciones.append(
                {
                    "value": str(contrato.get("id")),
                    "label": f"{codigo} ({estatus}) · máx {maximo}",
                }
            )
        return opciones

    @rx.var
    def opciones_categorias_contrato(self) -> List[dict]:
        agrupados: dict[str, dict] = {}
        for plaza in self.plazas:
            categoria_id = plaza.get("categoria_puesto_id")
            if categoria_id:
                key = str(categoria_id)
                if key not in agrupados:
                    agrupados[key] = {
                        "value": key,
                        "label": (
                            f"{plaza.get('categoria_clave', '')} - "
                            f"{plaza.get('categoria_nombre', 'Sin categoría')}"
                        ).strip(" -"),
                        "total": 0,
                    }
                agrupados[key]["total"] += 1
            else:
                if SIN_CATEGORIA_VALUE not in agrupados:
                    agrupados[SIN_CATEGORIA_VALUE] = {
                        "value": SIN_CATEGORIA_VALUE,
                        "label": "Sin categoría",
                        "total": 0,
                    }
                agrupados[SIN_CATEGORIA_VALUE]["total"] += 1

        opciones = [{"value": FILTRO_TODOS, "label": "Todas las categorías"}]
        opciones.extend(
            {
                "value": item["value"],
                "label": f"{item['label']} ({item['total']})",
            }
            for item in sorted(
                agrupados.values(),
                key=lambda item: (
                    item["value"] != SIN_CATEGORIA_VALUE,
                    item["label"],
                ),
            )
        )
        return opciones

    @rx.var
    def opciones_categorias_catalogo(self) -> List[dict]:
        return [
            {
                "value": str(categoria.get("id")),
                "label": (
                    f"{categoria.get('clave', '')} - {categoria.get('nombre', '')}"
                ).strip(" -"),
            }
            for categoria in self.categorias_catalogo
        ]

    @rx.var
    def opciones_sedes_catalogo(self) -> List[dict]:
        return [
            {
                "value": str(sede.get("id")),
                "label": (
                    f"{sede.get('codigo', '')} - "
                    f"{sede.get('nombre_corto') or sede.get('nombre', '')}"
                ).strip(" -"),
            }
            for sede in self.sedes_catalogo
        ]

    @rx.var
    def opciones_empleados(self) -> List[dict]:
        return [
            {
                "value": str(empleado.get("id")),
                "label": f"{empleado.get('clave', '')} - {empleado.get('nombre_completo', '')}",
            }
            for empleado in self.empleados_disponibles
        ]

    @rx.var
    def nombre_categoria_filtro(self) -> str:
        if self.categoria_filtro_id == FILTRO_TODOS:
            return ""
        if self.categoria_filtro_id == SIN_CATEGORIA_VALUE:
            return "Sin categoría"
        for opcion in self.opciones_categorias_contrato:
            if opcion["value"] == self.categoria_filtro_id:
                return opcion["label"]
        return ""

    @rx.var
    def titulo_contexto(self) -> str:
        if not self.contrato_codigo:
            return "Plazas"
        if self.nombre_categoria_filtro:
            return f"{self.contrato_codigo} - {self.nombre_categoria_filtro}"
        return self.contrato_codigo

    @rx.var
    def breadcrumb_items(self) -> List[dict]:
        items = [{"texto": "Plazas", "href": self.plazas_base_path}]
        if self.contrato_codigo:
            items.append({"texto": self.contrato_codigo, "href": ""})
        if self.nombre_categoria_filtro:
            items.append({"texto": self.nombre_categoria_filtro, "href": ""})
        return items

    @rx.var
    def plazas_filtradas(self) -> List[dict]:
        resultado = list(self.plazas)

        if self.categoria_filtro_id != FILTRO_TODOS:
            if self.categoria_filtro_id == SIN_CATEGORIA_VALUE:
                resultado = [p for p in resultado if not p.get("categoria_puesto_id")]
            else:
                resultado = [
                    p
                    for p in resultado
                    if str(p.get("categoria_puesto_id") or "") == self.categoria_filtro_id
                ]

        if self.filtro_estatus != FILTRO_TODOS:
            resultado = [p for p in resultado if p.get("estatus") == self.filtro_estatus]

        if self.filtro_busqueda:
            termino = self.filtro_busqueda.lower().strip()
            resultado = [
                p
                for p in resultado
                if termino in str(p.get("numero_plaza", "")).lower()
                or termino in p.get("codigo", "").lower()
                or termino in p.get("sede_nombre", "").lower()
                or termino in p.get("categoria_nombre", "").lower()
                or termino in p.get("empleado_nombre", "").lower()
            ]

        return resultado

    @rx.var
    def total_plazas_filtradas(self) -> int:
        return len(self.plazas_filtradas)

    @rx.var
    def tiene_filtros_activos(self) -> bool:
        return (
            self.filtro_estatus != FILTRO_TODOS
            or self.categoria_filtro_id != FILTRO_TODOS
            or bool(self.filtro_busqueda.strip())
        )

    @rx.var
    def puede_guardar(self) -> bool:
        return (
            bool(self.form_sede_id)
            and bool(self.form_fecha_inicio)
            and bool(self.form_salario_mensual)
            and bool(self.form_factor_jornada)
            and not self.tiene_errores_en_campos(
                [
                    "codigo",
                    "sede_id",
                    "categoria_puesto_id",
                    "fecha_inicio",
                    "salario_mensual",
                    "factor_jornada",
                ]
            )
            and not self.saving
        )

    @rx.var
    def puede_guardar_asignacion_lote(self) -> bool:
        errores = ["sede_id", "cantidad"]
        if self.es_modo_sede_categoria_lote:
            errores.append("categoria_puesto_id")
        return (
            bool(self.form_sede_id)
            and bool(self.form_cantidad)
            and (
                not self.es_modo_sede_categoria_lote
                or bool(self.form_categoria_puesto_id)
            )
            and not self.tiene_errores_en_campos(errores)
            and not self.saving
        )

    @rx.var
    def puede_asignar_empleado(self) -> bool:
        return bool(self.empleado_seleccionado_id) and not self.saving

    @rx.var
    def mensaje_tabla_vacia(self) -> str:
        if self.total_plazas == 0:
            return "Este contrato no tiene plazas materializadas"
        if self.tiene_filtros_activos:
            return "No hay plazas que coincidan con los filtros"
        return "No hay plazas disponibles para mostrar"

    @rx.var
    def submensaje_tabla_vacia(self) -> str:
        if self.total_plazas == 0:
            return (
                "Ajuste la cantidad máxima de plazas en el contrato para "
                "materializar nuevas plazas."
            )
        if self.tiene_filtros_activos:
            return "Limpie los filtros o seleccione otra categoría."
        return ""

    @rx.var
    def plazas_sin_sede_total(self) -> int:
        return len([plaza for plaza in self.plazas if not plaza.get("sede_id")])

    @rx.var
    def plazas_vacantes_sin_sede_total(self) -> int:
        return len(
            [
                plaza
                for plaza in self.plazas
                if plaza.get("estatus") == EstatusPlaza.VACANTE.value
                and not plaza.get("sede_id")
            ]
        )

    @rx.var
    def titulo_modo_asignacion_lote(self) -> str:
        if self.es_modo_sede_categoria_lote:
            return "Sede + categoría"
        return "Solo sede"

    @rx.var
    def descripcion_modo_asignacion_lote(self) -> str:
        if self.es_modo_sede_categoria_lote:
            return (
                "Asigne categoría a plazas vacantes sin categoría y complete la sede "
                "solo donde haga falta."
            )
        return "Asigne sede a plazas vacantes que ya tienen categoría."

    @rx.var
    def hint_sede_asignacion_lote(self) -> str:
        if self.es_modo_sede_categoria_lote:
            return (
                "La sede seleccionada se aplicará solo a las plazas del lote que aún no "
                "tengan sede."
            )
        return "La sede se asignará a todas las plazas del lote."

    # =========================================================================
    # SETTERS
    # =========================================================================
    def set_filtro_estatus(self, value: str):
        self.filtro_estatus = value or FILTRO_TODOS

    def set_categoria_filtro_id(self, value: str):
        self.categoria_filtro_id = value or FILTRO_TODOS
        if self.tiene_contexto:
            return rx.redirect(
                self._build_plazas_url(self.contrato_id, self.categoria_filtro_id),
                replace=True,
            )

    def set_form_codigo(self, value: str):
        self.form_codigo = value.upper() if value else ""

    def set_form_sede_id(self, value: str):
        self.form_sede_id = value or ""
        self.error_sede_id = ""

    def set_form_categoria_puesto_id(self, value: str):
        self.form_categoria_puesto_id = value or ""
        self.error_categoria_puesto_id = ""

    def set_form_fecha_inicio(self, value: str):
        self.form_fecha_inicio = normalize_date_input(value)
        self.error_fecha_inicio = ""

    def set_form_fecha_fin(self, value: str):
        self.form_fecha_fin = normalize_date_input(value)

    def set_form_salario_mensual(self, value: str):
        self.form_salario_mensual = formatear_moneda(value) if value else ""
        self.error_salario_mensual = ""

    def set_form_tipo_jornada(self, value: str):
        self.form_tipo_jornada = value or TipoJornadaPlaza.COMPLETA.value
        if self.form_tipo_jornada == TipoJornadaPlaza.COMPLETA.value:
            self.form_factor_jornada = "1.00"
        elif self.form_tipo_jornada == TipoJornadaPlaza.MEDIA_JORNADA.value:
            self.form_factor_jornada = "0.50"
        self.error_factor_jornada = ""

    def set_form_factor_jornada(self, value: str):
        valor = str(value or "").strip()
        permitido = "".join(c for c in valor if c.isdigit() or c == ".")
        if permitido.count(".") > 1:
            primer, *resto = permitido.split(".")
            permitido = primer + "." + "".join(resto)
        self.form_factor_jornada = permitido
        self.error_factor_jornada = ""

    def set_form_estatus(self, value: str):
        self.form_estatus = value or EstatusPlaza.VACANTE.value

    def set_form_notas(self, value: str):
        self.form_notas = value or ""

    def set_form_cantidad(self, value: str):
        self.form_cantidad = "".join(c for c in str(value) if c.isdigit()) if value else ""
        self._validar_cantidad_lote()

    def set_form_prefijo_codigo(self, value: str):
        self.form_prefijo_codigo = value.upper() if value else ""

    def set_modo_asignacion_lote(self, value: str):
        if value not in {MODO_ASIGNACION_SEDE_CATEGORIA, MODO_ASIGNACION_SOLO_SEDE}:
            value = MODO_ASIGNACION_SEDE_CATEGORIA
        self.modo_asignacion_lote = value
        disponibles = self.disponibles_asignacion_lote
        self.form_cantidad = str(disponibles) if disponibles > 0 else "1"
        self.error_cantidad = ""
        self._validar_cantidad_lote()

    def set_empleado_seleccionado_id(self, value: str):
        self.empleado_seleccionado_id = value or ""

    def set_contrato_seleccionado_id(self, value: str):
        self.contrato_seleccionado_id = value or ""
        if value:
            self.categoria_filtro_id = FILTRO_TODOS
            return PlazasState.seleccionar_contrato(int(value))
        return PlazasState.volver_a_resumen

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _empresa_filtro_actual(self) -> Optional[int]:
        if self.es_contexto_portal:
            return self.id_empresa_actual or None
        return None

    def _build_plazas_url(
        self,
        contrato_id: int | None = None,
        categoria_puesto_id: str = "",
    ) -> str:
        url = self.plazas_base_path
        parametros: list[str] = []

        if contrato_id:
            parametros.append(f"contrato_id={contrato_id}")

        if categoria_puesto_id and categoria_puesto_id != FILTRO_TODOS:
            parametros.append(f"categoria_puesto_id={categoria_puesto_id}")

        if parametros:
            return f"{url}?{'&'.join(parametros)}"
        return url

    def _asegurar_permiso_operar_plazas(self) -> None:
        if not self.puede_operar_plazas_en_contexto:
            if self.es_contexto_portal:
                raise BusinessRuleError(
                    "Solo RRHH o admin_empresa pueden operar plazas en el portal"
                )
            raise BusinessRuleError("No tienes permisos para operar plazas")

    async def _asegurar_acceso_contrato(self, contrato_id: int):
        contrato = await contrato_service.obtener_por_id(contrato_id)
        if (
            self.es_contexto_portal
            and (
                not self.id_empresa_actual
                or int(contrato.empresa_id or 0) != int(self.id_empresa_actual)
            )
        ):
            raise BusinessRuleError(
                "Solo puedes gestionar plazas de contratos de la empresa activa"
            )
        return contrato

    async def _asegurar_acceso_plaza(self, plaza_id: int):
        plaza = await plaza_service.obtener_por_id(plaza_id)
        await self._asegurar_acceso_contrato(plaza.contrato_id)
        return plaza

    def _serializar_plaza_resumen(self, plaza) -> dict:
        plaza_dict = plaza.model_dump(mode="json")
        plaza_dict["fecha_inicio_fmt"] = formatear_fecha(plaza.fecha_inicio)
        plaza_dict["fecha_fin_fmt"] = (
            formatear_fecha(plaza.fecha_fin) if plaza.fecha_fin else "-"
        )
        plaza_dict["salario_fmt"] = formatear_moneda(str(plaza.salario_mensual))
        plaza_dict["tipo_jornada_label"] = TipoJornadaPlaza(
            str(getattr(plaza.tipo_jornada, "value", plaza.tipo_jornada))
        ).descripcion
        plaza_dict["sede_nombre"] = plaza_dict.get("sede_nombre") or "Sin sede"
        plaza_dict["sede_codigo"] = plaza_dict.get("sede_codigo") or ""
        plaza_dict["categoria_nombre"] = plaza_dict.get("categoria_nombre") or "Sin categoría"
        plaza_dict["categoria_clave"] = plaza_dict.get("categoria_clave") or ""
        plaza_dict["tiene_sede"] = bool(plaza_dict.get("sede_id"))
        plaza_dict["tiene_categoria"] = bool(plaza_dict.get("categoria_puesto_id"))
        return plaza_dict

    def _cargar_plaza_en_formulario(self, plaza: dict) -> None:
        self.form_codigo = plaza.get("codigo", "") or ""
        self.form_sede_id = str(plaza.get("sede_id")) if plaza.get("sede_id") else ""
        self.form_categoria_puesto_id = (
            str(plaza.get("categoria_puesto_id"))
            if plaza.get("categoria_puesto_id")
            else ""
        )
        self.form_fecha_inicio = str(plaza.get("fecha_inicio") or "")
        self.form_fecha_fin = str(plaza.get("fecha_fin") or "")
        self.form_salario_mensual = str(plaza.get("salario_mensual", "") or "0")
        self.form_tipo_jornada = str(
            plaza.get("tipo_jornada") or TipoJornadaPlaza.COMPLETA.value
        )
        self.form_factor_jornada = str(plaza.get("factor_jornada") or "1.0")
        self.form_estatus = plaza.get("estatus", EstatusPlaza.VACANTE.value)
        self.form_notas = plaza.get("notas", "") or ""

    def _parse_decimal(self, value: str) -> Decimal:
        if not value or value.strip() == "":
            return Decimal("0")
        try:
            return Decimal(value.replace(",", "").replace("$", "").strip())
        except Exception:
            return Decimal("0")

    def _validar_cantidad_lote(self) -> None:
        self.error_cantidad = ""
        if not self.form_cantidad:
            return
        cantidad = int(self.form_cantidad)
        if cantidad <= 0:
            self.error_cantidad = "La cantidad debe ser mayor a cero"
            return
        if cantidad > self.disponibles_asignacion_lote:
            if self.es_modo_sede_categoria_lote:
                self.error_cantidad = (
                    "La cantidad excede las vacantes sin categoría disponibles"
                )
            else:
                self.error_cantidad = (
                    "La cantidad excede las vacantes con categoría y sin sede disponibles"
                )

    async def _cargar_totales_contrato(self, contrato_id: int) -> None:
        resumen = await plaza_service.calcular_totales_contrato(contrato_id)
        self.total_plazas = resumen.total_plazas
        self.plazas_vacantes = resumen.plazas_vacantes
        self.plazas_ocupadas = resumen.plazas_ocupadas
        self.plazas_suspendidas = resumen.plazas_suspendidas
        self.plazas_canceladas = resumen.plazas_canceladas
        self.plazas_categorizadas = resumen.plazas_categorizadas
        self.plazas_sin_categoria = resumen.plazas_sin_categoria
        self.cantidad_plazas_minima = resumen.cantidad_plazas_minima
        self.cantidad_plazas_maxima = resumen.cantidad_plazas_maxima
        self.plazas_desfase = resumen.plazas_desfase

    async def _cargar_tipo_servicio_contrato(self, tipo_servicio_id: Optional[int]) -> None:
        self.contrato_tipo_servicio_clave = ""
        self.contrato_tipo_servicio_nombre = ""
        if not tipo_servicio_id:
            return

        try:
            tipo_servicio = await tipo_servicio_service.obtener_por_id(int(tipo_servicio_id))
            self.contrato_tipo_servicio_clave = tipo_servicio.clave or ""
            self.contrato_tipo_servicio_nombre = tipo_servicio.nombre or ""
        except Exception:
            self.contrato_tipo_servicio_clave = ""
            self.contrato_tipo_servicio_nombre = ""

    async def _recargar_contexto_actual(self) -> None:
        contrato_id = self.contrato_id
        if contrato_id:
            await self.cargar_plazas_de_contrato(contrato_id)
        await self.cargar_resumen_inicial()
        await self.cargar_contratos_con_personal()

    def _limpiar_contexto_contrato(self) -> None:
        self.plazas = []
        self.plaza_seleccionada = None
        self.contrato_id = 0
        self.contrato_codigo = ""
        self.contrato_estatus = ""
        self.contrato_tipo_servicio_clave = ""
        self.contrato_tipo_servicio_nombre = ""
        self.contrato_seleccionado_id = ""
        self.categoria_filtro_id = FILTRO_TODOS
        self.total_plazas = 0
        self.plazas_vacantes = 0
        self.plazas_ocupadas = 0
        self.plazas_suspendidas = 0
        self.plazas_canceladas = 0
        self.plazas_categorizadas = 0
        self.plazas_sin_categoria = 0
        self.cantidad_plazas_minima = 0
        self.cantidad_plazas_maxima = 0
        self.plazas_desfase = 0
        self.filtro_estatus = FILTRO_TODOS
        self.filtro_busqueda = ""

    def _cerrar_overlays(self) -> None:
        self.mostrar_modal_plaza = False
        self.mostrar_modal_detalle = False
        self.mostrar_modal_confirmar_cancelar = False
        self.mostrar_modal_crear_lote = False
        self.mostrar_modal_asignar_empleado = False
        self.empleado_seleccionado_id = ""
        self.empleados_disponibles = []

    def _limpiar_formulario(self) -> None:
        for campo, default in FORM_DEFAULTS.items():
            setattr(self, f"form_{campo}", default)
        self.modo_asignacion_lote = MODO_ASIGNACION_SEDE_CATEGORIA
        self.limpiar_errores_campos(
            [
                "codigo",
                "sede_id",
                "categoria_puesto_id",
                "fecha_inicio",
                "salario_mensual",
                "factor_jornada",
                "cantidad",
            ]
        )
        self.plaza_seleccionada = None

    # =========================================================================
    # CARGA DE DATOS
    # =========================================================================
    async def cargar_contratos_con_personal(self):
        self.cargando_contratos = True
        try:
            contratos_disponibles: list[dict] = []
            if self.es_contexto_portal and self.id_empresa_actual:
                contratos = await contrato_service.obtener_por_empresa(
                    self.id_empresa_actual,
                    incluir_inactivos=False,
                )
                for contrato in contratos:
                    estatus = str(getattr(contrato.estatus, "value", contrato.estatus))
                    if contrato.tiene_personal and estatus == "ACTIVO":
                        contratos_disponibles.append(
                            {
                                "id": contrato.id,
                                "codigo": contrato.codigo,
                                "estatus": estatus,
                                "cantidad_plazas_minima": contrato.cantidad_plazas_minima,
                                "cantidad_plazas_maxima": contrato.cantidad_plazas_maxima,
                            }
                        )
            else:
                contratos = await contrato_service.obtener_con_personal(
                    solo_activos=False,
                    limite=200,
                )
                for contrato in contratos:
                    estatus = str(getattr(contrato.estatus, "value", contrato.estatus))
                    if estatus in {"BORRADOR", "ACTIVO", "SUSPENDIDO"}:
                        contratos_disponibles.append(contrato.model_dump(mode="json"))

            self.contratos_disponibles = sorted(
                contratos_disponibles,
                key=lambda item: (item.get("codigo", ""), item.get("estatus", "")),
            )
        except Exception as e:
            self.manejar_error(e, "cargar contratos")
            self.contratos_disponibles = []
            return rx.toast.error(f"Error al cargar contratos: {e}")
        finally:
            self.cargando_contratos = False

    async def cargar_categorias_catalogo(self):
        self.cargando_categorias = True
        try:
            categorias = await categoria_puesto_service.obtener_todas(
                incluir_inactivas=False,
                limite=500,
            )
            self.categorias_catalogo = [
                categoria.model_dump(mode="json") for categoria in categorias
            ]
        except Exception as e:
            self.categorias_catalogo = []
            self.manejar_error(e, "cargar categorías")
        finally:
            self.cargando_categorias = False

    async def cargar_sedes_catalogo(self):
        try:
            sedes = await sede_service.obtener_todas(
                incluir_inactivas=False,
                limite=500,
            )
            self.sedes_catalogo = [sede.model_dump(mode="json") for sede in sedes]
        except Exception as e:
            self.sedes_catalogo = []
            self.manejar_error(e, "cargar sedes")

    async def cargar_resumen_inicial(self):
        try:
            if self.es_contexto_portal:
                self.resumen_contratos = (
                    await plaza_service.obtener_resumen_contratos_con_plazas(
                        empresa_id=self._empresa_filtro_actual(),
                        solo_activos=True,
                    )
                )
                self.resumen_categorias = []
            else:
                self.resumen_categorias = (
                    await plaza_service.obtener_resumen_categorias_con_plazas(
                        empresa_id=self._empresa_filtro_actual(),
                    )
                )
                self.resumen_contratos = []
        except Exception as e:
            self.manejar_error(e, "cargar resumen")
            self.resumen_categorias = []
            self.resumen_contratos = []
            return rx.toast.error(f"Error al cargar resumen: {e}")

    async def cargar_plazas_de_contrato(self, contrato_id: int):
        self.loading = True
        try:
            contrato = await self._asegurar_acceso_contrato(contrato_id)
            plazas_resumen = await plaza_service.obtener_resumen_de_contrato(contrato_id)
            self.plazas = [
                self._serializar_plaza_resumen(plaza) for plaza in plazas_resumen
            ]
            self.contrato_id = contrato_id
            self.contrato_codigo = contrato.codigo
            self.contrato_estatus = str(
                getattr(contrato.estatus, "value", contrato.estatus) or ""
            )
            self.contrato_seleccionado_id = str(contrato_id)
            await self._cargar_tipo_servicio_contrato(getattr(contrato, "tipo_servicio_id", None))

            await self._cargar_totales_contrato(contrato_id)

            opciones_validas = {item["value"] for item in self.opciones_categorias_contrato}
            if self.categoria_filtro_id not in opciones_validas:
                self.categoria_filtro_id = FILTRO_TODOS
        except Exception as e:
            self.manejar_error(e, "cargar plazas")
            self._limpiar_contexto_contrato()
            return rx.toast.error(f"Error al cargar plazas: {e}")
        finally:
            self.loading = False

    async def seleccionar_contrato(self, contrato_id: int):
        self.categoria_filtro_id = FILTRO_TODOS
        await self.cargar_plazas_de_contrato(contrato_id)
        return rx.redirect(self._build_plazas_url(contrato_id), replace=True)

    async def seleccionar_resumen(self, item: dict):
        categoria_id = item.get("categoria_puesto_id")
        self.categoria_filtro_id = (
            str(categoria_id) if categoria_id is not None else SIN_CATEGORIA_VALUE
        )
        await self.cargar_plazas_de_contrato(int(item["contrato_id"]))
        return rx.redirect(
            self._build_plazas_url(
                int(item["contrato_id"]),
                self.categoria_filtro_id,
            ),
            replace=True,
        )

    async def volver_a_resumen(self):
        self._cerrar_overlays()
        self._limpiar_contexto_contrato()
        await self.cargar_resumen_inicial()
        return rx.redirect(self._build_plazas_url(), replace=True)

    async def _fetch_desde_url(self):
        self._cerrar_overlays()
        await self.cargar_sedes_catalogo()
        await self.cargar_categorias_catalogo()
        await self.cargar_contratos_con_personal()

        contrato_id = self.router.url.query_parameters.get("contrato_id", "")
        categoria_puesto_id = self.router.url.query_parameters.get("categoria_puesto_id", "")

        if contrato_id:
            try:
                self.categoria_filtro_id = (
                    categoria_puesto_id if categoria_puesto_id else FILTRO_TODOS
                )
                await self.cargar_plazas_de_contrato(int(contrato_id))
                return
            except ValueError:
                self.categoria_filtro_id = FILTRO_TODOS

        self._limpiar_contexto_contrato()
        await self.cargar_resumen_inicial()

    async def on_mount_plazas(self):
        if self.es_contexto_portal:
            resultado = await self.verificar_y_redirigir()
            if resultado:
                self.loading = False
                yield resultado
                return

            if self.es_admin:
                yield rx.redirect("/")
                return

            if self.es_empleado_portal or not self.id_empresa_actual or not self.puede_acceder_rrhh:
                yield rx.redirect("/portal")
                return

            async for _ in self._montar_pagina(self._fetch_desde_url):
                yield
            return

        async for _ in self._montar_pagina_auth(self._fetch_desde_url):
            yield

    # =========================================================================
    # MODALES
    # =========================================================================
    def abrir_modal_editar(self, plaza: dict):
        try:
            self._asegurar_permiso_operar_plazas()
        except BusinessRuleError as e:
            return rx.toast.error(str(e))

        self._limpiar_formulario()
        self.plaza_seleccionada = plaza
        self._cargar_plaza_en_formulario(plaza)
        self.mostrar_modal_plaza = True

    def cerrar_modal_plaza(self):
        self.mostrar_modal_plaza = False
        self._limpiar_formulario()

    def abrir_modal_detalle(self, plaza: dict):
        self.plaza_seleccionada = plaza
        self.mostrar_modal_detalle = True

    def cerrar_modal_detalle(self):
        self.mostrar_modal_detalle = False
        self.plaza_seleccionada = None

    def abrir_confirmar_cancelar(self, plaza: dict):
        self.plaza_seleccionada = plaza
        self.mostrar_modal_confirmar_cancelar = True

    def cerrar_confirmar_cancelar(self):
        self.mostrar_modal_confirmar_cancelar = False
        self.plaza_seleccionada = None

    def abrir_modal_crear_lote(self):
        try:
            self._asegurar_permiso_operar_plazas()
        except BusinessRuleError as e:
            return rx.toast.error(str(e))

        if not self.tiene_contexto:
            return rx.toast.error("Seleccione un contrato primero")
        if not self.puede_asignar_lote:
            return rx.toast.error("No hay plazas vacantes disponibles para asignar en lote")

        self._limpiar_formulario()
        if (
            self.vacantes_sin_categoria_disponibles == 0
            and self.vacantes_sin_sede_con_categoria_disponibles > 0
        ):
            self.modo_asignacion_lote = MODO_ASIGNACION_SOLO_SEDE
        else:
            self.modo_asignacion_lote = MODO_ASIGNACION_SEDE_CATEGORIA
        self.form_cantidad = str(self.disponibles_asignacion_lote)
        self._validar_cantidad_lote()
        self.mostrar_modal_crear_lote = True

    def cerrar_modal_crear_lote(self):
        self.mostrar_modal_crear_lote = False
        self._limpiar_formulario()

    async def abrir_asignar_empleado(self, plaza: dict):
        try:
            self._asegurar_permiso_operar_plazas()
            if not plaza.get("sede_id"):
                raise BusinessRuleError(
                    "La plaza debe tener sede antes de asignar un empleado"
                )
            if not plaza.get("categoria_puesto_id"):
                raise BusinessRuleError(
                    "La plaza debe tener categoría antes de asignar un empleado"
                )
        except BusinessRuleError as e:
            return rx.toast.error(str(e))

        self.plaza_seleccionada = plaza
        self.empleado_seleccionado_id = ""
        self.empleados_disponibles = []
        self.cargando_empleados = True
        self.mostrar_modal_asignar_empleado = True

        try:
            from core.domain.services import empleado_service

            if self.es_contexto_portal and self.id_empresa_actual:
                empleados = await empleado_service.obtener_resumen_por_empresa(
                    empresa_id=self.id_empresa_actual,
                    incluir_inactivos=False,
                    limite=200,
                )
            else:
                empleados = await empleado_service.obtener_resumen_empleados(
                    incluir_inactivos=False
                )

            empleados_asignados = await plaza_service.obtener_empleados_asignados(
                empresa_id=self._empresa_filtro_actual(),
            )
            empleados_asignados_set = set(empleados_asignados)

            self.empleados_disponibles = [
                {
                    "id": empleado.id,
                    "clave": empleado.clave,
                    "nombre_completo": empleado.nombre_completo,
                }
                for empleado in empleados
                if empleado.id not in empleados_asignados_set
            ]
        except Exception as e:
            self.manejar_error(e, "cargar empleados")
            self.empleados_disponibles = []
            return rx.toast.error(f"Error al cargar empleados: {e}")
        finally:
            self.cargando_empleados = False

    def cerrar_modal_asignar_empleado(self):
        self.mostrar_modal_asignar_empleado = False
        self.plaza_seleccionada = None
        self.empleado_seleccionado_id = ""
        self.empleados_disponibles = []

    # =========================================================================
    # OPERACIONES
    # =========================================================================
    async def confirmar_asignar_empleado(self):
        if not self.plaza_seleccionada or not self.empleado_seleccionado_id:
            yield rx.toast.error("Seleccione un empleado")
            return

        self.saving = True
        yield
        try:
            self._asegurar_permiso_operar_plazas()
            plaza_id = int(self.plaza_seleccionada["id"])
            await self._asegurar_acceso_plaza(plaza_id)
            empleado_id = self.parse_id(self.empleado_seleccionado_id)
            if empleado_id is None:
                raise BusinessRuleError("Seleccione un empleado válido")

            await plaza_service.asignar_empleado(plaza_id, empleado_id)
            self.cerrar_modal_asignar_empleado()
            await self._recargar_contexto_actual()
            yield rx.toast.success("Empleado asignado a la plaza")
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "asignar empleado")
        finally:
            self.saving = False

    async def guardar_plaza(self):
        if not self.plaza_seleccionada:
            yield rx.toast.error("No hay plaza seleccionada")
            return
        if not self.puede_guardar:
            yield rx.toast.error("Complete los campos requeridos")
            return

        self.saving = True
        yield
        try:
            self._asegurar_permiso_operar_plazas()
            plaza_id = int(self.plaza_seleccionada["id"])
            await self._asegurar_acceso_plaza(plaza_id)

            plaza_update = PlazaUpdate(
                codigo=self.form_codigo.strip() or None,
                sede_id=self.parse_id(self.form_sede_id),
                categoria_puesto_id=self.parse_id(self.form_categoria_puesto_id),
                fecha_inicio=(
                    parse_date_input(self.form_fecha_inicio)
                    if self.form_fecha_inicio
                    else None
                ),
                fecha_fin=(
                    parse_date_input(self.form_fecha_fin)
                    if self.form_fecha_fin
                    else None
                ),
                salario_mensual=self._parse_decimal(self.form_salario_mensual),
                tipo_jornada=TipoJornadaPlaza(self.form_tipo_jornada),
                factor_jornada=self._parse_decimal(self.form_factor_jornada),
                estatus=EstatusPlaza(self.form_estatus) if self.form_estatus else None,
                notas=self.form_notas.strip() or None,
            )

            await plaza_service.actualizar(plaza_id, plaza_update)
            numero = self.plaza_seleccionada.get("numero_plaza")
            self.cerrar_modal_plaza()
            await self._recargar_contexto_actual()
            yield rx.toast.success(f"Plaza #{numero} actualizada")
        except DuplicateError as e:
            yield rx.toast.error(f"Número de plaza duplicado: {e}")
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "guardar plaza")
        finally:
            self.saving = False

    async def crear_plazas_lote(self):
        if not self.tiene_contexto:
            yield rx.toast.error("Seleccione un contrato primero")
            return

        self._validar_cantidad_lote()
        if not self.puede_guardar_asignacion_lote:
            yield rx.toast.error("Complete los campos requeridos")
            return

        self.saving = True
        yield
        try:
            self._asegurar_permiso_operar_plazas()
            await self._asegurar_acceso_contrato(self.contrato_id)

            sede_id = self.parse_id(self.form_sede_id)
            if sede_id is None:
                raise BusinessRuleError("Seleccione una sede")

            cantidad = int(self.form_cantidad or "0")
            if self.es_modo_sede_categoria_lote:
                categoria_puesto_id = self.parse_id(self.form_categoria_puesto_id)
                if categoria_puesto_id is None:
                    raise BusinessRuleError("Seleccione una categoría")

                salario = (
                    self._parse_decimal(self.form_salario_mensual)
                    if self.form_salario_mensual
                    else None
                )

                plazas = await plaza_service.asignar_categoria_en_lote(
                    contrato_id=self.contrato_id,
                    categoria_puesto_id=categoria_puesto_id,
                    cantidad=cantidad,
                    sede_id=sede_id,
                    salario_mensual=salario,
                    prefijo_codigo=self.form_prefijo_codigo.strip(),
                )
                mensaje = f"{len(plazas)} plaza(s) asignadas a sede y categoría"
            else:
                plazas = await plaza_service.asignar_sede_en_lote(
                    contrato_id=self.contrato_id,
                    sede_id=sede_id,
                    cantidad=cantidad,
                )
                mensaje = f"{len(plazas)} plaza(s) asignadas a sede"

            self.cerrar_modal_crear_lote()
            await self._recargar_contexto_actual()
            yield rx.toast.success(mensaje)
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "asignar plazas")
        finally:
            self.saving = False

    async def cancelar_plaza(self):
        if not self.plaza_seleccionada:
            yield rx.toast.error("No hay plaza seleccionada")
            return

        self.saving = True
        yield
        try:
            self._asegurar_permiso_operar_plazas()
            plaza_id = int(self.plaza_seleccionada["id"])
            await self._asegurar_acceso_plaza(plaza_id)
            await plaza_service.cancelar(plaza_id)
            numero = self.plaza_seleccionada.get("numero_plaza")
            self.cerrar_confirmar_cancelar()
            await self._recargar_contexto_actual()
            yield rx.toast.success(f"Plaza #{numero} cancelada")
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "cancelar plaza")
        finally:
            self.saving = False

    async def liberar_plaza(self, plaza_id: int):
        try:
            self._asegurar_permiso_operar_plazas()
            await self._asegurar_acceso_plaza(plaza_id)
            await plaza_service.liberar_plaza(plaza_id)
            await self._recargar_contexto_actual()
            return rx.toast.success("Plaza liberada")
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "liberar plaza")

    async def suspender_plaza(self, plaza_id: int):
        try:
            self._asegurar_permiso_operar_plazas()
            await self._asegurar_acceso_plaza(plaza_id)
            await plaza_service.suspender_plaza(plaza_id)
            await self._recargar_contexto_actual()
            return rx.toast.success("Plaza suspendida")
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "suspender plaza")

    async def reactivar_plaza(self, plaza_id: int):
        try:
            self._asegurar_permiso_operar_plazas()
            await self._asegurar_acceso_plaza(plaza_id)
            await plaza_service.reactivar_plaza(plaza_id)
            await self._recargar_contexto_actual()
            return rx.toast.success("Plaza reactivada")
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "reactivar plaza")
