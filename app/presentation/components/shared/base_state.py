"""
Estado base para todos los módulos.

Incluye helpers para:
- Generar setters de forma declarativa
- Manejo centralizado de errores
- Reducir código repetitivo en los states de Reflex
"""
import reflex as rx
from typing import Callable, Optional, Any, Dict, Type
from contextlib import contextmanager

# Importar excepciones para manejo centralizado
from app.core.exceptions import (
    ApplicationError,
    ValidationError,
    NotFoundError,
    DuplicateError,
    DatabaseError,
    BusinessRuleError,
)


# ============================================================================
# HELPERS PARA GENERAR SETTERS
# ============================================================================

def crear_setter(campo: str, transformacion: Optional[Callable[[Any], Any]] = None):
    """
    Crea un setter simple para un campo de estado.

    Args:
        campo: Nombre del campo (sin prefijo 'form_')
        transformacion: Función opcional para transformar el valor antes de asignar

    Returns:
        Función setter que puede asignarse a una clase

    Ejemplo:
        class MiState(BaseState):
            form_nombre: str = ""
            form_monto: str = ""

            # Setters generados
            set_form_nombre = crear_setter("form_nombre")
            set_form_monto = crear_setter("form_monto", formatear_moneda)
    """
    def setter(self, value):
        if transformacion:
            value = transformacion(value)
        setattr(self, campo, value)
    return setter


def crear_setter_con_callback(
    campo: str,
    callback: Callable,
    transformacion: Optional[Callable[[Any], Any]] = None
):
    """
    Crea un setter que asigna el valor y retorna un event handler.

    Útil para filtros que deben recargar datos automáticamente.

    Args:
        campo: Nombre del campo
        callback: Event handler a retornar después de asignar
        transformacion: Función opcional para transformar el valor

    Returns:
        Función setter que retorna el callback

    Ejemplo:
        class MiState(BaseState):
            filtro_empresa: str = ""

            set_filtro_empresa = crear_setter_con_callback(
                "filtro_empresa",
                lambda: MiState.cargar_datos,
                lambda v: v if v else "0"
            )
    """
    def setter(self, value):
        if transformacion:
            value = transformacion(value)
        setattr(self, campo, value)
        return callback()
    return setter


def crear_setter_upper(campo: str):
    """
    Crea un setter que convierte el valor a mayúsculas.

    Args:
        campo: Nombre del campo

    Ejemplo:
        set_form_codigo = crear_setter_upper("form_codigo")
    """
    def setter(self, value):
        setattr(self, campo, value.upper() if value else "")
    return setter


def crear_setter_strip(campo: str):
    """
    Crea un setter que limpia espacios del valor.

    Args:
        campo: Nombre del campo

    Ejemplo:
        set_form_nombre = crear_setter_strip("form_nombre")
    """
    def setter(self, value):
        setattr(self, campo, value.strip() if value else "")
    return setter


def crear_setter_numerico(campo: str):
    """
    Crea un setter que solo permite dígitos.

    Args:
        campo: Nombre del campo

    Ejemplo:
        set_form_cantidad = crear_setter_numerico("form_cantidad")
    """
    def setter(self, value):
        limpio = ''.join(c for c in str(value) if c.isdigit())
        setattr(self, campo, limpio)
    return setter


# ============================================================================
# ESTADO BASE
# ============================================================================

