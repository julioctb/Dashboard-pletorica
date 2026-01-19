"""Estado base para todos los módulos"""
import reflex as rx


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
