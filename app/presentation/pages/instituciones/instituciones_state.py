"""
Estado de Reflex para el modulo de Instituciones.
Maneja el estado de la UI y las operaciones CRUD + gestion de empresas.
"""
import reflex as rx
from typing import List, Optional

from app.core.text_utils import normalizar_mayusculas
from app.entities import InstitucionCreate, InstitucionUpdate
from app.services import institucion_service, empresa_service
from app.presentation.components.shared.auth_state import AuthState


# Campos con sus valores por defecto
FORM_DEFAULTS = {
    "nombre": "",
    "codigo": "",
}


class InstitucionesState(AuthState):
    """Estado para el modulo de Instituciones"""

    # ========================
    # ESTADO DE DATOS
    # ========================
    instituciones: List[dict] = []
    institucion_seleccionada: Optional[dict] = None
    total_instituciones: int = 0

    # Empresas asignadas a la institucion seleccionada
    empresas_asignadas: List[dict] = []
    # Todas las empresas disponibles para asignar
    opciones_empresas: List[dict] = []
    form_empresa_id: str = ""

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_institucion: bool = False
    mostrar_modal_empresas: bool = False
    mostrar_modal_confirmar_desactivar: bool = False
    es_edicion: bool = False

    # Vista (tabla/cards)
    view_mode: str = "table"

    # Filtros
    incluir_inactivas: bool = False

    # ========================
    # ESTADO DEL FORMULARIO
    # ========================
    form_nombre: str = ""
    form_codigo: str = ""

    # Errores de validacion
    error_nombre: str = ""
    error_codigo: str = ""

    # ========================
    # SETTERS EXPLICITOS
    # ========================
    async def on_change_busqueda(self, value: str):
        """Actualizar filtro y buscar automaticamente"""
        self.filtro_busqueda = value
        await self._fetch_instituciones()

    def set_incluir_inactivas(self, value: bool):
        self.incluir_inactivas = value

    def set_form_nombre(self, value: str):
        self.form_nombre = value

    def set_form_codigo(self, value: str):
        self.form_codigo = normalizar_mayusculas(value)

    def set_form_empresa_id(self, value: str):
        self.form_empresa_id = value

    def set_mostrar_modal_institucion(self, value: bool):
        self.mostrar_modal_institucion = value

    def set_mostrar_modal_confirmar_desactivar(self, value: bool):
        self.mostrar_modal_confirmar_desactivar = value

    # ========================
    # VALIDACION
    # ========================
    @staticmethod
    def _validar_nombre(valor: str) -> str:
        texto = (valor or "").strip()
        if len(texto) < 2:
            return "El nombre debe tener al menos 2 caracteres"
        return ""

    @staticmethod
    def _validar_codigo(valor: str) -> str:
        texto = (valor or "").strip()
        if len(texto) < 2:
            return "El codigo debe tener al menos 2 caracteres"
        if len(texto) > 20:
            return "El codigo no puede exceder 20 caracteres"
        return ""

    def validar_nombre_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_nombre,
            validador=self._validar_nombre,
            error_attr="error_nombre",
        )

    def validar_codigo_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_codigo,
            validador=self._validar_codigo,
            error_attr="error_codigo",
        )

    def validar_todos_los_campos(self):
        self.validar_lote_campos(
            [
                ("error_nombre", self.form_nombre, self._validar_nombre),
                ("error_codigo", self.form_codigo, self._validar_codigo),
            ]
        )

    @rx.var
    def tiene_errores_formulario(self) -> bool:
        return bool(self.error_nombre or self.error_codigo)

    @rx.var
    def puede_guardar(self) -> bool:
        tiene_datos = bool(self.form_nombre and self.form_codigo)
        return tiene_datos and not self.tiene_errores_formulario and not self.saving

    @rx.var
    def tiene_filtros_activos(self) -> bool:
        return bool(self.filtro_busqueda.strip()) or self.incluir_inactivas

    @rx.var
    def mostrar_tabla(self) -> bool:
        return self.total_instituciones > 0 or bool(self.filtro_busqueda.strip())

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_instituciones(self):
        """Carga instituciones desde BD (sin manejo de loading)."""
        try:
            instituciones = await institucion_service.obtener_todas(
                solo_activas=not self.incluir_inactivas
            )

            # Filtrar por busqueda si hay termino
            if self.filtro_busqueda:
                termino = self.filtro_busqueda.upper()
                instituciones = [
                    i for i in instituciones
                    if termino in i.codigo.upper()
                    or termino in i.nombre.upper()
                ]

            self.instituciones = [
                {
                    "id": i.id,
                    "nombre": i.nombre,
                    "codigo": i.codigo,
                    "activo": i.activo,
                    "cantidad_empresas": i.cantidad_empresas,
                    "estatus": "ACTIVO" if i.activo else "INACTIVO",
                }
                for i in instituciones
            ]
            self.total_instituciones = len(self.instituciones)

        except Exception as e:
            self.manejar_error(e, "al cargar instituciones")
            self.instituciones = []

    async def on_mount_instituciones(self):
        """Montaje de la pagina."""
        async for _ in self._montar_pagina_auth(self._fetch_instituciones):
            yield

    async def cargar_instituciones(self):
        """Recarga con skeleton loading."""
        async for _ in self._recargar_datos(self._fetch_instituciones):
            yield

    async def buscar_instituciones(self):
        async for _ in self.cargar_instituciones():
            yield

    def handle_key_down(self, key: str):
        if key == "Enter":
            return InstitucionesState.buscar_instituciones

    def toggle_inactivas(self, value: bool = None):
        if value is not None:
            self.incluir_inactivas = value
        else:
            self.incluir_inactivas = not self.incluir_inactivas
        return InstitucionesState.cargar_instituciones

    async def limpiar_filtros(self):
        self.filtro_busqueda = ""
        self.incluir_inactivas = False
        async for _ in self._recargar_datos(self._fetch_instituciones):
            yield

    async def limpiar_busqueda(self):
        self.filtro_busqueda = ""
        async for _ in self._recargar_datos(self._fetch_instituciones):
            yield

    # ========================
    # CRUD INSTITUCIONES
    # ========================
    def abrir_modal_crear(self):
        self._limpiar_formulario()
        self.es_edicion = False
        self.mostrar_modal_institucion = True

    def abrir_modal_editar(self, institucion: dict):
        self._limpiar_formulario()
        self.es_edicion = True
        self.institucion_seleccionada = institucion
        self.form_nombre = institucion.get("nombre", "")
        self.form_codigo = institucion.get("codigo", "")
        self.mostrar_modal_institucion = True

    def cerrar_modal_institucion(self):
        self.mostrar_modal_institucion = False
        self._limpiar_formulario()

    def abrir_confirmar_desactivar(self, institucion: dict):
        self.institucion_seleccionada = institucion
        self.mostrar_modal_confirmar_desactivar = True

    def cerrar_confirmar_desactivar(self):
        self.mostrar_modal_confirmar_desactivar = False
        self.institucion_seleccionada = None

    async def guardar_institucion(self):
        """Guardar institucion (crear o actualizar)"""
        self.validar_todos_los_campos()
        if self.tiene_errores_formulario:
            return

        self.saving = True
        try:
            if self.es_edicion:
                await self._actualizar_institucion()
            else:
                await self._crear_institucion()

            self.cerrar_modal_institucion()
            await self._fetch_instituciones()

        except Exception as e:
            self.manejar_error(
                e,
                "al guardar institucion",
                campo_duplicado="error_codigo",
                valor_duplicado=self.form_codigo,
            )
        finally:
            self.saving = False

    async def _crear_institucion(self):
        datos = InstitucionCreate(
            nombre=self.form_nombre.strip(),
            codigo=normalizar_mayusculas(self.form_codigo),
        )
        await institucion_service.crear(datos)
        return rx.toast.success(
            f"Institucion '{datos.nombre}' creada exitosamente",
            position="top-center",
            duration=3000,
        )

    async def _actualizar_institucion(self):
        if not self.institucion_seleccionada:
            return
        datos = InstitucionUpdate(
            nombre=self.form_nombre.strip(),
            codigo=normalizar_mayusculas(self.form_codigo),
        )
        await institucion_service.actualizar(
            self.institucion_seleccionada["id"],
            datos,
        )
        return rx.toast.success(
            f"Institucion '{datos.nombre}' actualizada exitosamente",
            position="top-center",
            duration=3000,
        )

    async def desactivar_institucion(self):
        if not self.institucion_seleccionada:
            return

        self.saving = True
        try:
            await institucion_service.desactivar(self.institucion_seleccionada["id"])
            self.cerrar_confirmar_desactivar()
            await self._fetch_instituciones()
            return rx.toast.success(
                f"Institucion '{self.institucion_seleccionada['nombre']}' desactivada",
                position="top-center",
                duration=3000,
            )
        except Exception as e:
            self.manejar_error(e, "al desactivar institucion")
        finally:
            self.saving = False
            self.cerrar_confirmar_desactivar()

    async def activar_institucion(self, institucion: dict):
        try:
            await institucion_service.activar(institucion["id"])
            await self._fetch_instituciones()
            return rx.toast.success(
                f"Institucion '{institucion['nombre']}' activada",
                position="top-center",
                duration=3000,
            )
        except Exception as e:
            self.manejar_error(e, "al activar institucion")

    # ========================
    # GESTION DE EMPRESAS
    # ========================
    async def abrir_modal_empresas(self, institucion: dict):
        """Abre el modal para gestionar empresas de una institucion."""
        self.institucion_seleccionada = institucion
        self.form_empresa_id = ""

        # Cargar empresas asignadas
        try:
            asignadas = await institucion_service.obtener_empresas(institucion["id"])
            self.empresas_asignadas = [
                {
                    "id": a.id,
                    "empresa_id": a.empresa_id,
                    "empresa_nombre": a.empresa_nombre or f"Empresa {a.empresa_id}",
                    "empresa_rfc": a.empresa_rfc or "",
                }
                for a in asignadas
            ]
        except Exception as e:
            self.manejar_error(e, "al cargar empresas asignadas")
            self.empresas_asignadas = []

        # Cargar todas las empresas para el select
        try:
            todas = await empresa_service.obtener_todas(incluir_inactivas=False, limite=500)
            ids_asignados = {a["empresa_id"] for a in self.empresas_asignadas}
            self.opciones_empresas = [
                {"label": f"{e.nombre_comercial} ({e.rfc})", "value": str(e.id)}
                for e in todas
                if e.id not in ids_asignados
            ]
        except Exception as e:
            self.manejar_error(e, "al cargar catalogo de empresas")
            self.opciones_empresas = []

        self.mostrar_modal_empresas = True

    def cerrar_modal_empresas(self):
        self.mostrar_modal_empresas = False
        self.institucion_seleccionada = None
        self.empresas_asignadas = []
        self.opciones_empresas = []
        self.form_empresa_id = ""

    async def asignar_empresa(self):
        """Asigna la empresa seleccionada a la institucion."""
        if not self.form_empresa_id or not self.institucion_seleccionada:
            return

        self.saving = True
        try:
            await institucion_service.asignar_empresa(
                self.institucion_seleccionada["id"],
                int(self.form_empresa_id),
            )
            # Recargar el modal
            await self.abrir_modal_empresas(self.institucion_seleccionada)
            # Recargar tabla principal (cantidad_empresas cambio)
            await self._fetch_instituciones()
            return rx.toast.success("Empresa asignada", position="top-center")
        except Exception as e:
            self.manejar_error(e, "al asignar empresa")
        finally:
            self.saving = False

    async def quitar_empresa(self, asignacion: dict):
        """Remueve una empresa de la institucion."""
        if not self.institucion_seleccionada:
            return

        self.saving = True
        try:
            await institucion_service.quitar_empresa(
                self.institucion_seleccionada["id"],
                asignacion["empresa_id"],
            )
            # Recargar el modal
            await self.abrir_modal_empresas(self.institucion_seleccionada)
            # Recargar tabla principal
            await self._fetch_instituciones()
            return rx.toast.success("Empresa removida", position="top-center")
        except Exception as e:
            self.manejar_error(e, "al quitar empresa")
        finally:
            self.saving = False

    # ========================
    # HELPERS PRIVADOS
    # ========================
    def _limpiar_formulario(self):
        for campo, default in FORM_DEFAULTS.items():
            setattr(self, f"form_{campo}", default)
        self.limpiar_errores_campos(["nombre", "codigo"])
        self.institucion_seleccionada = None
        self.es_edicion = False
