"""Estado base para todos los módulos"""
import reflex as rx



class BaseState(rx.State):
    """Estado base con funcionalidad común para todos los módulos"""

    loading: bool = False
    mensaje_info: str = ""
    tipo_mensaje: str = "info" # info, success, error

    def mostrar_mensaje(self, mensaje: str, tipo: str = "info"):
        self.mensaje_info = mensaje
        self.tipo_mensaje = tipo

    def limpiar_mensajes(self):
        """Limpiar mensajes informativos"""
        self.mensaje_info = ""
        self.tipo_mensaje = "info"