"""Validadores centralizados para campos de usuario (UI + entidades)."""
import re
from typing import Optional

from .constants import (
    EMAIL_PATTERN,
    TELEFONO_DIGITOS,
    NOMBRE_COMPLETO_MIN,
    NOMBRE_COMPLETO_MAX,
    PASSWORD_MIN,
)
from .custom_validators import limpiar_telefono


# =============================================================================
# VALIDADORES UI (retornan mensaje)
# =============================================================================


def validar_email_usuario(email: str) -> str:
    """Valida email requerido para formularios de usuario."""
    if not email or not email.strip():
        return "El email es requerido"
    if not re.match(EMAIL_PATTERN, email.strip().lower()):
        return "Formato de email invalido"
    return ""


def validar_password_usuario(password: str) -> str:
    """Valida política mínima de contraseña para usuarios."""
    if not password:
        return "La contrasena es requerida"
    if len(password) < PASSWORD_MIN:
        return f"Minimo {PASSWORD_MIN} caracteres"
    return ""


def validar_nombre_completo_usuario(nombre: str) -> str:
    """Valida nombre completo requerido."""
    if not nombre or not nombre.strip():
        return "El nombre es requerido"

    valor = nombre.strip()
    if len(valor) < NOMBRE_COMPLETO_MIN:
        return f"Minimo {NOMBRE_COMPLETO_MIN} caracteres"
    if len(valor) > NOMBRE_COMPLETO_MAX:
        return f"Maximo {NOMBRE_COMPLETO_MAX} caracteres"
    return ""


def validar_telefono_usuario(telefono: str) -> str:
    """Valida teléfono opcional (10 dígitos) para usuarios."""
    if not telefono or not str(telefono).strip():
        return ""

    digitos = limpiar_telefono(str(telefono))
    if len(digitos) != TELEFONO_DIGITOS:
        return f"Debe tener {TELEFONO_DIGITOS} digitos"
    if not digitos.isdigit():
        return f"Debe tener {TELEFONO_DIGITOS} digitos"
    return ""


# =============================================================================
# NORMALIZACIÓN / VALIDACIÓN PARA BACKEND (lanza ValueError)
# =============================================================================


def normalizar_email_usuario(email: Optional[str], requerido: bool = True) -> Optional[str]:
    """Normaliza y valida email. Retorna string normalizado o None."""
    if email is None:
        if requerido:
            raise ValueError("Formato de email invalido")
        return None

    valor = str(email).strip().lower()
    if not valor:
        if requerido:
            raise ValueError("Formato de email invalido")
        return None

    error = validar_email_usuario(valor)
    if error:
        raise ValueError(error)
    return valor


def normalizar_nombre_completo_usuario(
    nombre: Optional[str],
    *,
    requerido: bool = False,
) -> Optional[str]:
    """Normaliza nombre completo (title case) y valida longitudes."""
    if nombre is None:
        if requerido:
            raise ValueError("El nombre es requerido")
        return None

    valor = str(nombre).strip()
    if not valor:
        if requerido:
            raise ValueError("El nombre es requerido")
        return None

    error = validar_nombre_completo_usuario(valor)
    if error:
        raise ValueError(error)

    return valor.title()


def normalizar_telefono_usuario(
    telefono: Optional[str],
    *,
    requerido: bool = False,
) -> Optional[str]:
    """Limpia y valida teléfono, retornando solo dígitos."""
    if telefono is None:
        if requerido:
            raise ValueError(f"El teléfono debe tener {TELEFONO_DIGITOS} dígitos")
        return None

    valor = str(telefono)
    if not valor.strip():
        if requerido:
            raise ValueError(f"El teléfono debe tener {TELEFONO_DIGITOS} dígitos")
        return None

    error = validar_telefono_usuario(valor)
    if error:
        raise ValueError(f"El teléfono debe tener {TELEFONO_DIGITOS} dígitos")

    return limpiar_telefono(valor)


__all__ = [
    "validar_email_usuario",
    "validar_password_usuario",
    "validar_nombre_completo_usuario",
    "validar_telefono_usuario",
    "normalizar_email_usuario",
    "normalizar_nombre_completo_usuario",
    "normalizar_telefono_usuario",
]
