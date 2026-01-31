"""
Estado base para todos los módulos.

Incluye helpers para:
- Manejo centralizado de errores
- Reducir código repetitivo en los states de Reflex

Nota: Los setters deben definirse explícitamente en cada state.
Reflex no reconoce funciones asignadas dinámicamente como event handlers.
"""
import reflex as rx
from typing import Optional

# Importar excepciones para manejo centralizado
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    DuplicateError,
    DatabaseError,
    BusinessRuleError,
)


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
