"""
Funciones de normalización de texto centralizadas.

Este módulo contiene funciones para normalizar texto usadas
tanto en entities (Pydantic) como en validators (frontend).

IMPORTANTE: Cualquier cambio aquí afecta ambas capas.
"""
from datetime import date, datetime
from typing import Optional, Union


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


def formatear_moneda(valor: Optional[str], con_simbolo: bool = True) -> str:
    """
    Formatea un valor como moneda con separadores de miles.

    Args:
        valor: Valor a formatear (puede contener $, comas, espacios)
        con_simbolo: Si incluir "$ " al inicio

    Returns:
        Valor formateado con comas como separadores de miles

    Ejemplo:
        >>> formatear_moneda("1234567.89")
        '$ 1,234,567.89'
        >>> formatear_moneda("$ 1,234.50")
        '$ 1,234.50'
        >>> formatear_moneda("1234", con_simbolo=False)
        '1,234'
    """
    if not valor:
        return ""

    # Limpiar: quitar $, comas y espacios
    limpio = valor.replace(",", "").replace("$", "").replace(" ", "").strip()

    if not limpio:
        return ""

    # Validar que sea número
    if not limpio.replace(".", "").isdigit():
        return limpio

    # Separar parte entera y decimal
    partes = limpio.split(".")
    entero = int(partes[0])
    decimal = partes[1] if len(partes) > 1 else ""

    # Formatear con comas
    formateado = f"{entero:,}"
    if decimal:
        formateado += f".{decimal}"

    # Agregar símbolo si se requiere
    if con_simbolo:
        return f"$ {formateado}"
    return formateado


def formatear_fecha(
    fecha: Optional[Union[date, datetime, str]],
    formato: str = "%d/%m/%Y",
    valor_vacio: str = "-"
) -> str:
    """
    Formatea una fecha al formato especificado.

    Args:
        fecha: Fecha a formatear (date, datetime, string ISO, o None)
        formato: Formato de salida (default: DD/MM/YYYY)
        valor_vacio: Valor a retornar si fecha es None o inválida

    Returns:
        Fecha formateada o valor_vacio si es None

    Ejemplo:
        >>> formatear_fecha(date(2025, 1, 20))
        '20/01/2025'
        >>> formatear_fecha("2025-01-20")
        '20/01/2025'
        >>> formatear_fecha(None)
        '-'
    """
    if not fecha:
        return valor_vacio

    try:
        # Si es string, convertir a date
        if isinstance(fecha, str):
            fecha = date.fromisoformat(fecha)

        # Si es datetime, usar directamente
        return fecha.strftime(formato)
    except (ValueError, TypeError, AttributeError):
        return valor_vacio


