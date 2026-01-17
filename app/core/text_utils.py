"""
Funciones de normalización de texto centralizadas.

Este módulo contiene funciones para normalizar texto usadas
tanto en entities (Pydantic) como en validators (frontend).

IMPORTANTE: Cualquier cambio aquí afecta ambas capas.
"""
import re
from typing import Optional


def normalizar_mayusculas(texto: Optional[str]) -> str:
    """
    Normaliza texto: strip + uppercase.

    Args:
        texto: Texto a normalizar (puede ser None)

    Returns:
        Texto normalizado en mayúsculas, o string vacío si es None

    Ejemplo:
        >>> normalizar_mayusculas("  hola mundo  ")
        'HOLA MUNDO'
    """
    if not texto:
        return ""
    return texto.strip().upper()


def normalizar_minusculas(texto: Optional[str]) -> str:
    """
    Normaliza texto: strip + lowercase.

    Args:
        texto: Texto a normalizar (puede ser None)

    Returns:
        Texto normalizado en minúsculas, o string vacío si es None

    Ejemplo:
        >>> normalizar_minusculas("  HOLA@EMAIL.COM  ")
        'hola@email.com'
    """
    if not texto:
        return ""
    return texto.strip().lower()


def limpiar_alfanumerico(texto: Optional[str]) -> str:
    """
    Limpia texto dejando solo letras y números en mayúsculas.
    Útil para limpiar RFC, registros patronales, etc.

    Args:
        texto: Texto a limpiar (puede ser None)

    Returns:
        Texto solo con caracteres alfanuméricos en mayúsculas

    Ejemplo:
        >>> limpiar_alfanumerico("Y12-34567-10-1")
        'Y1234567101'
    """
    if not texto:
        return ""
    return re.sub(r'[^A-Z0-9]', '', texto.upper())


