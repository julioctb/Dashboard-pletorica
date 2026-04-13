"""State para el catálogo de puestos del portal."""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

import reflex as rx

from app.core.catalogs import PoliticaFiscalResolver, Tolerancias
from app.core.text_utils import (
    capitalizar_con_preposiciones,
    formatear_moneda,
    normalizar_mayusculas,
)
from app.domain.models import CategoriaPuesto, TipoServicio
from app.modules.application import categoria_puesto_service, tipo_servicio_service
from app.presentation.pages.portal.state.portal_state import PortalState

FILTRO_TODOS = "all"
DIAS_MES_FISCAL = Decimal("30")


class EmpresaCategoriasState(PortalState):
    """Gestión del catálogo de puestos agrupado por tipo de servicio."""

    tipos_servicio_catalogo: list[dict] = []
    categorias_catalogo: list[dict] = []

    busqueda_categoria: str = ""
    filtro_estatus_categoria: str = FILTRO_TODOS

    creando_tipo_servicio: bool = False
    form_nombre_tipo: str = ""
    error_form_nombre_tipo: str = ""

    modal_categoria_abierto: bool = False
    categoria_editando_id: int = 0
    categoria_editando_contratos_count: int = 0
    categoria_editando_puede_desactivar: bool = False

    form_tipo_servicio_id: str = ""
    form_nombre_categoria: str = ""
    form_clave_categoria: str = ""
    form_salario_base_categoria: str = ""

    error_form_tipo_servicio_id: str = ""
    error_form_nombre_categoria: str = ""
    error_form_clave_categoria: str = ""
    error_form_salario_base_categoria: str = ""

    @staticmethod
    def _formatear_moneda_catalogo(valor: Decimal | str | int | None) -> str:
        monto = Decimal(str(valor or 0))
        return formatear_moneda(
            str(monto),
            decimales_fijos=2,
            espacio_simbolo=False,
        )

    @staticmethod
    def _parse_salario(valor: str) -> Decimal:
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

    def _salario_base_es_menor_salario_minimo(self, salario: Decimal) -> bool:
        return (
            salario > Decimal("0")
            and salario < self._salario_minimo_mensual_decimal()
        )

    @staticmethod
    def _serializar_tipo(tipo: TipoServicio) -> dict:
        tipo_id = int(getattr(tipo, "id", 0) or 0)
        nombre = str(getattr(tipo, "nombre", "") or "")
        return {
            "id": tipo_id,
            "id_str": str(tipo_id),
            "nombre": nombre,
            "nombre_display": capitalizar_con_preposiciones(nombre),
        }

    def _serializar_categoria(
        self,
        categoria: CategoriaPuesto,
        *,
        tipo_servicio: TipoServicio,
        contratos_count: int,
    ) -> dict:
        categoria_id = int(getattr(categoria, "id", 0) or 0)
        tipo_id = int(getattr(categoria, "tipo_servicio_id", 0) or 0)
        salario = Decimal(str(getattr(categoria, "salario_base_mensual", 0) or 0))
        estatus = str(getattr(categoria, "estatus", "") or "").upper()
        es_activa = estatus == "ACTIVO"

        return {
            "id": categoria_id,
            "tipo_servicio_id": tipo_id,
            "tipo_servicio_id_str": str(tipo_id),
            "tipo_servicio_nombre": str(getattr(tipo_servicio, "nombre", "") or ""),
            "tipo_servicio_nombre_display": capitalizar_con_preposiciones(
                str(getattr(tipo_servicio, "nombre", "") or "")
            ),
            "clave": str(getattr(categoria, "clave", "") or ""),
            "clave_display": normalizar_mayusculas(getattr(categoria, "clave", "")),
            "nombre": str(getattr(categoria, "nombre", "") or ""),
            "nombre_display": normalizar_mayusculas(getattr(categoria, "nombre", "")),
            "salario_base_mensual": str(salario),
            "salario_base_fmt": self._formatear_moneda_catalogo(salario),
            "contratos_count": int(contratos_count or 0),
            "contratos_label": (
                f"{int(contratos_count or 0)} contrato(s)"
                if int(contratos_count or 0) > 0
                else "Sin uso"
            ),
            "tiene_contratos": bool(int(contratos_count or 0) > 0),
            "estatus": estatus,
            "estatus_label": "Activa" if es_activa else "Inactiva",
            "es_activa": es_activa,
        }

    def _buscar_categoria_local(self, categoria_id: int) -> Optional[dict]:
        categoria_int = int(categoria_id or 0)
        for categoria in self.categorias_catalogo:
            if int(categoria.get("id") or 0) == categoria_int:
                return dict(categoria)
        return None

    def _tipos_select_options(self) -> list[dict]:
        return [
            {
                "value": tipo["id_str"],
                "label": tipo["nombre_display"],
            }
            for tipo in self.tipos_servicio_catalogo
        ]

    async def on_mount_empresa_categorias(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not (self.es_admin_empresa or self.puede_acceder_rrhh):
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_catalogo):
            yield

    async def _fetch_catalogo(self):
        if not self.id_empresa_actual:
            self.tipos_servicio_catalogo = []
            self.categorias_catalogo = []
            return

        tipos = await tipo_servicio_service.obtener_portal_empresa(
            self.id_empresa_actual,
            incluir_inactivas=False,
        )
        tipos = sorted(
            tipos,
            key=lambda tipo: str(getattr(tipo, "nombre", "") or "").lower(),
        )
        tipos_por_id = {int(getattr(tipo, "id", 0) or 0): tipo for tipo in tipos}

        categorias_por_tipo = await asyncio.gather(
            *[
                categoria_puesto_service.obtener_por_tipo_servicio(
                    int(getattr(tipo, "id", 0) or 0),
                    incluir_inactivas=True,
                )
                for tipo in tipos
            ],
            return_exceptions=True,
        )

        categorias: list[CategoriaPuesto] = []
        for resultado in categorias_por_tipo:
            if isinstance(resultado, Exception):
                continue
            categorias.extend(resultado)

        conteos_contratos = await categoria_puesto_service.contar_contratos_por_categorias(
            [int(getattr(categoria, "id", 0) or 0) for categoria in categorias]
        )

        self.tipos_servicio_catalogo = [self._serializar_tipo(tipo) for tipo in tipos]
        self.categorias_catalogo = [
            self._serializar_categoria(
                categoria,
                tipo_servicio=tipos_por_id.get(int(getattr(categoria, "tipo_servicio_id", 0) or 0)),
                contratos_count=conteos_contratos.get(int(getattr(categoria, "id", 0) or 0), 0),
            )
            for categoria in categorias
            if int(getattr(categoria, "tipo_servicio_id", 0) or 0) in tipos_por_id
        ]

    def set_busqueda_categoria(self, value: str):
        self.busqueda_categoria = value

    def limpiar_busqueda_categoria(self):
        self.busqueda_categoria = ""

    def set_filtro_estatus_categoria(self, value: str):
        self.filtro_estatus_categoria = value if value else FILTRO_TODOS

    def iniciar_crear_tipo(self):
        self.creando_tipo_servicio = True
        self.form_nombre_tipo = ""
        self.error_form_nombre_tipo = ""

    def cancelar_crear_tipo(self):
        self.creando_tipo_servicio = False
        self.form_nombre_tipo = ""
        self.error_form_nombre_tipo = ""

    def set_form_nombre_tipo(self, value: str):
        self.form_nombre_tipo = value
        self.error_form_nombre_tipo = ""

    async def crear_tipo_servicio(self):
        nombre = str(self.form_nombre_tipo or "").strip()
        if not nombre:
            self.error_form_nombre_tipo = "Capture un tipo de servicio"
            return

        self.saving = True
        yield
        try:
            await tipo_servicio_service.crear_portal_empresa(
                self.id_empresa_actual,
                nombre=nombre,
            )
            await self._fetch_catalogo()
            self.creando_tipo_servicio = False
            self.form_nombre_tipo = ""
            self.error_form_nombre_tipo = ""
            yield self.crear_toast("Tipo de servicio creado", "success")
        except Exception as error:
            mensaje = str(error)
            self.error_form_nombre_tipo = mensaje
            yield self.manejar_error_con_toast(error, "al crear el tipo de servicio")
        finally:
            self.saving = False
            yield

    def handle_key_down_crear_tipo(self, key: str):
        if key == "Enter":
            return EmpresaCategoriasState.crear_tipo_servicio
        return None

    def _limpiar_form_categoria(self):
        self.form_tipo_servicio_id = ""
        self.form_nombre_categoria = ""
        self.form_clave_categoria = ""
        self.form_salario_base_categoria = ""
        self.error_form_tipo_servicio_id = ""
        self.error_form_nombre_categoria = ""
        self.error_form_clave_categoria = ""
        self.error_form_salario_base_categoria = ""
        self.categoria_editando_id = 0
        self.categoria_editando_contratos_count = 0
        self.categoria_editando_puede_desactivar = False

    def abrir_modal_crear_categoria(self):
        self._limpiar_form_categoria()
        if self.tipos_servicio_catalogo:
            self.form_tipo_servicio_id = self.tipos_servicio_catalogo[0]["id_str"]
        self.modal_categoria_abierto = True

    def abrir_modal_categoria_en_tipo(self, tipo_servicio_id: int | str):
        self._limpiar_form_categoria()
        self.form_tipo_servicio_id = str(tipo_servicio_id or "")
        self.modal_categoria_abierto = True

    async def editar_categoria_puesto(self, categoria_id: int):
        categoria = self._buscar_categoria_local(categoria_id)
        if categoria is None:
            yield self.crear_toast("La categoría ya no está disponible", "error")
            return

        self._limpiar_form_categoria()
        self.categoria_editando_id = int(categoria.get("id") or 0)
        self.form_tipo_servicio_id = str(categoria.get("tipo_servicio_id_str") or "")
        self.form_nombre_categoria = normalizar_mayusculas(str(categoria.get("nombre") or ""))
        self.form_clave_categoria = normalizar_mayusculas(str(categoria.get("clave") or ""))
        salario_raw = str(categoria.get("salario_base_mensual") or "0")
        self.form_salario_base_categoria = (
            formatear_moneda(salario_raw) if Decimal(salario_raw) > Decimal("0") else ""
        )
        self.categoria_editando_contratos_count = await categoria_puesto_service.contar_contratos_por_categoria(
            self.categoria_editando_id
        )
        self.categoria_editando_puede_desactivar = await categoria_puesto_service.puede_desactivar_portal_empresa(
            self.categoria_editando_id,
            self.id_empresa_actual,
        )
        self.modal_categoria_abierto = True

    def cerrar_modal_categoria(self):
        self.modal_categoria_abierto = False
        self._limpiar_form_categoria()

    def set_form_tipo_servicio_id(self, value: str):
        self.form_tipo_servicio_id = value
        self.error_form_tipo_servicio_id = ""

    def set_form_nombre_categoria(self, value: str):
        self.form_nombre_categoria = normalizar_mayusculas(value)
        self.error_form_nombre_categoria = ""

    def set_form_clave_categoria(self, value: str):
        self.form_clave_categoria = normalizar_mayusculas(value)
        self.error_form_clave_categoria = ""

    def set_form_salario_base_categoria(self, value: str):
        self.form_salario_base_categoria = formatear_moneda(value) if value else ""
        self.error_form_salario_base_categoria = ""

    def _validar_form_categoria(self) -> bool:
        self.error_form_tipo_servicio_id = ""
        self.error_form_nombre_categoria = ""
        self.error_form_clave_categoria = ""
        self.error_form_salario_base_categoria = ""

        if not self.form_tipo_servicio_id:
            self.error_form_tipo_servicio_id = "Seleccione un tipo de servicio"

        if not str(self.form_nombre_categoria or "").strip():
            self.error_form_nombre_categoria = "Capture un nombre para la categoría"

        try:
            self._parse_salario(self.form_salario_base_categoria)
        except ValueError as error:
            self.error_form_salario_base_categoria = str(error)

        return not any(
            (
                self.error_form_tipo_servicio_id,
                self.error_form_nombre_categoria,
                self.error_form_clave_categoria,
                self.error_form_salario_base_categoria,
            )
        )

    async def guardar_categoria(self):
        if not self._validar_form_categoria():
            yield self.crear_toast("Corrija los errores del formulario", "error")
            return

        salario = self._parse_salario(self.form_salario_base_categoria)
        self.saving = True
        yield
        try:
            if self.categoria_editando_id > 0:
                await categoria_puesto_service.actualizar_portal_empresa(
                    self.categoria_editando_id,
                    self.id_empresa_actual,
                    nombre=self.form_nombre_categoria,
                    clave=self.form_clave_categoria,
                    salario_base_mensual=salario,
                )
            else:
                await categoria_puesto_service.crear_portal_empresa(
                    self.id_empresa_actual,
                    tipo_servicio_id=int(self.form_tipo_servicio_id),
                    nombre=self.form_nombre_categoria,
                    clave=self.form_clave_categoria,
                    salario_base_mensual=salario,
                )

            await self._fetch_catalogo()
            self.modal_categoria_abierto = False
            self._limpiar_form_categoria()
            yield self.crear_toast("Categoría guardada", "success")
        except Exception as error:
            mensaje = str(error)
            if "clave" in mensaje.lower():
                self.error_form_clave_categoria = mensaje
            elif "nombre" in mensaje.lower():
                self.error_form_nombre_categoria = mensaje
            else:
                yield self.manejar_error_con_toast(error, "al guardar la categoría")
        finally:
            self.saving = False
            yield

    async def desactivar_categoria_puesto(self):
        if self.categoria_editando_id <= 0:
            return
        self.saving = True
        yield
        try:
            await categoria_puesto_service.desactivar_portal_empresa(
                self.categoria_editando_id,
                self.id_empresa_actual,
            )
            await self._fetch_catalogo()
            self.modal_categoria_abierto = False
            self._limpiar_form_categoria()
            yield self.crear_toast("Categoría desactivada", "success")
        except Exception as error:
            yield self.manejar_error_con_toast(error, "al desactivar la categoría")
        finally:
            self.saving = False
            yield

    async def reactivar_categoria_puesto(self, categoria_id: int):
        self.saving = True
        yield
        try:
            await categoria_puesto_service.activar_portal_empresa(
                int(categoria_id or 0),
                self.id_empresa_actual,
            )
            await self._fetch_catalogo()
            yield self.crear_toast("Categoría reactivada", "success")
        except Exception as error:
            yield self.manejar_error_con_toast(error, "al reactivar la categoría")
        finally:
            self.saving = False
            yield

    @rx.var
    def total_tipos(self) -> int:
        return len(self.tipos_servicio_catalogo)

    @rx.var
    def total_activas(self) -> int:
        return sum(1 for categoria in self.categorias_catalogo if categoria.get("estatus") == "ACTIVO")

    @rx.var
    def total_inactivas(self) -> int:
        return sum(1 for categoria in self.categorias_catalogo if categoria.get("estatus") == "INACTIVO")

    @rx.var
    def anio_actual(self) -> int:
        return self._fecha_calculo_fiscal().year

    @rx.var
    def salario_minimo_mensual_vigente(self) -> Decimal:
        return self._salario_minimo_mensual_decimal()

    @rx.var
    def salario_minimo_mensual_vigente_fmt(self) -> str:
        return self._formatear_moneda_catalogo(self.salario_minimo_mensual_vigente)

    @rx.var
    def mostrar_warning_salario_minimo_categoria(self) -> bool:
        if not str(self.form_salario_base_categoria or "").strip():
            return False
        try:
            salario = self._parse_salario(self.form_salario_base_categoria)
        except ValueError:
            return False
        return self._salario_base_es_menor_salario_minimo(salario)

    @rx.var
    def mensaje_warning_salario_minimo_categoria(self) -> str:
        return (
            f"El salario capturado es menor al salario mínimo vigente {self.anio_actual} "
            f"({self.salario_minimo_mensual_vigente_fmt}/mes). "
            "Revíselo si no corresponde a jornada parcial o por horas."
        )

    @rx.var
    def tipos_servicio_select_options(self) -> list[dict]:
        return self._tipos_select_options()

    @rx.var
    def tiene_filtros_activos(self) -> bool:
        return bool(str(self.busqueda_categoria or "").strip()) or self.filtro_estatus_categoria != FILTRO_TODOS

    @rx.var
    def tipos_servicio_con_categorias(self) -> list[dict]:
        termino = str(self.busqueda_categoria or "").strip().lower()
        filtro_estatus = str(self.filtro_estatus_categoria or FILTRO_TODOS).upper()

        grupos: list[dict] = []
        for tipo in self.tipos_servicio_catalogo:
            tipo_id = int(tipo.get("id") or 0)
            categorias_tipo = [
                categoria
                for categoria in self.categorias_catalogo
                if int(categoria.get("tipo_servicio_id") or 0) == tipo_id
            ]
            categorias_visibles = []
            for categoria in categorias_tipo:
                if termino:
                    nombre = str(categoria.get("nombre_display") or "").lower()
                    clave = str(categoria.get("clave_display") or "").lower()
                    if termino not in nombre and termino not in clave:
                        continue
                if filtro_estatus != FILTRO_TODOS.upper() and str(categoria.get("estatus") or "").upper() != filtro_estatus:
                    continue
                categorias_visibles.append(categoria)

            if self.tiene_filtros_activos and not categorias_visibles:
                continue

            total_categorias = len(categorias_tipo)
            grupos.append(
                {
                    **tipo,
                    "total_categorias": total_categorias,
                    "total_categorias_label": (
                        f"{total_categorias} categoría" if total_categorias == 1 else f"{total_categorias} categorías"
                    ),
                    "categorias": categorias_visibles if self.tiene_filtros_activos else categorias_tipo,
                    "tiene_categorias": bool(categorias_visibles if self.tiene_filtros_activos else categorias_tipo),
                }
            )

        return grupos

    @rx.var
    def mostrar_empty_state_principal(self) -> bool:
        return self.total_tipos == 0 and len(self.categorias_catalogo) == 0

    @rx.var
    def mostrar_empty_state_filtros(self) -> bool:
        return self.tiene_filtros_activos and len(self.tipos_servicio_con_categorias) == 0

    @rx.var
    def titulo_modal_categoria(self) -> str:
        return "Editar categoría" if self.categoria_editando_id > 0 else "Nueva categoría"

    @rx.var
    def descripcion_modal_categoria(self) -> str:
        if self.categoria_editando_id > 0:
            return "Actualice la categoría del catálogo de la empresa."
        return "Se agrega al catálogo de la empresa y quedará disponible para nuevos contratos."

    @rx.var
    def categoria_editando(self) -> bool:
        return self.categoria_editando_id > 0

    @rx.var
    def puede_guardar_categoria(self) -> bool:
        return (
            bool(self.form_tipo_servicio_id)
            and bool(str(self.form_nombre_categoria or "").strip())
            and not self.saving
        )
