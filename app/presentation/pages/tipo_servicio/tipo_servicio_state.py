"""
Estado de Reflex para el módulo de Tipos de Servicio.
Maneja el estado de la UI y las operaciones del módulo.
"""
import reflex as rx
from typing import List, Optional

from app.entities import TipoServicio, TipoServicioCreate, TipoServicioUpdate
from app.services import tipo_servicio_service
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, BusinessRuleError
from app.presentation.components.shared.base_state import BaseState
from app.presentation.pages.tipo_servicio.tipo_servicio_validators import (
    validar_clave,
    validar_nombre,
    validar_descripcion,
)


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
    loading: bool = False
    saving: bool = False
    mostrar_modal_tipo: bool = False
    mostrar_modal_confirmar_eliminar: bool = False
    es_edicion: bool = False

    # Filtros
    filtro_busqueda: str = ""
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
    def set_filtro_busqueda(self, value: str):
        self.filtro_busqueda = value

    def set_incluir_inactivas(self, value: bool):
        self.incluir_inactivas = value

    def set_form_clave(self, value: str):
        """Set clave con auto-conversión a mayúsculas"""
        self.form_clave = value.upper() if value else ""

    def set_form_nombre(self, value: str):
        """Set nombre con auto-conversión a mayúsculas"""
        self.form_nombre = value.upper() if value else ""

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
        self.error_clave = validar_clave(self.form_clave)

    def validar_nombre_campo(self):
        """Validar nombre en tiempo real"""
        self.error_nombre = validar_nombre(self.form_nombre)

    def validar_descripcion_campo(self):
        """Validar descripción en tiempo real"""
        self.error_descripcion = validar_descripcion(self.form_descripcion)

    def validar_todos_los_campos(self):
        """Validar todos los campos del formulario"""
        self.validar_clave_campo()
        self.validar_nombre_campo()
        self.validar_descripcion_campo()

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

    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def cargar_tipos(self):
        """Cargar la lista de tipos de servicio"""
        self.loading = True
        try:
            # Obtener tipos según filtros
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

        except DatabaseError as e:
            self.mostrar_mensaje(f"Error al cargar tipos: {str(e)}", "error")
            self.tipos = []
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
            self.tipos = []
        finally:
            self.loading = False

    async def buscar_tipos(self):
        """Buscar tipos con el filtro actual"""
        await self.cargar_tipos()

    def handle_key_down(self, key: str):
        """Manejar tecla presionada en búsqueda"""
        if key == "Enter":
            return TipoServicioState.buscar_tipos

    def toggle_inactivas(self):
        """Alternar mostrar/ocultar inactivas y recargar"""
        self.incluir_inactivas = not self.incluir_inactivas
        return TipoServicioState.cargar_tipos

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
            await self.cargar_tipos()

        except DuplicateError as e:
            self.error_clave = f"La clave '{self.form_clave}' ya existe"
        except NotFoundError as e:
            self.mostrar_mensaje(str(e), "error")
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error de base de datos: {str(e)}", "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
        finally:
            self.saving = False

    async def _crear_tipo(self):
        """Crear nuevo tipo"""
        tipo_create = TipoServicioCreate(
            clave=self.form_clave.strip().upper(),
            nombre=self.form_nombre.strip().upper(),
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
            clave=self.form_clave.strip().upper(),
            nombre=self.form_nombre.strip().upper(),
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

        self.saving = True
        try:
            await tipo_servicio_service.eliminar(self.tipo_seleccionado["id"])

            self.cerrar_confirmar_eliminar()
            await self.cargar_tipos()

            return rx.toast.success(
                f"Tipo '{self.tipo_seleccionado['nombre']}' eliminado",
                position="top-center",
                duration=3000
            )

        except BusinessRuleError as e:
            self.mostrar_mensaje(str(e), "error")
        except NotFoundError as e:
            self.mostrar_mensaje(str(e), "error")
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error de base de datos: {str(e)}", "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
        finally:
            self.saving = False
            self.cerrar_confirmar_eliminar()

    async def activar_tipo(self, tipo: dict):
        """Activar un tipo inactivo"""
        try:
            await tipo_servicio_service.activar(tipo["id"])
            await self.cargar_tipos()

            return rx.toast.success(
                f"Tipo '{tipo['nombre']}' activado",
                position="top-center",
                duration=3000
            )

        except BusinessRuleError as e:
            self.mostrar_mensaje(str(e), "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error: {str(e)}", "error")

    # ========================
    # HELPERS PRIVADOS
    # ========================
    def _limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.form_clave = ""
        self.form_nombre = ""
        self.form_descripcion = ""
        self.error_clave = ""
        self.error_nombre = ""
        self.error_descripcion = ""
        self.tipo_seleccionado = None
        self.es_edicion = False
