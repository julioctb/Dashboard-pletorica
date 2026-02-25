"""
Estado de Reflex para el módulo de Tipos de Servicio.
Maneja el estado de la UI y las operaciones del módulo.
"""
import reflex as rx
from typing import List, Optional

from app.core.text_utils import normalizar_mayusculas
from app.core.utils import generar_candidatos_codigo
from app.entities import TipoServicioCreate, TipoServicioUpdate
from app.services import tipo_servicio_service
# Las excepciones se manejan centralizadamente en BaseState
from app.presentation.components.shared.base_state import BaseState
from app.presentation.pages.tipo_servicio.tipo_servicio_validators import (
    validar_clave,
    validar_nombre,
    validar_descripcion,
)

# Campos con sus valores por defecto para limpiar formulario
FORM_DEFAULTS = {
    "clave": "",
    "nombre": "",
    "descripcion": "",
}


class TipoServicioState(BaseState):
    """Estado para el módulo de Tipos de Servicio"""

    # ========================
    # ESTADO DE DATOS
    # ========================
    tipos: List[dict] = []
    tipo_seleccionado: Optional[dict] = None
    total_tipos: int = 0

    # ========================
    # ESTADO DE UI
    # ========================
    # loading, saving, filtro_busqueda vienen de BaseState
    mostrar_modal_tipo: bool = False
    mostrar_modal_confirmar_eliminar: bool = False
    es_edicion: bool = False

    # Vista (tabla/cards)
    view_mode: str = "table"

    # Filtros (filtro_busqueda viene de BaseState)
    incluir_inactivas: bool = False

    # ========================
    # ESTADO DEL FORMULARIO
    # ========================
    form_clave: str = ""
    form_nombre: str = ""
    form_descripcion: str = ""

    # Errores de validación
    error_clave: str = ""
    error_nombre: str = ""
    error_descripcion: str = ""

    # ========================
    # SETTERS EXPLÍCITOS (Reflex 0.8.9+)
    # ========================
    # set_filtro_busqueda viene de BaseState

    async def on_change_busqueda(self, value: str):
        """Actualizar filtro y buscar automáticamente"""
        self.filtro_busqueda = value
        await self._fetch_tipos()

    def set_incluir_inactivas(self, value: bool):
        self.incluir_inactivas = value

    # View toggle heredado de BaseState

    def set_form_clave(self, value: str):
        """Set clave con auto-conversión a mayúsculas"""
        self.form_clave = normalizar_mayusculas(value)

    async def set_form_nombre(self, value: str):
        """Set nombre con auto-conversión a mayúsculas y auto-sugerir clave única"""
        self.form_nombre = normalizar_mayusculas(value)
        # Auto-sugerir clave si está vacía y no es edición
        if not self.form_clave and not self.es_edicion and value:
            candidatos = generar_candidatos_codigo(value)
            for clave in candidatos[:10]:  # Probar máximo 10 candidatos
                clave_corta = clave[:5]  # Máximo 5 caracteres
                if not await tipo_servicio_service.existe_clave(clave_corta):
                    self.form_clave = clave_corta
                    break

    def set_form_descripcion(self, value: str):
        self.form_descripcion = value

    def set_mostrar_modal_tipo(self, value: bool):
        self.mostrar_modal_tipo = value

    def set_mostrar_modal_confirmar_eliminar(self, value: bool):
        self.mostrar_modal_confirmar_eliminar = value

    # ========================
    # VALIDACIÓN EN TIEMPO REAL
    # ========================
    def validar_clave_campo(self):
        """Validar clave en tiempo real"""
        self.validar_y_asignar_error(
            valor=self.form_clave,
            validador=validar_clave,
            error_attr="error_clave",
        )

    def validar_nombre_campo(self):
        """Validar nombre en tiempo real"""
        self.validar_y_asignar_error(
            valor=self.form_nombre,
            validador=validar_nombre,
            error_attr="error_nombre",
        )

    def validar_descripcion_campo(self):
        """Validar descripción en tiempo real"""
        self.validar_y_asignar_error(
            valor=self.form_descripcion,
            validador=validar_descripcion,
            error_attr="error_descripcion",
        )

    def validar_todos_los_campos(self):
        """Validar todos los campos del formulario"""
        self.validar_lote_campos([
            ("error_clave", self.form_clave, validar_clave),
            ("error_nombre", self.form_nombre, validar_nombre),
            ("error_descripcion", self.form_descripcion, validar_descripcion),
        ])

    @rx.var
    def tiene_errores_formulario(self) -> bool:
        """Verifica si hay errores de validación en el formulario"""
        return bool(
            self.error_clave or
            self.error_nombre or
            self.error_descripcion
        )

    @rx.var
    def puede_guardar(self) -> bool:
        """Verifica si el formulario puede guardarse"""
        tiene_datos = bool(self.form_clave and self.form_nombre)
        return tiene_datos and not self.tiene_errores_formulario and not self.saving

    @rx.var
    def tiene_filtros_activos(self) -> bool:
        """Indica si hay algún filtro aplicado"""
        return bool(self.filtro_busqueda.strip()) or self.incluir_inactivas

    @rx.var
    def mostrar_tabla(self) -> bool:
        """Muestra tabla si hay tipos O si hay filtro activo (para mantener el input visible)"""
        return self.total_tipos > 0 or bool(self.filtro_busqueda.strip())

    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def _fetch_tipos(self):
        """Carga tipos de servicio desde BD (sin manejo de loading)."""
        try:
            tipos = await tipo_servicio_service.obtener_todas(
                incluir_inactivas=self.incluir_inactivas
            )

            # Filtrar por búsqueda si hay término
            if self.filtro_busqueda:
                termino = self.filtro_busqueda.upper()
                tipos = [
                    t for t in tipos
                    if termino in t.clave.upper() or termino in t.nombre.upper()
                ]

            # Convertir a dict para Reflex
            self.tipos = [tipo.model_dump() for tipo in tipos]
            self.total_tipos = len(self.tipos)

        except Exception as e:
            self.manejar_error(e, "al cargar tipos")
            self.tipos = []

    async def on_mount_tipos(self):
        """Montaje de la página: skeleton en primera visita, silencioso en revisitas."""
        async for _ in self._montar_pagina(self._fetch_tipos):
            yield

    async def cargar_tipos(self):
        """Recarga tipos con skeleton loading (filtros, refresh)."""
        async for _ in self._recargar_datos(self._fetch_tipos):
            yield

    async def buscar_tipos(self):
        """Buscar tipos con el filtro actual"""
        async for _ in self.cargar_tipos():
            yield

    def handle_key_down(self, key: str):
        """Manejar tecla presionada en búsqueda"""
        if key == "Enter":
            return TipoServicioState.buscar_tipos

    def toggle_inactivas(self, value: bool = None):
        """Alternar mostrar/ocultar inactivas y recargar"""
        if value is not None:
            self.incluir_inactivas = value
        else:
            self.incluir_inactivas = not self.incluir_inactivas
        return TipoServicioState.cargar_tipos

    async def limpiar_filtros(self):
        """Limpiar todos los filtros y recargar"""
        self.resetear_filtros(
            {
                "filtro_busqueda": "",
                "incluir_inactivas": False,
            },
            resetear_pagina=False,
        )
        async for _ in self._recargar_datos(self._fetch_tipos):
            yield

    async def limpiar_busqueda(self):
        """Limpiar solo el campo de búsqueda y recargar"""
        self.filtro_busqueda = ""
        async for _ in self._recargar_datos(self._fetch_tipos):
            yield

    # ========================
    # OPERACIONES CRUD
    # ========================
    def abrir_modal_crear(self):
        """Abrir modal para crear nuevo tipo"""
        self._limpiar_formulario()
        self.es_edicion = False
        self.mostrar_modal_tipo = True

    def abrir_modal_editar(self, tipo: dict):
        """Abrir modal para editar tipo existente"""
        self._limpiar_formulario()
        self.es_edicion = True
        self.tipo_seleccionado = tipo

        # Cargar datos en el formulario
        self.form_clave = tipo.get("clave", "")
        self.form_nombre = tipo.get("nombre", "")
        self.form_descripcion = tipo.get("descripcion", "") or ""

        self.mostrar_modal_tipo = True

    def cerrar_modal_tipo(self):
        """Cerrar modal de crear/editar"""
        self.mostrar_modal_tipo = False
        self._limpiar_formulario()

    def abrir_confirmar_eliminar(self, tipo: dict):
        """Abrir modal de confirmación para eliminar"""
        self.tipo_seleccionado = tipo
        self.mostrar_modal_confirmar_eliminar = True

    def cerrar_confirmar_eliminar(self):
        """Cerrar modal de confirmación"""
        self.mostrar_modal_confirmar_eliminar = False
        self.tipo_seleccionado = None

    async def guardar_tipo(self):
        """Guardar tipo (crear o actualizar)"""
        # Validar campos
        self.validar_todos_los_campos()
        if self.tiene_errores_formulario:
            return

        self.saving = True
        try:
            if self.es_edicion:
                await self._actualizar_tipo()
            else:
                await self._crear_tipo()

            # Cerrar modal y recargar
            self.cerrar_modal_tipo()
            await self._fetch_tipos()

        except Exception as e:
            self.manejar_error(
                e,
                "al guardar tipo",
                campo_duplicado="error_clave",
                valor_duplicado=self.form_clave
            )
        finally:
            self.saving = False

    async def _crear_tipo(self):
        """Crear nuevo tipo"""
        tipo_create = TipoServicioCreate(
            clave=normalizar_mayusculas(self.form_clave),
            nombre=normalizar_mayusculas(self.form_nombre),
            descripcion=self.form_descripcion.strip() if self.form_descripcion else None
        )

        await tipo_servicio_service.crear(tipo_create)

        return rx.toast.success(
            f"Tipo '{tipo_create.nombre}' creado exitosamente",
            position="top-center",
            duration=3000
        )

    async def _actualizar_tipo(self):
        """Actualizar tipo existente"""
        if not self.tipo_seleccionado:
            return

        tipo_update = TipoServicioUpdate(
            clave=normalizar_mayusculas(self.form_clave),
            nombre=normalizar_mayusculas(self.form_nombre),
            descripcion=self.form_descripcion.strip() if self.form_descripcion else None
        )

        await tipo_servicio_service.actualizar(
            self.tipo_seleccionado["id"],
            tipo_update
        )

        return rx.toast.success(
            f"Tipo '{tipo_update.nombre}' actualizado exitosamente",
            position="top-center",
            duration=3000
        )

    async def eliminar_tipo(self):
        """Eliminar (desactivar) tipo seleccionado"""
        if not self.tipo_seleccionado:
            return

        nombre = self.tipo_seleccionado["nombre"]
        tipo_id = self.tipo_seleccionado["id"]

        async def _on_exito():
            self.cerrar_confirmar_eliminar()
            await self._fetch_tipos()

        return await self.ejecutar_guardado(
            operacion=lambda: tipo_servicio_service.eliminar(tipo_id),
            mensaje_exito=f"Tipo '{nombre}' eliminado",
            on_exito=_on_exito,
        )

    async def activar_tipo(self, tipo: dict):
        """Activar un tipo inactivo"""
        return await self.ejecutar_guardado(
            operacion=lambda: tipo_servicio_service.activar(tipo["id"]),
            mensaje_exito=f"Tipo '{tipo['nombre']}' activado",
            on_exito=self._fetch_tipos,
        )

    # ========================
    # HELPERS PRIVADOS
    # ========================
    def _limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        for campo, default in FORM_DEFAULTS.items():
            setattr(self, f"form_{campo}", default)
        self.limpiar_errores_campos(["clave", "nombre", "descripcion"])
        self.tipo_seleccionado = None
        self.es_edicion = False
