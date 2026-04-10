"""
Pagina Contratos del portal de cliente.

Muestra TODOS los contratos de la empresa (incluyendo borradores) agrupados por
año de fecha de inicio, con CTAs contextuales según estatus e inclusión de
personal. Es el punto de entrada del flujo Contratos → Plazas → Nómina.
"""
from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import List

import reflex as rx
from pydantic import BaseModel, Field

from app.core.exceptions import BusinessRuleError, DatabaseError
from app.core.text_utils import (
    capitalizar_con_preposiciones,
    capitalizar_palabras,
    formatear_vigencia_meses,
    normalizar_mayusculas,
)
from app.core.ui_helpers import FILTRO_TODOS
from app.domain.enums import EstatusPlaza
from app.modules.application import (
    contrato_categoria_service,
    contrato_service,
    plaza_service,
    tipo_servicio_service,
)
from app.presentation.components.shared.auth_state import AuthState
from app.core.utils import normalize_date_input, parse_date_input
from app.presentation.components.ui import (
    boton_cancelar,
    empty_state_card,
    estatus_badge,
    feedback_callout,
    form_date,
    form_input,
    input_busqueda,
    metric_card,
    metric_card_grid,
    modal_confirmar_accion,
    modal_formulario,
    page_header,
    skeleton_tabla,
    status_badge_reactive,
    tabla_cta_button,
    table_shell,
    wizard_stepper,
)
from app.presentation.layouts.backoffice import page_layout
from app.presentation.pages.backoffice.contratos.contrato_detail_sections import (
    contrato_detail_info_sections,
    contrato_detail_text,
)
from app.presentation.pages.backoffice.contratos.contrato_presentacion import (
    enriquecer_contrato_presentacion,
    serializar_categoria_contrato_detalle,
)
from app.presentation.pages.backoffice.contratos.contratos_modals import modal_contrato
from app.presentation.pages.backoffice.contratos.contratos_state import ContratosState
from app.presentation.pages.portal.state.portal_state import PortalState
from app.presentation.theme import Colors, Radius, Spacing, Typography


logger = logging.getLogger(__name__)


# =============================================================================
# STATE
# =============================================================================


CONTRATOS_HEADERS = [
    {"nombre": "Contrato", "ancho": "240px", "header_align": "left"},
    {"nombre": "Tipo", "ancho": "180px", "header_align": "center"},
    {"nombre": "Vigencia", "ancho": "150px", "header_align": "center"},
    {"nombre": "Plazas", "ancho": "90px", "header_align": "center"},
    {"nombre": "Estatus", "ancho": "120px", "header_align": "center"},
    {"nombre": "", "ancho": "140px", "header_align": "right"},
]


class GrupoContratosAnio(BaseModel):
    """Grupo de contratos renderizado por año de fecha de inicio."""

    anio: str = ""
    count: int = 0
    contratos: list[dict] = Field(default_factory=list)


