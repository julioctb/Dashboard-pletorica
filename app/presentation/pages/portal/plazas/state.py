"""State para /portal/plazas enfocado en estructura contractual."""

from __future__ import annotations

import asyncio
from decimal import Decimal, InvalidOperation
from typing import Any

import reflex as rx

from app.core.enums import EstatusContrato, EstatusPlaza
from app.core.text_utils import (
    capitalizar_con_preposiciones,
    capitalizar_palabras,
    normalizar_mayusculas,
)
from app.domain.enums import TipoSueldo
from app.modules.application import (
    categoria_puesto_service,
    contrato_categoria_service,
    empresa_service,
    plaza_service,
    tipo_servicio_service,
)
from app.presentation.pages.backoffice.contratos.contrato_presentacion import (
    serializar_categoria_contrato_detalle,
)
from app.presentation.pages.portal.contrato_plazas.state import ContratoPlazasState
from app.presentation.pages.portal.mis_empleados.state import MisEmpleadosState
from app.presentation.pages.portal.state.portal_state import PortalState
from app.presentation.theme import Colors


FILTRO_TODOS = "all"


class PlazasListadoState(PortalState):
    """Vista resumida de plazas por categoría contractual activa."""

    DEFAULT_PRIMA_RIESGO = ContratoPlazasState.DEFAULT_PRIMA_RIESGO
    DEFAULT_PRIMA_RIESGO_LABEL = ContratoPlazasState.DEFAULT_PRIMA_RIESGO_LABEL
    DIAS_MES_FISCAL = ContratoPlazasState.DIAS_MES_FISCAL

    _parse_decimal_seguro = staticmethod(MisEmpleadosState._parse_decimal_seguro)
    _pluralizar = staticmethod(MisEmpleadosState._pluralizar)
    _formatear_moneda_operativa = staticmethod(
        ContratoPlazasState._formatear_moneda_operativa
    )
    _coerce_tipo_sueldo = staticmethod(ContratoPlazasState._coerce_tipo_sueldo)
    _fecha_calculo_fiscal = ContratoPlazasState._fecha_calculo_fiscal
    _contexto_fiscal_actual = ContratoPlazasState._contexto_fiscal_actual
    _salario_minimo_diario_decimal = ContratoPlazasState._salario_minimo_diario_decimal
    _salario_minimo_mensual_decimal = ContratoPlazasState._salario_minimo_mensual_decimal
    _prima_riesgo_decimal = ContratoPlazasState._prima_riesgo_decimal
    _factor_integracion_actual = ContratoPlazasState._factor_integracion_actual
    _calcular_snapshot_desde_bruto = ContratoPlazasState._calcular_snapshot_desde_bruto
    _resolver_bruto_desde_neto = ContratoPlazasState._resolver_bruto_desde_neto
    _calcular_snapshot_categoria = ContratoPlazasState._calcular_snapshot_categoria

    _is_loading: bool = False
    _contratos_resumen: list[dict] = []
    _filas_categoria: list[dict] = []

    contrato_seleccionado: str = FILTRO_TODOS

    empresa_prima_riesgo: str = ""
    empresa_tiene_nivel_riesgo_configurado: bool = False
    empresa_nombre_fiscal: str = ""
    modal_categoria_rapida_abierto: bool = False
    tipos_servicio_catalogo_rapido: list[dict] = []
    form_tipo_servicio_rapido_id: str = ""
    form_nombre_categoria_rapida: str = ""
    form_clave_categoria_rapida: str = ""
    form_salario_categoria_rapida: str = ""
    error_tipo_servicio_rapido: str = ""
    error_nombre_categoria_rapida: str = ""
    error_clave_categoria_rapida: str = ""
    error_salario_categoria_rapida: str = ""

    @staticmethod
    def _normalizar_selector_contrato(valor: str | int | None) -> str:
        codigo = normalizar_mayusculas(str(valor or ""))
        if codigo in {"", FILTRO_TODOS.upper()}:
            return FILTRO_TODOS
        return codigo

    @staticmethod
    def _resolver_color_cobertura(
        porcentaje: int,
        *,
        umbral_warning: int = 40,
    ) -> str:
        if porcentaje <= 0:
            return Colors.TEXT_MUTED
        if porcentaje >= 80:
            return Colors.SUCCESS
        if porcentaje >= umbral_warning:
            return Colors.WARNING
        return Colors.ERROR

    @staticmethod
    def _resolver_scheme_cobertura(porcentaje: int) -> str:
        if porcentaje >= 80:
            return "green"
        if porcentaje >= 40:
            return "amber"
        return "red"

    @classmethod
    def _resolver_color_cobertura_metrica(cls, porcentaje: int) -> str:
        return cls._resolver_color_cobertura(porcentaje, umbral_warning=60)

    def _sumar_costos(self, filas: list[dict], campo: str) -> Decimal:
        total = Decimal("0")
        for fila in filas:
            total += self._parse_decimal_seguro(fila.get(campo))
        return total

    async def _cargar_contexto_fiscal_empresa(self) -> None:
        self.empresa_prima_riesgo = ""
        self.empresa_tiene_nivel_riesgo_configurado = False
        self.empresa_nombre_fiscal = str(self.nombre_empresa_actual or "").strip()

        if not self.id_empresa_actual:
            return

        try:
            empresa = await empresa_service.obtener_por_id(self.id_empresa_actual)
            self.empresa_nombre_fiscal = str(
                getattr(empresa, "nombre_comercial", "") or self.nombre_empresa_actual or ""
            ).strip()
            prima = getattr(empresa, "prima_riesgo", None)
            if prima is not None:
                self.empresa_tiene_nivel_riesgo_configurado = True
                self.empresa_prima_riesgo = str(prima)
        except Exception:
            self.empresa_prima_riesgo = ""
            self.empresa_tiene_nivel_riesgo_configurado = False

    async def _cargar_tipos_servicio_catalogo_rapido(self) -> None:
        """Carga tipos de servicio activos de la empresa para el modal rápido."""
        self.tipos_servicio_catalogo_rapido = []
        if not self.id_empresa_actual:
            return

        try:
            tipos = await tipo_servicio_service.obtener_activas_portal_empresa(
                self.id_empresa_actual,
            )
        except Exception:
            tipos = []

        opciones = []
        for tipo in tipos or []:
            tipo_id = int(getattr(tipo, "id", 0) or 0)
            nombre = str(getattr(tipo, "nombre", "") or "").strip()
            if tipo_id <= 0 or not nombre:
                continue
            opciones.append(
                {
                    "id": tipo_id,
                    "id_str": str(tipo_id),
                    "nombre_display": capitalizar_con_preposiciones(nombre),
                }
            )
        opciones.sort(key=lambda item: str(item.get("nombre_display") or "").lower())
        self.tipos_servicio_catalogo_rapido = opciones

    @staticmethod
    def _conteos_plazas_por_categoria(plazas: list[Any]) -> dict[int, dict[str, int]]:
        conteos: dict[int, dict[str, int]] = {}
        for plaza in plazas:
            categoria_id = int(getattr(plaza, "categoria_puesto_id", 0) or 0)
            if categoria_id <= 0:
                continue

            item = conteos.setdefault(
                categoria_id,
                {
                    "total": 0,
                    "ocupadas": 0,
                    "sin_sede": 0,
                },
            )
            item["total"] += 1

            estatus = str(getattr(plaza, "estatus", "") or "").upper()
            if estatus == EstatusPlaza.OCUPADA.value:
                item["ocupadas"] += 1

            sede_id = int(getattr(plaza, "sede_id", 0) or 0)
            if sede_id <= 0:
                item["sin_sede"] += 1

        return conteos

    def _serializar_contrato_resumen(
        self,
        resumen_contrato: dict,
        plazas: list[Any],
    ) -> dict:
        total_plazas = int(resumen_contrato.get("total_plazas") or 0)
        ocupadas = int(resumen_contrato.get("plazas_ocupadas") or 0)
        vacantes = int(resumen_contrato.get("plazas_vacantes") or 0)
        suspendidas = int(resumen_contrato.get("plazas_suspendidas") or 0)
        plazas_sin_sede = sum(
            1 for plaza in plazas if int(getattr(plaza, "sede_id", 0) or 0) <= 0
        )
        cobertura_pct = (
            int(round((ocupadas / total_plazas) * 100)) if total_plazas > 0 else 0
        )
        cobertura_color = self._resolver_color_cobertura(cobertura_pct)
        codigo = normalizar_mayusculas(str(resumen_contrato.get("contrato_codigo") or ""))

        return {
            "contrato_id": int(resumen_contrato.get("contrato_id") or 0),
            "codigo": codigo,
            "tipo_servicio": capitalizar_con_preposiciones(
                str(resumen_contrato.get("tipo_servicio_nombre") or "Sin tipo de servicio")
            ),
            "estatus": str(resumen_contrato.get("contrato_estatus") or "").upper(),
            "total_plazas": total_plazas,
            "ocupadas": ocupadas,
            "vacantes": vacantes,
            "suspendidas": suspendidas,
            "plazas_sin_sede": plazas_sin_sede,
            "cobertura_pct": cobertura_pct,
            "cobertura_color": cobertura_color,
            "cobertura_width": f"{min(max(cobertura_pct, 0), 100)}%",
            "cobertura_texto": f"{ocupadas}/{total_plazas}",
            "ruta_edicion": PortalState.construir_ruta_plazas_contrato(codigo),
        }

    def _serializar_filas_contrato(
        self,
        contrato: dict,
        categorias: list[Any],
        plazas: list[Any],
    ) -> list[dict]:
        conteos_categoria = self._conteos_plazas_por_categoria(plazas)
        filas: list[dict] = []

        for resumen_categoria in categorias or []:
            categoria = serializar_categoria_contrato_detalle(resumen_categoria)
            categoria_id = int(categoria.get("categoria_puesto_id") or 0)
            categoria_row_id = int(categoria.get("id") or 0)
            conteos = conteos_categoria.get(
                categoria_id,
                {"total": 0, "ocupadas": 0, "sin_sede": 0},
            )

            sueldo_base = self._parse_decimal_seguro(categoria.get("sueldo_base"))
            tipo_sueldo = self._coerce_tipo_sueldo(categoria.get("tipo_sueldo") or TipoSueldo.BRUTO.value)
            snapshot = self._calcular_snapshot_categoria(sueldo_base, tipo_sueldo)
            sueldo_bruto = Decimal(str(snapshot.get("sueldo_bruto") or 0))
            costo_empresa = Decimal(str(snapshot.get("costo_empresa") or 0))
            sueldo_diario = Decimal(str(snapshot.get("sueldo_diario") or 0))
            carga_patronal_pct = Decimal(str(snapshot.get("carga_patronal_pct") or 0))

            total_actual = int(conteos["total"] or 0)
            ocupadas = int(conteos["ocupadas"] or 0)
            pct_cobertura = (
                int(round((ocupadas / total_actual) * 100)) if total_actual > 0 else 0
            )
            cobertura_color = self._resolver_color_cobertura(pct_cobertura)
            costo_total_presupuestado = sueldo_bruto * Decimal(str(total_actual))
            costo_total_actual = sueldo_bruto * Decimal(str(ocupadas))
            cantidad_minima = int(categoria.get("cantidad_minima") or 0)
            cantidad_maxima_raw = int(categoria.get("cantidad_maxima") or 0)

            if cantidad_maxima_raw > 0:
                plazas_rango_texto = f"Min {cantidad_minima} · Max {cantidad_maxima_raw}"
            else:
                plazas_rango_texto = f"Min {cantidad_minima}"

            filas.append(
                {
                    "id": categoria_row_id,
                    "categoria_puesto_id": categoria_id,
                    "contrato_id": int(contrato.get("contrato_id") or 0),
                    "codigo_contrato": contrato.get("codigo", ""),
                    "descripcion_contrato": contrato.get("tipo_servicio", ""),
                    "ruta_edicion": contrato.get("ruta_edicion", ""),
                    "tipo_servicio": contrato.get("tipo_servicio", ""),
                    "nombre_categoria": capitalizar_palabras(
                        str(
                            categoria.get("nombre")
                            or categoria.get("categoria_nombre")
                            or "Sin categoría"
                        )
                    ),
                    "sueldo_bruto": str(sueldo_bruto),
                    "sueldo_bruto_fmt": self._formatear_moneda_operativa(sueldo_bruto),
                    "sueldo_diario_fmt": self._formatear_moneda_operativa(sueldo_diario),
                    "sueldo_diario_label": (
                        "Diario: " + self._formatear_moneda_operativa(sueldo_diario)
                    ),
                    "costo_empresa": str(costo_empresa),
                    "costo_empresa_fmt": self._formatear_moneda_operativa(costo_empresa),
                    "carga_patronal_pct_texto": f"+{carga_patronal_pct:.2f}%",
                    "min_plazas": cantidad_minima,
                    "max_plazas": cantidad_maxima_raw if cantidad_maxima_raw > 0 else None,
                    "min_plazas_texto": str(cantidad_minima),
                    "max_plazas_texto": (
                        str(cantidad_maxima_raw) if cantidad_maxima_raw > 0 else "—"
                    ),
                    "max_plazas_es_null": cantidad_maxima_raw <= 0,
                    "plazas_rango_texto": plazas_rango_texto,
                    "total_plazas_actual": total_actual,
                    "ocupadas": ocupadas,
                    "plazas_sin_sede": int(conteos["sin_sede"] or 0),
                    "pct_cobertura": pct_cobertura,
                    "cobertura_texto": f"{ocupadas}/{total_actual}",
                    "cobertura_color": cobertura_color,
                    "cobertura_color_scheme": self._resolver_scheme_cobertura(pct_cobertura),
                    "cobertura_width": f"{min(max(pct_cobertura, 0), 100)}%",
                    "costo_total_presupuestado": str(costo_total_presupuestado),
                    "costo_total_presupuestado_fmt": self._formatear_moneda_operativa(
                        costo_total_presupuestado
                    ),
                    "costo_total_actual": str(costo_total_actual),
                    "costo_total_actual_fmt": self._formatear_moneda_operativa(
                        costo_total_actual
                    ),
                    "costo_total_actual_label": (
                        self._formatear_moneda_operativa(costo_total_actual) + " actual"
                    ),
                    "mostrar_costo_total_actual": ocupadas > 0,
                    "mostrar_warning_salario_minimo": bool(
                        snapshot.get("es_menor_salario_minimo", False)
                    ),
                    "imss_obrero_fmt": self._formatear_moneda_operativa(
                        Decimal(str(snapshot.get("imss_obrero") or 0))
                    ),
                    "imss_patronal_fmt": self._formatear_moneda_operativa(
                        Decimal(str(snapshot.get("imss_patronal") or 0))
                    ),
                    "isr_estimado_fmt": self._formatear_moneda_operativa(
                        Decimal(str(snapshot.get("isr_estimado") or 0))
                    ),
                    "infonavit_fmt": self._formatear_moneda_operativa(
                        Decimal(str(snapshot.get("infonavit") or 0))
                    ),
                    "retiro_cesantia_fmt": self._formatear_moneda_operativa(
                        Decimal(str(snapshot.get("retiro_cesantia") or 0))
                    ),
                    "neto_estimado_fmt": self._formatear_moneda_operativa(
                        Decimal(str(snapshot.get("sueldo_neto") or 0))
                    ),
                }
            )

        filas.sort(
            key=lambda item: (
                str(item.get("codigo_contrato") or ""),
                str(item.get("nombre_categoria") or ""),
                int(item.get("id") or 0),
            )
        )
        return filas

    async def cargar_contratos(self):
        """Carga contratos activos y sus categorías contractuales."""
        resultado = await self.on_mount_portal()
        if resultado:
            self._is_loading = False
            yield resultado
            return

        if not self.mostrar_seccion_plazas_portal:
            yield rx.redirect("/portal")
            return

        self._is_loading = True
        yield

        try:
            empresa_id = int(self.id_empresa_actual or 0)
            if empresa_id <= 0:
                self._contratos_resumen = []
                self._filas_categoria = []
                self.contrato_seleccionado = FILTRO_TODOS
                return

            resumenes_contrato = await plaza_service.obtener_resumen_contratos_con_plazas(
                empresa_id=empresa_id,
                solo_activos=True,
            )
            resumenes_activos = [
                item
                for item in list(resumenes_contrato or [])
                if str(item.get("contrato_estatus") or "").upper() == EstatusContrato.ACTIVO.value
            ]
            resumenes_activos.sort(
                key=lambda item: normalizar_mayusculas(str(item.get("contrato_codigo") or ""))
            )

            contrato_ids = [
                int(item.get("contrato_id") or 0)
                for item in resumenes_activos
                if int(item.get("contrato_id") or 0) > 0
            ]

            categorias_resultados, plazas_resultados, _, _ = await asyncio.gather(
                asyncio.gather(
                    *[
                        contrato_categoria_service.obtener_resumen_de_contrato(contrato_id)
                        for contrato_id in contrato_ids
                    ],
                    return_exceptions=True,
                ),
                asyncio.gather(
                    *[
                        plaza_service.obtener_resumen_de_contrato(contrato_id)
                        for contrato_id in contrato_ids
                    ],
                    return_exceptions=True,
                ),
                self._cargar_contexto_fiscal_empresa(),
                self._cargar_tipos_servicio_catalogo_rapido(),
            )

            contratos: list[dict] = []
            filas_categoria: list[dict] = []
            for resumen_contrato, categorias, plazas in zip(
                resumenes_activos,
                categorias_resultados,
                plazas_resultados,
            ):
                categorias_lista = [] if isinstance(categorias, Exception) else list(categorias or [])
                plazas_lista = [] if isinstance(plazas, Exception) else list(plazas or [])

                contrato = self._serializar_contrato_resumen(resumen_contrato, plazas_lista)
                contratos.append(contrato)
                filas_categoria.extend(
                    self._serializar_filas_contrato(
                        contrato,
                        categorias_lista,
                        plazas_lista,
                    )
                )

            self._contratos_resumen = contratos
            self._filas_categoria = filas_categoria

            seleccion_actual = self._normalizar_selector_contrato(self.contrato_seleccionado)
            codigos_validos = {item.get("codigo", "") for item in contratos}
            if seleccion_actual != FILTRO_TODOS and seleccion_actual not in codigos_validos:
                self.contrato_seleccionado = FILTRO_TODOS
            else:
                self.contrato_seleccionado = seleccion_actual
        except Exception as exc:
            print(f"Error cargando /portal/plazas: {exc}")
            self._contratos_resumen = []
            self._filas_categoria = []
            self.contrato_seleccionado = FILTRO_TODOS
        finally:
            self._is_loading = False

    @rx.var
    def is_loading(self) -> bool:
        return self._is_loading

    @rx.var
    def nombre_empresa(self) -> str:
        return str(self.nombre_empresa_actual or "Empresa actual").strip()

    @rx.var
    def tiene_contratos_activos(self) -> bool:
        return len(self._contratos_resumen) > 0

    @rx.var
    def contratos_activos_total(self) -> int:
        return len(self._contratos_resumen)

    @rx.var
    def contratos_visibles(self) -> list[dict]:
        if self.contrato_seleccionado == FILTRO_TODOS:
            return list(self._contratos_resumen)
        codigo = self._normalizar_selector_contrato(self.contrato_seleccionado)
        return [
            item
            for item in self._contratos_resumen
            if str(item.get("codigo") or "") == codigo
        ]

    @rx.var
    def filas_categoria_visibles(self) -> list[dict]:
        codigo = self._normalizar_selector_contrato(self.contrato_seleccionado)
        return [
            fila
            for fila in self._filas_categoria
            if codigo == FILTRO_TODOS or str(fila.get("codigo_contrato") or "") == codigo
        ]

    @rx.var
    def tiene_filas_categoria(self) -> bool:
        return len(self.filas_categoria_visibles) > 0

    @rx.var
    def filas_tabla(self) -> list[dict]:
        """Lista plana con separadores de sección + filas de detalle por contrato."""
        filas = self.filas_categoria_visibles
        grupos: dict[int, dict] = {}
        orden: list[int] = []

        for fila in filas:
            cat_id = int(fila.get("categoria_puesto_id") or 0)
            if cat_id <= 0:
                continue
            if cat_id not in grupos:
                grupos[cat_id] = {
                    "categoria_puesto_id": cat_id,
                    "nombre_categoria": fila.get("nombre_categoria", ""),
                    "tipo_servicio": fila.get("tipo_servicio", ""),
                    "detalles": [],
                    "sueldos": [],
                    "sum_min": 0,
                    "sum_max_definido": 0,
                    "tiene_max_abierto": False,
                    "sum_ocupadas": 0,
                    "sum_total": 0,
                }
                orden.append(cat_id)
            grupo = grupos[cat_id]
            grupo["detalles"].append(fila)
            grupo["sueldos"].append(self._parse_decimal_seguro(fila.get("sueldo_bruto")))
            grupo["sum_min"] += int(fila.get("min_plazas") or 0)
            max_raw = fila.get("max_plazas")
            if max_raw is None:
                grupo["tiene_max_abierto"] = True
            else:
                grupo["sum_max_definido"] += int(max_raw or 0)
            grupo["sum_ocupadas"] += int(fila.get("ocupadas") or 0)
            grupo["sum_total"] += int(fila.get("total_plazas_actual") or 0)

        resultado: list[dict] = []
        for cat_id in orden:
            grupo = grupos[cat_id]
            detalles = grupo["detalles"]
            total_contratos = len(detalles)
            sueldos = grupo["sueldos"]
            sueldo_min = min(sueldos) if sueldos else Decimal("0")
            sueldo_max = max(sueldos) if sueldos else Decimal("0")
            if sueldo_min == sueldo_max:
                sueldo_separador = self._formatear_moneda_operativa(sueldo_min)
            else:
                sueldo_separador = (
                    self._formatear_moneda_operativa(sueldo_min)
                    + " – "
                    + self._formatear_moneda_operativa(sueldo_max)
                )

            sum_total = int(grupo["sum_total"])
            sum_ocupadas = int(grupo["sum_ocupadas"])
            pct = int(round((sum_ocupadas / sum_total) * 100)) if sum_total > 0 else 0
            sum_max_texto = (
                "—"
                if grupo["tiene_max_abierto"]
                else str(int(grupo["sum_max_definido"]))
            )
            meta_texto = (
                f"{grupo['tipo_servicio']} · {total_contratos} "
                f"{self._pluralizar(total_contratos, 'contrato', 'contratos')}"
            )

            resultado.append(
                {
                    "key": f"sep-{cat_id}",
                    "es_separador": True,
                    "nombre_categoria": grupo["nombre_categoria"],
                    "meta_texto": meta_texto,
                    "sueldo_separador_texto": sueldo_separador,
                    "sum_min_texto": str(int(grupo["sum_min"])),
                    "sum_max_texto": sum_max_texto,
                    "cobertura_texto": f"{sum_ocupadas}/{sum_total}",
                    "cobertura_color": self._resolver_color_cobertura(pct),
                    # Campos de detalle (placeholders para mismo shape)
                    "codigo_contrato": "",
                    "descripcion_contrato": "",
                    "sueldo_bruto_fmt": "",
                    "sueldo_diario_label": "",
                    "mostrar_warning_salario_minimo": False,
                    "min_plazas_texto": "",
                    "max_plazas_texto": "",
                    "max_plazas_es_null": False,
                    "cobertura_color_scheme": "gray",
                }
            )
            for detalle in detalles:
                resultado.append(
                    {
                        "key": f"det-{int(detalle.get('id') or 0)}",
                        "es_separador": False,
                        # Separador placeholders
                        "nombre_categoria": "",
                        "meta_texto": "",
                        "sueldo_separador_texto": "",
                        "sum_min_texto": "",
                        "sum_max_texto": "",
                        "cobertura_color": Colors.TEXT_MUTED,
                        # Detalle
                        "codigo_contrato": detalle.get("codigo_contrato", ""),
                        "descripcion_contrato": detalle.get("descripcion_contrato", ""),
                        "sueldo_bruto_fmt": detalle.get("sueldo_bruto_fmt", ""),
                        "sueldo_diario_label": detalle.get("sueldo_diario_label", ""),
                        "mostrar_warning_salario_minimo": bool(
                            detalle.get("mostrar_warning_salario_minimo", False)
                        ),
                        "min_plazas_texto": detalle.get("min_plazas_texto", ""),
                        "max_plazas_texto": detalle.get("max_plazas_texto", ""),
                        "max_plazas_es_null": bool(detalle.get("max_plazas_es_null", False)),
                        "cobertura_texto": detalle.get("cobertura_texto", ""),
                        "cobertura_color_scheme": detalle.get(
                            "cobertura_color_scheme", "gray"
                        ),
                    }
                )
        return resultado

    @rx.var
    def tiene_filas_tabla(self) -> bool:
        return len(self.filas_tabla) > 0

    @rx.var
    def plazas_configuradas(self) -> int:
        return sum(int(item.get("total_plazas") or 0) for item in self.contratos_visibles)

    @rx.var
    def plazas_ocupadas(self) -> int:
        return sum(int(item.get("ocupadas") or 0) for item in self.contratos_visibles)

    @rx.var
    def plazas_vacantes(self) -> int:
        return sum(int(item.get("vacantes") or 0) for item in self.contratos_visibles)

    @rx.var
    def plazas_suspendidas(self) -> int:
        return sum(int(item.get("suspendidas") or 0) for item in self.contratos_visibles)

    @rx.var
    def plazas_sin_sede(self) -> int:
        return sum(int(item.get("plazas_sin_sede") or 0) for item in self.filas_categoria_visibles)

    @rx.var
    def categorias_sin_sede(self) -> int:
        return sum(
            1 for item in self.filas_categoria_visibles if int(item.get("plazas_sin_sede") or 0) > 0
        )

    @rx.var
    def cobertura_pct(self) -> int:
        if self.plazas_configuradas <= 0:
            return 0
        return int(round((self.plazas_ocupadas / self.plazas_configuradas) * 100))

    @rx.var
    def cobertura_pct_texto(self) -> str:
        return f"{self.cobertura_pct}%"

    @rx.var
    def cobertura_texto(self) -> str:
        return f"{self.plazas_ocupadas}/{self.plazas_configuradas}"

    @rx.var
    def cobertura_color_metrica(self) -> str:
        return self._resolver_color_cobertura_metrica(self.cobertura_pct)

    @rx.var
    def cobertura_color_chip_global(self) -> str:
        return self._resolver_color_cobertura(self.cobertura_pct)

    @rx.var
    def cobertura_width(self) -> str:
        return f"{min(max(self.cobertura_pct, 0), 100)}%"

    @rx.var
    def presupuesto_mensual(self) -> Decimal:
        return self._sumar_costos(self.filas_categoria_visibles, "costo_total_presupuestado")

    @rx.var
    def costo_real_mensual(self) -> Decimal:
        return self._sumar_costos(self.filas_categoria_visibles, "costo_total_actual")

    @rx.var
    def presupuesto_mensual_fmt(self) -> str:
        return self._formatear_moneda_operativa(self.presupuesto_mensual)

    @rx.var
    def costo_real_mensual_fmt(self) -> str:
        return self._formatear_moneda_operativa(self.costo_real_mensual)

    @rx.var
    def descripcion_metrica_plazas(self) -> str:
        total = len(self.contratos_visibles)
        return f"{total} {self._pluralizar(total, 'contrato activo', 'contratos activos')}"

    @rx.var
    def descripcion_metrica_cobertura(self) -> str:
        return f"{self.plazas_ocupadas} ocupadas de {self.plazas_configuradas}"

    @rx.var
    def descripcion_metrica_presupuesto(self) -> str:
        return "Todas las plazas"

    @rx.var
    def descripcion_metrica_costo_real(self) -> str:
        return "Solo ocupadas"

    @rx.var
    def chips_contrato(self) -> list[dict]:
        chips = [
            {
                "selector_value": FILTRO_TODOS,
                "codigo_display": "Todos",
                "descripcion": self.descripcion_metrica_plazas,
                "cobertura_texto": self.cobertura_texto,
                "cobertura_pct": self.cobertura_pct,
                "cobertura_color": self.cobertura_color_chip_global,
                "cobertura_width": self.cobertura_width,
                "activo": self.contrato_seleccionado == FILTRO_TODOS,
            }
        ]

        for contrato in self._contratos_resumen:
            chips.append(
                {
                    "selector_value": contrato.get("codigo", ""),
                    "codigo_display": contrato.get("codigo", ""),
                    "descripcion": contrato.get("tipo_servicio", ""),
                    "cobertura_texto": contrato.get("cobertura_texto", "0/0"),
                    "cobertura_pct": int(contrato.get("cobertura_pct") or 0),
                    "cobertura_color": contrato.get("cobertura_color", Colors.TEXT_MUTED),
                    "cobertura_width": contrato.get("cobertura_width", "0%"),
                    "activo": self.contrato_seleccionado == contrato.get("codigo", ""),
                }
            )

        return chips

    @rx.var
    def mostrar_callout_sin_sede(self) -> bool:
        return self.plazas_sin_sede > 0

    @rx.var
    def mensaje_callout_sin_sede(self) -> str:
        plazas = self.plazas_sin_sede
        categorias = self.categorias_sin_sede
        return (
            f"{plazas} {self._pluralizar(plazas, 'plaza', 'plazas')} sin sede asignada en "
            f"{categorias} {self._pluralizar(categorias, 'categoría', 'categorías')} — "
            f"{'requiere' if plazas == 1 else 'requieren'} configuración"
        )

    @rx.var
    def puede_editar_configuracion(self) -> bool:
        return (
            self.contrato_seleccionado != FILTRO_TODOS
            and len(self.contratos_visibles) == 1
        )

    @rx.var
    def ruta_editar_configuracion(self) -> str:
        if not self.puede_editar_configuracion:
            return ""
        return str(self.contratos_visibles[0].get("ruta_edicion") or "")

    @rx.var
    def titulo_empty_state(self) -> str:
        if not self.tiene_contratos_activos:
            return "No hay contratos activos con personal"
        return "No hay categorías configuradas en contratos activos"

    @rx.var
    def descripcion_empty_state(self) -> str:
        if not self.tiene_contratos_activos:
            return (
                "Los contratos activos con personal aparecerán aquí para monitorear cobertura, "
                "sueldos y presupuesto."
            )
        return (
            "Agrega categorías en un contrato activo para visualizar estructura, costos y cobertura."
        )

    @rx.var
    def caption_tabla(self) -> str:
        if not self.tiene_filas_categoria:
            return ""
        categorias = len(self.filas_categoria_visibles)
        contratos = len(self.contratos_visibles)
        return (
            f"{categorias} {self._pluralizar(categorias, 'categoría', 'categorías')} en "
            f"{contratos} {self._pluralizar(contratos, 'contrato', 'contratos')} · "
            f"{self.plazas_configuradas} {self._pluralizar(self.plazas_configuradas, 'plaza', 'plazas')} totales · "
            f"Presupuesto: {self.presupuesto_mensual_fmt}/mes"
        )

    @rx.var
    def tipos_servicio_catalogo_rapido_options(self) -> list[dict]:
        return [
            {
                "value": item["id_str"],
                "label": item["nombre_display"],
            }
            for item in self.tipos_servicio_catalogo_rapido
        ]

    @rx.var
    def puede_guardar_categoria_rapida(self) -> bool:
        return (
            bool(self.form_tipo_servicio_rapido_id)
            and bool(str(self.form_nombre_categoria_rapida or "").strip())
            and not self.saving
        )

    def _limpiar_form_categoria_rapida(self) -> None:
        self.form_tipo_servicio_rapido_id = ""
        self.form_nombre_categoria_rapida = ""
        self.form_clave_categoria_rapida = ""
        self.form_salario_categoria_rapida = ""
        self.error_tipo_servicio_rapido = ""
        self.error_nombre_categoria_rapida = ""
        self.error_clave_categoria_rapida = ""
        self.error_salario_categoria_rapida = ""

    @staticmethod
    def _parse_salario_categoria_rapida(valor: str) -> Decimal:
        limpio = (
            str(valor or "")
            .replace(",", "")
            .replace("$", "")
            .replace(" ", "")
            .strip()
        )
        if not limpio:
            return Decimal("0")
        try:
            return Decimal(limpio)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Capture un salario base válido") from exc

    def abrir_modal_categoria_rapida(self):
        self._limpiar_form_categoria_rapida()
        if not self.tipos_servicio_catalogo_rapido:
            return rx.redirect("/portal/empresa/categorias")
        self.form_tipo_servicio_rapido_id = self.tipos_servicio_catalogo_rapido[0]["id_str"]
        self.modal_categoria_rapida_abierto = True

    def cerrar_modal_categoria_rapida(self):
        self.modal_categoria_rapida_abierto = False
        self._limpiar_form_categoria_rapida()

    def set_form_tipo_servicio_rapido_id(self, value: str):
        self.form_tipo_servicio_rapido_id = value
        self.error_tipo_servicio_rapido = ""

    def set_form_nombre_categoria_rapida(self, value: str):
        self.form_nombre_categoria_rapida = value
        self.error_nombre_categoria_rapida = ""

    def set_form_clave_categoria_rapida(self, value: str):
        self.form_clave_categoria_rapida = normalizar_mayusculas(value)
        self.error_clave_categoria_rapida = ""

    def set_form_salario_categoria_rapida(self, value: str):
        self.form_salario_categoria_rapida = value
        self.error_salario_categoria_rapida = ""

    def _validar_categoria_rapida(self) -> bool:
        self.error_tipo_servicio_rapido = ""
        self.error_nombre_categoria_rapida = ""
        self.error_clave_categoria_rapida = ""
        self.error_salario_categoria_rapida = ""

        if not self.form_tipo_servicio_rapido_id:
            self.error_tipo_servicio_rapido = "Seleccione un tipo de servicio"
        if not str(self.form_nombre_categoria_rapida or "").strip():
            self.error_nombre_categoria_rapida = "Capture un nombre para la categoría"
        try:
            self._parse_salario_categoria_rapida(self.form_salario_categoria_rapida)
        except ValueError as error:
            self.error_salario_categoria_rapida = str(error)

        return not any(
            (
                self.error_tipo_servicio_rapido,
                self.error_nombre_categoria_rapida,
                self.error_clave_categoria_rapida,
                self.error_salario_categoria_rapida,
            )
        )

    async def crear_categoria_rapida(self):
        if not self._validar_categoria_rapida():
            yield self.crear_toast("Corrija los errores del formulario", "error")
            return

        salario = self._parse_salario_categoria_rapida(self.form_salario_categoria_rapida)
        self.saving = True
        yield
        try:
            await categoria_puesto_service.crear_portal_empresa(
                self.id_empresa_actual,
                tipo_servicio_id=int(self.form_tipo_servicio_rapido_id),
                nombre=self.form_nombre_categoria_rapida,
                clave=self.form_clave_categoria_rapida,
                salario_base_mensual=salario,
            )
            self.modal_categoria_rapida_abierto = False
            self._limpiar_form_categoria_rapida()
            yield self.crear_toast("Categoría agregada al catálogo", "success")
        except Exception as error:
            mensaje = str(error)
            if "clave" in mensaje.lower():
                self.error_clave_categoria_rapida = mensaje
            elif "tipo" in mensaje.lower():
                self.error_tipo_servicio_rapido = mensaje
            elif "nombre" in mensaje.lower():
                self.error_nombre_categoria_rapida = mensaje
            else:
                yield self.manejar_error_con_toast(error, "al crear la categoría")
        finally:
            self.saving = False
            yield

    def seleccionar_contrato(self, codigo_contrato: str):
        self.contrato_seleccionado = self._normalizar_selector_contrato(codigo_contrato)

    def ir_a_plazas_contrato(self, codigo_contrato: str | int):
        ruta = PortalState.construir_ruta_plazas_contrato(codigo_contrato)
        if ruta == "/portal/contratos":
            return rx.redirect("/portal/plazas")
        return rx.redirect(ruta)

    def ir_a_editar_configuracion(self):
        if not self.puede_editar_configuracion:
            return None
        return rx.redirect(self.ruta_editar_configuracion)

    def ir_a_catalogo_puestos(self):
        return rx.redirect("/portal/empresa/categorias")

    def ir_a_contratos(self):
        return rx.redirect("/portal/contratos")
