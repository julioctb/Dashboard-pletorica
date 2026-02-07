"""
Funciones de normalización de texto centralizadas.

Este módulo contiene funciones para normalizar texto usadas
tanto en entities (Pydantic) como en validators (frontend).

IMPORTANTE: Cualquier cambio aquí afecta ambas capas.
"""
from datetime import date, datetime
from typing import Optional, Union

from app.core.validation.custom_validators import limpiar_telefono


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


def capitalizar_palabras(texto: Optional[str]) -> str:
    """
    Title Case para texto general (nombres, ciudades, titulos, etc).

    Args:
        texto: Texto a capitalizar (puede ser None)

    Returns:
        Texto en Title Case, o string vacío si es None

    Ejemplo:
        >>> capitalizar_palabras("  juan perez  ")
        'Juan Perez'
    """
    if not texto:
        return ""
    return " ".join(w.capitalize() for w in texto.strip().split())


def capitalizar_con_preposiciones(texto: Optional[str]) -> str:
    """
    Title Case respetando preposiciones en español.

    Util para cargos, direcciones, dependencias, etc.

    Args:
        texto: Texto a capitalizar (puede ser None)

    Returns:
        Texto en Title Case con preposiciones en minúsculas

    Ejemplo:
        >>> capitalizar_con_preposiciones("director de recursos humanos")
        'Director de Recursos Humanos'
    """
    if not texto:
        return ""
    preposiciones = {"de", "del", "la", "las", "los", "el", "en", "y", "e"}
    palabras = texto.strip().split()
    resultado = []
    for i, palabra in enumerate(palabras):
        if i > 0 and palabra.lower() in preposiciones:
            resultado.append(palabra.lower())
        else:
            resultado.append(palabra.capitalize())
    return " ".join(resultado)


def normalizar_email(texto: Optional[str]) -> str:
    """
    Normaliza email: minúsculas y sin espacios.

    Args:
        texto: Email a normalizar (puede ser None)

    Returns:
        Email en minúsculas sin espacios, o string vacío si es None

    Ejemplo:
        >>> normalizar_email("  Juan@Example.COM  ")
        'juan@example.com'
    """
    if not texto:
        return ""
    return texto.strip().lower()


def formatear_telefono(texto: Optional[str]) -> str:
    """
    Formatea teléfono mexicano: solo dígitos, formato XXX XXX XXXX.

    Usa limpiar_telefono() de custom_validators para extraer dígitos.

    Args:
        texto: Teléfono a formatear (puede ser None)

    Returns:
        Teléfono formateado o solo dígitos si no tiene 10

    Ejemplo:
        >>> formatear_telefono("(222) 123-4567")
        '222 123 4567'
    """
    if not texto:
        return ""
    digitos = limpiar_telefono(texto)
    if len(digitos) == 10:
        return f"{digitos[:3]} {digitos[3:6]} {digitos[6:]}"
    return digitos


def limpiar_espacios(texto: Optional[str]) -> str:
    """
    Trim y colapsar espacios múltiples.

    Args:
        texto: Texto a limpiar (puede ser None)

    Returns:
        Texto sin espacios extra, o string vacío si es None

    Ejemplo:
        >>> limpiar_espacios("  hola   mundo  ")
        'hola mundo'
    """
    if not texto:
        return ""
    return " ".join(texto.split())


# Claves exactas que usan MAYUSCULAS (prioridad sobre sufijo)
_NORMALIZADORES_POR_CLAVE = {
    "elabora_nombre": normalizar_mayusculas,
    "solicita_nombre": normalizar_mayusculas,
    "validacion_asesor": normalizar_mayusculas,
    "elabora_cargo": normalizar_mayusculas,
    "solicita_cargo": normalizar_mayusculas,
}

# Mapa de sufijos de clave → normalizador
_NORMALIZADORES_POR_SUFIJO = {
    "_nombre": capitalizar_palabras,
    "_cargo": capitalizar_con_preposiciones,
    "_email": normalizar_email,
    "_telefono": formatear_telefono,
}


def normalizar_por_sufijo(clave: str, valor: str) -> str:
    """
    Aplica el normalizador adecuado según la clave.

    Prioridad:
      1. Clave exacta (ej: elabora_nombre → MAYUSCULAS)
      2. Sufijo (ej: _nombre → capitalizar_palabras)
      3. Fallback → limpiar_espacios

    Args:
        clave: Clave del campo (ej: "titular_nombre", "elabora_cargo")
        valor: Valor a normalizar

    Returns:
        Valor normalizado
    """
    if not valor or not valor.strip():
        return ""
    # 1. Clave exacta
    if clave in _NORMALIZADORES_POR_CLAVE:
        return _NORMALIZADORES_POR_CLAVE[clave](valor)
    # 2. Sufijo
    for sufijo, fn in _NORMALIZADORES_POR_SUFIJO.items():
        if clave.endswith(sufijo):
            return fn(valor)
    # 3. Fallback
    return limpiar_espacios(valor)


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


