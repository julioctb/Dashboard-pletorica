"""
Validadores de formulario para gestion de usuarios.

Funciones puras que retornan mensaje de error o cadena vacia.
Sincronizado con app/entities/user_profile.py.
"""
import re

from app.core.validation.constants import (
    EMAIL_PATTERN,
    TELEFONO_DIGITOS,
    NOMBRE_COMPLETO_MIN as NOMBRE_MIN,
    NOMBRE_COMPLETO_MAX as NOMBRE_MAX,
    PASSWORD_MIN,
)


def validar_email(email: str) -> str:
    """Valida formato de email. Retorna mensaje de error o cadena vacia."""
    if not email:
        return "El email es requerido"
    if not re.match(EMAIL_PATTERN, email):
        return "Formato de email invalido"
    return ""


def validar_password(password: str) -> str:
    """Valida contrasena. Retorna mensaje de error o cadena vacia."""
    if not password:
        return "La contrasena es requerida"
    if len(password) < PASSWORD_MIN:
        return f"Minimo {PASSWORD_MIN} caracteres"
    return ""


def validar_nombre_completo(nombre: str) -> str:
    """Valida nombre completo."""
    if not nombre:
        return "El nombre es requerido"
    if len(nombre.strip()) < NOMBRE_MIN:
        return f"Minimo {NOMBRE_MIN} caracteres"
    if len(nombre) > NOMBRE_MAX:
        return f"Maximo {NOMBRE_MAX} caracteres"
    return ""


def validar_telefono(telefono: str) -> str:
    """Valida telefono (opcional, pero si se proporciona debe ser valido)."""
    if not telefono:
        return ""  # Opcional
    digitos = ''.join(c for c in telefono if c.isdigit())
    if len(digitos) != TELEFONO_DIGITOS:
        return f"Debe tener {TELEFONO_DIGITOS} digitos"
    return ""