class MisContratosState(PortalState):
    """State para la lista de contratos del portal."""

    contratos: List[dict] = []
    total_contratos_lista: int = 0

    tipos_servicio_opciones: List[dict] = []

    # Filtros
    filtro_busqueda_cto: str = ""
    filtro_estatus_cto: str = FILTRO_TODOS
    filtro_tipo_cto: str = FILTRO_TODOS

    # Colapso del historial por año (lista de años colapsados).
    anios_historial_colapsados: List[str] = []

    # Detalle / modales heredados
    contrato_detalle: dict = {}
    categorias_detalle_contrato: List[dict] = []
    modal_detalle_abierto: bool = False
    mostrar_modal_confirmar_cancelar: bool = False
    saving_accion_contrato: bool = False

    # Extensión de contrato — wizard multi-paso
    modal_extension_abierto: bool = False
    contrato_a_extender: dict = {}
    wizard_paso_actual: int = 1  # pasos activos: 1 (vigencia), 2 (categorías), 4 (confirmar)
    form_extension_fecha_inicio: str = ""
    form_extension_fecha_fin: str = ""
    error_form_extension_fecha_inicio: str = ""
    error_form_extension_fecha_fin: str = ""
    # Paso 2: snapshot editable de las categorías del padre. Cada item es un
    # dict con keys: id (del ContratoCategoria del padre), nombre,
    # form_sueldo_base, form_tipo_sueldo, form_costo_contractual,
    # form_cantidad_minima, form_cantidad_maxima.
    wizard_categorias: List[dict] = []
    wizard_error_categorias: str = ""
    # Paso 3: empleados activos del padre. Cada item tiene:
    #   empleado_id, nombre, categoria_puesto_id, categoria_nombre,
    #   plaza_id, plaza_numero
    wizard_empleados_padre: List[dict] = []
    # IDs de empleados marcados para migrar a la extensión.
    wizard_empleado_ids_seleccionados: List[int] = []
    wizard_error_empleados: str = ""
    saving_extension: bool = False

    # -----------------------------
    # Setters
    # -----------------------------
    def set_filtro_busqueda_cto(self, value: str):
        self.filtro_busqueda_cto = value or ""

    def limpiar_busqueda_contratos(self):
        self.filtro_busqueda_cto = ""

    def set_filtro_estatus_cto(self, value: str):
        self.filtro_estatus_cto = value if value else FILTRO_TODOS

    def set_filtro_tipo_cto(self, value: str):
        self.filtro_tipo_cto = value if value else FILTRO_TODOS

    def limpiar_filtros_contratos(self):
        self.filtro_busqueda_cto = ""
        self.filtro_estatus_cto = FILTRO_TODOS
        self.filtro_tipo_cto = FILTRO_TODOS

    def toggle_historial_anio(self, anio: str):
        anio_str = str(anio or "")
        if not anio_str:
            return
        if anio_str in self.anios_historial_colapsados:
            self.anios_historial_colapsados = [
                a for a in self.anios_historial_colapsados if a != anio_str
            ]
        else:
            self.anios_historial_colapsados = [
                *self.anios_historial_colapsados,
                anio_str,
            ]

    # -----------------------------
    # Computed vars
    # -----------------------------
    # -----------------------------
    # Clasificación por estatus
    # -----------------------------
    _ESTATUS_ACTIVOS = ("ACTIVO", "SUSPENDIDO")
    _ESTATUS_HISTORIAL = ("VENCIDO", "LIQUIDADO", "CANCELADO")

    @rx.var
    def hay_filtros_activos(self) -> bool:
        return (
            bool(self.filtro_busqueda_cto.strip())
            or self.filtro_estatus_cto != FILTRO_TODOS
            or self.filtro_tipo_cto != FILTRO_TODOS
        )

    def _contratos_coinciden_filtros(self, contrato: dict) -> bool:
        """Aplica filtros locales (búsqueda + tipo) a un contrato.

        El filtro por estatus NO se aplica aquí: cada sección define su
        propio conjunto de estatus. El select de estatus actúa como filtro
        adicional contra la sección aplicable.
        """
        termino = self.filtro_busqueda_cto.strip().lower()
        if termino:
            haystack = " ".join(
                [
                    str(contrato.get("codigo") or ""),
                    str(contrato.get("numero_folio_buap") or ""),
                    str(contrato.get("descripcion_objeto") or ""),
                ]
            ).lower()
            if termino not in haystack:
                return False
        if self.filtro_tipo_cto != FILTRO_TODOS:
            if str(int(contrato.get("tipo_servicio_id") or 0)) != self.filtro_tipo_cto:
                return False
        return True

    def _filtro_estatus_aplicable(self, contrato: dict, estatus_seccion: tuple) -> bool:
        estatus = str(contrato.get("estatus") or "").upper()
        if estatus not in estatus_seccion:
            return False
        if self.filtro_estatus_cto != FILTRO_TODOS:
            return estatus == self.filtro_estatus_cto
        return True

    def _agrupar_por_anio(self, contratos: list[dict]) -> list[GrupoContratosAnio]:
        grupos: dict[int, list[dict]] = {}
        for item in contratos:
            grupos.setdefault(int(item.get("anio_inicio") or 0), []).append(item)
        resultado: list[GrupoContratosAnio] = []
        for anio in sorted(grupos.keys(), reverse=True):
            items = sorted(
                grupos[anio],
                key=lambda c: str(c.get("fecha_inicio") or ""),
                reverse=True,
            )
            resultado.append(
                GrupoContratosAnio(
                    anio=str(anio) if anio > 0 else "Sin fecha",
                    count=len(items),
                    contratos=items,
                )
            )
        return resultado

    # -----------------------------
    # Secciones reactivas
    # -----------------------------
    @rx.var
    def contratos_borradores(self) -> list[dict]:
        filtrados = [
            c
            for c in self.contratos
            if str(c.get("estatus") or "").upper() == "BORRADOR"
            and self._contratos_coinciden_filtros(c)
            and (
                self.filtro_estatus_cto == FILTRO_TODOS
                or self.filtro_estatus_cto == "BORRADOR"
            )
        ]
        return sorted(
            filtrados,
            key=lambda c: str(c.get("fecha_inicio") or c.get("fecha_creacion") or ""),
            reverse=True,
        )

    @rx.var
    def contratos_activos_grupos(self) -> list[GrupoContratosAnio]:
        filtrados = [
            c
            for c in self.contratos
            if self._filtro_estatus_aplicable(c, self._ESTATUS_ACTIVOS)
            and self._contratos_coinciden_filtros(c)
        ]
        return self._agrupar_por_anio(filtrados)

    @rx.var
    def contratos_historial_grupos(self) -> list[GrupoContratosAnio]:
        filtrados = [
            c
            for c in self.contratos
            if self._filtro_estatus_aplicable(c, self._ESTATUS_HISTORIAL)
            and self._contratos_coinciden_filtros(c)
        ]
        return self._agrupar_por_anio(filtrados)

    @rx.var
    def tiene_borradores_listado(self) -> bool:
        return len(self.contratos_borradores) > 0

    @rx.var
    def tiene_activos_listado(self) -> bool:
        return any(int(g.count) > 0 for g in self.contratos_activos_grupos)

    @rx.var
    def tiene_historial_listado(self) -> bool:
        return any(int(g.count) > 0 for g in self.contratos_historial_grupos)

    @rx.var
    def total_contratos_visibles(self) -> int:
        total = len(self.contratos_borradores)
        total += sum(int(g.count) for g in self.contratos_activos_grupos)
        total += sum(int(g.count) for g in self.contratos_historial_grupos)
        return total

    @rx.var
    def tiene_grupos_visibles(self) -> bool:
        return self.total_contratos_visibles > 0

    @rx.var
    def mensaje_callout_borradores(self) -> str:
        n = len(self.contratos_borradores)
        if n == 0:
            return ""
        sustantivo = "contrato" if n == 1 else "contratos"
        verbo = "necesita" if n == 1 else "necesitan"
        return f"{n} {sustantivo} en borrador {verbo} configuración"

    # -----------------------------
    # Métricas KPI (sobre datos sin filtros de búsqueda/tipo)
    # -----------------------------
    @rx.var
    def total_borradores(self) -> int:
        return sum(
            1 for c in self.contratos
            if str(c.get("estatus") or "").upper() == "BORRADOR"
        )

    @rx.var
    def total_activos(self) -> int:
        return sum(
            1 for c in self.contratos
            if str(c.get("estatus") or "").upper() in self._ESTATUS_ACTIVOS
        )

    @rx.var
    def total_historial(self) -> int:
        return sum(
            1 for c in self.contratos
            if str(c.get("estatus") or "").upper() in self._ESTATUS_HISTORIAL
        )

    def _cobertura_global_raw(self) -> tuple[int, int]:
        total = 0
        ocupadas = 0
        for c in self.contratos:
            if str(c.get("estatus") or "").upper() != "ACTIVO":
                continue
            if not bool(c.get("tiene_personal")):
                continue
            total += int(c.get("total_plazas") or 0)
            ocupadas += int(c.get("plazas_ocupadas") or 0)
        return ocupadas, total

    @rx.var
    def cobertura_global_pct(self) -> int:
        ocupadas, total = self._cobertura_global_raw()
        if total <= 0:
            return 0
        return int(round((ocupadas / total) * 100))

    @rx.var
    def cobertura_global_texto(self) -> str:
        ocupadas, total = self._cobertura_global_raw()
        if total <= 0:
            return "—"
        return f"{ocupadas}/{total}"

    @rx.var
    def cobertura_global_descripcion(self) -> str:
        _, total = self._cobertura_global_raw()
        if total <= 0:
            return "Sin plazas configuradas"
        pct = self.cobertura_global_pct
        if pct >= 80:
            return "Saludable"
        if pct >= 60:
            return "Aceptable"
        return "Requiere atención"

    @rx.var
    def cobertura_global_color(self) -> str:
        _, total = self._cobertura_global_raw()
        if total <= 0:
            return Colors.TEXT_MUTED
        pct = self.cobertura_global_pct
        if pct >= 80:
            return Colors.SUCCESS
        if pct >= 60:
            return Colors.WARNING
        return Colors.ERROR

    @rx.var
    def color_metrica_borradores(self) -> str:
        return Colors.WARNING if self.total_borradores > 0 else Colors.TEXT_MUTED

    def historial_anio_colapsado(self, anio: str) -> bool:
        return str(anio or "") in self.anios_historial_colapsados

    @rx.var
    def puede_navegar_plazas_desde_contratos(self) -> bool:
        return self.mostrar_seccion_plazas_portal

    @rx.var
    def contrato_detalle_tiene_plazas(self) -> bool:
        return bool(
            self.es_usuario_empresa_portal
            and self.tiene_contratos_con_personal
            and (self.puede_gestionar_personal or self.puede_registrar_personal)
            and self._contrato_tiene_personal(self.contrato_detalle)
        )

    @rx.var
    def puede_editar_detalle(self) -> bool:
        contrato = self.contrato_detalle
        if not self.es_admin_empresa or not contrato:
            return False
        estatus = str(contrato.get("estatus", ""))
        return estatus in ("BORRADOR", "SUSPENDIDO")

    @rx.var
    def puede_activar_detalle(self) -> bool:
        contrato = self.contrato_detalle
        return bool(
            self.es_admin_empresa
            and contrato
            and contrato.get("estatus") == "BORRADOR"
        )

    @rx.var
    def puede_suspender_detalle(self) -> bool:
        contrato = self.contrato_detalle
        return bool(
            self.es_admin_empresa
            and contrato
            and contrato.get("estatus") == "ACTIVO"
        )

    @rx.var
    def puede_reactivar_detalle(self) -> bool:
        contrato = self.contrato_detalle
        return bool(
            self.es_admin_empresa
            and contrato
            and contrato.get("estatus") == "SUSPENDIDO"
        )

    @rx.var
    def puede_cancelar_detalle(self) -> bool:
        """Un contrato cancelable no puede estar ya cancelado ni liquidado."""
        contrato = self.contrato_detalle
        if not self.es_admin_empresa or not contrato:
            return False
        estatus = str(contrato.get("estatus") or "").upper()
        return estatus not in ("CANCELADO", "LIQUIDADO")

    @rx.var
    def puede_liquidar_detalle(self) -> bool:
        """Solo contratos VENCIDOS pueden liquidarse definitivamente."""
        contrato = self.contrato_detalle
        return bool(
            self.es_admin_empresa
            and contrato
            and contrato.get("estatus") == "VENCIDO"
        )

    @rx.var
    def tiene_categorias_detalle_contrato(self) -> bool:
        return len(self.categorias_detalle_contrato) > 0

    @rx.var
    def total_categorias_detalle_contrato(self) -> int:
        return len(self.categorias_detalle_contrato)

    # -----------------------------
    # Ciclo de vida
    # -----------------------------
    async def on_mount_contratos(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.mostrar_seccion_contrato:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_contratos):
            yield
        # Datos derivados (tipos servicio, resumenes de plazas) son best-effort
        # y no deben bloquear la carga principal ni romper los tests unitarios.
        try:
            await self._cargar_datos_extra()
        except Exception:
            pass

    async def _fetch_contratos(self):
        """Carga contratos de la empresa del usuario."""
        if not self.id_empresa_actual:
            self.contratos = []
            self.total_contratos_lista = 0
            return

        try:
            # Siempre incluimos inactivos: el filtro por estatus ahora solo
            # afecta las secciones en memoria (borradores/activos/historial),
            # no el query. Así garantizamos que métricas y secciones tengan
            # todos los contratos disponibles.
            contratos = await contrato_service.obtener_por_empresa(
                empresa_id=self.id_empresa_actual,
                incluir_inactivos=True,
            )
            self.contratos = [
                self._enriquecer_contrato(
                    c.model_dump(mode="json") if hasattr(c, "model_dump") else c
                )
                for c in contratos
            ]
            self.total_contratos_lista = len(self.contratos)
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando contratos: {e}", "error")
            self.contratos = []
            self.total_contratos_lista = 0
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.contratos = []
            self.total_contratos_lista = 0

    async def cargar_contratos(self):
        """Recarga contratos con skeleton (para refrescos manuales)."""
        async for _ in self._recargar_datos(self._fetch_contratos):
            yield
        try:
            await self._cargar_datos_extra()
        except Exception:
            pass

    async def _recargar_contratos_y_sidebar(self) -> None:
        """Sincroniza listado local y progressive disclosure del sidebar."""
        await self._fetch_contratos()
        try:
            await self._cargar_datos_extra()
        except Exception:
            pass
        await self.refrescar_sidebar()

    async def _cargar_datos_extra(self) -> None:
        """Carga tipos de servicio y resumenes de plazas para la UI."""
        # Tipos de servicio activos para el filtro y los badges.
        try:
            tipos = await tipo_servicio_service.obtener_activas_portal_empresa(
                self.id_empresa_actual
            )
        except Exception:
            tipos = []

        nombres_por_id: dict[int, str] = {}
        opciones: list[dict] = []
        for tipo in tipos or []:
            tipo_id = int(getattr(tipo, "id", 0) or 0)
            nombre = str(getattr(tipo, "nombre", "") or "")
            if tipo_id <= 0 or not nombre:
                continue
            nombres_por_id[tipo_id] = nombre
            opciones.append({"id": str(tipo_id), "nombre": capitalizar_palabras(nombre)})
        opciones.sort(key=lambda item: item["nombre"])
        self.tipos_servicio_opciones = opciones

        # Resumen de plazas por contrato (ocupadas / total).
        contratos_ids = [
            int(c.get("id") or 0)
            for c in self.contratos
            if int(c.get("id") or 0) > 0 and bool(c.get("tiene_personal"))
        ]
        resumenes = await asyncio.gather(
            *[plaza_service.calcular_totales_contrato(cid) for cid in contratos_ids],
            return_exceptions=True,
        )
        totales_por_id: dict[int, dict] = {}
        for cid, resumen in zip(contratos_ids, resumenes):
            if isinstance(resumen, Exception):
                continue
            totales_por_id[cid] = {
                "total": int(getattr(resumen, "total_plazas", 0) or 0),
                "ocupadas": int(getattr(resumen, "plazas_ocupadas", 0) or 0),
            }

        # Aplicar información extra sobre la lista ya enriquecida.
        nueva_lista: list[dict] = []
        for contrato in self.contratos:
            data = dict(contrato)
            tipo_id = int(data.get("tipo_servicio_id") or 0)
            if tipo_id and tipo_id in nombres_por_id:
                data["tipo_servicio_nombre"] = capitalizar_palabras(nombres_por_id[tipo_id])
            cid = int(data.get("id") or 0)
            resumen = totales_por_id.get(cid)
            if resumen:
                data["total_plazas"] = resumen["total"]
                data["plazas_ocupadas"] = resumen["ocupadas"]
                data["pct_cobertura"] = self._calcular_pct_cobertura(
                    resumen["ocupadas"], resumen["total"]
                )
            nueva_lista.append(data)
        self.contratos = nueva_lista

    # -----------------------------
    # Navegación desde CTA
    # -----------------------------
    async def navegar_contrato(self, contrato: dict):
        """Enruta el CTA de la fila según estatus.

        - BORRADOR / ACTIVO con personal: redirige al detalle de plazas
          del contrato.
        - Resto (ACTIVO sin personal, SUSPENDIDO, VENCIDO, ...): abre el
          modal de detalle general. NO existe una ruta standalone
          `/portal/contratos/{codigo}`; el detalle se muestra via modal.
        """
        codigo_norm = normalizar_mayusculas(str(contrato.get("codigo") or ""))
        if not codigo_norm:
            return rx.redirect("/portal/contratos")
        estatus_norm = str(contrato.get("estatus") or "").upper()
        tiene_personal = bool(contrato.get("tiene_personal"))

        if estatus_norm == "BORRADOR" or (
            estatus_norm == "ACTIVO" and tiene_personal
        ):
            return rx.redirect(
                PortalState.construir_ruta_plazas_contrato(codigo_norm)
            )

        # Detalle general vía modal.
        await self.abrir_detalle(contrato)
        return None

    @rx.event
    def ir_a_plazas_contrato(self, codigo_contrato: int | str):
        return rx.redirect(
            PortalState.construir_ruta_plazas_contrato(codigo_contrato),
        )

    @rx.event
    def ir_a_plazas_contrato_detalle(self):
        codigo_contrato = str(self.contrato_detalle.get("codigo") or "").strip()
        if not codigo_contrato:
            return rx.redirect("/portal/contratos")
        self.cerrar_detalle()
        return rx.redirect(
            PortalState.construir_ruta_plazas_contrato(codigo_contrato),
        )

    # -----------------------------
    # Detalle / acciones existentes
    # -----------------------------
    async def abrir_detalle(self, contrato: dict):
        """Abre el modal de detalle de un contrato."""
        self.contrato_detalle = self._enriquecer_contrato(contrato)
        self.categorias_detalle_contrato = []
        contrato_id = int(contrato.get("id") or 0)
        if contrato_id:
            await self._cargar_categorias_detalle_contrato(contrato_id)
        self.modal_detalle_abierto = True

    def cerrar_detalle(self):
        self.modal_detalle_abierto = False
        self.contrato_detalle = {}
        self.categorias_detalle_contrato = []

    def abrir_confirmar_cancelar(self):
        if not self.contrato_detalle:
            return rx.toast.error("No hay contrato seleccionado")
        self.modal_detalle_abierto = False
        self.mostrar_modal_confirmar_cancelar = True

    def cerrar_confirmar_cancelar(self):
        self.mostrar_modal_confirmar_cancelar = False

    async def abrir_edicion_contrato(self):
        if not self.es_admin_empresa:
            return rx.toast.error(
                "Solo admin_empresa puede editar contratos en el portal"
            )

        contrato = self.contrato_detalle
        if not contrato:
            return rx.toast.error("No hay contrato seleccionado")

        contrato_empresa_id = int(contrato.get("empresa_id") or 0)
        if not self.id_empresa_actual or contrato_empresa_id != int(
            self.id_empresa_actual
        ):
            return rx.toast.error("Solo puedes editar contratos de la empresa activa")

        contratos_state = await self.get_state(ContratosState)
        await contratos_state.cargar_empresas()
        await contratos_state.cargar_tipos_servicio()

        self.cerrar_detalle()
        return await contratos_state.abrir_modal_editar(contrato)

    def _asegurar_permiso_operar_contrato(self, contrato: dict):
        if not self.es_admin_empresa:
            raise BusinessRuleError(
                "Solo admin_empresa puede operar contratos en el portal"
            )
        if not contrato:
            raise BusinessRuleError("No hay contrato seleccionado")
        contrato_empresa_id = int(contrato.get("empresa_id") or 0)
        if not self.id_empresa_actual or contrato_empresa_id != int(
            self.id_empresa_actual
        ):
            raise BusinessRuleError(
                "Solo puedes operar contratos de la empresa activa"
            )

    async def activar_contrato(self):
        contrato = self.contrato_detalle
        try:
            self._asegurar_permiso_operar_contrato(contrato)
            self.saving_accion_contrato = True
            codigo = contrato.get("codigo", "")
            await contrato_service.activar(int(contrato["id"]))
            self.cerrar_detalle()
            await self._recargar_contratos_y_sidebar()
            return rx.toast.success(f"Contrato '{codigo}' activado exitosamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "activando contrato")
        finally:
            self.saving_accion_contrato = False

    async def suspender_contrato(self):
        contrato = self.contrato_detalle
        try:
            self._asegurar_permiso_operar_contrato(contrato)
            self.saving_accion_contrato = True
            codigo = contrato.get("codigo", "")
            await contrato_service.suspender(int(contrato["id"]))
            self.cerrar_detalle()
            await self._recargar_contratos_y_sidebar()
            return rx.toast.success(f"Contrato '{codigo}' suspendido exitosamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "suspendiendo contrato")
        finally:
            self.saving_accion_contrato = False

    async def reactivar_contrato(self):
        contrato = self.contrato_detalle
        try:
            self._asegurar_permiso_operar_contrato(contrato)
            self.saving_accion_contrato = True
            codigo = contrato.get("codigo", "")
            await contrato_service.reactivar(int(contrato["id"]))
            self.cerrar_detalle()
            await self._recargar_contratos_y_sidebar()
            return rx.toast.success(f"Contrato '{codigo}' reactivado exitosamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "reactivando contrato")
        finally:
            self.saving_accion_contrato = False

    async def cancelar_contrato(self):
        contrato = self.contrato_detalle
        try:
            self._asegurar_permiso_operar_contrato(contrato)
            self.saving_accion_contrato = True
            codigo = contrato.get("codigo", "")
            await contrato_service.cancelar(int(contrato["id"]))
            self.cerrar_confirmar_cancelar()
            self.contrato_detalle = {}
            await self._recargar_contratos_y_sidebar()
            return rx.toast.success(f"Contrato '{codigo}' cancelado exitosamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "cancelando contrato")
        finally:
            self.saving_accion_contrato = False

    async def liquidar_contrato(self):
        """Cierra definitivamente un contrato vencido (VENCIDO → LIQUIDADO)."""
        contrato = self.contrato_detalle
        try:
            self._asegurar_permiso_operar_contrato(contrato)
            self.saving_accion_contrato = True
            codigo = contrato.get("codigo", "")
            await contrato_service.liquidar(int(contrato["id"]))
            self.cerrar_detalle()
            await self._recargar_contratos_y_sidebar()
            return rx.toast.success(f"Contrato '{codigo}' liquidado")
        except Exception as e:
            return self.manejar_error_con_toast(e, "liquidando contrato")
        finally:
            self.saving_accion_contrato = False

    # -----------------------------
    # Extensión de contrato — wizard
    # -----------------------------
    @staticmethod
    def _fecha_inicio_sugerida_extension(contrato: dict) -> str:
        """Devuelve el día siguiente a la `fecha_fin` del padre (ISO YYYY-MM-DD)."""
        from datetime import datetime, timedelta

        raw = str(contrato.get("fecha_fin") or "").strip()
        if not raw:
            return ""
        candidato = raw[:10]
        try:
            fecha_fin = datetime.strptime(candidato, "%Y-%m-%d").date()
        except ValueError:
            return ""
        siguiente = fecha_fin + timedelta(days=1)
        return siguiente.isoformat()

    def _resetear_wizard_extension(self) -> None:
        self.wizard_paso_actual = 1
        self.contrato_a_extender = {}
        self.form_extension_fecha_inicio = ""
        self.form_extension_fecha_fin = ""
        self.error_form_extension_fecha_inicio = ""
        self.error_form_extension_fecha_fin = ""
        self.wizard_categorias = []
        self.wizard_error_categorias = ""
        self.wizard_empleados_padre = []
        self.wizard_empleado_ids_seleccionados = []
        self.wizard_error_empleados = ""

    async def abrir_modal_extension(self, contrato: dict):
        """Abre el wizard de extensión cargando las categorías del padre."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede extender contratos")
            return

        self._resetear_wizard_extension()
        self.contrato_a_extender = dict(contrato or {})
        self.form_extension_fecha_inicio = self._fecha_inicio_sugerida_extension(
            self.contrato_a_extender
        )
        self.modal_extension_abierto = True
        yield

        contrato_id = int(self.contrato_a_extender.get("id") or 0)
        if contrato_id <= 0:
            return

        try:
            categorias = await contrato_categoria_service.obtener_categorias_de_contrato(
                contrato_id
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudieron cargar categorías del padre %s: %s", contrato_id, exc)
            self.wizard_error_categorias = (
                "No se pudieron cargar las categorías del contrato padre. "
                "Puedes continuar y editarlas después en la tab Categorías."
            )
            yield
            return

        snapshot: list[dict] = []
        for cat in categorias:
            snapshot.append(
                {
                    "id": int(cat.id or 0),
                    "categoria_puesto_id": int(cat.categoria_puesto_id or 0),
                    "nombre": str(cat.nombre or "Sin nombre"),
                    "form_sueldo_base": self._decimal_a_texto(cat.sueldo_base),
                    "form_tipo_sueldo": str(
                        cat.tipo_sueldo.value if hasattr(cat.tipo_sueldo, "value") else cat.tipo_sueldo
                    ).upper() or "BRUTO",
                    "form_costo_contractual": self._decimal_a_texto(cat.costo_contractual),
                    "form_cantidad_minima": str(int(cat.cantidad_minima or 0)),
                    "form_cantidad_maxima": str(int(cat.cantidad_maxima or 0)),
                    "costo_unitario_original": str(cat.costo_unitario or ""),
                }
            )
        self.wizard_categorias = snapshot
        yield

        # Cargar empleados activos del padre para el paso 3.
        try:
            plazas_padre_resumen = await plaza_service.obtener_resumen_de_contrato(
                contrato_id
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "No se pudieron cargar empleados del contrato padre %s: %s",
                contrato_id,
                exc,
            )
            self.wizard_error_empleados = (
                "No se pudieron cargar los empleados actuales del contrato."
            )
            yield
            return

        empleados_snapshot: list[dict] = []
        for plaza in plazas_padre_resumen:
            if plaza.estatus != EstatusPlaza.OCUPADA or not plaza.empleado_id:
                continue
            empleado_id = int(plaza.empleado_id)
            empleados_snapshot.append(
                {
                    "empleado_id": empleado_id,
                    "nombre": str(plaza.empleado_nombre or "Sin nombre"),
                    "categoria_puesto_id": int(plaza.categoria_puesto_id or 0),
                    "categoria_nombre": str(plaza.categoria_nombre or "Sin categoría"),
                    "plaza_id": int(plaza.id or 0),
                    "plaza_numero": str(plaza.numero_plaza or ""),
                    "sede_nombre": str(plaza.sede_nombre or "Sin sede"),
                }
            )
        # Ordenar por categoría y nombre para facilitar revisión.
        empleados_snapshot.sort(
            key=lambda e: (e["categoria_nombre"].lower(), e["nombre"].lower())
        )
        self.wizard_empleados_padre = empleados_snapshot
        yield

    @staticmethod
    def _decimal_a_texto(valor) -> str:
        if valor is None:
            return ""
        try:
            return f"{Decimal(str(valor)):.2f}"
        except Exception:  # noqa: BLE001
            return ""

    def cerrar_modal_extension(self):
        self.modal_extension_abierto = False
        self._resetear_wizard_extension()

    def set_form_extension_fecha_inicio(self, value: str):
        self.form_extension_fecha_inicio = normalize_date_input(value)
        self.error_form_extension_fecha_inicio = ""

    def set_form_extension_fecha_fin(self, value: str):
        self.form_extension_fecha_fin = normalize_date_input(value)
        self.error_form_extension_fecha_fin = ""

    def _actualizar_categoria_wizard(self, index: int, campo: str, value: str) -> None:
        """Reasigna la lista completa para que Reflex detecte el cambio."""
        if not (0 <= index < len(self.wizard_categorias)):
            return
        lista = [dict(item) for item in self.wizard_categorias]
        lista[index] = {**lista[index], campo: str(value or "").strip()}
        self.wizard_categorias = lista
        self.wizard_error_categorias = ""

    def wizard_set_sueldo_base(self, index: int, value: str):
        self._actualizar_categoria_wizard(index, "form_sueldo_base", value)

    def wizard_set_tipo_sueldo(self, index: int, value: str):
        tipo = (str(value or "").upper() or "BRUTO")
        if tipo not in ("BRUTO", "NETO"):
            tipo = "BRUTO"
        self._actualizar_categoria_wizard(index, "form_tipo_sueldo", tipo)

    def wizard_set_costo_contractual(self, index: int, value: str):
        self._actualizar_categoria_wizard(index, "form_costo_contractual", value)

    def wizard_set_cantidad_minima(self, index: int, value: str):
        self._actualizar_categoria_wizard(
            index, "form_cantidad_minima", "".join(ch for ch in str(value or "") if ch.isdigit()) or "0",
        )

    def wizard_set_cantidad_maxima(self, index: int, value: str):
        self._actualizar_categoria_wizard(
            index, "form_cantidad_maxima", "".join(ch for ch in str(value or "") if ch.isdigit()) or "0",
        )

    # ---- Paso 3: selección de empleados ----
    def wizard_toggle_empleado(self, empleado_id: int):
        """Agrega o quita un empleado de la lista de seleccionados para migrar."""
        try:
            eid = int(empleado_id or 0)
        except (TypeError, ValueError):
            return
        if eid <= 0:
            return
        if eid in self.wizard_empleado_ids_seleccionados:
            self.wizard_empleado_ids_seleccionados = [
                x for x in self.wizard_empleado_ids_seleccionados if x != eid
            ]
        else:
            if not self._puede_agregar_empleado(eid):
                return rx.toast.error(
                    "No hay capacidad disponible en la categoría del empleado"
                )
            self.wizard_empleado_ids_seleccionados = [
                *self.wizard_empleado_ids_seleccionados,
                eid,
            ]
        self.wizard_error_empleados = ""

    def _puede_agregar_empleado(self, empleado_id: int) -> bool:
        """Verifica que marcar este empleado no exceda la capacidad de su categoría."""
        info = self._empleado_info(empleado_id)
        if info is None:
            return False
        cat_id = int(info.get("categoria_puesto_id") or 0)
        if cat_id <= 0:
            return True
        capacidad = self._capacidad_categoria(cat_id)
        seleccionados = self._seleccionados_en_categoria(cat_id)
        return seleccionados < capacidad

    def _empleado_info(self, empleado_id: int) -> dict | None:
        for item in self.wizard_empleados_padre:
            if int(item.get("empleado_id") or 0) == int(empleado_id):
                return item
        return None

    def _capacidad_categoria(self, categoria_puesto_id: int) -> int:
        """Capacidad máxima actual (según el paso 2) de una categoría.

        Las categorías del wizard se identifican por el id del
        ContratoCategoria del padre, no por categoria_puesto_id. Pero la
        relación 1:1 se mantiene porque `crear_extension` clona preservando
        `categoria_puesto_id`. Hacemos match por ese campo.
        """
        # Mapeo categoria_puesto_id → cantidad_maxima del wizard.
        # Como `wizard_categorias` no expone categoria_puesto_id (solo el id
        # del ContratoCategoria), necesitamos conservarlo desde la carga.
        # El snapshot lo incluye como campo "categoria_puesto_id" agregado
        # abajo.
        for item in self.wizard_categorias:
            if int(item.get("categoria_puesto_id") or 0) == int(categoria_puesto_id):
                try:
                    return int(item.get("form_cantidad_maxima") or "0")
                except ValueError:
                    return 0
        return 0

    def _seleccionados_en_categoria(self, categoria_puesto_id: int) -> int:
        """Cuántos empleados marcados tienen esta categoría."""
        return sum(
            1
            for eid in self.wizard_empleado_ids_seleccionados
            if (
                (info := self._empleado_info(eid)) is not None
                and int(info.get("categoria_puesto_id") or 0) == int(categoria_puesto_id)
            )
        )

    # ---- Navegación multi-paso ----
    _WIZARD_PASOS = (1, 2, 3, 4)

    def _validar_paso_1(self) -> bool:
        self.error_form_extension_fecha_inicio = ""
        self.error_form_extension_fecha_fin = ""
        if not self.form_extension_fecha_inicio.strip():
            self.error_form_extension_fecha_inicio = "Captura la fecha de inicio"
            return False
        if parse_date_input(self.form_extension_fecha_inicio) is None:
            self.error_form_extension_fecha_inicio = "Fecha inválida (DD/MM/AAAA)"
            return False
        if self.form_extension_fecha_fin.strip():
            if parse_date_input(self.form_extension_fecha_fin) is None:
                self.error_form_extension_fecha_fin = "Fecha inválida (DD/MM/AAAA)"
                return False
        return True

    def _validar_paso_2(self) -> bool:
        self.wizard_error_categorias = ""
        for item in self.wizard_categorias:
            try:
                sueldo = Decimal(str(item.get("form_sueldo_base") or "0"))
                if sueldo <= 0:
                    self.wizard_error_categorias = (
                        f"Captura un sueldo mayor a 0 para '{item.get('nombre', '')}'"
                    )
                    return False
            except Exception:  # noqa: BLE001
                self.wizard_error_categorias = (
                    f"Sueldo inválido para '{item.get('nombre', '')}'"
                )
                return False
            if item.get("form_costo_contractual", "").strip():
                try:
                    contractual = Decimal(str(item["form_costo_contractual"]))
                    if contractual < 0:
                        self.wizard_error_categorias = (
                            f"Costo contractual no puede ser negativo en '{item.get('nombre', '')}'"
                        )
                        return False
                except Exception:  # noqa: BLE001
                    self.wizard_error_categorias = (
                        f"Costo contractual inválido en '{item.get('nombre', '')}'"
                    )
                    return False
            try:
                min_p = int(item.get("form_cantidad_minima") or "0")
                max_p = int(item.get("form_cantidad_maxima") or "0")
            except ValueError:
                self.wizard_error_categorias = (
                    f"Plazas inválidas en '{item.get('nombre', '')}'"
                )
                return False
            if max_p > 0 and max_p < min_p:
                self.wizard_error_categorias = (
                    f"En '{item.get('nombre', '')}': plazas máximas deben ser ≥ mínimas"
                )
                return False
        return True

    def _validar_paso_3(self) -> bool:
        """Valida capacidad por categoría: seleccionados ≤ cantidad_maxima."""
        self.wizard_error_empleados = ""
        if not self.wizard_empleado_ids_seleccionados:
            return True  # migrar 0 empleados es válido
        # Agrupar seleccionados por categoría
        por_categoria: dict[int, int] = {}
        nombre_por_cat: dict[int, str] = {}
        for eid in self.wizard_empleado_ids_seleccionados:
            info = self._empleado_info(int(eid))
            if info is None:
                continue
            cat_id = int(info.get("categoria_puesto_id") or 0)
            por_categoria[cat_id] = por_categoria.get(cat_id, 0) + 1
            nombre_por_cat[cat_id] = str(info.get("categoria_nombre", ""))
        # Comparar contra capacidad del paso 2
        for cat_id, seleccionados in por_categoria.items():
            capacidad = self._capacidad_categoria(cat_id)
            if seleccionados > capacidad:
                self.wizard_error_empleados = (
                    f"En '{nombre_por_cat.get(cat_id, 'categoría')}' seleccionaste "
                    f"{seleccionados} empleados pero solo hay {capacidad} plazas."
                )
                return False
        return True

    def wizard_siguiente_paso(self):
        if self.wizard_paso_actual == 1 and not self._validar_paso_1():
            return rx.toast.error("Revisa los datos del paso 1")
        if self.wizard_paso_actual == 2 and not self._validar_paso_2():
            return rx.toast.error(self.wizard_error_categorias or "Revisa las categorías")
        if self.wizard_paso_actual == 3 and not self._validar_paso_3():
            return rx.toast.error(
                self.wizard_error_empleados or "Revisa la selección de empleados"
            )
        try:
            idx = self._WIZARD_PASOS.index(self.wizard_paso_actual)
        except ValueError:
            idx = 0
        if idx < len(self._WIZARD_PASOS) - 1:
            self.wizard_paso_actual = self._WIZARD_PASOS[idx + 1]

    def wizard_paso_anterior(self):
        try:
            idx = self._WIZARD_PASOS.index(self.wizard_paso_actual)
        except ValueError:
            idx = 0
        if idx > 0:
            self.wizard_paso_actual = self._WIZARD_PASOS[idx - 1]

    def wizard_ir_paso(self, paso: int):
        """Navegación directa desde el stepper. Valida los pasos previos."""
        destino = int(paso or 0)
        if destino not in self._WIZARD_PASOS:
            return
        if destino == self.wizard_paso_actual:
            return
        # Si vamos hacia adelante, validar pasos intermedios.
        if destino > self.wizard_paso_actual:
            if self.wizard_paso_actual <= 1 and not self._validar_paso_1():
                return rx.toast.error("Completa el paso 1 antes de avanzar")
            if self.wizard_paso_actual <= 2 and destino > 2 and not self._validar_paso_2():
                return rx.toast.error(
                    self.wizard_error_categorias or "Completa el paso 2 antes de avanzar"
                )
            if self.wizard_paso_actual <= 3 and destino > 3 and not self._validar_paso_3():
                return rx.toast.error(
                    self.wizard_error_empleados or "Completa el paso 3 antes de avanzar"
                )
        self.wizard_paso_actual = destino

    @rx.var
    def wizard_es_paso_vigencia(self) -> bool:
        return self.wizard_paso_actual == 1

    @rx.var
    def wizard_es_paso_categorias(self) -> bool:
        return self.wizard_paso_actual == 2

    @rx.var
    def wizard_es_paso_empleados(self) -> bool:
        return self.wizard_paso_actual == 3

    @rx.var
    def wizard_es_paso_confirmacion(self) -> bool:
        return self.wizard_paso_actual == 4

    @rx.var
    def wizard_puede_ir_atras(self) -> bool:
        return self.wizard_paso_actual > 1

    @rx.var
    def wizard_empleados_padre_enriquecidos(self) -> list[dict]:
        """Enriquecer cada empleado con flag `seleccionado` para la UI."""
        seleccionados = set(self.wizard_empleado_ids_seleccionados)
        resultado: list[dict] = []
        for item in self.wizard_empleados_padre:
            empleado_id = int(item.get("empleado_id") or 0)
            resultado.append(
                {
                    **item,
                    "seleccionado": empleado_id in seleccionados,
                }
            )
        return resultado

    @rx.var
    def wizard_total_empleados_seleccionados(self) -> int:
        return len(self.wizard_empleado_ids_seleccionados)

    @rx.var
    def wizard_total_empleados_padre(self) -> int:
        return len(self.wizard_empleados_padre)

    @rx.var
    def wizard_resumen_seleccion_empleados(self) -> str:
        total = len(self.wizard_empleados_padre)
        sel = len(self.wizard_empleado_ids_seleccionados)
        if total == 0:
            return "El contrato padre no tiene empleados activos"
        return f"{sel} de {total} seleccionados para migrar"

    @rx.var
    def puede_crear_extension(self) -> bool:
        return bool(
            self.wizard_paso_actual == 4
            and self.form_extension_fecha_inicio.strip()
            and not self.saving_extension
        )

    @rx.var
    def titulo_modal_extension(self) -> str:
        codigo = str(self.contrato_a_extender.get("codigo") or "")
        return f"Extender contrato {codigo}" if codigo else "Extender contrato"

    @rx.var
    def resumen_vigencia_extension(self) -> str:
        inicio = self.form_extension_fecha_inicio or "Sin fecha"
        fin = self.form_extension_fecha_fin or "Indefinida"
        return f"{inicio} → {fin}"

    @rx.var
    def resumen_total_categorias(self) -> int:
        return len(self.wizard_categorias)

    # ---- Submit final ----
    async def guardar_extension(self):
        """Crea la extensión aplicando los overrides capturados en el wizard."""
        contrato = self.contrato_a_extender
        if not contrato or not contrato.get("id"):
            yield rx.toast.error("No se pudo identificar el contrato padre")
            return

        if not self._validar_paso_1():
            self.wizard_paso_actual = 1
            yield rx.toast.error("Revisa los datos del paso 1")
            return

        if not self._validar_paso_2():
            self.wizard_paso_actual = 2
            yield rx.toast.error(self.wizard_error_categorias or "Revisa las categorías")
            return

        if not self._validar_paso_3():
            self.wizard_paso_actual = 3
            yield rx.toast.error(
                self.wizard_error_empleados or "Revisa la selección de empleados"
            )
            return

        fecha_inicio = parse_date_input(self.form_extension_fecha_inicio)
        fecha_fin = (
            parse_date_input(self.form_extension_fecha_fin)
            if self.form_extension_fecha_fin.strip()
            else None
        )

        overrides: dict[int, dict] = {}
        for item in self.wizard_categorias:
            cid = int(item.get("id") or 0)
            if cid <= 0:
                continue
            try:
                sueldo_base = Decimal(str(item.get("form_sueldo_base") or "0"))
            except Exception:  # noqa: BLE001
                sueldo_base = None
            costo_contractual_raw = item.get("form_costo_contractual", "").strip()
            costo_contractual = None
            if costo_contractual_raw:
                try:
                    costo_contractual = Decimal(costo_contractual_raw)
                except Exception:  # noqa: BLE001
                    costo_contractual = None
            try:
                cmin = int(item.get("form_cantidad_minima") or "0")
                cmax = int(item.get("form_cantidad_maxima") or "0")
            except ValueError:
                cmin, cmax = 0, 0
            tipo_sueldo = str(item.get("form_tipo_sueldo", "BRUTO") or "BRUTO").upper()
            override: dict = {
                "sueldo_base": sueldo_base,
                "tipo_sueldo": tipo_sueldo,
                "cantidad_minima": cmin,
                "cantidad_maxima": cmax,
            }
            if costo_contractual is not None:
                override["costo_contractual"] = costo_contractual
            # costo_unitario se recalcula desde sueldo_base BRUTO (aproximación).
            # Para mantener consistencia con el flujo del portal que captura
            # `costo_unitario = sueldo_bruto`, si tipo == BRUTO usamos el mismo
            # valor; si tipo == NETO dejamos que el servicio conserve el del padre.
            if sueldo_base is not None and tipo_sueldo == "BRUTO":
                override["costo_unitario"] = sueldo_base
            overrides[cid] = override

        empleado_ids_a_migrar = [
            int(eid) for eid in self.wizard_empleado_ids_seleccionados
        ]

        self.saving_extension = True
        yield
        try:
            extension = await contrato_service.crear_extension(
                int(contrato["id"]),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                overrides_categorias=overrides,
            )

            mensaje = f"Extensión {getattr(extension, 'codigo', '')} creada"
            if empleado_ids_a_migrar:
                resultado = await contrato_service.migrar_empleados_a_extension(
                    padre_id=int(contrato["id"]),
                    extension_id=int(extension.id),
                    empleado_ids=empleado_ids_a_migrar,
                )
                migrados = len(resultado.get("migrados", []))
                fallidos = resultado.get("fallidos", [])
                if fallidos:
                    mensaje += (
                        f" · {migrados} empleado(s) migrados, "
                        f"{len(fallidos)} con problemas (revisa la extensión)"
                    )
                else:
                    mensaje += f" con {migrados} empleado(s) migrados"

            self.cerrar_modal_extension()
            self.cerrar_detalle()
            await self._recargar_contratos_y_sidebar()
            yield rx.toast.success(mensaje)
        except Exception as e:
            yield self.manejar_error_con_toast(e, "creando extensión")
        finally:
            self.saving_extension = False

    @staticmethod
    def _calcular_pct_cobertura(ocupadas: int, total: int) -> int:
        if total <= 0:
            return 0
        return int(round((ocupadas / total) * 100))

    async def _cargar_categorias_detalle_contrato(self, contrato_id: int):
        """Carga el desglose de categorías del contrato para el modal resumen."""
        try:
            resumen = await contrato_categoria_service.obtener_resumen_de_contrato(
                contrato_id
            )
            self.categorias_detalle_contrato = [
                serializar_categoria_contrato_detalle(item) for item in resumen
            ]
        except Exception:
            self.categorias_detalle_contrato = []

    def _enriquecer_contrato(self, contrato: dict) -> dict:
        """Agrega campos derivados para la UI del portal."""
        data = enriquecer_contrato_presentacion(contrato)
        data.setdefault("total_plazas", 0)
        data.setdefault("plazas_ocupadas", 0)
        data.setdefault("tipo_servicio_nombre", "")
        data["pct_cobertura"] = self._calcular_pct_cobertura(
            int(data.get("plazas_ocupadas") or 0),
            int(data.get("total_plazas") or 0),
        )

        # Año de inicio para agrupar.
        fecha_inicio = str(data.get("fecha_inicio") or "")
        anio = 0
        if len(fecha_inicio) >= 4:
            try:
                anio = int(fecha_inicio[:4])
            except ValueError:
                anio = 0
        data["anio_inicio"] = anio

        data["vigencia_fmt"] = formatear_vigencia_meses(
            data.get("fecha_inicio"),
            data.get("fecha_fin"),
            valor_vacio="Sin vigencia",
        )

        # Texto de descripción seguro para UI.
        descripcion = str(data.get("descripcion_objeto") or "").strip()
        data["descripcion_objeto_display_cap"] = (
            capitalizar_con_preposiciones(descripcion)
            if descripcion
            else "Sin objeto capturado"
        )

        # Normaliza flags usados en CTAs contextuales.
        data["tiene_personal"] = bool(data.get("tiene_personal"))
        data["estatus"] = str(data.get("estatus") or "").upper()
        data["codigo"] = str(data.get("codigo") or "")
        data["numero_folio_buap_txt"] = str(data.get("numero_folio_buap") or "")

        return data


# =============================================================================
# COMPONENTES DE LA TABLA
# =============================================================================


def _celda_contrato(item: rx.Var) -> rx.Component:
    return rx.table.cell(
        rx.box(
            rx.flex(
                rx.text(
                    item["codigo"],
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.PORTAL_PRIMARY_TEXT,
                    font_size=Typography.SIZE_SM,
                ),
                rx.cond(
                    item["es_extension"],
                    rx.badge(
                        "Extensión",
                        color_scheme="blue",
                        size="1",
                        variant="soft",
                    ),
                    rx.fragment(),
                ),
                align="center",
                gap=Spacing.SM,
                wrap="wrap",
            ),
            rx.text(
                item["descripcion_objeto_display_cap"],
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            rx.cond(
                item["numero_folio_buap_txt"] != "",
                rx.text(
                    "Folio: ",
                    item["numero_folio_buap_txt"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                rx.fragment(),
            ),
            min_width="0",
        ),
    )


def _celda_tipo(item: rx.Var) -> rx.Component:
    return rx.table.cell(
        rx.flex(
            rx.badge(
                rx.cond(
                    item["tipo_servicio_nombre"] != "",
                    item["tipo_servicio_nombre"],
                    item["tipo_contrato_fmt"],
                ),
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                variant="soft",
                size="1",
            ),
            rx.cond(
                item["tiene_personal"],
                rx.flex(
                    rx.icon("users", size=11, color=Colors.TEXT_MUTED),
                    rx.text(
                        "Personal",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                    align="center",
                    gap=Spacing.XS,
                ),
                rx.fragment(),
            ),
            align="center",
            justify="center",
            gap=Spacing.SM,
            wrap="wrap",
        ),
        text_align="center",
    )


def _celda_vigencia(item: rx.Var) -> rx.Component:
    return rx.table.cell(
        rx.text(
            item["vigencia_fmt"],
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        text_align="center",
    )


def _celda_plazas(item: rx.Var) -> rx.Component:
    pct = item["pct_cobertura"].to(int)
    color_cobertura = rx.cond(
        pct >= 80,
        Colors.SUCCESS,
        rx.cond(
            pct >= 40,
            Colors.WARNING,
            Colors.ERROR,
        ),
    )
    return rx.table.cell(
        rx.cond(
            item["tiene_personal"] & (item["total_plazas"].to(int) > 0),
            rx.box(
                rx.text(
                    item["plazas_ocupadas"].to(str) + "/" + item["total_plazas"].to(str),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    font_variant_numeric="tabular-nums",
                    color=color_cobertura,
                ),
                rx.box(
                    rx.box(
                        width=pct.to(str) + "%",
                        height="100%",
                        border_radius="2px",
                        background=color_cobertura,
                    ),
                    width="50px",
                    height="4px",
                    border_radius="2px",
                    background=Colors.BORDER,
                    overflow="hidden",
                    margin_x="auto",
                    margin_top=Spacing.XS,
                ),
            ),
            rx.text("—", color=Colors.TEXT_MUTED, font_size=Typography.SIZE_SM),
        ),
        text_align="center",
    )


def _celda_estatus(item: rx.Var) -> rx.Component:
    return rx.table.cell(estatus_badge(item["estatus"]), text_align="center")


def _celda_cta(item: rx.Var) -> rx.Component:
    cta_text = rx.match(
        item["estatus"],
        ("BORRADOR", "Configurar"),
        (
            "ACTIVO",
            rx.cond(item["tiene_personal"], "Ver plazas", "Entregables"),
        ),
        ("SUSPENDIDO", "Ver detalle"),
        ("VENCIDO", "Consultar"),
        ("LIQUIDADO", "Consultar"),
        "Ver",
    )
    cta_color = rx.match(
        item["estatus"],
        ("BORRADOR", "amber"),
        (
            "ACTIVO",
            rx.cond(
                item["tiene_personal"],
                Colors.PORTAL_ACCENT_SCHEME,
                Colors.NEUTRAL_SCHEME,
            ),
        ),
        Colors.NEUTRAL_SCHEME,
    )
    puede_extender = item["estatus"] == "VENCIDO"
    return rx.table.cell(
        rx.flex(
            rx.cond(
                puede_extender,
                tabla_cta_button(
                    text="Extender",
                    on_click=MisContratosState.abrir_modal_extension(item).stop_propagation,
                    color_scheme=Colors.NEUTRAL_SCHEME,
                    size="1",
                    variant="ghost",
                ),
                rx.fragment(),
            ),
            tabla_cta_button(
                text=cta_text,
                on_click=MisContratosState.navegar_contrato(item).stop_propagation,
                color_scheme=cta_color,
                size="1",
                variant="outline",
            ),
            align="center",
            justify="end",
            gap=Spacing.XS,
            wrap="wrap",
        ),
        text_align="right",
    )


def _fila_contrato(item: rx.Var) -> rx.Component:
    return rx.table.row(
        _celda_contrato(item),
        _celda_tipo(item),
        _celda_vigencia(item),
        _celda_plazas(item),
        _celda_estatus(item),
        _celda_cta(item),
        _hover={"background": Colors.SURFACE_HOVER, "cursor": "pointer"},
        on_click=MisContratosState.abrir_detalle(item),
    )


def _empty_state_tabla() -> rx.Component:
    return rx.cond(
        MisContratosState.hay_filtros_activos,
        empty_state_card(
            title="No se encontraron contratos",
            description="Ajusta la búsqueda o los filtros para volver a ver contratos.",
            icon="search-x",
            action_button=rx.button(
                rx.icon("rotate-ccw", size=16),
                "Limpiar filtros",
                on_click=MisContratosState.limpiar_filtros_contratos,
                color_scheme=Colors.NEUTRAL_SCHEME,
                variant="outline",
                size="2",
            ),
        ),
        empty_state_card(
            title="No hay contratos creados",
            description="Crea el primer contrato para comenzar a gestionar plazas y entregables.",
            icon="file-text",
            action_button=rx.cond(
                AuthState.es_admin_empresa,
                rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo contrato",
                    on_click=ContratosState.abrir_modal_crear_portal,
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    size="2",
                ),
                rx.fragment(),
            ),
        ),
    )


def _label_anio(grupo: rx.Var) -> rx.Component:
    return rx.flex(
        rx.text(
            grupo.anio,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.text(
            grupo.count.to(str) + " contratos",
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
        ),
        rx.box(flex="1", height="1px", background=Colors.BORDER),
        align="center",
        gap=Spacing.SM,
        width="100%",
        padding_y=Spacing.SM,
    )


def _tabla_grupo(grupo: rx.Var) -> rx.Component:
    return rx.box(
        _label_anio(grupo),
        rx.box(
            table_shell(
                loading=False,
                headers=CONTRATOS_HEADERS,
                rows=grupo.contratos,
                row_renderer=_fila_contrato,
                has_rows=grupo.count.to(int) > 0,
                empty_component=rx.fragment(),
                table_size="1",
            ),
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
            overflow="hidden",
            width="100%",
        ),
        width="100%",
    )


def _tipo_select_option(opcion: rx.Var) -> rx.Component:
    return rx.select.item(opcion["nombre"], value=opcion["id"])


def _label_select(label: str, value_cond) -> rx.Component:
    """Etiqueta inline al estilo `Estatus: Todos` dentro del trigger."""
    return rx.flex(
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
            weight="medium",
        ),
        rx.text(
            value_cond,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_PRIMARY,
            weight="medium",
        ),
        align="center",
        gap=Spacing.XS,
    )


def _toolbar() -> rx.Component:
    estatus_label = rx.match(
        MisContratosState.filtro_estatus_cto,
        ("BORRADOR", "Borrador"),
        ("ACTIVO", "Activo"),
        ("SUSPENDIDO", "Suspendido"),
        ("VENCIDO", "Vencido"),
        ("LIQUIDADO", "Liquidado"),
        ("CANCELADO", "Cancelado"),
        "Todos",
    )
    tipo_label = rx.cond(
        MisContratosState.filtro_tipo_cto == FILTRO_TODOS,
        "Todos",
        "Filtrado",
    )
    return rx.flex(
        rx.box(
            input_busqueda(
                value=MisContratosState.filtro_busqueda_cto,
                on_change=MisContratosState.set_filtro_busqueda_cto,
                on_clear=MisContratosState.limpiar_busqueda_contratos,
                placeholder="Buscar por código, folio u objeto...",
                toolbar_style=True,
                width="100%",
            ),
            flex="1 1 0px",
            min_width="200px",
        ),
        rx.select.root(
            rx.select.trigger(
                _label_select("Estatus:", estatus_label),
                width="190px",
            ),
            rx.select.content(
                rx.select.item("Todos", value=FILTRO_TODOS),
                rx.select.item("Borrador", value="BORRADOR"),
                rx.select.item("Activo", value="ACTIVO"),
                rx.select.item("Suspendido", value="SUSPENDIDO"),
                rx.select.item("Vencido", value="VENCIDO"),
                rx.select.item("Liquidado", value="LIQUIDADO"),
                rx.select.item("Cancelado", value="CANCELADO"),
            ),
            value=MisContratosState.filtro_estatus_cto,
            on_change=MisContratosState.set_filtro_estatus_cto,
            size="2",
        ),
        rx.select.root(
            rx.select.trigger(
                _label_select("Tipo:", tipo_label),
                width="190px",
            ),
            rx.select.content(
                rx.select.item("Todos", value=FILTRO_TODOS),
                rx.foreach(
                    MisContratosState.tipos_servicio_opciones,
                    _tipo_select_option,
                ),
            ),
            value=MisContratosState.filtro_tipo_cto,
            on_change=MisContratosState.set_filtro_tipo_cto,
            size="2",
        ),
        width="100%",
        align="center",
        wrap="wrap",
        gap=Spacing.SM,
    )


def _metricas_contratos() -> rx.Component:
    return metric_card_grid(
        metric_card(
            titulo="Por configurar",
            valor=MisContratosState.total_borradores,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            value_color=MisContratosState.color_metrica_borradores,
            descripcion="Borradores pendientes",
        ),
        metric_card(
            titulo="Activos",
            valor=MisContratosState.total_activos,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            value_color=Colors.SUCCESS,
            descripcion="En operación",
        ),
        metric_card(
            titulo="Cobertura global",
            valor=MisContratosState.cobertura_global_texto,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            value_color=MisContratosState.cobertura_global_color,
            descripcion=MisContratosState.cobertura_global_descripcion,
        ),
        metric_card(
            titulo="Historial",
            valor=MisContratosState.total_historial,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            value_color=Colors.TEXT_PRIMARY,
            descripcion="Vencidos y liquidados",
        ),
    )


def _contratos_skeleton() -> rx.Component:
    """Skeleton del listado: imita un grupo con encabezado de año y tabla."""
    return rx.vstack(
        rx.flex(
            rx.skeleton(
                rx.text("2026", color="transparent"),
                loading=True,
                width="60px",
                height="16px",
            ),
            rx.skeleton(
                rx.text("0 contratos", color="transparent"),
                loading=True,
                width="90px",
                height="14px",
            ),
            rx.box(flex="1", height="1px", background=Colors.BORDER),
            align="center",
            gap=Spacing.SM,
            width="100%",
            padding_y=Spacing.SM,
        ),
        rx.box(
            skeleton_tabla(CONTRATOS_HEADERS, filas=5),
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
            overflow="hidden",
            width="100%",
        ),
        width="100%",
        spacing="2",
    )


def _seccion_titulo(texto: str, contador) -> rx.Component:
    return rx.flex(
        rx.text(
            texto,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_PRIMARY,
            text_transform="uppercase",
            letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
        ),
        rx.text(
            contador,
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
        ),
        rx.box(flex="1", height="1px", background=Colors.BORDER),
        align="center",
        gap=Spacing.SM,
        width="100%",
        padding_y=Spacing.SM,
    )


def _tabla_plana(rows, has_rows) -> rx.Component:
    return rx.box(
        table_shell(
            loading=False,
            headers=CONTRATOS_HEADERS,
            rows=rows,
            row_renderer=_fila_contrato,
            has_rows=has_rows,
            empty_component=rx.fragment(),
            table_size="1",
        ),
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        background=Colors.SURFACE,
        overflow="hidden",
        width="100%",
    )


def _seccion_borradores() -> rx.Component:
    return rx.cond(
        MisContratosState.tiene_borradores_listado,
        rx.vstack(
            _seccion_titulo(
                "Por configurar",
                MisContratosState.contratos_borradores.length().to(str)
                + " borrador(es)",
            ),
            feedback_callout(
                content=rx.text(
                    MisContratosState.mensaje_callout_borradores,
                    font_size=Typography.SIZE_SM,
                ),
                kind="warning",
            ),
            _tabla_plana(
                MisContratosState.contratos_borradores,
                MisContratosState.tiene_borradores_listado,
            ),
            width="100%",
            spacing="2",
        ),
        rx.fragment(),
    )


def _seccion_activos() -> rx.Component:
    return rx.vstack(
        _seccion_titulo(
            "Activos",
            MisContratosState.total_activos.to(str) + " contrato(s)",
        ),
        rx.cond(
            MisContratosState.tiene_activos_listado,
            rx.vstack(
                rx.foreach(MisContratosState.contratos_activos_grupos, _tabla_grupo),
                width="100%",
                spacing="3",
            ),
            _empty_state_tabla(),
        ),
        width="100%",
        spacing="2",
    )


def _grupo_historial(grupo: rx.Var) -> rx.Component:
    colapsado = MisContratosState.anios_historial_colapsados.contains(grupo.anio)
    icono = rx.cond(colapsado, "chevron-right", "chevron-down")
    return rx.box(
        rx.flex(
            rx.icon(icono, size=16, color=Colors.TEXT_MUTED),
            rx.text(
                grupo.anio,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.text(
                grupo.count.to(str) + " contrato(s)",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            rx.box(flex="1", height="1px", background=Colors.BORDER),
            align="center",
            gap=Spacing.SM,
            width="100%",
            padding_y=Spacing.SM,
            cursor="pointer",
            on_click=MisContratosState.toggle_historial_anio(grupo.anio),
            _hover={"opacity": "0.8"},
        ),
        rx.cond(
            ~colapsado,
            rx.box(
                _tabla_plana(grupo.contratos, grupo.count.to(int) > 0),
                opacity="0.85",
            ),
            rx.fragment(),
        ),
        width="100%",
    )


def _seccion_historial() -> rx.Component:
    return rx.cond(
        MisContratosState.tiene_historial_listado,
        rx.vstack(
            _seccion_titulo(
                "Historial",
                MisContratosState.total_historial.to(str) + " contrato(s)",
            ),
            rx.foreach(
                MisContratosState.contratos_historial_grupos,
                _grupo_historial,
            ),
            width="100%",
            spacing="2",
        ),
        rx.fragment(),
    )


def _contratos_contenido() -> rx.Component:
    return rx.cond(
        MisContratosState.loading,
        _contratos_skeleton(),
        rx.cond(
            MisContratosState.tiene_grupos_visibles,
            rx.vstack(
                _seccion_borradores(),
                _seccion_activos(),
                _seccion_historial(),
                rx.text(
                    "Mostrando ",
                    MisContratosState.total_contratos_visibles,
                    " contrato(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                width="100%",
                spacing="5",
            ),
            _empty_state_tabla(),
        ),
    )


# =============================================================================
# MODALES EXISTENTES
# =============================================================================


def _modal_detalle_contrato() -> rx.Component:
    """Modal con detalle del contrato seleccionado."""
    datos = MisContratosState.contrato_detalle

    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                datos,
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.dialog.title(
                                rx.hstack(
                                    rx.icon(
                                        "file-text",
                                        size=20,
                                        color=Colors.PORTAL_PRIMARY,
                                    ),
                                    rx.text("Resumen del Contrato"),
                                    spacing="2",
                                    align="center",
                                ),
                            ),
                            rx.hstack(
                                rx.badge(
                                    datos["tipo_contrato_fmt"],
                                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                                    variant="soft",
                                    size="1",
                                ),
                                contrato_detail_text(
                                    datos["codigo"],
                                    fallback="Sin código",
                                    color=Colors.TEXT_SECONDARY,
                                ),
                                spacing="2",
                                wrap="wrap",
                                width="100%",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.spacer(),
                        status_badge_reactive(
                            datos["estatus"],
                            show_icon=True,
                        ),
                        rx.icon_button(
                            rx.icon("x", size=18),
                            variant="ghost",
                            color_scheme=Colors.NEUTRAL_SCHEME,
                            size="2",
                            on_click=MisContratosState.cerrar_detalle,
                            cursor="pointer",
                        ),
                        width="100%",
                        align="start",
                    ),
                    contrato_detail_info_sections(
                        datos,
                        MisContratosState.categorias_detalle_contrato,
                        total_categorias=MisContratosState.total_categorias_detalle_contrato,
                        tiene_categorias=MisContratosState.tiene_categorias_detalle_contrato,
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.cond(
                                MisContratosState.contrato_detalle_tiene_plazas,
                                rx.button(
                                    rx.icon("briefcase", size=16),
                                    "Plazas",
                                    on_click=MisContratosState.ir_a_plazas_contrato_detalle,
                                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                                    variant="soft",
                                    disabled=MisContratosState.saving_accion_contrato,
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                MisContratosState.puede_editar_detalle,
                                rx.button(
                                    rx.icon("pencil", size=16),
                                    "Editar contrato",
                                    on_click=MisContratosState.abrir_edicion_contrato,
                                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                                    variant="soft",
                                    disabled=MisContratosState.saving_accion_contrato,
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                MisContratosState.puede_activar_detalle,
                                rx.button(
                                    rx.icon("check", size=16),
                                    "Activar",
                                    on_click=MisContratosState.activar_contrato,
                                    color_scheme="green",
                                    variant="soft",
                                    disabled=MisContratosState.saving_accion_contrato,
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                MisContratosState.puede_suspender_detalle,
                                rx.button(
                                    rx.icon("pause", size=16),
                                    "Suspender",
                                    on_click=MisContratosState.suspender_contrato,
                                    color_scheme="amber",
                                    variant="outline",
                                    disabled=MisContratosState.saving_accion_contrato,
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                MisContratosState.puede_reactivar_detalle,
                                rx.button(
                                    rx.icon("play", size=16),
                                    "Reactivar",
                                    on_click=MisContratosState.reactivar_contrato,
                                    color_scheme="green",
                                    variant="soft",
                                    disabled=MisContratosState.saving_accion_contrato,
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                MisContratosState.puede_liquidar_detalle,
                                rx.button(
                                    rx.icon("lock", size=16),
                                    "Liquidar contrato",
                                    on_click=MisContratosState.liquidar_contrato,
                                    color_scheme=Colors.NEUTRAL_SCHEME,
                                    variant="soft",
                                    disabled=MisContratosState.saving_accion_contrato,
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                MisContratosState.puede_cancelar_detalle,
                                rx.button(
                                    rx.icon("x", size=16),
                                    "Cancelar contrato",
                                    on_click=MisContratosState.abrir_confirmar_cancelar,
                                    color_scheme="red",
                                    variant="outline",
                                    disabled=MisContratosState.saving_accion_contrato,
                                ),
                                rx.fragment(),
                            ),
                            spacing="2",
                            wrap="wrap",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.spacer(),
                            boton_cancelar(
                                texto="Cerrar",
                                on_click=MisContratosState.cerrar_detalle,
                            ),
                            width="100%",
                            align="center",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.fragment(),
            ),
            max_width="960px",
        ),
        open=MisContratosState.modal_detalle_abierto,
        on_open_change=rx.noop,
    )


def _modal_confirmar_cancelar() -> rx.Component:
    """Modal de confirmación para cancelar el contrato desde el portal."""
    datos = MisContratosState.contrato_detalle
    return modal_confirmar_accion(
        open=MisContratosState.mostrar_modal_confirmar_cancelar,
        titulo="Cancelar contrato",
        mensaje=rx.cond(
            datos,
            rx.text(
                "¿Está seguro que desea cancelar el contrato ",
                rx.text(datos["codigo"], weight="bold", as_="span"),
                "? Esta acción no se puede deshacer.",
            ),
            rx.text("¿Está seguro que desea cancelar este contrato?"),
        ),
        on_confirmar=MisContratosState.cancelar_contrato,
        on_cancelar=MisContratosState.cerrar_confirmar_cancelar,
        loading=MisContratosState.saving_accion_contrato,
        texto_confirmar="Sí, cancelar",
        texto_confirmando="Cancelando...",
        texto_cancelar="No, conservar",
        color_confirmar="red",
    )


# =============================================================================
# PAGINA
# =============================================================================


_WIZARD_STEPS_META = (
    (1, "Vigencia"),
    (2, "Categorías"),
    (3, "Empleados"),
    (4, "Confirmar"),
)


def _wizard_stepper_extension() -> rx.Component:
    """Stepper del wizard de extensión, delega al componente shared."""
    return wizard_stepper(
        steps=_WIZARD_STEPS_META,
        current_step=MisContratosState.wizard_paso_actual,
        on_step_click=MisContratosState.wizard_ir_paso,
    )


def _wizard_paso_vigencia() -> rx.Component:
    return rx.vstack(
        rx.text(
            "Define la vigencia de la nueva extensión",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.flex(
            rx.box(
                form_date(
                    label="Fecha de inicio",
                    required=True,
                    value=MisContratosState.form_extension_fecha_inicio,
                    on_change=MisContratosState.set_form_extension_fecha_inicio,
                    error=MisContratosState.error_form_extension_fecha_inicio,
                    label_variant="portal",
                ),
                width="200px",
            ),
            rx.box(
                form_date(
                    label="Fecha de fin",
                    value=MisContratosState.form_extension_fecha_fin,
                    on_change=MisContratosState.set_form_extension_fecha_fin,
                    error=MisContratosState.error_form_extension_fecha_fin,
                    hint="Vacío = indefinida",
                    label_variant="portal",
                ),
                width="200px",
            ),
            gap=Spacing.MD,
            align="start",
            wrap="wrap",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def _wizard_categoria_row(item: rx.Var, index: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                item["nombre"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
            width="180px",
        ),
        rx.table.cell(
            rx.input(
                value=item["form_sueldo_base"],
                on_change=lambda v: MisContratosState.wizard_set_sueldo_base(index, v),
                type="number",
                step="0.01",
                min="0",
                size="1",
                width="110px",
            ),
            width="120px",
        ),
        rx.table.cell(
            rx.select.root(
                rx.select.trigger(width="90px"),
                rx.select.content(
                    rx.select.item("Bruto", value="BRUTO"),
                    rx.select.item("Neto", value="NETO"),
                ),
                value=item["form_tipo_sueldo"],
                on_change=lambda v: MisContratosState.wizard_set_tipo_sueldo(index, v),
                size="1",
            ),
            width="100px",
        ),
        rx.table.cell(
            rx.input(
                value=item["form_costo_contractual"],
                on_change=lambda v: MisContratosState.wizard_set_costo_contractual(index, v),
                type="number",
                step="0.01",
                min="0",
                placeholder="—",
                size="1",
                width="120px",
            ),
            width="130px",
        ),
        rx.table.cell(
            rx.input(
                value=item["form_cantidad_minima"],
                on_change=lambda v: MisContratosState.wizard_set_cantidad_minima(index, v),
                type="number",
                min="0",
                size="1",
                width="70px",
            ),
            width="80px",
        ),
        rx.table.cell(
            rx.input(
                value=item["form_cantidad_maxima"],
                on_change=lambda v: MisContratosState.wizard_set_cantidad_maxima(index, v),
                type="number",
                min="0",
                size="1",
                width="70px",
            ),
            width="80px",
        ),
    )


def _wizard_paso_categorias() -> rx.Component:
    return rx.vstack(
        rx.text(
            "Revisa y ajusta los sueldos, costo contractual y cantidades de plazas "
            "de cada categoría heredada. El nombre no se puede cambiar.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.cond(
            MisContratosState.wizard_error_categorias != "",
            rx.text(
                MisContratosState.wizard_error_categorias,
                font_size=Typography.SIZE_XS,
                color=Colors.ERROR,
            ),
            rx.fragment(),
        ),
        rx.cond(
            MisContratosState.wizard_categorias.length() > 0,
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                "Categoría",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.table.column_header_cell(
                                "Sueldo",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.table.column_header_cell(
                                "Tipo",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.table.column_header_cell(
                                "Costo contractual",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.table.column_header_cell(
                                "Min",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.table.column_header_cell(
                                "Max",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            MisContratosState.wizard_categorias,
                            lambda item, index: _wizard_categoria_row(item, index),
                        ),
                    ),
                    variant="surface",
                    size="1",
                    width="100%",
                ),
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.MD,
                overflow="auto",
                width="100%",
            ),
            rx.text(
                "Este contrato no tiene categorías configuradas. "
                "Puedes crear la extensión sin categorías y capturarlas después.",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
                font_style="italic",
            ),
        ),
        spacing="3",
        width="100%",
    )


def _wizard_empleado_row(item: rx.Var) -> rx.Component:
    """Fila de la tabla del paso 3: empleado con checkbox de migración."""
    return rx.table.row(
        rx.table.cell(
            rx.checkbox(
                checked=item["seleccionado"],
                on_change=lambda _: MisContratosState.wizard_toggle_empleado(
                    item["empleado_id"]
                ),
                size="2",
            ),
            width="40px",
        ),
        rx.table.cell(
            rx.text(
                item["nombre"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.badge(
                item["categoria_nombre"],
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                variant="soft",
                size="1",
            ),
        ),
        rx.table.cell(
            rx.text(
                item["sede_nombre"],
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
        ),
        rx.table.cell(
            rx.text(
                "#",
                item["plaza_numero"],
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
                font_variant_numeric="tabular-nums",
            ),
        ),
    )


def _wizard_paso_empleados() -> rx.Component:
    return rx.vstack(
        rx.text(
            "Selecciona los empleados que continuarán en la extensión. "
            "Los empleados marcados serán reasignados de la plaza actual "
            "(del contrato vencido) a una plaza de la extensión con la "
            "misma categoría.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.flex(
            rx.text(
                MisContratosState.wizard_resumen_seleccion_empleados,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.spacer(),
            width="100%",
            align="center",
        ),
        rx.cond(
            MisContratosState.wizard_error_empleados != "",
            rx.text(
                MisContratosState.wizard_error_empleados,
                font_size=Typography.SIZE_XS,
                color=Colors.ERROR,
            ),
            rx.fragment(),
        ),
        rx.cond(
            MisContratosState.wizard_total_empleados_padre > 0,
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(""),
                            rx.table.column_header_cell(
                                "Empleado",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.table.column_header_cell(
                                "Categoría",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.table.column_header_cell(
                                "Sede actual",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                            rx.table.column_header_cell(
                                "Plaza",
                                font_size=Typography.SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            MisContratosState.wizard_empleados_padre_enriquecidos,
                            _wizard_empleado_row,
                        ),
                    ),
                    variant="surface",
                    size="1",
                    width="100%",
                ),
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.MD,
                overflow="auto",
                max_height="380px",
                width="100%",
            ),
            rx.box(
                rx.text(
                    "El contrato padre no tiene empleados activos. "
                    "Puedes continuar sin migración.",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                    font_style="italic",
                ),
                padding=Spacing.LG,
                background=Colors.SURFACE,
                border=f"1px dashed {Colors.BORDER}",
                border_radius=Radius.MD,
                width="100%",
            ),
        ),
        feedback_callout(
            content=rx.text(
                "Los empleados NO seleccionados permanecerán en la plaza del "
                "contrato vencido. Puedes darles baja manualmente después "
                "si es necesario.",
                font_size=Typography.SIZE_XS,
            ),
            kind="info",
        ),
        spacing="3",
        width="100%",
    )


def _wizard_paso_confirmacion() -> rx.Component:
    return rx.vstack(
        rx.text(
            "Revisa la configuración antes de crear la extensión.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.box(
            rx.vstack(
                rx.flex(
                    rx.text(
                        "Contrato padre",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
                        width="160px",
                    ),
                    rx.text(
                        MisContratosState.contrato_a_extender["codigo"],
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    align="center",
                ),
                rx.flex(
                    rx.text(
                        "Vigencia",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
                        width="160px",
                    ),
                    rx.text(
                        MisContratosState.resumen_vigencia_extension,
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    align="center",
                ),
                rx.flex(
                    rx.text(
                        "Categorías heredadas",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
                        width="160px",
                    ),
                    rx.text(
                        MisContratosState.resumen_total_categorias.to(str)
                        + " categoría(s)",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    align="center",
                ),
                rx.flex(
                    rx.text(
                        "Empleados a migrar",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
                        width="160px",
                    ),
                    rx.text(
                        MisContratosState.wizard_total_empleados_seleccionados.to(str)
                        + " de "
                        + MisContratosState.wizard_total_empleados_padre.to(str),
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    align="center",
                ),
                spacing="3",
                width="100%",
                align="start",
            ),
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.MD,
            padding=Spacing.LG,
            width="100%",
        ),
        feedback_callout(
            content=rx.text(
                "Al confirmar se creará un nuevo contrato en estado BORRADOR "
                "vinculado al padre como extensión, con las categorías y ajustes "
                "que definiste. Las plazas se crearán vacantes — los empleados "
                "deberán migrarse manualmente desde la tab Plazas de la extensión.",
                font_size=Typography.SIZE_XS,
            ),
            kind="info",
        ),
        spacing="4",
        width="100%",
    )


def _wizard_contenido_paso() -> rx.Component:
    return rx.match(
        MisContratosState.wizard_paso_actual,
        (1, _wizard_paso_vigencia()),
        (2, _wizard_paso_categorias()),
        (3, _wizard_paso_empleados()),
        (4, _wizard_paso_confirmacion()),
        _wizard_paso_vigencia(),
    )


def _wizard_botonera() -> rx.Component:
    return rx.flex(
        rx.cond(
            MisContratosState.wizard_puede_ir_atras,
            rx.button(
                rx.icon("chevron-left", size=16),
                "Atrás",
                on_click=MisContratosState.wizard_paso_anterior,
                variant="soft",
                color_scheme=Colors.NEUTRAL_SCHEME,
                disabled=MisContratosState.saving_extension,
            ),
            rx.box(),
        ),
        rx.spacer(),
        rx.button(
            "Cancelar",
            on_click=MisContratosState.cerrar_modal_extension,
            variant="ghost",
            color_scheme=Colors.NEUTRAL_SCHEME,
            disabled=MisContratosState.saving_extension,
        ),
        rx.cond(
            MisContratosState.wizard_es_paso_confirmacion,
            rx.button(
                rx.icon("check", size=16),
                "Crear extensión",
                on_click=MisContratosState.guardar_extension,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                disabled=~MisContratosState.puede_crear_extension,
                loading=MisContratosState.saving_extension,
            ),
            rx.button(
                "Siguiente",
                rx.icon("chevron-right", size=16),
                on_click=MisContratosState.wizard_siguiente_paso,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                disabled=MisContratosState.saving_extension,
            ),
        ),
        width="100%",
        align="center",
        gap=Spacing.SM,
    )


def _modal_extension_contrato() -> rx.Component:
    """Wizard multi-paso para crear una extensión del contrato padre."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(
                        "file-plus",
                        size=20,
                        color=Colors.PORTAL_PRIMARY,
                    ),
                    rx.dialog.title(MisContratosState.titulo_modal_extension),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=18),
                        variant="ghost",
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        size="2",
                        on_click=MisContratosState.cerrar_modal_extension,
                        cursor="pointer",
                        disabled=MisContratosState.saving_extension,
                    ),
                    align="center",
                    spacing="2",
                    width="100%",
                ),
                _wizard_stepper_extension(),
                rx.box(
                    _wizard_contenido_paso(),
                    padding_y=Spacing.LG,
                    width="100%",
                    min_height="320px",
                ),
                _wizard_botonera(),
                spacing="3",
                width="100%",
            ),
            max_width="880px",
            width="min(880px, 95vw)",
        ),
        open=MisContratosState.modal_extension_abierto,
    )


def mis_contratos_page() -> rx.Component:
    """Pagina de lista de contratos del portal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Contratos",
                subtitulo="Contratos de la empresa",
                icono="file-text",
                accion_principal=rx.cond(
                    AuthState.es_admin_empresa,
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo contrato",
                        on_click=ContratosState.abrir_modal_crear_portal,
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    ),
                    rx.fragment(),
                ),
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
            ),
            content=rx.vstack(
                _metricas_contratos(),
                _toolbar(),
                _contratos_contenido(),
                _modal_detalle_contrato(),
                _modal_confirmar_cancelar(),
                _modal_extension_contrato(),
                modal_contrato(),
                width="100%",
                spacing="4",
            ),
        ),
        width="100%",
        max_width="1200px",
        margin_x="auto",
        min_height="100vh",
        on_mount=MisContratosState.on_mount_contratos,
    )
