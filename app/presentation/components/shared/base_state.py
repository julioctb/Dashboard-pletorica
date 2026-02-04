"""
Estado base para todos los módulos.

Incluye helpers para:
- Manejo centralizado de errores
- Reducir código repetitivo en los states de Reflex

Nota: Los setters deben definirse explícitamente en cada state.
Reflex no reconoce funciones asignadas dinámicamente como event handlers.
"""
import logging
import traceback
import reflex as rx
from typing import Optional

from app.core.config import Config

# Importar excepciones para manejo centralizado
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    DuplicateError,
    DatabaseError,
    BusinessRuleError,
)

logger = logging.getLogger(__name__)


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
            if Config.DEBUG:
                logger.error(f"{prefijo}{type(error).__name__}: {error}", exc_info=True)
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
            if Config.DEBUG:
                logger.error(f"{prefijo}{type(error).__name__}: {error}", exc_info=True)

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

    # ========================
    # CONVERSIÓN DE IDS
    # ========================
    @staticmethod
    def parse_id(value: str) -> Optional[int]:
        """
        Convierte un ID de string (rx.select) a int para servicios.

        rx.select requiere valores string, pero los servicios esperan int.
        Este helper centraliza la conversión para evitar int() dispersos.

        Args:
            value: ID como string desde un rx.select

        Returns:
            int si value es no vacío, None si vacío/falsy
        """
        return int(value) if value else None

    # ========================
    # OPERACIONES CRUD GENÉRICAS
    # ========================
    async def ejecutar_guardado(
        self,
        operacion,
        mensaje_exito: str,
        on_exito=None,
    ):
        """
        Ejecuta una operación de guardado con manejo de errores estándar.

        Patrón: saving=True → operación → toast success → on_exito → saving=False
        En caso de error: toast error → saving=False

        Args:
            operacion: Callable async que ejecuta la operación (crear, actualizar, etc.)
            mensaje_exito: Mensaje para el toast de éxito
            on_exito: Callable async opcional a ejecutar tras éxito (cerrar modal, recargar, etc.)

        Returns:
            rx.toast.success en éxito, rx.toast.error en fallo
        """
        self.saving = True
        try:
            resultado = await operacion()
            if on_exito:
                await on_exito()
            return rx.toast.success(mensaje_exito, position="top-center")
        except (DuplicateError, NotFoundError, BusinessRuleError, ValidationError) as e:
            return rx.toast.error(str(e), position="top-center")
        except DatabaseError as e:
            return rx.toast.error(
                f"Error de base de datos: {str(e)}", position="top-center"
            )
        except Exception as e:
            if Config.DEBUG:
                logger.error(f"Error inesperado en guardado: {type(e).__name__}: {e}", exc_info=True)
            return rx.toast.error(
                f"Error inesperado: {str(e)}", position="top-center"
            )
        finally:
            self.saving = False

    async def ejecutar_carga(
        self,
        operacion,
        contexto: str = "",
    ):
        """
        Ejecuta una operación de carga con manejo de loading y errores.

        Patrón: loading=True → operación → loading=False
        En caso de error: manejar_error → loading=False

        Args:
            operacion: Callable async que carga los datos
            contexto: Descripción para el mensaje de error

        Returns:
            Resultado de la operación, o None si falla
        """
        self.loading = True
        try:
            return await operacion()
        except Exception as e:
            if Config.DEBUG:
                logger.error(f"Error en carga ({contexto}): {type(e).__name__}: {e}", exc_info=True)
            self.manejar_error(e, contexto)
            return None
        finally:
            self.loading = False
