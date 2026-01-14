"""
Generador de códigos cortos para empresas.
Funciones puras sin dependencia de base de datos.
"""
import re
import unicodedata
from typing import List

# Palabras a ignorar (artículos, preposiciones, sufijos legales)
PALABRAS_IGNORAR = {
    # Artículos y preposiciones
    "de", "del", "la", "las", "los", "el", "y", "e", "en", "con", "para", "por",
    # Sufijos legales mexicanos
    "sa", "cv", "sapi", "sas", "sc", "srl", "sab",
    # Palabras genéricas comunes
    "servicios", "grupo", "empresa", "empresas", "comercial", "comercializadora",
    "industrial", "industrias", "corporativo", "corporacion", "compania", "cia",
    "internacional", "nacional", "mexicana", "mexico"
}


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto: quita acentos, convierte a mayúsculas, solo letras y números.

    Args:
        texto: Texto a normalizar

    Returns:
        Texto normalizado (solo A-Z0-9)
    """
    if not texto:
        return ""

    # Quitar acentos (é -> e, ñ -> n, etc.)
    texto_sin_acentos = unicodedata.normalize('NFD', texto)
    texto_sin_acentos = ''.join(
        c for c in texto_sin_acentos
        if unicodedata.category(c) != 'Mn'
    )

    # Convertir a mayúsculas y quitar caracteres especiales
    return re.sub(r'[^A-Z0-9]', '', texto_sin_acentos.upper())


def extraer_palabras_significativas(nombre: str) -> List[str]:
    """
    Extrae palabras significativas del nombre comercial.
    Ignora artículos, preposiciones y sufijos legales.

    Args:
        nombre: Nombre comercial completo

    Returns:
        Lista de palabras significativas normalizadas

    Example:
        "Servicios de Mantenimiento SA de CV" -> ["MANTENIMIENTO"]
        "Pletórica Consultores" -> ["PLETORICA", "CONSULTORES"]
    """
    if not nombre:
        return []

    # Separar en palabras y normalizar
    palabras = nombre.split()
    significativas = []

    for palabra in palabras:
        # Normalizar para comparación (sin acentos, mayúsculas)
        normalizada = normalizar_texto(palabra)

        # Comparar sin acentos y en minúsculas
        palabra_para_comparar = normalizada.lower()

        # Ignorar palabras vacías o en lista de ignorar
        if not normalizada or palabra_para_comparar in PALABRAS_IGNORAR:
            continue

        # Ignorar palabras muy cortas (< 2 caracteres)
        if len(normalizada) < 2:
            continue

        significativas.append(normalizada)

    return significativas


def generar_codigo_nivel1(nombre: str) -> str:
    """
    Nivel 1: Primeras 3 letras de la primera palabra significativa.

    Args:
        nombre: Nombre comercial

    Returns:
        Código de 3 caracteres o string vacío si no es posible

    Example:
        "Pletórica" -> "PLE"
        "ABC Servicios" -> "ABC"
    """
    palabras = extraer_palabras_significativas(nombre)

    if not palabras:
        return ""

    primera = palabras[0]

    # Si la primera palabra tiene al menos 3 caracteres
    if len(primera) >= 3:
        return primera[:3]

    return ""


def generar_codigo_nivel2(nombre: str) -> str:
    """
    Nivel 2: Iniciales de las primeras 3 palabras significativas (estilo RFC).

    Args:
        nombre: Nombre comercial

    Returns:
        Código de 3 caracteres o string vacío si no es posible

    Example:
        "Servicios de Mantenimiento Industrial" -> "SMI"
        "Grupo Acme México" -> "GAM"
    """
    palabras = extraer_palabras_significativas(nombre)

    if len(palabras) < 2:
        return ""

    # Tomar iniciales de hasta 3 palabras
    iniciales = ''.join(p[0] for p in palabras[:3])

    # Debe tener exactamente 3 caracteres
    if len(iniciales) >= 3:
        return iniciales[:3]

    return ""


def generar_candidatos_codigo(nombre: str) -> List[str]:
    """
    Genera lista ordenada de códigos candidatos para probar.

    Orden de prioridad:
    1. Nivel 1: Primeras 3 letras (PLE)
    2. Nivel 2: Iniciales de 3 palabras (SMI)
    3. Fallback numérico: XX2, XX3, XX4... hasta XX99

    Args:
        nombre: Nombre comercial

    Returns:
        Lista de códigos candidatos (mínimo 100 opciones)

    Example:
        "Pletórica" -> ["PLE", "PL2", "PL3", ..., "PL99"]
        "Servicios Mantenimiento Industrial" -> ["SER", "SMI", "SE2", "SE3", ...]
    """
    candidatos = []

    # Intentar nivel 1
    codigo_n1 = generar_codigo_nivel1(nombre)
    if codigo_n1:
        candidatos.append(codigo_n1)

    # Intentar nivel 2
    codigo_n2 = generar_codigo_nivel2(nombre)
    if codigo_n2 and codigo_n2 not in candidatos:
        candidatos.append(codigo_n2)

    # Determinar base para fallback numérico
    if codigo_n1:
        base = codigo_n1[:2]  # Primeras 2 letras
    elif codigo_n2:
        base = codigo_n2[:2]
    else:
        # Fallback: usar nombre normalizado
        nombre_norm = normalizar_texto(nombre)
        base = nombre_norm[:2] if len(nombre_norm) >= 2 else "XX"

    # Generar fallbacks numéricos (base + número)
    for i in range(2, 100):
        candidatos.append(f"{base}{i}")

    return candidatos
