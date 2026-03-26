"""State compartido del modulo de incapacidades para el portal."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import reflex as rx

from core.core.enums import (
    EstatusEmpleado,
    EstatusIncapacidad,
    OrigenIncapacidad,
    TipoIncapacidad,
)
from core.core.exceptions import BusinessRuleError
from core.core.text_utils import capitalizar_palabras, formatear_fecha, normalizar_mayusculas
from core.core.ui_helpers import FILTRO_TODOS
from core.core.utils import normalize_date_input, parse_date_input
from core.domain.models.incapacidad import IncapacidadCreate
from core.presentation.pages.portal.state.portal_state import PortalState
from core.domain.services.empleado_service import empleado_service
from core.domain.services.incapacidad_service import incapacidad_service


CATALOGO_EMPLEADOS_MODAL_LIMITE = 25
INCAPACIDADES_POR_PAGINA = 10


class IncapacidadState(PortalState):
    """State reusable para registro y consulta de incapacidades."""

    incapacidades_empleado: list[dict] = []
    cargando_incapacidades: bool = False
    error_incapacidades: str = ""

    incapacidades_empresa: list[dict] = []
    error_incapacidades_empresa: str = ""
    conteos_empresa: dict = {"activas": 0, "vencidas": 0, "total": 0}
    filtro_estatus_empresa: str = FILTRO_TODOS
    pagina_incapacidades_actual: int = 1

    modal_abierto: bool = False
    modal_modo_global: bool = False
    cargando_empleados_modal: bool = False
    error_empleados_modal: str = ""
    busqueda_empleado_modal: str = ""
    empleados_catalogo_modal: list[dict] = []
    empleado_seleccionado_modal_id: str = ""
    contexto_empleado_resumen: str = ""
    contexto_empleado_error: str = ""

    empleado_contexto_id: int = 0
    empleado_contexto_uuid: str = ""
    empleado_contexto_clave: str = ""
    empleado_contexto_nombre: str = ""
    form_plaza_id: int = 0
    form_contrato_id: int = 0
    form_origen: str = OrigenIncapacidad.FORMAL.value
    form_tipo: str = TipoIncapacidad.ENF_GENERAL.value
    form_fecha_inicio: str = ""
    form_fecha_fin_estimada: str = ""
    form_folio_imss: str = ""
    form_dias_certificado: str = ""
    form_porcentaje_pago: str = "100.00"
    form_requiere_cobertura: bool = False
    form_notas: str = ""
    form_error: str = ""

    @rx.var
    def tiene_incapacidades(self) -> bool:
        return len(self.incapacidades_empleado) > 0

    @rx.var
    def total_incapacidades_empleado(self) -> int:
        return len(self.incapacidades_empleado)

    @rx.var
    def tiene_incapacidades_empresa(self) -> bool:
        return len(self.incapacidades_empresa_filtradas) > 0

    @rx.var
    def conteo_activas_empresa(self) -> int:
        return int((self.conteos_empresa or {}).get("activas") or 0)

    @rx.var
    def conteo_vencidas_empresa(self) -> int:
        return int((self.conteos_empresa or {}).get("vencidas") or 0)

    @rx.var
    def conteo_total_empresa(self) -> int:
        return int((self.conteos_empresa or {}).get("total") or 0)

    @rx.var
    def es_formal(self) -> bool:
        return self.form_origen == OrigenIncapacidad.FORMAL.value

    @rx.var
    def es_por_acuerdo(self) -> bool:
        return self.form_origen == OrigenIncapacidad.POR_ACUERDO.value

    @rx.var
    def form_saving(self) -> bool:
        return self.saving

    @rx.var
    def mostrar_selector_empleado_modal(self) -> bool:
        return self.modal_modo_global

    @rx.var
    def tiene_empleados_modal(self) -> bool:
        return len(self.empleados_catalogo_modal) > 0

    @rx.var
    def puede_guardar_incapacidad(self) -> bool:
        if self.empleado_contexto_id <= 0:
            return False
        if self.modal_modo_global:
            return self.form_contrato_id > 0 and self.contexto_empleado_error == ""
        return True

    @rx.var
    def tipos_disponibles(self) -> list[dict]:
        if self.form_origen == OrigenIncapacidad.POR_ACUERDO.value:
            return [
                {
                    "value": TipoIncapacidad.ACUERDO.value,
                    "label": TipoIncapacidad.ACUERDO.descripcion,
                }
            ]

        return [
            {
                "value": TipoIncapacidad.ENF_GENERAL.value,
                "label": TipoIncapacidad.ENF_GENERAL.descripcion,
            },
            {
                "value": TipoIncapacidad.RIESGO_TRABAJO.value,
                "label": TipoIncapacidad.RIESGO_TRABAJO.descripcion,
            },
            {
                "value": TipoIncapacidad.MATERNIDAD.value,
                "label": TipoIncapacidad.MATERNIDAD.descripcion,
            },
        ]

    @rx.var
    def opciones_empleados_modal(self) -> list[dict]:
        return [
            {
                "value": str(item.get("id") or ""),
                "label": str(item.get("label") or ""),
            }
            for item in self.empleados_catalogo_modal
            if str(item.get("id") or "").strip() != ""
        ]

    @rx.var
    def incapacidades_empresa_filtradas(self) -> list[dict]:
        return self._filtrar_incapacidades_empresa()

    @rx.var
    def incapacidades_empresa_paginadas(self) -> list[dict]:
        items = self._filtrar_incapacidades_empresa()
        inicio = (max(self.pagina_incapacidades_actual, 1) - 1) * INCAPACIDADES_POR_PAGINA
        fin = inicio + INCAPACIDADES_POR_PAGINA
        return items[inicio:fin]

    @rx.var
    def total_incapacidades_filtradas(self) -> int:
        return len(self._filtrar_incapacidades_empresa())

    @rx.var
    def total_paginas_incapacidades(self) -> int:
        total = self.total_incapacidades_filtradas
        if total <= 0:
            return 1
        return ((total - 1) // INCAPACIDADES_POR_PAGINA) + 1

    @rx.var
    def paginas_visibles_incapacidades(self) -> list[int]:
        return list(range(1, self.total_paginas_incapacidades + 1))

    @rx.var
    def resumen_paginacion_incapacidades(self) -> str:
        total = self.total_incapacidades_filtradas
        if total <= 0:
            return "0 incapacidad(es)"

        inicio = ((max(self.pagina_incapacidades_actual, 1) - 1) * INCAPACIDADES_POR_PAGINA) + 1
        fin = min(inicio + INCAPACIDADES_POR_PAGINA - 1, total)
        return f"Mostrando {inicio}-{fin} de {total} incapacidad(es)"

    @staticmethod
    def _detalle_plaza(categoria: str, sede: str) -> str:
        partes = [capitalizar_palabras(categoria), capitalizar_palabras(sede)]
        return " · ".join(part for part in partes if part)

    @classmethod
    def _serializar_resumen(cls, resumen) -> dict:
        tipo = TipoIncapacidad(str(getattr(resumen.tipo, "value", resumen.tipo) or ""))
        origen = OrigenIncapacidad(str(getattr(resumen.origen, "value", resumen.origen) or ""))
        estatus = EstatusIncapacidad(str(getattr(resumen.estatus, "value", resumen.estatus) or ""))
        dias = int(resumen.dias_certificados or 0)
        total_certificados = int(resumen.total_certificados or 0)
        folio = str(getattr(resumen, "ultimo_folio_imss", "") or "").strip()
        return {
            "id": int(resumen.id or 0),
            "empleado_id": int(resumen.empleado_id or 0),
            "empleado_uuid": str(getattr(resumen, "empleado_uuid", "") or ""),
            "empleado_clave": str(getattr(resumen, "empleado_clave", "") or ""),
            "empleado_nombre": capitalizar_palabras(str(resumen.empleado_nombre or "")),
            "tipo": tipo.value,
            "tipo_label": tipo.descripcion,
            "origen": origen.value,
            "origen_label": origen.descripcion,
            "fecha_inicio": resumen.fecha_inicio.isoformat(),
            "fecha_inicio_fmt": formatear_fecha(resumen.fecha_inicio, valor_vacio="—"),
            "fecha_fin_estimada": (
                resumen.fecha_fin_estimada.isoformat()
                if resumen.fecha_fin_estimada
                else ""
            ),
            "fecha_fin_estimada_fmt": formatear_fecha(
                resumen.fecha_fin_estimada,
                valor_vacio="—",
            ),
            "periodo_label": (
                formatear_fecha(resumen.fecha_inicio, valor_vacio="—")
                + " — "
                + formatear_fecha(resumen.fecha_fin_estimada, valor_vacio="—")
            ),
            "estatus": estatus.value,
            "estatus_label": estatus.descripcion,
            "dias_certificados": dias,
            "dias_certificados_label": f"{dias} día(s)",
            "total_certificados": total_certificados,
            "total_certificados_label": f"{total_certificados} certificado(s)",
            "ultimo_folio_imss": folio,
            "folio_imss_label": folio or "Sin folio IMSS",
            "requiere_cobertura": bool(resumen.requiere_cobertura),
            "plaza_id": int(resumen.plaza_id or 0) or None,
            "contrato_id": int(resumen.contrato_id or 0) or None,
            "plaza_detalle": cls._detalle_plaza(
                str(resumen.plaza_categoria or ""),
                str(resumen.plaza_sede or ""),
            ),
        }

    @staticmethod
    def _normalizar_nombre_empleado_catalogo(empleado) -> str:
        nombre_attr = getattr(empleado, "nombre_completo", "")
        if callable(nombre_attr):
            return capitalizar_palabras(str(nombre_attr() or ""))
        return capitalizar_palabras(str(nombre_attr or ""))

    @classmethod
    def _serializar_empleado_catalogo(cls, empleado) -> dict:
        nombre = cls._normalizar_nombre_empleado_catalogo(empleado)
        clave = str(getattr(empleado, "clave", "") or "")
        etiqueta = nombre
        if clave:
            etiqueta = f"{clave} · {nombre}"
        return {
            "id": int(getattr(empleado, "id", 0) or 0),
            "uuid": str(getattr(empleado, "uuid", "") or ""),
            "clave": clave,
            "nombre": nombre,
            "label": etiqueta,
            "estatus": str(getattr(empleado, "estatus", "") or ""),
        }

    @staticmethod
    def _construir_resumen_contexto(contexto: dict) -> str:
        partes: list[str] = []
        categoria = capitalizar_palabras(str(contexto.get("categoria_nombre") or ""))
        sede = capitalizar_palabras(str(contexto.get("sede_nombre") or ""))
        detalle_plaza = " · ".join(part for part in [categoria, sede] if part)
        if detalle_plaza:
            partes.append(detalle_plaza)

        contrato_id = int(contexto.get("contrato_id") or 0)
        plaza_id = int(contexto.get("plaza_id") or 0)
        if contrato_id > 0:
            partes.append(f"Contrato #{contrato_id}")
        if plaza_id > 0:
            partes.append(f"Plaza #{plaza_id}")

        return " · ".join(partes)

    def _filtrar_incapacidades_empresa(self) -> list[dict]:
        items = list(self.incapacidades_empresa or [])

        if self.filtro_estatus_empresa != FILTRO_TODOS:
            items = [
                item
                for item in items
                if str(item.get("estatus") or "").upper() == self.filtro_estatus_empresa
            ]

        termino = str(self.filtro_busqueda or "").strip().lower()
        if not termino:
            return items

        filtrados: list[dict] = []
        for item in items:
            searchable = " ".join(
                [
                    str(item.get("empleado_nombre") or ""),
                    str(item.get("empleado_clave") or ""),
                    str(item.get("tipo_label") or ""),
                    str(item.get("origen_label") or ""),
                    str(item.get("periodo_label") or ""),
                    str(item.get("plaza_detalle") or ""),
                    str(item.get("folio_imss_label") or ""),
                ]
            ).lower()
            if termino in searchable:
                filtrados.append(item)
        return filtrados

    def _normalizar_pagina_incapacidades(self) -> None:
        total = len(self._filtrar_incapacidades_empresa())
        total_paginas = 1 if total <= 0 else ((total - 1) // INCAPACIDADES_POR_PAGINA) + 1
        if self.pagina_incapacidades_actual < 1:
            self.pagina_incapacidades_actual = 1
        elif self.pagina_incapacidades_actual > total_paginas:
            self.pagina_incapacidades_actual = total_paginas

    def _limpiar_selector_empleado_modal(self) -> None:
        self.empleado_seleccionado_modal_id = ""
        self.empleado_contexto_id = 0
        self.empleado_contexto_uuid = ""
        self.empleado_contexto_clave = ""
        self.empleado_contexto_nombre = ""
        self.form_plaza_id = 0
        self.form_contrato_id = 0
        self.contexto_empleado_resumen = ""
        self.contexto_empleado_error = ""

    def _reset_form(self) -> None:
        self.form_origen = OrigenIncapacidad.FORMAL.value
        self.form_tipo = TipoIncapacidad.ENF_GENERAL.value
        self.form_fecha_inicio = ""
        self.form_fecha_fin_estimada = ""
        self.form_folio_imss = ""
        self.form_dias_certificado = ""
        self.form_porcentaje_pago = "100.00"
        self.form_requiere_cobertura = False
        self.form_notas = ""
        self.form_error = ""

    async def _cargar_incapacidades_empleado(self, empleado_id: int) -> None:
        try:
            resultados = await incapacidad_service.listar_por_empleado(empleado_id)
            self.incapacidades_empleado = [
                self._serializar_resumen(resultado)
                for resultado in resultados
            ]
            self.error_incapacidades = ""
        except Exception as exc:
            self.incapacidades_empleado = []
            self.error_incapacidades = str(exc)

    async def _cargar_incapacidades_empresa(self) -> None:
        if not self.id_empresa_actual:
            self.incapacidades_empresa = []
            self.error_incapacidades_empresa = ""
            return

        try:
            resultados = await incapacidad_service.listar_por_empresa(self.id_empresa_actual)
            self.incapacidades_empresa = [
                self._serializar_resumen(resultado)
                for resultado in resultados
            ]
            self.error_incapacidades_empresa = ""
            self._normalizar_pagina_incapacidades()
        except Exception as exc:
            self.incapacidades_empresa = []
            self.error_incapacidades_empresa = str(exc)

    async def _cargar_conteos_empresa(self) -> None:
        if not self.id_empresa_actual:
            self.conteos_empresa = {"activas": 0, "vencidas": 0, "total": 0}
            return

        try:
            self.conteos_empresa = await incapacidad_service.obtener_conteos(self.id_empresa_actual)
        except Exception as exc:
            self.conteos_empresa = {"activas": 0, "vencidas": 0, "total": 0}
            self.error_incapacidades_empresa = str(exc)

    async def _cargar_catalogo_empleados_modal(self) -> None:
        if not self.id_empresa_actual:
            self.empleados_catalogo_modal = []
            self.error_empleados_modal = ""
            return

        termino = str(self.busqueda_empleado_modal or "").strip()

        try:
            if len(termino) >= 2:
                empleados = await empleado_service.buscar(
                    termino,
                    empresa_id=self.id_empresa_actual,
                    limite=CATALOGO_EMPLEADOS_MODAL_LIMITE,
                )
                empleados = [
                    emp
                    for emp in empleados
                    if str(getattr(emp, "estatus", "") or "").upper() == EstatusEmpleado.ACTIVO.value
                ]
            else:
                empleados = await empleado_service.obtener_por_empresa(
                    self.id_empresa_actual,
                    incluir_inactivos=False,
                    limite=CATALOGO_EMPLEADOS_MODAL_LIMITE,
                    offset=0,
                )

            serializados = [self._serializar_empleado_catalogo(emp) for emp in empleados]
            serializados = [item for item in serializados if int(item.get("id") or 0) > 0]

            seleccionado_actual = None
            if self.empleado_contexto_id > 0:
                seleccionado_actual = {
                    "id": self.empleado_contexto_id,
                    "uuid": self.empleado_contexto_uuid,
                    "clave": self.empleado_contexto_clave,
                    "nombre": self.empleado_contexto_nombre,
                    "label": (
                        f"{self.empleado_contexto_clave} · {self.empleado_contexto_nombre}"
                        if self.empleado_contexto_clave
                        else self.empleado_contexto_nombre
                    ),
                }

            if (
                seleccionado_actual is not None
                and not any(
                    int(item.get("id") or 0) == self.empleado_contexto_id
                    for item in serializados
                )
            ):
                serializados.insert(0, seleccionado_actual)

            self.empleados_catalogo_modal = serializados
            self.error_empleados_modal = ""
        except Exception as exc:
            self.empleados_catalogo_modal = []
            self.error_empleados_modal = f"Error cargando empleados: {exc}"

    async def on_mount_incapacidades(self):
        """Monta la pagina administrativa de incapacidades del portal."""
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return

        if not self.mostrar_seccion_rrhh or not self.puede_acceder_rrhh:
            yield rx.redirect("/portal")
            return

        self.filtro_busqueda = ""
        self.filtro_estatus_empresa = FILTRO_TODOS
        self.pagina_incapacidades_actual = 1
        async for _ in self._montar_pagina(
            self._cargar_incapacidades_empresa,
            self._cargar_conteos_empresa,
        ):
            yield

    async def abrir_modal_registro_global(self):
        """Abre el modal en modo global y carga empleados activos."""
        self.modal_modo_global = True
        self.modal_abierto = True
        self._reset_form()
        self._limpiar_selector_empleado_modal()
        self.error_empleados_modal = ""
        self.busqueda_empleado_modal = ""
        self.empleados_catalogo_modal = []
        self.cargando_empleados_modal = True
        yield

        try:
            await self._cargar_catalogo_empleados_modal()
        finally:
            self.cargando_empleados_modal = False

    def abrir_modal_registro(
        self,
        empleado_id: int,
        empleado_nombre: str,
        plaza_id: int = 0,
        contrato_id: int = 0,
    ):
        empleado_id_int = int(empleado_id or 0)
        if empleado_id_int <= 0:
            return rx.toast.error("No se pudo identificar al empleado")

        self.modal_modo_global = False
        self.modal_abierto = True
        self._reset_form()
        self._limpiar_selector_empleado_modal()
        self.error_empleados_modal = ""
        self.empleados_catalogo_modal = []
        self.busqueda_empleado_modal = ""

        self.empleado_contexto_id = empleado_id_int
        self.empleado_seleccionado_modal_id = str(empleado_id_int)
        self.empleado_contexto_nombre = capitalizar_palabras(str(empleado_nombre or ""))
        self.form_plaza_id = int(plaza_id or 0)
        self.form_contrato_id = int(contrato_id or 0)

    def cerrar_modal_registro(self):
        self.modal_abierto = False
        self.modal_modo_global = False
        self.form_error = ""
        self.error_empleados_modal = ""
        self.cargando_empleados_modal = False
        self.busqueda_empleado_modal = ""
        self.empleados_catalogo_modal = []
        self._limpiar_selector_empleado_modal()

    def set_filtro_busqueda_incapacidades(self, value: str):
        self.filtro_busqueda = str(value or "")
        self.pagina_incapacidades_actual = 1
        self._normalizar_pagina_incapacidades()

    def limpiar_filtro_busqueda_incapacidades(self):
        self.filtro_busqueda = ""
        self.pagina_incapacidades_actual = 1
        self._normalizar_pagina_incapacidades()

    def set_filtro_estatus_empresa(self, value: str):
        valor = str(value or FILTRO_TODOS)
        valores_validos = {
            FILTRO_TODOS,
            EstatusIncapacidad.ACTIVA.value,
            EstatusIncapacidad.VENCIDA.value,
            EstatusIncapacidad.CERRADA.value,
        }
        self.filtro_estatus_empresa = valor if valor in valores_validos else FILTRO_TODOS
        self.pagina_incapacidades_actual = 1
        self._normalizar_pagina_incapacidades()

    def ir_a_pagina_incapacidades(self, pagina):
        self.set_int_attr("pagina_incapacidades_actual", pagina, 1)
        self._normalizar_pagina_incapacidades()

    def pagina_anterior_incapacidades(self):
        self.pagina_incapacidades_actual = max(self.pagina_incapacidades_actual - 1, 1)

    def pagina_siguiente_incapacidades(self):
        self.pagina_incapacidades_actual = min(
            self.pagina_incapacidades_actual + 1,
            self.total_paginas_incapacidades,
        )

    async def set_busqueda_empleado_modal(self, value: str):
        self.busqueda_empleado_modal = str(value or "")
        self.error_empleados_modal = ""
        self.cargando_empleados_modal = True
        yield

        try:
            await self._cargar_catalogo_empleados_modal()
        finally:
            self.cargando_empleados_modal = False

    async def limpiar_busqueda_empleado_modal(self):
        self.busqueda_empleado_modal = ""
        self.error_empleados_modal = ""
        self.cargando_empleados_modal = True
        yield

        try:
            await self._cargar_catalogo_empleados_modal()
        finally:
            self.cargando_empleados_modal = False

    async def set_empleado_seleccionado_modal_id(self, value: str):
        seleccionado = str(value or "").strip()
        self.empleado_seleccionado_modal_id = seleccionado
        self.contexto_empleado_error = ""
        self.contexto_empleado_resumen = ""
        self.form_error = ""
        self.form_plaza_id = 0
        self.form_contrato_id = 0

        if not seleccionado:
            self._limpiar_selector_empleado_modal()
            return

        empleado = next(
            (
                item
                for item in self.empleados_catalogo_modal
                if str(item.get("id") or "") == seleccionado
            ),
            None,
        )
        if empleado is None:
            self.contexto_empleado_error = "Seleccione un empleado valido"
            return

        self.empleado_contexto_id = int(empleado.get("id") or 0)
        self.empleado_contexto_uuid = str(empleado.get("uuid") or "")
        self.empleado_contexto_clave = str(empleado.get("clave") or "")
        self.empleado_contexto_nombre = capitalizar_palabras(str(empleado.get("nombre") or ""))
        self.cargando_empleados_modal = True
        yield

        try:
            contexto = await incapacidad_service.obtener_contexto_operativo_empleado(
                self.empleado_contexto_id,
            )
            self.form_plaza_id = int(contexto.get("plaza_id") or 0)
            self.form_contrato_id = int(contexto.get("contrato_id") or 0)
            self.contexto_empleado_resumen = self._construir_resumen_contexto(contexto)
            self.contexto_empleado_error = ""
        except BusinessRuleError as exc:
            self.contexto_empleado_resumen = ""
            self.contexto_empleado_error = str(exc)
        except Exception as exc:
            self.contexto_empleado_resumen = ""
            self.contexto_empleado_error = f"Error resolviendo contexto laboral: {exc}"
        finally:
            self.cargando_empleados_modal = False

    def set_form_origen(self, value: str):
        origen = str(value or OrigenIncapacidad.FORMAL.value).upper()
        if origen not in {
            OrigenIncapacidad.FORMAL.value,
            OrigenIncapacidad.POR_ACUERDO.value,
        }:
            origen = OrigenIncapacidad.FORMAL.value
        self.form_origen = origen
        if origen == OrigenIncapacidad.POR_ACUERDO.value:
            self.form_tipo = TipoIncapacidad.ACUERDO.value
            self.form_folio_imss = ""
        elif self.form_tipo == TipoIncapacidad.ACUERDO.value:
            self.form_tipo = TipoIncapacidad.ENF_GENERAL.value

    def set_form_tipo(self, value: str):
        self.form_tipo = str(value or "").upper()

    def set_form_fecha_inicio(self, value: str):
        self.form_fecha_inicio = normalize_date_input(value)

    def set_form_fecha_fin_estimada(self, value: str):
        self.form_fecha_fin_estimada = normalize_date_input(value)

    def set_form_folio_imss(self, value: str):
        self.form_folio_imss = normalizar_mayusculas(value)

    def set_form_dias_certificado(self, value: str):
        self.form_dias_certificado = str(value or "").strip()

    def set_form_porcentaje_pago(self, value: str):
        self.form_porcentaje_pago = str(value or "").strip()

    def set_form_requiere_cobertura(self, value: bool):
        self.form_requiere_cobertura = bool(value)

    def set_form_notas(self, value: str):
        self.form_notas = str(value or "")

    async def cargar_por_empleado(self, empleado_id: int):
        empleado_id_int = int(empleado_id or 0)
        if empleado_id_int <= 0:
            self.incapacidades_empleado = []
            self.error_incapacidades = ""
            return

        self.empleado_contexto_id = empleado_id_int
        self.cargando_incapacidades = True
        self.error_incapacidades = ""
        yield

        try:
            await self._cargar_incapacidades_empleado(empleado_id_int)
        finally:
            self.cargando_incapacidades = False

    def ir_a_ficha_empleado(self, incapacidad: dict):
        empleado_ref = str(
            incapacidad.get("empleado_uuid")
            or incapacidad.get("empleado_id")
            or ""
        ).strip()
        if empleado_ref == "":
            return rx.toast.error("No se pudo abrir la ficha del empleado")
        return rx.redirect(f"/portal/empleados/{empleado_ref}")

    async def guardar_incapacidad(self):
        if self.empleado_contexto_id <= 0:
            self.form_error = "No hay un empleado seleccionado para registrar la incapacidad"
            return

        if self.modal_modo_global and self.form_contrato_id <= 0:
            self.form_error = (
                self.contexto_empleado_error
                or "Seleccione un empleado con contexto laboral vigente antes de guardar"
            )
            return

        fecha_inicio = parse_date_input(self.form_fecha_inicio)
        fecha_fin = parse_date_input(self.form_fecha_fin_estimada)
        if fecha_inicio is None:
            self.form_error = "Capture una fecha de inicio valida"
            return

        dias_certificado = None
        if self.form_dias_certificado:
            try:
                dias_certificado = int(self.form_dias_certificado)
            except ValueError:
                self.form_error = "Los dias del certificado deben ser un numero entero"
                return

        try:
            porcentaje_pago = Decimal(self.form_porcentaje_pago or "100")
        except (InvalidOperation, ValueError):
            self.form_error = "Capture un porcentaje de pago valido"
            return

        self.saving = True
        self.form_error = ""
        yield

        try:
            await incapacidad_service.registrar_incapacidad(
                IncapacidadCreate(
                    empleado_id=self.empleado_contexto_id,
                    plaza_id=self.form_plaza_id or None,
                    contrato_id=self.form_contrato_id or None,
                    empresa_id=self.id_empresa_actual,
                    origen=OrigenIncapacidad(self.form_origen),
                    tipo=TipoIncapacidad(self.form_tipo),
                    fecha_inicio=fecha_inicio,
                    fecha_fin_estimada=fecha_fin,
                    porcentaje_pago=porcentaje_pago,
                    requiere_cobertura=self.form_requiere_cobertura,
                    notas=self.form_notas or None,
                    registrado_por=self.obtener_uuid_usuario_actual(),
                    folio_imss=self.form_folio_imss or None,
                    dias_certificado=dias_certificado,
                    archivo_id=None,
                )
            )
            modal_global = self.modal_modo_global
            empleado_id = self.empleado_contexto_id
            self.cerrar_modal_registro()

            if modal_global:
                await self._cargar_incapacidades_empresa()
                await self._cargar_conteos_empresa()
            elif empleado_id > 0:
                await self._cargar_incapacidades_empleado(empleado_id)

            yield rx.toast.success("Incapacidad registrada correctamente")
        except (BusinessRuleError, ValueError) as exc:
            self.form_error = str(exc)
        except Exception as exc:
            self.form_error = f"Error al registrar incapacidad: {exc}"
        finally:
            self.saving = False