class BaseState(rx.State):
    """Estado base con funcionalidad común para todos los módulos"""

    # ========================
    # ESTADO DE CARGA
    # ========================
    loading: bool = True  # Inicia en True para mostrar skeleton
    saving: bool = False

    # ========================
    # FILTROS COMUNES
    # ========================
    filtro_busqueda: str = ""

    # ========================
    # MENSAJES
    # ========================
    mensaje_info: str = ""
    tipo_mensaje: str = "info"  # info, success, error

    # ========================
    # SETTERS COMUNES
    # ========================
    def set_filtro_busqueda(self, value: str):
        """Setter para filtro de búsqueda"""
        self.filtro_busqueda = value

    def set_saving(self, value: bool):
        """Setter para estado de guardado"""
        self.saving = value

    # ========================
    # MENSAJES
    # ========================
    def mostrar_mensaje(self, mensaje: str, tipo: str = "info"):
        """Mostrar mensaje informativo"""
        self.mensaje_info = mensaje
        self.tipo_mensaje = tipo

    def limpiar_mensajes(self):
        """Limpiar mensajes informativos"""
        self.mensaje_info = ""
        self.tipo_mensaje = "info"

    # ========================
    # MANEJO DE ERRORES
    # ========================
    def manejar_error(
        self,
        error: Exception,
        contexto: str = "",
        campo_duplicado: Optional[str] = None,
        valor_duplicado: Optional[str] = None,
    ) -> Optional[rx.Component]:
        """
        Maneja errores de operaciones de forma centralizada.

        Este método procesa diferentes tipos de excepciones y muestra
        mensajes apropiados al usuario. Reduce código repetitivo en
        los bloques try/except de los states.

        Args:
            error: La excepción capturada
            contexto: Descripción opcional para el mensaje (ej: "al guardar")
            campo_duplicado: Atributo donde asignar error de duplicado (ej: "error_clave")
            valor_duplicado: Valor a mostrar en mensaje de duplicado

        Returns:
            None - Solo muestra mensaje y actualiza estado

        Ejemplo:
            try:
                await servicio.crear(entidad)
            except Exception as e:
                self.manejar_error(e, "al crear", campo_duplicado="error_codigo")

        Patrones de manejo:
            - DuplicateError: Asigna a campo_duplicado o muestra mensaje
            - NotFoundError: Muestra mensaje del error
            - BusinessRuleError: Muestra mensaje del error
            - ValidationError: Muestra "Error de validación: ..."
            - DatabaseError: Muestra "Error de base de datos: ..."
            - Exception: Muestra "Error inesperado: ..."
        """
        prefijo = f"Error {contexto}: " if contexto else ""

        if isinstance(error, DuplicateError):
            if campo_duplicado:
                # Asignar error al campo específico del formulario
                valor = valor_duplicado or error.value or ""
                mensaje = f"Ya existe: {valor}" if valor else "Este valor ya existe"
                setattr(self, campo_duplicado, mensaje)
            else:
                self.mostrar_mensaje(f"{prefijo}{str(error)}", "error")

        elif isinstance(error, NotFoundError):
            self.mostrar_mensaje(f"{prefijo}{str(error)}", "error")

        elif isinstance(error, BusinessRuleError):
            self.mostrar_mensaje(f"{prefijo}{str(error)}", "error")

        elif isinstance(error, ValidationError):
            self.mostrar_mensaje(f"{prefijo}Error de validación: {str(error)}", "error")

        elif isinstance(error, DatabaseError):
            self.mostrar_mensaje(f"{prefijo}Error de base de datos: {str(error)}", "error")

        else:
            # Error inesperado
            self.mostrar_mensaje(f"{prefijo}Error inesperado: {str(error)}", "error")

        return None

    def manejar_error_con_toast(
        self,
        error: Exception,
        contexto: str = "",
    ) -> rx.Component:
        """
        Maneja errores y retorna un toast de error.

        Similar a manejar_error pero retorna un rx.toast.error
        en lugar de usar mostrar_mensaje. Útil para métodos que
        deben retornar un componente.

        Args:
            error: La excepción capturada
            contexto: Descripción opcional para el mensaje

        Returns:
            rx.toast.error con el mensaje apropiado

        Ejemplo:
            try:
                await servicio.crear(entidad)
                return rx.toast.success("Creado")
            except Exception as e:
                return self.manejar_error_con_toast(e, "al crear")
        """
        prefijo = f"Error {contexto}: " if contexto else ""

        if isinstance(error, DuplicateError):
            mensaje = f"{prefijo}Ya existe: {error.value}" if error.value else f"{prefijo}Este valor ya existe"
        elif isinstance(error, (NotFoundError, BusinessRuleError)):
            mensaje = f"{prefijo}{str(error)}"
        elif isinstance(error, ValidationError):
            mensaje = f"{prefijo}Error de validación: {str(error)}"
        elif isinstance(error, DatabaseError):
            mensaje = f"{prefijo}Error de base de datos: {str(error)}"
        else:
            mensaje = f"{prefijo}Error inesperado: {str(error)}"

        return rx.toast.error(mensaje, position="top-center")

    def iniciar_guardado(self):
        """Inicia estado de guardado (saving=True)"""
        self.saving = True

    def finalizar_guardado(self):
        """Finaliza estado de guardado (saving=False)"""
        self.saving = False

    def iniciar_carga(self):
        """Inicia estado de carga (loading=True)"""
        self.loading = True

    def finalizar_carga(self):
        """Finaliza estado de carga (loading=False)"""
        self.loading = False
