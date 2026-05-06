"""State de plazas por contrato en portal."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

import reflex as rx

from app.core.calculations import CalculadoraIMSS, CalculadoraISR
from app.core.catalogs import CatalogoINFONAVIT, Tolerancias
from app.core.catalogs.fiscal.politica import PoliticaFiscalResolver
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.text_utils import (
    capitalizar_con_preposiciones,
    capitalizar_palabras,
    formatear_moneda,
    formatear_vigencia_meses,
    normalizar_mayusculas,
)
from app.domain.enums import EstatusPlaza, TipoSueldo
from app.domain.models.costo_patronal import ConfiguracionEmpresa
from app.modules.application import (
    contrato_categoria_service,
    contrato_service,
    empresa_service,
)
from app.presentation.pages.backoffice.contratos.contrato_presentacion import (
    enriquecer_contrato_presentacion,
    serializar_categoria_contrato_detalle,
)
from app.presentation.pages.portal.mis_empleados.state import (
    MisEmpleadosState,
    VISTA_PERSONAL_PLAZA,
)
from app.presentation.pages.portal.state.portal_state import PortalState
from app.presentation.theme import Colors

logger = logging.getLogger(__name__)

DEFAULT_PRIMA_RIESGO = Decimal("0.025984")
DEFAULT_PRIMA_RIESGO_LABEL = "2.59840%"
DIAS_MES_FISCAL = Decimal("30")


class ContratoPlazasState(MisEmpleadosState):
    """Vista portal de plazas ligada a un contrato específico."""

    DEFAULT_PRIMA_RIESGO = DEFAULT_PRIMA_RIESGO
    DEFAULT_PRIMA_RIESGO_LABEL = DEFAULT_PRIMA_RIESGO_LABEL
    DIAS_MES_FISCAL = DIAS_MES_FISCAL

    contrato_actual_portal: dict = {}
    categorias_detalle_contrato: list[dict] = []
    tab_activa: str = "plazas"
    modal_categoria_abierto: bool = False
    categoria_editando_id: int = 0
    form_nombre_categoria: str = ""
    form_tipo_sueldo: str = TipoSueldo.BRUTO.value
    form_sueldo_base: str = ""
    form_costo_contractual: str = ""
    form_min_plazas: str = "0"
    form_max_plazas: str = ""
    error_form_nombre_categoria: str = ""
    error_form_sueldo_base: str = ""
    error_form_costo_contractual: str = ""
    error_form_min_plazas: str = ""
    error_form_max_plazas: str = ""
    combobox_nombre_categoria_abierto: bool = False
    nombres_categoria_sugerencias: list[str] = []
    empresa_prima_riesgo: str = ""
    empresa_tiene_nivel_riesgo_configurado: bool = False
    empresa_nombre_fiscal: str = ""

    @staticmethod
    def _estatus_visual_plaza(plaza: dict) -> str:
        """Estado visual unificado: prioriza configuración sobre ocupación.

        Una plaza solo puede estar OCUPADA / VACANTE cuando tiene sede y
        categoría. Si falta cualquiera, reporta SIN_SEDE / SIN_CATEGORIA /
        CONFIGURACION_INCOMPLETA — que el filtro y la UI agrupan como
        "No disponible".
        """
        if not isinstance(plaza, dict):
            return ""
        sede_ok = int(plaza.get("sede_id") or 0) > 0
        categoria_ok = int(plaza.get("categoria_puesto_id") or 0) > 0
        if not sede_ok and not categoria_ok:
            return "CONFIGURACION_INCOMPLETA"
        if not sede_ok:
            return "SIN_SEDE"
        if not categoria_ok:
            return "SIN_CATEGORIA"
        estatus = str(plaza.get("estatus", "") or "").strip().upper()
        if estatus == EstatusPlaza.OCUPADA.value:
            return EstatusPlaza.OCUPADA.value
        if estatus == EstatusPlaza.VACANTE.value:
            return EstatusPlaza.VACANTE.value
        return estatus

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

    def _obtener_codigo_contrato_ruta(self) -> str:
        raw_codigo = ""

        try:
            raw = getattr(self, "codigo_contrato", None)
            if raw is not None and callable(raw) is False:
                raw_codigo = str(raw).strip()
        except Exception:
            raw_codigo = ""

        if not raw_codigo:
            try:
                raw = getattr(self, "contrato_codigo", None)
                if raw is not None and callable(raw) is False:
                    raw_codigo = str(raw).strip()
            except Exception:
                raw_codigo = ""

        if not raw_codigo:
            router_data = self.router_data or {}
            for fuente in ("query", "params", "path_params", "kwargs"):
                datos = router_data.get(fuente, {}) or {}
                for llave in (
                    "codigo_contrato",
                    "contrato_codigo",
                    "id_contrato",
                    "contrato_id",
                    "id",
                ):
                    raw_codigo = str(datos.get(llave) or "").strip()
                    if raw_codigo:
                        break
                if raw_codigo:
                    break

        if not raw_codigo:
            path = self._ruta_actual()
            partes = [segmento for segmento in path.strip("/").split("/") if segmento]
            if (
                len(partes) >= 4
                and partes[0] == "portal"
                and partes[1] == "contratos"
                and partes[3] == "plazas"
            ):
                raw_codigo = str(partes[2] or "").strip()

        return normalizar_mayusculas(raw_codigo)

    @staticmethod
    def _formatear_moneda_operativa(monto: Decimal) -> str:
        return formatear_moneda(
            str(monto),
            decimales_fijos=2,
            espacio_simbolo=False,
        )

    def _costos_categoria_por_id(self) -> dict[int, Decimal]:
        costos: dict[int, Decimal] = {}
        for categoria in self.categorias_detalle_contrato:
            categoria_id = int(categoria.get("categoria_puesto_id") or 0)
            if categoria_id <= 0:
                continue
            costos[categoria_id] = self._parse_decimal_seguro(
                categoria.get("costo_unitario"),
            )
        return costos

    def _descripcion_servicio_actual(self) -> str:
        contrato = dict(self.contrato_actual_portal or {})
        descripcion = str(
            contrato.get("descripcion_objeto")
            or contrato.get("descripcion_objeto_display")
            or contrato.get("nombre_servicio_fmt")
            or ""
        ).strip()
        return capitalizar_con_preposiciones(descripcion)

    def _vigencia_contrato_actual(self) -> str:
        contrato = dict(self.contrato_actual_portal or {})
        return formatear_vigencia_meses(
            contrato.get("fecha_inicio"),
            contrato.get("fecha_fin"),
        )

    @staticmethod
    def _decimal_a_texto_input(valor: Decimal) -> str:
        return f"{Tolerancias.redondear_moneda(valor):.2f}" if valor > Decimal("0") else ""

    @staticmethod
    def _coerce_tipo_sueldo(valor) -> TipoSueldo:
        if isinstance(valor, TipoSueldo):
            return valor
        raw = getattr(valor, "value", valor)
        try:
            return TipoSueldo(str(raw or TipoSueldo.BRUTO.value).upper())
        except ValueError:
            return TipoSueldo.BRUTO

    def _tipo_sueldo_form_actual(self) -> TipoSueldo:
        return self._coerce_tipo_sueldo(self.form_tipo_sueldo)

    def _fecha_calculo_fiscal(self) -> date:
        return date.today()

    def _contexto_fiscal_actual(self):
        return PoliticaFiscalResolver.resolver(
            self._fecha_calculo_fiscal(),
            zona_frontera=False,
        )

    def _salario_minimo_diario_decimal(self) -> Decimal:
        return Decimal(
            str(self._contexto_fiscal_actual().salario_minimo_diario_aplicable or 0)
        )

    def _salario_minimo_mensual_decimal(self) -> Decimal:
        return Tolerancias.redondear_moneda(
            self._salario_minimo_diario_decimal() * DIAS_MES_FISCAL
        )

    def _prima_riesgo_decimal(self) -> Decimal:
        prima = self._parse_decimal_seguro(self.empresa_prima_riesgo)
        if prima > Decimal("0"):
            return prima
        return DEFAULT_PRIMA_RIESGO

    def _factor_integracion_actual(self) -> Decimal:
        try:
            configuracion = ConfiguracionEmpresa(
                nombre=self.empresa_nombre_fiscal or "Empresa portal",
                estado="puebla",
                prima_riesgo=float(self._prima_riesgo_decimal()),
            )
            return Decimal(str(configuracion.calcular_factor_integracion(1)))
        except Exception:
            return Decimal("1.0452")

    def _calcular_snapshot_desde_bruto(self, sueldo_bruto: Decimal) -> dict:
        bruto = Tolerancias.redondear_moneda(max(Decimal("0"), sueldo_bruto))
        if bruto <= Decimal("0"):
            return {
                "sueldo_bruto": Decimal("0"),
                "sueldo_neto": Decimal("0"),
                "sueldo_diario": Decimal("0"),
                "costo_empresa": Decimal("0"),
                "carga_patronal_pct": Decimal("0"),
                "imss_obrero": Decimal("0"),
                "imss_patronal": Decimal("0"),
                "isr_estimado": Decimal("0"),
                "infonavit": Decimal("0"),
                "retiro_cesantia": Decimal("0"),
                "es_menor_salario_minimo": False,
            }

        contexto = self._contexto_fiscal_actual()
        salario_diario = bruto / DIAS_MES_FISCAL
        salario_minimo_diario = Decimal(str(contexto.salario_minimo_diario_aplicable or 0))
        es_salario_minimo = (
            salario_minimo_diario > Decimal("0")
            and Tolerancias.es_salario_minimo(salario_diario, salario_minimo_diario)
        )

        factor_integracion = self._factor_integracion_actual()
        sbc_diario = salario_diario * factor_integracion
        tope_sbc = Decimal(str(contexto.tope_sbc or 0))
        if tope_sbc > Decimal("0"):
            sbc_diario = min(sbc_diario, tope_sbc)

        calculadora_imss = CalculadoraIMSS()
        calculadora_isr = CalculadoraISR()
        dias_mes = int(DIAS_MES_FISCAL)
        prima_riesgo = float(self._prima_riesgo_decimal())
        uma_diaria = float(contexto.uma_diaria or 0)

        cuotas_patronales = calculadora_imss.calcular_patronal(
            sbc_diario=float(sbc_diario),
            dias=dias_mes,
            prima_riesgo=prima_riesgo,
            uma_diaria=uma_diaria,
            salario_minimo_diario=float(salario_minimo_diario),
            ano=contexto.fecha_referencia.year,
        )
        cuotas_obreras, imss_obrero_absorbido = calculadora_imss.calcular_obrero(
            sbc_diario=float(sbc_diario),
            dias=dias_mes,
            es_salario_minimo=es_salario_minimo,
            aplicar_art_36=True,
            uma_diaria=uma_diaria,
        )
        isr = calculadora_isr.calcular(
            float(bruto),
            es_salario_minimo=es_salario_minimo,
            fecha_referencia=contexto.fecha_referencia,
        )

        total_imss_patronal = Decimal(str(sum(cuotas_patronales.values())))
        total_imss_obrero = Decimal(str(sum(cuotas_obreras.values())))
        infonavit = Decimal(str(
            float(sbc_diario) * float(CatalogoINFONAVIT.TASA_PATRONAL) * dias_mes
        ))
        isr_estimado = Decimal(str(isr.get("isr_a_retener", 0)))
        neto_estimado = Tolerancias.redondear_moneda(
            bruto - total_imss_obrero - isr_estimado
        )
        carga_patronal_total = Tolerancias.redondear_moneda(
            total_imss_patronal
            + infonavit
            + Decimal(str(imss_obrero_absorbido))
        )
        costo_empresa = Tolerancias.redondear_moneda(bruto + carga_patronal_total)
        retiro_cesantia = Tolerancias.redondear_moneda(
            Decimal(str(cuotas_patronales.get("retiro", 0)))
            + Decimal(str(cuotas_patronales.get("cesantia_vejez", 0)))
        )
        carga_patronal_pct = (
            Tolerancias.redondear_moneda((carga_patronal_total / bruto) * Decimal("100"))
            if bruto > Decimal("0")
            else Decimal("0")
        )

        return {
            "sueldo_bruto": bruto,
            "sueldo_neto": neto_estimado,
            "sueldo_diario": Tolerancias.redondear_moneda(salario_diario),
            "costo_empresa": costo_empresa,
            "carga_patronal_pct": carga_patronal_pct,
            "imss_obrero": Tolerancias.redondear_moneda(total_imss_obrero),
            "imss_patronal": Tolerancias.redondear_moneda(total_imss_patronal),
            "isr_estimado": Tolerancias.redondear_moneda(isr_estimado),
            "infonavit": Tolerancias.redondear_moneda(infonavit),
            "retiro_cesantia": retiro_cesantia,
            "es_menor_salario_minimo": bruto < self._salario_minimo_mensual_decimal(),
        }

    def _resolver_bruto_desde_neto(self, sueldo_neto: Decimal) -> Decimal:
        neto_objetivo = Tolerancias.redondear_moneda(max(Decimal("0"), sueldo_neto))
        if neto_objetivo <= Decimal("0"):
            return Decimal("0")

        minimo_mensual = self._salario_minimo_mensual_decimal()
        inferior = min(neto_objetivo, minimo_mensual if minimo_mensual > Decimal("0") else neto_objetivo)
        superior = max(neto_objetivo * Decimal("2"), minimo_mensual, Decimal("1000"))

        snapshot_superior = self._calcular_snapshot_desde_bruto(superior)
        while snapshot_superior["sueldo_neto"] < neto_objetivo:
            superior *= Decimal("1.5")
            snapshot_superior = self._calcular_snapshot_desde_bruto(superior)
            if superior > Decimal("1000000"):
                break

        for _ in range(40):
            punto_medio = (inferior + superior) / Decimal("2")
            snapshot = self._calcular_snapshot_desde_bruto(punto_medio)
            neto_medio = snapshot["sueldo_neto"]
            if abs(neto_medio - neto_objetivo) <= Decimal("0.01"):
                return Tolerancias.redondear_moneda(punto_medio)
            if neto_medio < neto_objetivo:
                inferior = punto_medio
            else:
                superior = punto_medio

        return Tolerancias.redondear_moneda(superior)

    def _calcular_snapshot_categoria(
        self,
        sueldo_base: Decimal,
        tipo_sueldo: TipoSueldo | str,
    ) -> dict:
        tipo = self._coerce_tipo_sueldo(tipo_sueldo)
        base = Tolerancias.redondear_moneda(max(Decimal("0"), sueldo_base))
        if base <= Decimal("0"):
            return self._calcular_snapshot_desde_bruto(Decimal("0")) | {
                "tipo_sueldo": tipo.value,
                "sueldo_base": Decimal("0"),
            }

        if tipo == TipoSueldo.NETO:
            sueldo_bruto = self._resolver_bruto_desde_neto(base)
        else:
            sueldo_bruto = base

        snapshot = self._calcular_snapshot_desde_bruto(sueldo_bruto)
        snapshot["tipo_sueldo"] = tipo.value
        snapshot["sueldo_base"] = base
        return snapshot

    def _buscar_categoria_detalle(self, categoria_id: int) -> dict:
        for categoria in self.categorias_detalle_contrato:
            if int(categoria.get("id") or 0) == int(categoria_id or 0):
                return dict(categoria)
        return {}

    async def _cargar_contrato_actual_portal(self, codigo_contrato: str) -> None:
        codigo_ruta = normalizar_mayusculas(codigo_contrato)
        contrato = None
        if codigo_ruta:
            contrato = await contrato_service.obtener_por_codigo(codigo_ruta)
        if contrato is None and codigo_ruta.isdigit():
            try:
                contrato = await contrato_service.obtener_por_id(int(codigo_ruta))
            except NotFoundError:
                contrato = None
        if contrato is None:
            raise NotFoundError(f"Contrato {codigo_ruta or codigo_contrato} no encontrado")
        contrato_empresa_id = int(getattr(contrato, "empresa_id", 0) or 0)
        if not self.id_empresa_actual or contrato_empresa_id != int(self.id_empresa_actual):
            raise BusinessRuleError("Solo puedes consultar plazas de contratos de la empresa activa")
        if not bool(getattr(contrato, "tiene_personal", False)):
            raise BusinessRuleError("Este contrato no tiene plazas configurables en portal")
        self.contrato_actual_portal = enriquecer_contrato_presentacion(contrato)

    async def _cargar_categorias_detalle_contrato(self, contrato_id: int) -> None:
        self.categorias_detalle_contrato = []
        if contrato_id <= 0:
            return

        try:
            resumen = await contrato_categoria_service.obtener_resumen_de_contrato(contrato_id)
            categorias: list[dict] = []
            for item in resumen:
                categoria = serializar_categoria_contrato_detalle(item)
                costo_unitario = getattr(item, "costo_unitario", None)
                categoria["costo_unitario"] = str(costo_unitario) if costo_unitario is not None else ""
                categorias.append(categoria)
            self.categorias_detalle_contrato = categorias
        except Exception:
            self.categorias_detalle_contrato = []

    async def _cargar_detalle_contrato(self) -> None:
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        if contrato_id <= 0:
            self.categorias_detalle_contrato = []
            return
        await self._cargar_categorias_detalle_contrato(contrato_id)

    async def _cargar_contexto_fiscal_empresa(self) -> None:
        self.empresa_prima_riesgo = ""
        self.empresa_tiene_nivel_riesgo_configurado = False
        self.empresa_nombre_fiscal = ""
        self.nombres_categoria_sugerencias = []
        if not self.id_empresa_actual:
            return

        try:
            empresa = await empresa_service.obtener_por_id(self.id_empresa_actual)
            self.empresa_nombre_fiscal = str(
                getattr(empresa, "nombre_comercial", "") or ""
            ).strip()
            prima = getattr(empresa, "prima_riesgo", None)
            if prima is not None:
                self.empresa_tiene_nivel_riesgo_configurado = True
                self.empresa_prima_riesgo = str(prima)
        except Exception:
            self.empresa_prima_riesgo = ""
            self.empresa_tiene_nivel_riesgo_configurado = False

        try:
            self.nombres_categoria_sugerencias = (
                await contrato_categoria_service.obtener_sugerencias_nombres_empresa(
                    int(self.id_empresa_actual),
                )
            )
        except Exception:
            self.nombres_categoria_sugerencias = []

    async def on_mount_contrato_plazas(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return

        if not self.mostrar_seccion_plazas_portal:
            yield rx.redirect("/portal")
            return

        codigo_contrato = self._obtener_codigo_contrato_ruta()
        if not codigo_contrato:
            yield rx.redirect("/portal/contratos")
            return

        self.tab_activa = "plazas"
        self.categorias_detalle_contrato = []

        try:
            await self._cargar_contrato_actual_portal(codigo_contrato)
        except NotFoundError:
            yield rx.toast.error("Contrato no encontrado")
            yield rx.redirect("/portal/contratos")
            return
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
            yield rx.redirect("/portal/contratos")
            return
        except Exception as e:
            logger.error("Error cargando contrato portal %s: %s", codigo_contrato, e)
            yield rx.toast.error("No se pudo abrir la sección de plazas")
            yield rx.redirect("/portal/contratos")
            return

        codigo_canonico = normalizar_mayusculas(
            str(self.contrato_actual_portal.get("codigo") or "")
        )
        if codigo_canonico and codigo_canonico != codigo_contrato:
            yield rx.redirect(
                PortalState.construir_ruta_plazas_contrato(codigo_canonico),
                replace=True,
            )
            return

        contrato_id = int(self.contrato_actual_portal.get("id") or 0)
        if contrato_id <= 0:
            yield rx.redirect("/portal/contratos")
            return

        self.vista_personal = VISTA_PERSONAL_PLAZA
        self.filtro_contrato_id = str(contrato_id)
        self.contrato_expandido_plaza_id = contrato_id
        self._reset_filtros_internos_plaza()

        async for _ in self._montar_pagina(
            self._fetch_empleados,
            self._cargar_detalle_contrato,
            self._cargar_contexto_fiscal_empresa,
        ):
            yield

    def set_tab_activa(self, value: str):
        self.tab_activa = value or "plazas"

    def set_form_nombre_categoria(self, value: str):
        self.form_nombre_categoria = " ".join(str(value or "").split())
        self.error_form_nombre_categoria = ""

    def set_form_tipo_sueldo(self, value: str):
        self.form_tipo_sueldo = (
            value if value in {TipoSueldo.BRUTO.value, TipoSueldo.NETO.value}
            else TipoSueldo.BRUTO.value
        )
        self.error_form_sueldo_base = ""

    def set_form_sueldo_base(self, value: str):
        self.form_sueldo_base = str(value or "").strip()
        self.error_form_sueldo_base = ""

    def set_form_costo_contractual(self, value: str):
        self.form_costo_contractual = str(value or "").strip()
        self.error_form_costo_contractual = ""

    def set_form_min_plazas(self, value: str):
        self.form_min_plazas = "".join(ch for ch in str(value or "") if ch.isdigit()) or "0"
        self.error_form_min_plazas = ""

    def set_form_max_plazas(self, value: str):
        self.form_max_plazas = "".join(ch for ch in str(value or "") if ch.isdigit())
        self.error_form_max_plazas = ""

    def abrir_combobox_nombre_categoria(self):
        self.combobox_nombre_categoria_abierto = True

    def cerrar_combobox_nombre_categoria(self):
        self.combobox_nombre_categoria_abierto = False

    def seleccionar_sugerencia_nombre_categoria(self, valor: str):
        self.form_nombre_categoria = " ".join(str(valor or "").split())
        self.error_form_nombre_categoria = ""
        self.combobox_nombre_categoria_abierto = False

    def _resetear_form_categoria(self):
        self.categoria_editando_id = 0
        self.form_nombre_categoria = ""
        self.form_tipo_sueldo = TipoSueldo.BRUTO.value
        self.form_sueldo_base = ""
        self.form_costo_contractual = ""
        self.form_min_plazas = "0"
        self.form_max_plazas = ""
        self.error_form_nombre_categoria = ""
        self.error_form_sueldo_base = ""
        self.error_form_costo_contractual = ""
        self.error_form_min_plazas = ""
        self.error_form_max_plazas = ""
        self.combobox_nombre_categoria_abierto = False

    def abrir_modal_categoria(self):
        if self.contrato_solo_consulta:
            return rx.toast.error("Este contrato está en modo consulta.")
        self._resetear_form_categoria()
        self.modal_categoria_abierto = True

    def editar_categoria(self, categoria_id: int):
        if self.contrato_solo_consulta:
            return rx.toast.error("Este contrato está en modo consulta.")
        categoria = self._buscar_categoria_detalle(categoria_id)
        if not categoria:
            return rx.toast.error("No se pudo identificar la categoría")

        self._resetear_form_categoria()
        sueldo_base = self._parse_decimal_seguro(
            categoria.get("sueldo_base") or categoria.get("costo_unitario")
        )
        costo_contractual = self._parse_decimal_seguro(
            categoria.get("costo_contractual")
        )
        cantidad_minima = int(categoria.get("cantidad_minima") or 0)
        cantidad_maxima = int(categoria.get("cantidad_maxima") or 0)

        self.categoria_editando_id = int(categoria.get("id") or 0)
        self.form_nombre_categoria = str(
            categoria.get("nombre") or categoria.get("categoria_nombre") or ""
        ).strip()
        self.form_tipo_sueldo = self._coerce_tipo_sueldo(
            categoria.get("tipo_sueldo")
        ).value
        self.form_sueldo_base = self._decimal_a_texto_input(sueldo_base)
        self.form_costo_contractual = self._decimal_a_texto_input(costo_contractual)
        self.form_min_plazas = str(cantidad_minima)
        self.form_max_plazas = "" if cantidad_maxima <= 0 else str(cantidad_maxima)
        self.modal_categoria_abierto = True

    def cerrar_modal_categoria(self):
        self.modal_categoria_abierto = False
        self._resetear_form_categoria()

    def _validar_formulario_categoria(self) -> bool:
        self.error_form_nombre_categoria = ""
        self.error_form_sueldo_base = ""
        self.error_form_costo_contractual = ""
        self.error_form_min_plazas = ""
        self.error_form_max_plazas = ""

        if not self.form_nombre_categoria.strip():
            self.error_form_nombre_categoria = "Capture el nombre de la categoría"

        sueldo_base = self._parse_decimal_seguro(self.form_sueldo_base)
        if sueldo_base <= Decimal("0"):
            self.error_form_sueldo_base = "Capture un sueldo mensual mayor a 0"

        if self.form_costo_contractual.strip():
            costo_contractual = self._parse_decimal_seguro(self.form_costo_contractual)
            if costo_contractual < Decimal("0"):
                self.error_form_costo_contractual = "El costo contractual no puede ser negativo"

        try:
            min_val = int(self.form_min_plazas or "0")
            if min_val < 0:
                raise ValueError
        except ValueError:
            self.error_form_min_plazas = "Captura un número válido"
            min_val = -1

        max_raw = self.form_max_plazas.strip()
        if max_raw:
            try:
                max_val = int(max_raw)
                if max_val < 0:
                    raise ValueError
            except ValueError:
                self.error_form_max_plazas = "Captura un número válido"
                max_val = -1
            else:
                if min_val >= 0 and max_val > 0 and max_val < min_val:
                    self.error_form_max_plazas = "Debe ser mayor o igual al mínimo"

        return not bool(
            self.error_form_nombre_categoria
            or self.error_form_sueldo_base
            or self.error_form_costo_contractual
            or self.error_form_min_plazas
            or self.error_form_max_plazas
        )

    async def guardar_categoria(self):
        if self.contrato_solo_consulta:
            yield rx.toast.error("Este contrato está en modo consulta.")
            return

        contrato_id = int(self.contrato_actual_portal.get("id") or 0)
        if contrato_id <= 0:
            yield rx.toast.error("No se pudo identificar el contrato")
            return

        if not self._validar_formulario_categoria():
            yield rx.toast.error("Revise los datos de la categoría")
            return

        sueldo_base = self._parse_decimal_seguro(self.form_sueldo_base)
        tipo_sueldo = self._tipo_sueldo_form_actual()
        snapshot = self._calcular_snapshot_categoria(sueldo_base, tipo_sueldo)
        sueldo_bruto = snapshot["sueldo_bruto"]

        costo_contractual_raw = self.form_costo_contractual.strip()
        costo_contractual = (
            self._parse_decimal_seguro(costo_contractual_raw)
            if costo_contractual_raw
            else None
        )
        min_plazas = int(self.form_min_plazas or "0")
        max_raw = self.form_max_plazas.strip()
        max_plazas = int(max_raw) if max_raw else None

        self.saving = True
        yield
        try:
            if self.categoria_editando_id > 0:
                await contrato_categoria_service.actualizar_categoria_portal(
                    self.categoria_editando_id,
                    nombre=self.form_nombre_categoria,
                    sueldo_base=sueldo_base,
                    tipo_sueldo=tipo_sueldo,
                    sueldo_bruto=sueldo_bruto,
                    costo_contractual=costo_contractual,
                    min_plazas=min_plazas,
                    max_plazas=max_plazas,
                )
                mensaje = "Categoría actualizada"
            else:
                await contrato_categoria_service.crear_categoria_portal(
                    contrato_id,
                    nombre=self.form_nombre_categoria,
                    sueldo_base=sueldo_base,
                    tipo_sueldo=tipo_sueldo,
                    sueldo_bruto=sueldo_bruto,
                    costo_contractual=costo_contractual,
                    min_plazas=min_plazas,
                    max_plazas=max_plazas,
                )
                mensaje = "Categoría agregada"

            self.cerrar_modal_categoria()
            await self._cargar_detalle_contrato()
            yield rx.toast.success(mensaje)
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "guardando categoría")
        finally:
            self.saving = False

    def limpiar_filtros_plazas_contrato(self):
        self._reset_filtros_internos_plaza()
        self._sincronizar_seleccion_contrato_actual()

    def volver_a_contratos(self):
        return rx.redirect("/portal/contratos")

    def toggle_plaza_contrato_actual(self, plaza_id: int, checked) -> None:
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        self.toggle_plaza_seleccionada(contrato_id, plaza_id, checked)

    def seleccionar_todas_plazas_actuales(self, checked) -> None:
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        self.seleccionar_todas_plazas_visibles(contrato_id, checked)

    def set_sede_masiva_actual(self, value: str) -> None:
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        self.set_sede_masiva_contrato(contrato_id, value)

    def set_categoria_masiva_actual(self, value: str) -> None:
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        self.set_categoria_masiva_contrato(contrato_id, value)

    async def asignar_sede_masiva_actual(self):
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        return await self.aplicar_sede_masiva_contrato(contrato_id)

    async def cambiar_categoria_masiva_actual(self):
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        return await self.aplicar_categoria_masiva_contrato(contrato_id)

    def deseleccionar_todas(self):
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        self.limpiar_seleccion_plazas(contrato_id)

    def ir_a_pagina_actual(self, pagina: int):
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        self.ir_a_pagina_plaza_contrato(contrato_id, pagina)

    def pagina_anterior_actual(self):
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        self.pagina_anterior_plaza_contrato(contrato_id)

    def pagina_siguiente_actual(self):
        contrato_id = int(self.contrato_actual_portal.get("id") or self.contrato_expandido_plaza_id or 0)
        self.pagina_siguiente_plaza_contrato(contrato_id)

    def accion_reasignar_plaza(self, plaza_id: int):
        plaza = self._buscar_plaza_contrato_expandido(plaza_id)
        if not plaza:
            return rx.toast.error("No se pudo identificar la plaza")
        return type(self).abrir_modal_reasignacion_plaza(plaza)

    def accion_ver_empleado_plaza(self, plaza_id: int):
        plaza = self._buscar_plaza_contrato_expandido(plaza_id)
        if not plaza:
            return rx.toast.error("No se pudo identificar la plaza")
        return self.ver_perfil_plaza(plaza)

    def ver_plaza(self, plaza_id: int):
        plaza = self._buscar_plaza_contrato_expandido(plaza_id)
        if not plaza:
            return rx.toast.error("No se pudo identificar la plaza")
        if int(plaza.get("empleado_id") or 0) > 0:
            return self.ver_perfil_plaza(plaza)
        return rx.toast.info("Este contrato solo permite consulta de las plazas.")

    def _resumen_plazas_actuales(self) -> dict[str, int]:
        plazas = list(self.plazas_contrato_expandido or [])
        total_plazas = len(plazas)
        plazas_ocupadas = sum(
            1
            for plaza in plazas
            if str(plaza.get("estatus", "") or "") == EstatusPlaza.OCUPADA.value
        )
        plazas_vacantes = sum(
            1
            for plaza in plazas
            if str(plaza.get("estatus", "") or "") == EstatusPlaza.VACANTE.value
        )
        plazas_sin_sede = sum(
            1
            for plaza in plazas
            if int(plaza.get("sede_id") or 0) <= 0
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
            "plazas_sin_sede": plazas_sin_sede,
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
        plazas_sin_sede = int(activo.get("plazas_sin_sede") or resumen["plazas_sin_sede"])
        total_sedes = int(activo.get("total_sedes") or resumen["total_sedes"])

        costos_categoria = self._costos_categoria_por_id()
        costo_presupuestado = Decimal("0")
        costo_actual = Decimal("0")
        for plaza in self.plazas_contrato_expandido:
            categoria_id = int(plaza.get("categoria_puesto_id") or 0)
            costo = costos_categoria.get(categoria_id, Decimal("0"))
            if costo <= 0:
                costo = self._parse_decimal_seguro(plaza.get("salario_mensual"))
            costo_presupuestado += costo
            if str(plaza.get("estatus", "") or "") == EstatusPlaza.OCUPADA.value:
                costo_actual += costo

        cobertura_pct = (
            int(round((plazas_ocupadas / total_plazas) * 100))
            if total_plazas > 0 else 0
        )

        descripcion = self._descripcion_servicio_actual()
        vigencia = self._vigencia_contrato_actual()
        subtitulo = descripcion or vigencia
        if descripcion and vigencia:
            subtitulo = f"{descripcion} · {vigencia}"

        contrato_codigo = normalizar_mayusculas(
            str(
                activo.get("contrato_codigo")
                or contrato.get("codigo")
                or "Sin contrato"
            ),
        )

        return {
            "contrato_id": contrato_id,
            "contrato_codigo": contrato_codigo,
            "contrato_estatus": str(
                contrato.get("estatus")
                or activo.get("contrato_estatus")
                or ""
            ),
            "descripcion_servicio": descripcion,
            "vigencia_texto": vigencia,
            "subtitulo": subtitulo or "Configuración y operación de plazas por contrato",
            "tipo_servicio_nombre": str(
                activo.get("tipo_servicio_nombre")
                or contrato.get("nombre_servicio_fmt")
                or ""
            ),
            "total_plazas": total_plazas,
            "plazas_ocupadas": plazas_ocupadas,
            "plazas_vacantes": plazas_vacantes,
            "plazas_sin_sede": plazas_sin_sede,
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
            "mostrar_badge_sin_sede": plazas_sin_sede > 0,
            "cobertura_pct": cobertura_pct,
            "costo_presupuestado": str(costo_presupuestado),
            "costo_actual": str(costo_actual),
            "costo_presupuestado_fmt": self._formatear_moneda_operativa(costo_presupuestado),
            "costo_actual_fmt": self._formatear_moneda_operativa(costo_actual),
            "total_categorias": len(self.categorias_detalle_contrato),
            "ruta_contrato": PortalState.construir_ruta_plazas_contrato(contrato_codigo),
        }

    @rx.var
    def contrato_plaza_contexto(self) -> dict:
        return self._construir_contrato_plaza_contexto()

    @rx.var
    def tiene_contrato_plaza_contexto(self) -> bool:
        return bool(self.contrato_plaza_contexto)

    @rx.var
    def contrato_actual_id(self) -> int:
        return int(
            self.contrato_plaza_contexto.get("contrato_id")
            or self.contrato_actual_portal.get("id")
            or self.contrato_expandido_plaza_id
            or 0
        )

    @rx.var
    def breadcrumb_items(self) -> list[dict]:
        """Breadcrumb lógico para la vista de plazas de un contrato.

        Mismo patrón que `/portal/empleados/[uuid]`: el primer nivel apunta a
        Contratos, el segundo nivel es la hoja (código del contrato)
        sin navegación. La UI renderiza este breadcrumb inline dentro del
        `page_header` — ver `_header_plazas`.
        """
        return [
            {"texto": "Contratos", "href": "/portal/contratos"},
            {"texto": self.codigo_contrato_actual or "Contrato", "href": ""},
        ]

    @rx.var
    def codigo_contrato_actual(self) -> str:
        return str(
            self.contrato_plaza_contexto.get("contrato_codigo")
            or self.contrato_actual_portal.get("codigo")
            or ""
        )

    @rx.var
    def subtitulo_contrato_actual(self) -> str:
        return str(
            self.contrato_plaza_contexto.get("subtitulo")
            or "Configuración y operación de plazas por contrato"
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
    def contrato_solo_consulta(self) -> bool:
        return self.estatus_contrato_actual in {"VENCIDO", "CANCELADO", "LIQUIDADO"}

    @rx.var
    def total_plazas_contrato_actual(self) -> int:
        return int(self.contrato_plaza_contexto.get("total_plazas") or 0)

    @rx.var
    def plazas_ocupadas_contrato_actual(self) -> int:
        return int(self.contrato_plaza_contexto.get("plazas_ocupadas") or 0)

    @rx.var
    def cobertura_pct_contrato_actual(self) -> int:
        return int(self.contrato_plaza_contexto.get("cobertura_pct") or 0)

    @rx.var
    def color_metrica_ocupadas(self) -> str:
        if self.total_plazas_contrato_actual <= 0:
            return Colors.TEXT_MUTED
        if self.cobertura_pct_contrato_actual > 100:
            return Colors.WARNING
        if self.cobertura_pct_contrato_actual >= 60:
            return Colors.SUCCESS
        return Colors.WARNING

    @rx.var
    def descripcion_metrica_ocupadas(self) -> str:
        if self.total_plazas_contrato_actual <= 0:
            return ""
        return f"{self.cobertura_pct_contrato_actual}% cobertura"

    @rx.var
    def hay_filtros_plazas_contrato_activos(self) -> bool:
        return bool(
            self.plaza_busqueda.strip()
            or self.plaza_filtro_categoria != "all"
            or self.plaza_filtro_estado != "all"
        )

    @rx.var
    def titulo_empty_state_plazas_contrato(self) -> str:
        if len(self.plazas_contrato_expandido or []) <= 0:
            return "No hay plazas configuradas en este contrato"
        if self.hay_filtros_plazas_contrato_activos:
            return "No se encontraron plazas con los filtros seleccionados"
        return "No se encontraron plazas"

    @rx.var
    def descripcion_empty_state_plazas_contrato(self) -> str:
        if len(self.plazas_contrato_expandido or []) <= 0:
            return "Este contrato todavía no tiene plazas visibles para operar en portal."
        if self.hay_filtros_plazas_contrato_activos:
            return "Prueba con otra búsqueda o limpia los filtros para ver todas las plazas."
        return "No hay plazas disponibles para este contrato."

    @rx.var
    def caption_plazas_contrato_actual(self) -> str:
        total = self.plaza_total_filtradas
        if total <= 0:
            return ""
        visibles = len(self.plazas_pagina_actual or [])
        return (
            f"Mostrando {visibles} de {total} plazas · "
            f"Página {self.pagina_plaza_actual} de {self.total_paginas_plaza_actual}"
        )

    @rx.var
    def categoria_editando(self) -> bool:
        return self.categoria_editando_id > 0

    @rx.var
    def titulo_modal_categoria(self) -> str:
        return "Editar categoría" if self.categoria_editando else "Nueva categoría"

    @rx.var
    def descripcion_modal_categoria(self) -> str:
        if self.categoria_editando:
            return "Actualice el nombre y el sueldo ancla de la categoría contractual."
        return "Agregue una categoría para este contrato y defina su sueldo mensual."

    @rx.var
    def puede_guardar_categoria(self) -> bool:
        return bool(
            self.form_nombre_categoria.strip()
            and self._parse_decimal_seguro(self.form_sueldo_base) > Decimal("0")
            and not self.saving
            and not self.contrato_solo_consulta
        )

    @rx.var
    def form_snapshot_categoria(self) -> dict:
        sueldo_base = self._parse_decimal_seguro(self.form_sueldo_base)
        return self._calcular_snapshot_categoria(
            sueldo_base,
            self._tipo_sueldo_form_actual(),
        )

    @rx.var
    def form_bruto_preview(self) -> Decimal:
        return Decimal(str(self.form_snapshot_categoria.get("sueldo_bruto") or 0))

    @rx.var
    def form_neto_preview(self) -> Decimal:
        return Decimal(str(self.form_snapshot_categoria.get("sueldo_neto") or 0))

    @rx.var
    def form_bruto_preview_fmt(self) -> str:
        if self.form_bruto_preview <= Decimal("0"):
            return ""
        return self._formatear_moneda_operativa(self.form_bruto_preview)

    @rx.var
    def form_neto_preview_fmt(self) -> str:
        if self.form_neto_preview <= Decimal("0"):
            return ""
        return self._formatear_moneda_operativa(self.form_neto_preview)

    @rx.var
    def form_preview_sueldo_hint(self) -> str:
        if self._tipo_sueldo_form_actual() == TipoSueldo.BRUTO:
            if self.form_neto_preview <= Decimal("0"):
                return ""
            return f"Neto estimado: {self.form_neto_preview_fmt}"
        if self.form_bruto_preview <= Decimal("0"):
            return ""
        return f"Bruto estimado: {self.form_bruto_preview_fmt}"

    @rx.var
    def form_es_menor_salario_minimo(self) -> bool:
        return bool(self.form_snapshot_categoria.get("es_menor_salario_minimo", False))

    @rx.var
    def nombres_categoria_sugerencias_filtradas(self) -> list[str]:
        consulta = " ".join(str(self.form_nombre_categoria or "").split()).lower()
        nombres_actuales = {
            str(categoria.get("nombre") or "").strip().upper()
            for categoria in self.categorias_detalle_contrato
        }
        nombres_actuales.discard("")
        resultado: list[str] = []
        for nombre in self.nombres_categoria_sugerencias:
            if nombre.strip().upper() in nombres_actuales:
                continue
            if consulta and consulta not in nombre.lower():
                continue
            resultado.append(nombre)
            if len(resultado) >= 12:
                break
        return resultado

    @rx.var
    def mostrar_sugerencias_nombre_categoria(self) -> bool:
        return bool(
            self.combobox_nombre_categoria_abierto
            and len(self.nombres_categoria_sugerencias_filtradas) > 0
        )

    @rx.var
    def plazas_tabla_rows(self) -> list[dict]:
        costos_categoria = self._costos_categoria_por_id()
        solo_consulta = self.contrato_solo_consulta
        filas: list[dict] = []
        nombres_categoria: dict[int, str] = {
            int(categoria.get("categoria_puesto_id") or 0): capitalizar_palabras(
                str(categoria.get("nombre") or categoria.get("categoria_nombre") or "Sin categoría")
            )
            for categoria in self.categorias_detalle_contrato
            if int(categoria.get("categoria_puesto_id") or 0) > 0
        }

        for plaza in self.plazas_pagina_actual:
            categoria_id = int(plaza.get("categoria_puesto_id") or 0)
            sueldo_categoria = costos_categoria.get(categoria_id, Decimal("0"))
            if sueldo_categoria <= 0:
                sueldo_categoria = self._parse_decimal_seguro(plaza.get("salario_mensual"))

            tiene_sede = int(plaza.get("sede_id") or 0) > 0
            tiene_empleado = int(plaza.get("empleado_id") or 0) > 0
            sede_codigo = normalizar_mayusculas(str(plaza.get("sede_codigo") or ""))
            sede_nombre = capitalizar_con_preposiciones(str(plaza.get("sede_nombre") or ""))
            sede_display = ""
            if tiene_sede:
                if sede_codigo and sede_nombre:
                    sede_display = f"{sede_codigo} – {sede_nombre}"
                else:
                    sede_display = sede_codigo or sede_nombre

            empleado_uuid = str(plaza.get("empleado_uuid") or "").strip()
            empleado_href = ""
            if empleado_uuid:
                empleado_href = f"/portal/empleados/{empleado_uuid}"

            categoria_nombre_ui = nombres_categoria.get(
                categoria_id,
                capitalizar_palabras(
                    str(plaza.get("categoria_nombre") or "Sin categoría"),
                ),
            )

            fila_cfg = self._fila_configuracion(plaza, categoria_nombre_ui, sede_display)

            filas.append(
                {
                    **plaza,
                    "numero_plaza_texto": str(plaza.get("numero_plaza") or "—"),
                    "categoria_nombre_ui": fila_cfg["categoria_nombre_ui"],
                    "tiene_sueldo_categoria": sueldo_categoria > 0,
                    "sueldo_categoria_fmt": (
                        self._formatear_moneda_operativa(sueldo_categoria)
                        if sueldo_categoria > 0 else ""
                    ),
                    "sueldo_categoria_label": (
                        f"{self._formatear_moneda_operativa(sueldo_categoria)}/mes"
                        if sueldo_categoria > 0 else ""
                    ),
                    "tiene_sede": tiene_sede,
                    "sede_display_tabla": fila_cfg["sede_display_tabla"],
                    "tiene_empleado": tiene_empleado,
                    "empleado_nombre_ui": capitalizar_palabras(
                        str(plaza.get("empleado_nombre") or ""),
                    ),
                    "empleado_href": empleado_href,
                    "configuracion_estado": fila_cfg["configuracion_estado"],
                    "ocupacion_estado": fila_cfg["ocupacion_estado"],
                    "mostrar_menu_acciones": fila_cfg["cta_tipo"] == "menu_ocupada",
                    "cta_tipo": fila_cfg["cta_tipo"],
                    "cta_texto": fila_cfg["cta_texto"],
                }
            )

        return filas

    @rx.var
    def mostrar_barra_acciones_masivas(self) -> bool:
        return bool(
            self.tab_activa == "plazas"
            and self.contrato_plaza_contexto.get("tiene_seleccion", False)
            and not self.contrato_solo_consulta
        )

    @rx.var
    def plazas_seleccionadas_count(self) -> int:
        return int(self.contrato_plaza_contexto.get("seleccion_count") or 0)

    @rx.var
    def sede_masiva_actual(self) -> str:
        return str(self.contrato_plaza_contexto.get("sede_masiva_value") or "")

    @rx.var
    def categoria_masiva_actual(self) -> str:
        return str(self.contrato_plaza_contexto.get("categoria_masiva_value") or "")

    @rx.var
    def opciones_categorias_masivas_actual(self) -> list[dict]:
        return list(self.contrato_plaza_contexto.get("opciones_categorias_masivas") or [])

    @rx.var
    def puede_asignar_sede_masiva_actual(self) -> bool:
        return bool(self.sede_masiva_actual) and not self.saving

    @rx.var
    def puede_cambiar_categoria_masiva_actual(self) -> bool:
        return bool(self.categoria_masiva_actual) and not self.saving

    @rx.var
    def mostrar_resumen_contrato_plaza(self) -> bool:
        """Oculta el resumen duplicado; el contexto vive en header, métricas y tabs."""
        return False

    # ------------------------------------------------------------------
    # Configuración / Ocupación — métricas y vistas derivadas
    # ------------------------------------------------------------------

    def _contar_por_configuracion(self) -> dict[str, int]:
        plazas = list(self.plazas_contrato_expandido or [])
        configuradas = 0
        sin_sede = 0
        sin_categoria = 0
        incompletas = 0
        ocupadas = 0
        vacantes_disponibles = 0
        for plaza in plazas:
            sede_ok = int(plaza.get("sede_id") or 0) > 0
            categoria_ok = int(plaza.get("categoria_puesto_id") or 0) > 0
            estatus = str(plaza.get("estatus") or "").upper()
            if sede_ok and categoria_ok:
                configuradas += 1
                if estatus == EstatusPlaza.OCUPADA.value:
                    ocupadas += 1
                elif estatus == EstatusPlaza.VACANTE.value:
                    vacantes_disponibles += 1
            elif not sede_ok and not categoria_ok:
                incompletas += 1
            elif not sede_ok:
                sin_sede += 1
            else:
                sin_categoria += 1
        total = len(plazas)
        pendientes = sin_sede + sin_categoria + incompletas
        return {
            "total": total,
            "configuradas": configuradas,
            "pendientes": pendientes,
            "sin_sede": sin_sede,
            "sin_categoria": sin_categoria,
            "incompletas": incompletas,
            "ocupadas": ocupadas,
            "vacantes_disponibles": vacantes_disponibles,
        }

    @rx.var
    def plazas_configuradas_contrato_actual(self) -> int:
        return int(self._contar_por_configuracion()["configuradas"])

    @rx.var
    def plazas_pendientes_contrato_actual(self) -> int:
        return int(self._contar_por_configuracion()["pendientes"])

    @rx.var
    def plazas_sin_categoria_contrato_actual(self) -> int:
        return int(self._contar_por_configuracion()["sin_categoria"])

    @rx.var
    def plazas_incompletas_contrato_actual(self) -> int:
        return int(self._contar_por_configuracion()["incompletas"])

    @rx.var
    def plazas_vacantes_disponibles_actual(self) -> int:
        return int(self._contar_por_configuracion()["vacantes_disponibles"])

    @rx.var
    def descripcion_metrica_configuradas(self) -> str:
        conteos = self._contar_por_configuracion()
        total = conteos["total"]
        configuradas = conteos["configuradas"]
        if total <= 0:
            return "Sin plazas registradas"
        pct = int(round((configuradas / total) * 100)) if total else 0
        return f"{pct}% del contrato"

    @rx.var
    def descripcion_metrica_pendientes(self) -> str:
        conteos = self._contar_por_configuracion()
        partes: list[str] = []
        if conteos["sin_sede"]:
            partes.append(f"{conteos['sin_sede']} sin sede")
        if conteos["sin_categoria"]:
            partes.append(f"{conteos['sin_categoria']} sin categoría")
        if conteos["incompletas"]:
            partes.append(f"{conteos['incompletas']} incompletas")
        return " · ".join(partes) if partes else "Sin pendientes"

    @rx.var
    def mostrar_banner_incidencias(self) -> bool:
        return self.plazas_pendientes_contrato_actual > 0

    @rx.var
    def mensaje_banner_incidencias(self) -> str:
        conteos = self._contar_por_configuracion()
        partes: list[str] = []
        if conteos["sin_sede"]:
            partes.append(
                f"{conteos['sin_sede']} {self._pluralizar(conteos['sin_sede'], 'plaza', 'plazas')} sin sede"
            )
        if conteos["sin_categoria"]:
            partes.append(
                f"{conteos['sin_categoria']} sin categoría"
            )
        if conteos["incompletas"]:
            partes.append(
                f"{conteos['incompletas']} {self._pluralizar(conteos['incompletas'], 'incompleta', 'incompletas')}"
            )
        if not partes:
            return ""
        total = conteos["pendientes"]
        encabezado = (
            f"{total} {self._pluralizar(total, 'plaza', 'plazas')} "
            f"no {'está' if total == 1 else 'están'} lista{'s' if total != 1 else ''} para ocuparse"
        )
        return f"{encabezado} — " + " · ".join(partes)

    def _fila_configuracion(self, plaza: dict, categoria_nombre: str, sede_display: str) -> dict:
        sede_ok = int(plaza.get("sede_id") or 0) > 0
        categoria_ok = int(plaza.get("categoria_puesto_id") or 0) > 0
        estatus = str(plaza.get("estatus") or "").upper()
        solo_consulta = self.contrato_solo_consulta

        if sede_ok and categoria_ok:
            configuracion_estado = "COMPLETA"
        elif not sede_ok and not categoria_ok:
            configuracion_estado = "CONFIGURACION_INCOMPLETA"
        elif not sede_ok:
            configuracion_estado = "SIN_SEDE"
        else:
            configuracion_estado = "SIN_CATEGORIA"

        if configuracion_estado != "COMPLETA":
            ocupacion_estado = "NO_DISPONIBLE"
        elif estatus == EstatusPlaza.OCUPADA.value:
            ocupacion_estado = EstatusPlaza.OCUPADA.value
        else:
            ocupacion_estado = EstatusPlaza.VACANTE.value

        if solo_consulta:
            cta_tipo = "ver"
            cta_texto = "Consultar"
        elif ocupacion_estado == EstatusPlaza.OCUPADA.value:
            cta_tipo = "menu_ocupada"
            cta_texto = "Acciones"
        elif configuracion_estado == "SIN_SEDE":
            cta_tipo = "asignar_sede"
            cta_texto = "Asignar sede"
        elif configuracion_estado in ("SIN_CATEGORIA", "CONFIGURACION_INCOMPLETA"):
            cta_tipo = "completar_config"
            cta_texto = "Completar configuración"
        else:
            cta_tipo = "ir_a_empleados"
            cta_texto = "Ir a empleados"

        return {
            "configuracion_estado": configuracion_estado,
            "ocupacion_estado": ocupacion_estado,
            "cta_tipo": cta_tipo,
            "cta_texto": cta_texto,
            "categoria_nombre_ui": categoria_nombre,
            "sede_display_tabla": sede_display,
        }

    @rx.var
    def pendientes_tabla_rows(self) -> list[dict]:
        filas: list[dict] = []
        for fila in self.plazas_tabla_rows:
            if str(fila.get("configuracion_estado") or "") != "COMPLETA":
                filas.append(fila)
        return filas

    @rx.var
    def total_pendientes_tabla(self) -> int:
        return len(self.pendientes_tabla_rows)

    @rx.var
    def categorias_resumen_simple(self) -> list[dict]:
        """Resumen operativo sin costos: mín, máx, configuradas, ocupadas, pendientes."""
        plazas = list(self.plazas_contrato_expandido or [])
        agrupacion: dict[int, dict] = {}
        for plaza in plazas:
            categoria_id = int(plaza.get("categoria_puesto_id") or 0)
            if categoria_id <= 0:
                continue
            bucket = agrupacion.setdefault(
                categoria_id,
                {
                    "id": categoria_id,
                    "total": 0,
                    "configuradas": 0,
                    "ocupadas": 0,
                    "pendientes": 0,
                },
            )
            sede_ok = int(plaza.get("sede_id") or 0) > 0
            estatus = str(plaza.get("estatus") or "").upper()
            bucket["total"] += 1
            if sede_ok:
                bucket["configuradas"] += 1
                if estatus == EstatusPlaza.OCUPADA.value:
                    bucket["ocupadas"] += 1
            else:
                bucket["pendientes"] += 1

        filas: list[dict] = []
        for categoria in self.categorias_detalle_contrato:
            categoria_id = int(categoria.get("categoria_puesto_id") or 0)
            if categoria_id <= 0:
                continue
            bucket = agrupacion.get(
                categoria_id,
                {"total": 0, "configuradas": 0, "ocupadas": 0, "pendientes": 0},
            )
            minimo = int(categoria.get("cantidad_minima") or 0)
            maximo = int(categoria.get("cantidad_maxima") or 0)
            configuradas = int(bucket["configuradas"])
            if minimo and configuradas < minimo:
                estado = "DEBAJO_MINIMO"
            elif maximo and bucket["total"] > maximo:
                estado = "ENCIMA_MAXIMO"
            elif bucket["pendientes"] > 0:
                estado = "CONFIGURACION_INCOMPLETA"
            elif bucket["total"] == 0:
                estado = "SIN_CONFIGURAR"
            else:
                estado = "COMPLETA"
            filas.append(
                {
                    "id": categoria_id,
                    "nombre": capitalizar_palabras(
                        str(categoria.get("nombre") or categoria.get("categoria_nombre") or "")
                    ) or "Sin categoría",
                    "minimo_texto": str(minimo),
                    "maximo_texto": str(maximo) if maximo else "∞",
                    "total_texto": str(bucket["total"]),
                    "configuradas_texto": str(bucket["configuradas"]),
                    "ocupadas_texto": str(bucket["ocupadas"]),
                    "pendientes_texto": str(bucket["pendientes"]),
                    "estado": estado,
                }
            )
        return filas

    @rx.var
    def tiene_categorias_resumen_simple(self) -> bool:
        return len(self.categorias_resumen_simple) > 0

    # ------------------------------------------------------------------
    # Handlers de navegación (sin duplicar flujo de empleados)
    # ------------------------------------------------------------------

    def accion_ir_a_empleados(self, plaza_id: int):
        pid = int(plaza_id or 0)
        if pid > 0:
            return rx.redirect(f"/portal/empleados?plaza_id={pid}")
        return rx.redirect("/portal/empleados")

    def accion_completar_configuracion(self, plaza_id: int):
        """Abre el modal de sede como primer paso de corrección."""
        return self.accion_cambiar_sede(plaza_id)
