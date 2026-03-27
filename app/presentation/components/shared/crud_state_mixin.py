"""
CRUD State Mixin - Funcionalidad común para estados CRUD.

Proporciona:
- Gestión de modales (abrir/cerrar con callbacks)
- Operaciones CRUD genéricas con manejo de errores
- Gestión de selección de items
- Validación de formularios

Uso:
    class MiModuloState(BaseState, CRUDStateMixin):
        # Configuración del mixin
        _entidad_nombre = "Empleado"
        _modal_principal = "mostrar_modal_empleado"

        async def crear_empleado(self):
            return await self.ejecutar_crear(
                crear_fn=lambda: empleado_service.crear(self._construir_entidad()),
                on_exito=self._on_crear_exito
            )
"""
import logging
from typing import Optional, Callable, Any, Dict, List
import reflex as rx

from app.core.config import Config
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    DuplicateError,
    DatabaseError,
    BusinessRuleError,
)

logger = logging.getLogger(__name__)


class CRUDStateMixin:
    """
    Mixin con funcionalidad CRUD reutilizable.

    Atributos de configuración (definir en subclase):
        _entidad_nombre: str - Nombre para mensajes (ej: "Empleado")
        _modal_principal: str - Nombre del var del modal principal
        _campos_formulario: Dict[str, Any] - Defaults para form_*
        _campos_error: List[str] - Campos con error_*
    """

    # Configuración por defecto (override en subclase)
    _entidad_nombre: str = "Registro"
    _modal_principal: str = "mostrar_modal"
    _campos_formulario: Dict[str, Any] = {}
    _campos_error: List[str] = []

    # =========================================================================
    # GESTIÓN DE MODALES
    # =========================================================================

    def abrir_modal(
        self,
        modal_var: Optional[str] = None,
        limpiar_form: bool = True,
        es_edicion: bool = False,
        on_open: Optional[Callable] = None
    ):
        """
        Abre un modal con setup opcional.

        Args:
            modal_var: Nombre del var del modal (default: _modal_principal)
            limpiar_form: Si True, limpia el formulario antes de abrir
            es_edicion: Valor para self.es_edicion
            on_open: Callback a ejecutar antes de abrir
        """
        if limpiar_form:
            self._limpiar_formulario_crud()

        if hasattr(self, 'es_edicion'):
            self.es_edicion = es_edicion

        if on_open:
            on_open()

        modal = modal_var or self._modal_principal
        if hasattr(self, modal):
            setattr(self, modal, True)

    def cerrar_modal(
        self,
        modal_var: Optional[str] = None,
        limpiar_form: bool = True,
        on_close: Optional[Callable] = None
    ):
        """
        Cierra un modal con cleanup opcional.

        Args:
            modal_var: Nombre del var del modal (default: _modal_principal)
            limpiar_form: Si True, limpia el formulario al cerrar
            on_close: Callback a ejecutar después de cerrar
        """
        modal = modal_var or self._modal_principal
        if hasattr(self, modal):
            setattr(self, modal, False)

        if limpiar_form:
            self._limpiar_formulario_crud()

        if on_close:
            on_close()

    def _limpiar_formulario_crud(self):
        """Limpia formulario usando configuración del mixin."""
        # Limpiar campos de formulario
        for campo, valor in self._campos_formulario.items():
            if hasattr(self, f"form_{campo}"):
                setattr(self, f"form_{campo}", valor)

        # Limpiar errores
        for campo in self._campos_error:
            if hasattr(self, f"error_{campo}"):
                setattr(self, f"error_{campo}", "")

        # Limpiar estado de edición
        if hasattr(self, 'es_edicion'):
            self.es_edicion = False
        if hasattr(self, 'id_edicion'):
            self.id_edicion = 0

    # =========================================================================
    # OPERACIONES CRUD
    # =========================================================================

    async def ejecutar_crear(
        self,
        crear_fn: Callable,
        on_exito: Optional[Callable] = None,
        mensaje_exito: Optional[str] = None,
        cerrar_modal: bool = True
    ):
        """
        Ejecuta operación de creación con manejo estándar.

        Args:
            crear_fn: Función async que ejecuta la creación
            on_exito: Callback async tras éxito (ej: recargar lista)
            mensaje_exito: Mensaje personalizado (default: "{Entidad} creado")
            cerrar_modal: Si True, cierra el modal al terminar

        Returns:
            rx.toast con resultado
        """
        if hasattr(self, 'saving'):
            self.saving = True

        try:
            resultado = await crear_fn()

            if cerrar_modal:
                self.cerrar_modal()

            if on_exito:
                await on_exito()

            msg = mensaje_exito or f"{self._entidad_nombre} creado exitosamente"
            return rx.toast.success(msg, position="top-center")

        except DuplicateError as e:
            return self._manejar_error_crud(e, "crear")
        except ValidationError as e:
            return rx.toast.error(f"Error de validación: {e}", position="top-center")
        except DatabaseError as e:
            return rx.toast.error(f"Error de base de datos: {e}", position="top-center")
        except Exception as e:
            return self._manejar_error_crud(e, "crear")
        finally:
            if hasattr(self, 'saving'):
                self.saving = False

    async def ejecutar_actualizar(
        self,
        actualizar_fn: Callable,
        on_exito: Optional[Callable] = None,
        mensaje_exito: Optional[str] = None,
        cerrar_modal: bool = True
    ):
        """
        Ejecuta operación de actualización con manejo estándar.

        Args:
            actualizar_fn: Función async que ejecuta la actualización
            on_exito: Callback async tras éxito
            mensaje_exito: Mensaje personalizado
            cerrar_modal: Si True, cierra el modal al terminar

        Returns:
            rx.toast con resultado
        """
        if hasattr(self, 'saving'):
            self.saving = True

        try:
            resultado = await actualizar_fn()

            if cerrar_modal:
                self.cerrar_modal()

            if on_exito:
                await on_exito()

            msg = mensaje_exito or f"{self._entidad_nombre} actualizado exitosamente"
            return rx.toast.success(msg, position="top-center")

        except NotFoundError as e:
            return rx.toast.error(str(e), position="top-center")
        except DuplicateError as e:
            return self._manejar_error_crud(e, "actualizar")
        except ValidationError as e:
            return rx.toast.error(f"Error de validación: {e}", position="top-center")
        except DatabaseError as e:
            return rx.toast.error(f"Error de base de datos: {e}", position="top-center")
        except Exception as e:
            return self._manejar_error_crud(e, "actualizar")
        finally:
            if hasattr(self, 'saving'):
                self.saving = False

    async def ejecutar_eliminar(
        self,
        eliminar_fn: Callable,
        on_exito: Optional[Callable] = None,
        mensaje_exito: Optional[str] = None,
        cerrar_modal: bool = True,
        modal_confirmacion: Optional[str] = None
    ):
        """
        Ejecuta operación de eliminación con manejo estándar.

        Args:
            eliminar_fn: Función async que ejecuta la eliminación
            on_exito: Callback async tras éxito
            mensaje_exito: Mensaje personalizado
            cerrar_modal: Si True, cierra modales al terminar
            modal_confirmacion: Nombre del modal de confirmación a cerrar

        Returns:
            rx.toast con resultado
        """
        if hasattr(self, 'saving'):
            self.saving = True

        try:
            resultado = await eliminar_fn()

            # Cerrar modal de confirmación si existe
            if modal_confirmacion and hasattr(self, modal_confirmacion):
                setattr(self, modal_confirmacion, False)

            if cerrar_modal:
                self.cerrar_modal()

            if on_exito:
                await on_exito()

            msg = mensaje_exito or f"{self._entidad_nombre} eliminado exitosamente"
            return rx.toast.success(msg, position="top-center")

        except NotFoundError as e:
            return rx.toast.error(str(e), position="top-center")
        except BusinessRuleError as e:
            return rx.toast.error(str(e), position="top-center")
        except DatabaseError as e:
            return rx.toast.error(f"Error de base de datos: {e}", position="top-center")
        except Exception as e:
            return self._manejar_error_crud(e, "eliminar")
        finally:
            if hasattr(self, 'saving'):
                self.saving = False

    async def ejecutar_carga_lista(
        self,
        cargar_fn: Callable,
        campo_destino: str,
        transformar: Optional[Callable] = None
    ):
        """
        Carga una lista de items con manejo de loading.

        Args:
            cargar_fn: Función async que retorna lista de items
            campo_destino: Nombre del atributo donde guardar
            transformar: Función para transformar cada item
        """
        if hasattr(self, 'loading'):
            self.loading = True

        try:
            items = await cargar_fn()

            if transformar:
                datos = [transformar(item) for item in items]
            else:
                datos = [
                    item.model_dump(mode='json') if hasattr(item, 'model_dump') else item
                    for item in items
                ]

            setattr(self, campo_destino, datos)

        except Exception as e:
            logger.error(f"Error cargando {campo_destino}: {e}")
            setattr(self, campo_destino, [])
            if hasattr(self, 'mostrar_mensaje'):
                self.mostrar_mensaje(f"Error cargando datos: {e}", "error")

        finally:
            if hasattr(self, 'loading'):
                self.loading = False

    # =========================================================================
    # SELECCIÓN DE ITEMS
    # =========================================================================

    def seleccionar_item(
        self,
        item: dict,
        campo_seleccionado: str = "item_seleccionado",
        abrir_modal: Optional[str] = None
    ):
        """
        Selecciona un item y opcionalmente abre un modal.

        Args:
            item: Dict con datos del item
            campo_seleccionado: Nombre del atributo donde guardar
            abrir_modal: Nombre del modal a abrir (opcional)
        """
        if not item or not isinstance(item, dict):
            return

        setattr(self, campo_seleccionado, item)

        if abrir_modal and hasattr(self, abrir_modal):
            setattr(self, abrir_modal, True)

    def deseleccionar_item(
        self,
        campo_seleccionado: str = "item_seleccionado",
        cerrar_modal: Optional[str] = None
    ):
        """
        Limpia selección y opcionalmente cierra modal.

        Args:
            campo_seleccionado: Nombre del atributo a limpiar
            cerrar_modal: Nombre del modal a cerrar (opcional)
        """
        setattr(self, campo_seleccionado, None)

        if cerrar_modal and hasattr(self, cerrar_modal):
            setattr(self, cerrar_modal, False)

    # =========================================================================
    # MANEJO DE ERRORES
    # =========================================================================

    def _manejar_error_crud(self, error: Exception, operacion: str):
        """
        Maneja errores de operaciones CRUD.

        Args:
            error: Excepción capturada
            operacion: Nombre de la operación ("crear", "actualizar", etc.)

        Returns:
            rx.toast.error con mensaje apropiado
        """
        if Config.DEBUG:
            logger.error(f"Error en {operacion} {self._entidad_nombre}: {error}", exc_info=True)

        if isinstance(error, DuplicateError):
            msg = f"Ya existe un {self._entidad_nombre.lower()} con esos datos"
            if error.field:
                msg = f"El campo {error.field} ya existe"
        else:
            msg = f"Error al {operacion}: {str(error)}"

        return rx.toast.error(msg, position="top-center")

    # =========================================================================
    # VALIDACIÓN
    # =========================================================================

    def validar_campo(
        self,
        campo: str,
        valor: Any,
        validador: Callable[[Any], str],
        error_field: Optional[str] = None
    ) -> bool:
        """
        Valida un campo y asigna error si falla.

        Args:
            campo: Nombre del campo (para mensajes)
            valor: Valor a validar
            validador: Función que retorna "" si ok, mensaje de error si falla
            error_field: Nombre del campo error_* (default: error_{campo})

        Returns:
            True si válido, False si hay error
        """
        error_msg = validador(valor)
        error_attr = error_field or f"error_{campo}"

        if hasattr(self, error_attr):
            setattr(self, error_attr, error_msg)

        return error_msg == ""

    def validar_formulario(
        self,
        validaciones: List[tuple]
    ) -> bool:
        """
        Ejecuta múltiples validaciones.

        Args:
            validaciones: Lista de (campo, valor, validador, error_field)

        Returns:
            True si todas pasan, False si alguna falla
        """
        todos_validos = True

        for validacion in validaciones:
            campo, valor, validador = validacion[:3]
            error_field = validacion[3] if len(validacion) > 3 else None

            if not self.validar_campo(campo, valor, validador, error_field):
                todos_validos = False

        return todos_validos

    def tiene_errores(self) -> bool:
        """
        Verifica si hay errores en los campos configurados.

        Returns:
            True si algún campo error_* tiene valor
        """
        for campo in self._campos_error:
            error_attr = f"error_{campo}"
            if hasattr(self, error_attr) and getattr(self, error_attr):
                return True
        return False
