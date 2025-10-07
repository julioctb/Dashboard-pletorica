"""Estado base para todos los módulos"""
import reflex as rx
from typing import Optional


class BaseState(rx.State):
    """Estado base con funcionalidad común para todos los módulos"""

    loading: bool = False
    error_message: str = ""
    success_message: str = ""

    def set_loading(self, value: bool):
        self.loading = value

    def set_error(self, message: str):
        self.error_message = message
        self.success_message = ""

    def set_success(self, message: str):
        self.success_message = message
        self.error_message = ""

    def clear_messages(self):
        self.error_message = ""
        self.success_message = ""
