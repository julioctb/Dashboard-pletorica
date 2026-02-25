"""
Validadores de formulario para gestion de usuarios.

Funciones puras que retornan mensaje de error o cadena vacia.
Sincronizado con app/entities/user_profile.py.
"""
from app.core.validation import (
    validar_email_usuario,
    validar_password_usuario,
    validar_nombre_completo_usuario,
    validar_telefono_usuario,
)


def validar_email(email: str) -> str:
    """Valida formato de email. Retorna mensaje de error o cadena vacia."""
    return validar_email_usuario(email)


def validar_password(password: str) -> str:
    """Valida contrasena. Retorna mensaje de error o cadena vacia."""
    return validar_password_usuario(password)


def validar_nombre_completo(nombre: str) -> str:
    """Valida nombre completo."""
    return validar_nombre_completo_usuario(nombre)


def validar_telefono(telefono: str) -> str:
    """Valida telefono (opcional, pero si se proporciona debe ser valido)."""
    return validar_telefono_usuario(telefono)
