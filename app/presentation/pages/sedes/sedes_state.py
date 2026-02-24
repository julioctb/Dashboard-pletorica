"""
Estado de Reflex para el modulo de Sedes BUAP.
Maneja el estado de la UI y las operaciones del modulo.
"""
import reflex as rx
from typing import List, Optional

from app.core.enums import TipoSede
from app.core.text_utils import normalizar_mayusculas
from app.entities import SedeCreate, SedeUpdate
from app.services import sede_service
from app.presentation.components.shared.base_state import BaseState
from app.presentation.pages.sedes.sedes_validators import (
    validar_codigo,
    validar_nombre,
    validar_nombre_corto,
)

# Campos con sus valores por defecto para limpiar formulario
FORM_DEFAULTS = {
    "codigo": "",
    "nombre": "",
    "nombre_corto": "",
    "tipo_sede": "",
    "es_ubicacion_fisica": True,
    "sede_padre_id": "",
    "ubicacion_fisica_id": "",
    "direccion": "",
    "notas": "",
}


class SedesState(BaseState):
    """Estado para el modulo de Sedes BUAP"""

    # ========================
    # ESTADO DE DATOS
    # ========================
    sedes: List[dict] = []
    sede_seleccionada: Optional[dict] = None
    total_sedes: int = 0

    # Opciones para selects
    opciones_tipo_sede: List[dict] = []
    opciones_sedes_padre: List[dict] = []

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_sede: bool = False
    mostrar_modal_confirmar_eliminar: bool = False
    es_edicion: bool = False

    # Vista (tabla/cards)
    view_mode: str = "table"

    # Filtros
    incluir_inactivas: bool = False

    # ========================
    # ESTADO DEL FORMULARIO
    # ========================
    form_codigo: str = ""
    form_nombre: str = ""
    form_nombre_corto: str = ""
    form_tipo_sede: str = ""
    form_es_ubicacion_fisica: bool = True
    form_sede_padre_id: str = ""
    form_ubicacion_fisica_id: str = ""
    form_direccion: str = ""
    form_notas: str = ""

    # Errores de validacion
    error_codigo: str = ""
    error_nombre: str = ""
    error_nombre_corto: str = ""
    error_tipo_sede: str = ""

    # ========================
    # SETTERS EXPLICITOS (Reflex 0.8.9+)
    # ========================

    async def on_change_busqueda(self, value: str):
        """Actualizar filtro y buscar automaticamente"""
        self.filtro_busqueda = value
        await self._fetch_sedes()

    def set_incluir_inactivas(self, value: bool):
        self.incluir_inactivas = value

    # View toggle heredado de BaseState

    # --- Form fields ---
    def set_form_codigo(self, value: str):
        self.form_codigo = normalizar_mayusculas(value)

    def set_form_nombre(self, value: str):
        self.form_nombre = value

    def set_form_nombre_corto(self, value: str):
        self.form_nombre_corto = value

    def set_form_tipo_sede(self, value: str):
        self.form_tipo_sede = value

    def set_form_es_ubicacion_fisica(self, value: bool):
        self.form_es_ubicacion_fisica = value
        # Si es ubicacion fisica, limpiar ubicacion_fisica_id
        if value:
            self.form_ubicacion_fisica_id = ""

    def set_form_sede_padre_id(self, value: str):
        self.form_sede_padre_id = value

    def set_form_ubicacion_fisica_id(self, value: str):
        self.form_ubicacion_fisica_id = value

    def set_form_direccion(self, value: str):
        self.form_direccion = value

    def set_form_notas(self, value: str):
        self.form_notas = value

    def set_mostrar_modal_sede(self, value: bool):
        self.mostrar_modal_sede = value

    def set_mostrar_modal_confirmar_eliminar(self, value: bool):
        self.mostrar_modal_confirmar_eliminar = value

    # ========================
    # VALIDACION EN TIEMPO REAL
    # ========================
    def validar_codigo_campo(self):
        self.error_codigo = validar_codigo(self.form_codigo)

    def validar_nombre_campo(self):
        self.error_nombre = validar_nombre(self.form_nombre)

    def validar_nombre_corto_campo(self):
        self.error_nombre_corto = validar_nombre_corto(self.form_nombre_corto)

    def validar_tipo_sede_campo(self):
        self.error_tipo_sede = "Seleccione un tipo de sede" if not self.form_tipo_sede else ""

    def validar_todos_los_campos(self):
        self.validar_codigo_campo()
        self.validar_nombre_campo()
        self.validar_nombre_corto_campo()
        self.validar_tipo_sede_campo()

    @rx.var
    def tiene_errores_formulario(self) -> bool:
        return bool(
            self.error_codigo or
            self.error_nombre or
            self.error_nombre_corto or
            self.error_tipo_sede
        )

    @rx.var
    def puede_guardar(self) -> bool:
        tiene_datos = bool(self.form_codigo and self.form_nombre and self.form_tipo_sede)
        return tiene_datos and not self.tiene_errores_formulario and not self.saving

    @rx.var
    def tiene_filtros_activos(self) -> bool:
        return bool(self.filtro_busqueda.strip()) or self.incluir_inactivas

    @rx.var
    def mostrar_tabla(self) -> bool:
        return self.total_sedes > 0 or bool(self.filtro_busqueda.strip())

    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def _fetch_sedes(self):
        """Carga sedes desde BD (sin manejo de loading)."""
        try:
            sedes = await sede_service.obtener_todas(
                incluir_inactivas=self.incluir_inactivas
            )

            # Filtrar por busqueda si hay termino
            if self.filtro_busqueda:
                termino = self.filtro_busqueda.upper()
                sedes = [
                    s for s in sedes
                    if termino in s.codigo.upper()
                    or termino in s.nombre.upper()
                    or (s.nombre_corto and termino in s.nombre_corto.upper())
                ]

            # Crear mapa de nombres para resolver padre/ubicacion
            mapa_nombres = {s.id: s.nombre_corto or s.nombre for s in sedes}

            # Convertir a dict con campos enriquecidos
            self.sedes = []
            for s in sedes:
                d = s.model_dump(mode='json')
                # Resolver nombres de relaciones
                if s.sede_padre_id and s.sede_padre_id in mapa_nombres:
                    d["sede_padre_nombre"] = mapa_nombres[s.sede_padre_id]
                else:
                    d["sede_padre_nombre"] = ""
                if s.ubicacion_fisica_id and s.ubicacion_fisica_id in mapa_nombres:
                    d["ubicacion_fisica_nombre"] = mapa_nombres[s.ubicacion_fisica_id]
                else:
                    d["ubicacion_fisica_nombre"] = ""
                # Descripcion del tipo
                try:
                    d["tipo_descripcion"] = TipoSede(d["tipo_sede"]).descripcion
                except (ValueError, KeyError):
                    d["tipo_descripcion"] = d.get("tipo_sede", "")
                self.sedes.append(d)

            self.total_sedes = len(self.sedes)

        except Exception as e:
            self.manejar_error(e, "al cargar sedes")
            self.sedes = []

    async def on_mount_sedes(self):
        """Montaje de la página: skeleton en primera visita, silencioso en revisitas."""
        async for _ in self._montar_pagina(self._fetch_sedes):
            yield

    async def cargar_sedes(self):
        """Recarga sedes con skeleton loading (filtros, refresh)."""
        async for _ in self._recargar_datos(self._fetch_sedes):
            yield

    async def cargar_opciones_sedes(self):
        """Cargar opciones para los selects de tipo_sede y sedes padre/ubicacion"""
        # Opciones de tipo sede desde enum
        self.opciones_tipo_sede = [
            {"label": t.descripcion, "value": t.value}
            for t in TipoSede
        ]

        # Opciones de sedes activas para padre/ubicacion
        try:
            sedes_activas = await sede_service.obtener_todas(incluir_inactivas=False)
            self.opciones_sedes_padre = [
                {"label": f"{s.codigo} - {s.nombre_corto or s.nombre}", "value": str(s.id)}
                for s in sedes_activas
            ]
        except Exception:
            self.opciones_sedes_padre = []

    async def buscar_sedes(self):
        async for _ in self.cargar_sedes():
            yield

    def handle_key_down(self, key: str):
        if key == "Enter":
            return SedesState.buscar_sedes

    def toggle_inactivas(self, value: bool = None):
        if value is not None:
            self.incluir_inactivas = value
        else:
            self.incluir_inactivas = not self.incluir_inactivas
        return SedesState.cargar_sedes

    async def limpiar_filtros(self):
        self.filtro_busqueda = ""
        self.incluir_inactivas = False
        async for _ in self._recargar_datos(self._fetch_sedes):
            yield

    async def limpiar_busqueda(self):
        self.filtro_busqueda = ""
        async for _ in self._recargar_datos(self._fetch_sedes):
            yield

    # ========================
    # OPERACIONES CRUD
    # ========================
    async def abrir_modal_crear(self):
        self._limpiar_formulario()
        self.es_edicion = False
        await self.cargar_opciones_sedes()
        self.mostrar_modal_sede = True

    async def abrir_modal_editar(self, sede: dict):
        self._limpiar_formulario()
        self.es_edicion = True
        self.sede_seleccionada = sede

        # Cargar datos en el formulario
        self.form_codigo = sede.get("codigo", "")
        self.form_nombre = sede.get("nombre", "")
        self.form_nombre_corto = sede.get("nombre_corto", "") or ""
        self.form_tipo_sede = sede.get("tipo_sede", "")
        self.form_es_ubicacion_fisica = sede.get("es_ubicacion_fisica", True)
        self.form_sede_padre_id = str(sede.get("sede_padre_id", "")) if sede.get("sede_padre_id") else ""
        self.form_ubicacion_fisica_id = str(sede.get("ubicacion_fisica_id", "")) if sede.get("ubicacion_fisica_id") else ""
        self.form_direccion = sede.get("direccion", "") or ""
        self.form_notas = sede.get("notas", "") or ""

        await self.cargar_opciones_sedes()
        self.mostrar_modal_sede = True

    def cerrar_modal_sede(self):
        self.mostrar_modal_sede = False
        self._limpiar_formulario()

    def abrir_confirmar_eliminar(self, sede: dict):
        self.sede_seleccionada = sede
        self.mostrar_modal_confirmar_eliminar = True

    def cerrar_confirmar_eliminar(self):
        self.mostrar_modal_confirmar_eliminar = False
        self.sede_seleccionada = None

    async def guardar_sede(self):
        """Guardar sede (crear o actualizar)"""
        self.validar_todos_los_campos()
        if self.tiene_errores_formulario:
            return

        self.saving = True
        try:
            if self.es_edicion:
                await self._actualizar_sede()
            else:
                await self._crear_sede()

            self.cerrar_modal_sede()
            await self._fetch_sedes()

        except Exception as e:
            self.manejar_error(
                e,
                "al guardar sede",
                campo_duplicado="error_codigo",
                valor_duplicado=self.form_codigo
            )
        finally:
            self.saving = False

    async def _crear_sede(self):
        sede_create = SedeCreate(
            codigo=normalizar_mayusculas(self.form_codigo),
            nombre=self.form_nombre.strip(),
            nombre_corto=self.form_nombre_corto.strip() if self.form_nombre_corto else None,
            tipo_sede=TipoSede(self.form_tipo_sede),
            es_ubicacion_fisica=self.form_es_ubicacion_fisica,
            sede_padre_id=self.parse_id(self.form_sede_padre_id),
            ubicacion_fisica_id=self.parse_id(self.form_ubicacion_fisica_id),
            direccion=self.form_direccion.strip() if self.form_direccion else None,
            notas=self.form_notas.strip() if self.form_notas else None,
        )

        await sede_service.crear(sede_create)

        return rx.toast.success(
            f"Sede '{sede_create.nombre}' creada exitosamente",
            position="top-center",
            duration=3000
        )

    async def _actualizar_sede(self):
        if not self.sede_seleccionada:
            return

        sede_update = SedeUpdate(
            codigo=normalizar_mayusculas(self.form_codigo),
            nombre=self.form_nombre.strip(),
            nombre_corto=self.form_nombre_corto.strip() if self.form_nombre_corto else None,
            tipo_sede=TipoSede(self.form_tipo_sede),
            es_ubicacion_fisica=self.form_es_ubicacion_fisica,
            sede_padre_id=self.parse_id(self.form_sede_padre_id),
            ubicacion_fisica_id=self.parse_id(self.form_ubicacion_fisica_id),
            direccion=self.form_direccion.strip() if self.form_direccion else None,
            notas=self.form_notas.strip() if self.form_notas else None,
        )

        await sede_service.actualizar(
            self.sede_seleccionada["id"],
            sede_update
        )

        return rx.toast.success(
            f"Sede '{sede_update.nombre}' actualizada exitosamente",
            position="top-center",
            duration=3000
        )

    async def eliminar_sede(self):
        if not self.sede_seleccionada:
            return

        self.saving = True
        try:
            await sede_service.eliminar(self.sede_seleccionada["id"])

            self.cerrar_confirmar_eliminar()
            await self._fetch_sedes()

            return rx.toast.success(
                f"Sede '{self.sede_seleccionada['nombre']}' eliminada",
                position="top-center",
                duration=3000
            )

        except Exception as e:
            self.manejar_error(e, "al eliminar sede")
        finally:
            self.saving = False
            self.cerrar_confirmar_eliminar()

    async def activar_sede(self, sede: dict):
        try:
            await sede_service.activar(sede["id"])
            await self._fetch_sedes()

            return rx.toast.success(
                f"Sede '{sede['nombre']}' activada",
                position="top-center",
                duration=3000
            )

        except Exception as e:
            self.manejar_error(e, "al activar sede")

    # ========================
    # HELPERS PRIVADOS
    # ========================
    def _limpiar_formulario(self):
        for campo, default in FORM_DEFAULTS.items():
            setattr(self, f"form_{campo}", default)
        self.error_codigo = ""
        self.error_nombre = ""
        self.error_nombre_corto = ""
        self.error_tipo_sede = ""
        self.sede_seleccionada = None
        self.es_edicion = False
