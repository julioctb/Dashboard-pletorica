"""
Estado de Reflex para el módulo de Categorías de Puesto.
Maneja el estado de la UI y las operaciones del módulo.
"""
import reflex as rx
from typing import List, Optional

from app.core.text_utils import normalizar_mayusculas
from app.core.utils import generar_candidatos_codigo
from app.entities.categoria_puesto import (
    CategoriaPuestoCreate,
    CategoriaPuestoUpdate,
)
from app.services import categoria_puesto_service, tipo_servicio_service
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, BusinessRuleError
from app.presentation.components.shared.base_state import BaseState
from app.presentation.pages.categorias_puesto.categorias_puesto_validators import (
    validar_clave,
    validar_nombre,
    validar_descripcion,
    validar_orden,
    validar_tipo_servicio_id,
)


class CategoriasPuestoState(BaseState):
    """Estado para el módulo de Categorías de Puesto"""

    # ========================
    # ESTADO DE DATOS
    # ========================
    categorias: List[dict] = []
    categoria_seleccionada: Optional[dict] = None
    total_categorias: int = 0

    # Tipos de servicio para el dropdown
    tipos_servicio: List[dict] = []

    # ========================
    # ESTADO DE UI
    # ========================
    # loading, saving, filtro_busqueda vienen de BaseState
    mostrar_modal_categoria: bool = False
    mostrar_modal_confirmar_eliminar: bool = False
    es_edicion: bool = False

    # Vista (tabla/cards)
    view_mode: str = "table"

    # Filtros (filtro_busqueda viene de BaseState)
    filtro_tipo_servicio_id: str = "0"  # "0" = todos, string para rx.select
    incluir_inactivas: bool = False

    # ========================
    # ESTADO DEL FORMULARIO
    # ========================
    form_tipo_servicio_id: str = ""  # String para compatibilidad con rx.select
    form_clave: str = ""
    form_nombre: str = ""
    form_descripcion: str = ""
    form_orden: str = "0"

    # Errores de validación
    error_tipo_servicio_id: str = ""
    error_clave: str = ""
    error_nombre: str = ""
    error_descripcion: str = ""
    error_orden: str = ""

    # ========================
    # SETTERS EXPLÍCITOS (Reflex 0.8.9+)
    # ========================
    # set_filtro_busqueda viene de BaseState

    async def on_change_busqueda(self, value: str):
        """Actualizar filtro y buscar automáticamente"""
        self.filtro_busqueda = value
        await self._fetch_categorias()

    def set_filtro_tipo_servicio_id(self, value: str):
        self.filtro_tipo_servicio_id = value if value else "0"
        return CategoriasPuestoState.filtrar_por_tipo  # Auto-filtrar al cambiar

    def set_incluir_inactivas(self, value: bool):
        self.incluir_inactivas = value

    # --- Vista (tabla/cards) ---
    def set_view_table(self):
        self.view_mode = "table"

    def set_view_cards(self):
        self.view_mode = "cards"

    def toggle_view(self):
        self.view_mode = "cards" if self.view_mode == "table" else "table"

    @rx.var
    def is_table_view(self) -> bool:
        return self.view_mode == "table"

    @rx.var
    def is_cards_view(self) -> bool:
        return self.view_mode == "cards"

    def set_form_tipo_servicio_id(self, value: str):
        self.form_tipo_servicio_id = value  # Mantener como string

    def set_form_clave(self, value: str):
        self.form_clave = normalizar_mayusculas(value)

    async def set_form_nombre(self, value: str):
        """Set nombre con auto-conversión a mayúsculas y auto-sugerir clave única"""
        self.form_nombre = normalizar_mayusculas(value)
        # Auto-sugerir clave si está vacía, no es edición y hay tipo seleccionado
        if not self.form_clave and not self.es_edicion and value and self.form_tipo_servicio_id:
            candidatos = generar_candidatos_codigo(value)
            tipo_id = self.parse_id(self.form_tipo_servicio_id)
            for clave in candidatos[:10]:  # Probar máximo 10 candidatos
                clave_corta = clave[:5]  # Máximo 5 caracteres
                if not await categoria_puesto_service.existe_clave_en_tipo(tipo_id, clave_corta):
                    self.form_clave = clave_corta
                    break

    def set_form_descripcion(self, value: str):
        self.form_descripcion = value

    def set_form_orden(self, value: str):
        self.form_orden = value

    def set_mostrar_modal_categoria(self, value: bool):
        self.mostrar_modal_categoria = value

    def set_mostrar_modal_confirmar_eliminar(self, value: bool):
        self.mostrar_modal_confirmar_eliminar = value

    # ========================
    # VALIDACIÓN EN TIEMPO REAL
    # ========================
    def validar_tipo_servicio_campo(self):
        self.error_tipo_servicio_id = validar_tipo_servicio_id(self.form_tipo_servicio_id)

    def validar_clave_campo(self):
        self.error_clave = validar_clave(self.form_clave)

    def validar_nombre_campo(self):
        self.error_nombre = validar_nombre(self.form_nombre)

    def validar_descripcion_campo(self):
        self.error_descripcion = validar_descripcion(self.form_descripcion)

    def validar_orden_campo(self):
        self.error_orden = validar_orden(self.form_orden)

    def validar_todos_los_campos(self):
        self.validar_tipo_servicio_campo()
        self.validar_clave_campo()
        self.validar_nombre_campo()
        self.validar_descripcion_campo()
        self.validar_orden_campo()

    @rx.var
    def tiene_errores_formulario(self) -> bool:
        return bool(
            self.error_tipo_servicio_id or
            self.error_clave or
            self.error_nombre or
            self.error_descripcion or
            self.error_orden
        )

    @rx.var
    def puede_guardar(self) -> bool:
        tiene_datos = bool(self.form_tipo_servicio_id) and bool(self.form_clave) and bool(self.form_nombre)
        return tiene_datos and not self.tiene_errores_formulario and not self.saving

    @rx.var
    def opciones_tipo_servicio(self) -> List[dict]:
        """Opciones formateadas para el select de tipo de servicio"""
        return [{"value": str(t["id"]), "label": f"{t['clave']} - {t['nombre']}"} for t in self.tipos_servicio]

    @rx.var
    def tiene_filtros_activos(self) -> bool:
        """Indica si hay algún filtro aplicado"""
        return (
            self.filtro_tipo_servicio_id != "0" or
            bool(self.filtro_busqueda.strip()) or
            self.incluir_inactivas
        )

    @rx.var
    def mostrar_tabla(self) -> bool:
        """Muestra tabla si hay categorías O si hay filtro activo"""
        return self.total_categorias > 0 or bool(self.filtro_busqueda.strip())

    @rx.var
    def nombre_tipo_filtrado(self) -> str:
        """Nombre del tipo de servicio seleccionado en el filtro"""
        if self.filtro_tipo_servicio_id == "0":
            return "Todos"
        for t in self.tipos_servicio:
            if str(t["id"]) == self.filtro_tipo_servicio_id:
                return t["nombre"]
        return "Todos"

    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def cargar_datos_iniciales(self):
        """Cargar tipos de servicio y categorías"""
        # Leer parámetro ?tipo=X de la URL (Reflex 0.8.9+)
        tipo_param = self.router.url.query_parameters.get("tipo", "")
        if tipo_param:
            self.filtro_tipo_servicio_id = tipo_param

        async for _ in self._montar_pagina(
            self.cargar_tipos_servicio,
            self._fetch_categorias,
        ):
            yield

    async def cargar_tipos_servicio(self):
        """Cargar tipos de servicio para el dropdown"""
        try:
            tipos = await tipo_servicio_service.obtener_activas()
            self.tipos_servicio = [t.model_dump() for t in tipos]
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar tipos de servicio: {str(e)}", "error")
            self.tipos_servicio = []

    async def _fetch_categorias(self):
        """Carga categorías desde BD (sin manejo de loading)."""
        try:
            # Si hay filtro de tipo (distinto de "0"), obtener solo de ese tipo
            if self.filtro_tipo_servicio_id and self.filtro_tipo_servicio_id != "0":
                categorias = await categoria_puesto_service.obtener_por_tipo_servicio(
                    int(self.filtro_tipo_servicio_id),
                    incluir_inactivas=self.incluir_inactivas
                )
            else:
                categorias = await categoria_puesto_service.obtener_todas(
                    incluir_inactivas=self.incluir_inactivas
                )

            # Filtrar por búsqueda si hay término
            if self.filtro_busqueda:
                termino = self.filtro_busqueda.upper()
                categorias = [
                    c for c in categorias
                    if termino in c.clave.upper() or termino in c.nombre.upper()
                ]

            self.categorias = [cat.model_dump() for cat in categorias]
            self.total_categorias = len(self.categorias)

        except DatabaseError as e:
            self.mostrar_mensaje(f"Error al cargar categorías: {str(e)}", "error")
            self.categorias = []
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
            self.categorias = []

    async def cargar_categorias(self):
        """Carga categorías con skeleton loading (público)."""
        async for _ in self._recargar_datos(self._fetch_categorias):
            yield

    async def buscar_categorias(self):
        await self.cargar_categorias()

    def handle_key_down(self, key: str):
        if key == "Enter":
            return CategoriasPuestoState.buscar_categorias

    def toggle_inactivas(self, value: bool = None):
        """Toggle o establecer el estado de incluir inactivas"""
        if value is not None:
            self.incluir_inactivas = value
        else:
            self.incluir_inactivas = not self.incluir_inactivas
        return CategoriasPuestoState.cargar_categorias

    def limpiar_busqueda(self):
        """Limpia el campo de búsqueda y recarga"""
        self.filtro_busqueda = ""
        return CategoriasPuestoState.cargar_categorias

    def limpiar_filtros(self):
        """Limpia todos los filtros y recarga"""
        self.filtro_busqueda = ""
        self.filtro_tipo_servicio_id = "0"
        self.incluir_inactivas = False
        return CategoriasPuestoState.cargar_categorias

    async def filtrar_por_tipo(self):
        """Recargar categorías cuando cambia el filtro de tipo"""
        await self._fetch_categorias()

    # ========================
    # OPERACIONES CRUD
    # ========================
    def abrir_modal_crear(self):
        self._limpiar_formulario()
        self.es_edicion = False
        # Auto-seleccionar tipo si hay filtro activo
        if self.filtro_tipo_servicio_id and self.filtro_tipo_servicio_id != "0":
            self.form_tipo_servicio_id = self.filtro_tipo_servicio_id
        self.mostrar_modal_categoria = True

    def abrir_modal_editar(self, categoria: dict):
        self._limpiar_formulario()
        self.es_edicion = True
        self.categoria_seleccionada = categoria

        # Cargar datos en el formulario (tipo_servicio_id como string para el select)
        self.form_tipo_servicio_id = str(categoria.get("tipo_servicio_id", ""))
        self.form_clave = categoria.get("clave", "")
        self.form_nombre = categoria.get("nombre", "")
        self.form_descripcion = categoria.get("descripcion", "") or ""
        self.form_orden = str(categoria.get("orden", 0))

        self.mostrar_modal_categoria = True

    def cerrar_modal_categoria(self):
        self.mostrar_modal_categoria = False
        self._limpiar_formulario()

    def abrir_confirmar_eliminar(self, categoria: dict):
        self.categoria_seleccionada = categoria
        self.mostrar_modal_confirmar_eliminar = True

    def cerrar_confirmar_eliminar(self):
        self.mostrar_modal_confirmar_eliminar = False
        self.categoria_seleccionada = None

    async def guardar_categoria(self):
        self.validar_todos_los_campos()
        if self.tiene_errores_formulario:
            return

        self.saving = True
        try:
            if self.es_edicion:
                await self._actualizar_categoria()
            else:
                await self._crear_categoria()

            self.cerrar_modal_categoria()
            await self._fetch_categorias()

        except DuplicateError:
            self.error_clave = f"La clave '{self.form_clave}' ya existe en este tipo de servicio"
        except NotFoundError as e:
            self.mostrar_mensaje(str(e), "error")
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error de base de datos: {str(e)}", "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
        finally:
            self.saving = False

    async def _crear_categoria(self):
        categoria_create = CategoriaPuestoCreate(
            tipo_servicio_id=self.parse_id(self.form_tipo_servicio_id),
            clave=normalizar_mayusculas(self.form_clave),
            nombre=normalizar_mayusculas(self.form_nombre),
            descripcion=self.form_descripcion.strip() if self.form_descripcion else None,
            orden=int(self.form_orden) if self.form_orden else 0
        )

        await categoria_puesto_service.crear(categoria_create)

        return rx.toast.success(
            f"Categoría '{categoria_create.nombre}' creada exitosamente",
            position="top-center",
            duration=3000
        )

    async def _actualizar_categoria(self):
        if not self.categoria_seleccionada:
            return

        categoria_update = CategoriaPuestoUpdate(
            tipo_servicio_id=self.parse_id(self.form_tipo_servicio_id),
            clave=normalizar_mayusculas(self.form_clave),
            nombre=normalizar_mayusculas(self.form_nombre),
            descripcion=self.form_descripcion.strip() if self.form_descripcion else None,
            orden=int(self.form_orden) if self.form_orden else 0
        )

        await categoria_puesto_service.actualizar(
            self.categoria_seleccionada["id"],
            categoria_update
        )

        return rx.toast.success(
            f"Categoría '{categoria_update.nombre}' actualizada exitosamente",
            position="top-center",
            duration=3000
        )

    async def eliminar_categoria(self):
        if not self.categoria_seleccionada:
            return

        # Guardar nombre antes de limpiar
        nombre_categoria = self.categoria_seleccionada["nombre"]
        categoria_id = self.categoria_seleccionada["id"]

        self.saving = True
        try:
            await categoria_puesto_service.eliminar(categoria_id)

            self.cerrar_confirmar_eliminar()
            await self._fetch_categorias()

            return rx.toast.success(
                f"Categoría '{nombre_categoria}' eliminada",
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

    async def activar_categoria(self, categoria: dict):
        try:
            await categoria_puesto_service.activar(categoria["id"])
            await self._fetch_categorias()

            return rx.toast.success(
                f"Categoría '{categoria['nombre']}' activada",
                position="top-center",
                duration=3000
            )

        except BusinessRuleError as e:
            self.mostrar_mensaje(str(e), "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error: {str(e)}", "error")

    # ========================
    # HELPERS
    # ========================
    def _limpiar_formulario(self):
        self.form_tipo_servicio_id = ""
        self.form_clave = ""
        self.form_nombre = ""
        self.form_descripcion = ""
        self.form_orden = "0"
        self.error_tipo_servicio_id = ""
        self.error_clave = ""
        self.error_nombre = ""
        self.error_descripcion = ""
        self.error_orden = ""
        self.categoria_seleccionada = None
        self.es_edicion = False

    def obtener_nombre_tipo(self, tipo_servicio_id: int) -> str:
        """Obtener nombre del tipo de servicio por ID"""
        for tipo in self.tipos_servicio:
            if tipo["id"] == tipo_servicio_id:
                return f"{tipo['clave']} - {tipo['nombre']}"
        return "Desconocido"
