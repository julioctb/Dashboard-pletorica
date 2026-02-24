"""
Estado base para todos los módulos.

Incluye helpers para:
- Manejo centralizado de errores
- Carga de catálogos genérica
- Limpieza de formularios
- Manejo de filtros y paginación
- Reducir código repetitivo en los states de Reflex

Nota: Los setters deben definirse explícitamente en cada state.
Reflex no reconoce funciones asignadas dinámicamente como event handlers.
"""
import logging
import reflex as rx
from typing import Optional, List, Dict, Any, Callable, Awaitable

from app.core.config import Config
from app.core.ui_helpers import (
    FILTRO_TODOS,
    FILTRO_SIN_SELECCION,
    calcular_paginas,
    calcular_offset,
    es_filtro_activo as es_filtro_activo_ui,
)

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

    # Tracking de módulos ya montados (backend-only, no se envía al cliente)
    _modulos_montados: List[str] = []

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
    # PATRÓN DE CARGA CON SKELETON
    # ========================

    async def _montar_pagina(self, *operaciones):
        """
        Patrón centralizado de carga con skeleton para on_mount.

        - Primera visita: loading=True → yield (skeleton) → fetch → loading=False → yield (datos)
        - Revisita: fetch silencioso → loading=False → yield (datos actualizados sin skeleton)

        Uso en cada módulo:
            async def on_mount(self):
                async for _ in self._montar_pagina(
                    self._fetch_datos,
                    self._cargar_catalogos,
                ):
                    yield

        Args:
            *operaciones: Callables async a ejecutar (fetch principal, catálogos, etc.)
        """
        self.limpiar_mensajes()

        modulo = type(self).__name__
        es_primera_carga = modulo not in self._modulos_montados

        if es_primera_carga:
            self.loading = True
            yield  # UI muestra skeleton

        # Ejecutar operaciones de carga
        for op in operaciones:
            await op()

        # Finalizar carga
        self.loading = False
        if es_primera_carga:
            self._modulos_montados = self._modulos_montados + [modulo]
        yield

    async def _recargar_datos(self, *operaciones):
        """
        Recarga datos con skeleton (para filtros, refresh manual, etc.).

        Siempre muestra skeleton independientemente de si ya hay datos.

        Uso:
            async def aplicar_filtros(self):
                async for _ in self._recargar_datos(self._fetch_datos):
                    yield

        Args:
            *operaciones: Callables async a ejecutar.
        """
        self.loading = True
        yield

        for op in operaciones:
            await op()

        self.loading = False
        yield

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

    # ========================
    # CARGA DE CATÁLOGOS
    # ========================
    async def cargar_catalogo(
        self,
        campo_destino: str,
        servicio_metodo: Callable[..., Awaitable[List[Any]]],
        transformar: Optional[Callable[[Any], dict]] = None,
        **kwargs
    ) -> List[dict]:
        """
        Carga un catálogo desde un servicio y lo asigna a un campo.

        Patrón común: cargar lista de empresas, categorías, tipos, etc.
        para usar en selects.

        Args:
            campo_destino: Nombre del atributo donde guardar (ej: "empresas")
            servicio_metodo: Método async del servicio (ej: empresa_service.obtener_todas)
            transformar: Función para transformar cada item (default: model_dump)
            **kwargs: Argumentos para el método del servicio

        Returns:
            Lista de dicts cargados

        Ejemplo:
            await self.cargar_catalogo(
                "empresas",
                empresa_service.obtener_todas,
                incluir_inactivas=False
            )
        """
        try:
            items = await servicio_metodo(**kwargs)
            if transformar:
                datos = [transformar(item) for item in items]
            else:
                datos = [
                    item.model_dump(mode='json') if hasattr(item, 'model_dump') else item
                    for item in items
                ]
            setattr(self, campo_destino, datos)
            return datos
        except Exception as e:
            logger.warning(f"Error cargando catálogo {campo_destino}: {e}")
            setattr(self, campo_destino, [])
            return []

    # ========================
    # LIMPIEZA DE FORMULARIOS
    # ========================
    def limpiar_formulario(
        self,
        campos_default: Dict[str, Any],
        campos_error: Optional[List[str]] = None,
        campos_extra: Optional[Dict[str, Any]] = None
    ):
        """
        Limpia formulario asignando valores por defecto.

        Args:
            campos_default: Dict de {campo: valor_default} para form_*
            campos_error: Lista de nombres de campos error_* a limpiar
            campos_extra: Dict de otros campos a resetear

        Ejemplo:
            self.limpiar_formulario(
                campos_default={"nombre": "", "email": "", "activo": True},
                campos_error=["nombre", "email"],
                campos_extra={"es_edicion": False, "id_edicion": 0}
            )
        """
        # Limpiar campos del formulario
        for campo, valor in campos_default.items():
            setattr(self, f"form_{campo}", valor)

        # Limpiar errores
        if campos_error:
            for campo in campos_error:
                setattr(self, f"error_{campo}", "")

        # Limpiar campos extra
        if campos_extra:
            for campo, valor in campos_extra.items():
                setattr(self, campo, valor)

    def limpiar_errores(self, campos: List[str]):
        """
        Limpia solo los campos de error especificados.

        Args:
            campos: Lista de nombres (sin prefijo error_)
        """
        for campo in campos:
            setattr(self, f"error_{campo}", "")

    # ========================
    # FILTROS Y PAGINACIÓN
    # ========================
    def resetear_filtros(
        self,
        filtros_default: Dict[str, Any],
        resetear_pagina: bool = True
    ):
        """
        Resetea filtros a sus valores por defecto.

        Args:
            filtros_default: Dict de {campo_filtro: valor_default}
            resetear_pagina: Si True, resetea self.pagina a 1
        """
        for campo, valor in filtros_default.items():
            setattr(self, campo, valor)

        if resetear_pagina and hasattr(self, 'pagina'):
            self.pagina = 1

    def es_filtro_activo(self, valor: Any) -> bool:
        """
        Verifica si un valor de filtro está activo.

        Args:
            valor: Valor del filtro

        Returns:
            True si no es "todos" ni vacío
        """
        return es_filtro_activo_ui(valor)

    def obtener_filtros_activos(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filtra solo los filtros que están activos.

        Args:
            filtros: Dict de {nombre: valor}

        Returns:
            Dict solo con filtros activos
        """
        return {k: v for k, v in filtros.items() if self.es_filtro_activo(v)}

    # ========================
    # HELPERS DE PAGINACIÓN
    # ========================
    def calcular_total_paginas(self, total_items: int, items_por_pagina: int = 20) -> int:
        """Calcula número total de páginas."""
        return calcular_paginas(total_items, items_por_pagina)

    def calcular_offset_actual(self, items_por_pagina: int = 20) -> int:
        """Calcula offset basado en self.pagina."""
        pagina = getattr(self, 'pagina', 1)
        return calcular_offset(pagina, items_por_pagina)

    # ========================
    # NORMALIZACIÓN DE SETTERS
    # ========================
    # ========================
    # VIEW TOGGLE (tabla/cards)
    # ========================
    def set_view_table(self):
        """Cambiar a vista de tabla."""
        self.view_mode = "table"

    def set_view_cards(self):
        """Cambiar a vista de cards."""
        self.view_mode = "cards"

    def toggle_view(self):
        """Alternar entre vistas."""
        self.view_mode = "cards" if self.view_mode == "table" else "table"

    @rx.var
    def is_table_view(self) -> bool:
        """True si la vista actual es tabla."""
        return getattr(self, 'view_mode', 'table') == "table"

    @rx.var
    def is_cards_view(self) -> bool:
        """True si la vista actual es cards."""
        return getattr(self, 'view_mode', 'table') == "cards"

    # ========================
    # NORMALIZACIÓN DE SETTERS
    # ========================
    @staticmethod
    def normalizar_mayusculas(valor: str) -> str:
        """Normaliza string a mayúsculas (para CURP, RFC, etc.)"""
        return valor.upper().strip() if valor else ""

    @staticmethod
    def normalizar_minusculas(valor: str) -> str:
        """Normaliza string a minúsculas (para emails)."""
        return valor.lower().strip() if valor else ""

    @staticmethod
    def normalizar_texto(valor: str) -> str:
        """Normaliza texto removiendo espacios extra."""
        return " ".join(valor.split()) if valor else ""

    @staticmethod
    def normalizar_digitos(valor: str) -> str:
        """Extrae solo dígitos de un string (para teléfonos, NSS)."""
        return "".join(c for c in valor if c.isdigit()) if valor else ""
