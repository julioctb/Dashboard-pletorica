"""
Funciones de normalización de texto centralizadas.

Este módulo contiene funciones para normalizar texto usadas
tanto en entities (Pydantic) como en validators (frontend).

IMPORTANTE: Cualquier cambio aquí afecta ambas capas.
"""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Union

_STOPWORDS_CODIGO = {
    "DE",
    "DEL",
    "LA",
    "LAS",
    "LOS",
    "EL",
    "Y",
    "E",
    "EN",
    "PARA",
    "POR",
}


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


UPPERCASE_TRANSFORM = "uppercase"


def _normalizar_fragmentos_codigo(texto: Optional[str]) -> list[str]:
    """Extrae palabras alfanuméricas normalizadas para generar claves."""
    texto_normalizado = normalizar_mayusculas(texto)
    if not texto_normalizado:
        return []

    fragmentos = re.findall(r"[A-Z0-9]+", texto_normalizado)
    return [
        fragmento
        for fragmento in fragmentos
        if fragmento and fragmento not in _STOPWORDS_CODIGO
    ]


def generar_candidatos_clave_categoria_puesto(
    tipo_servicio: Optional[str],
    nombre_categoria: Optional[str],
) -> list[str]:
    """
    Genera candidatos de clave corta para categorías de puesto.

    Respeta el contrato actual del sistema: claves de 2 a 5 caracteres
    alfanuméricos en mayúsculas, sin depender de un formato inline en UI.
    """
    tipo_tokens = _normalizar_fragmentos_codigo(tipo_servicio)
    categoria_tokens = _normalizar_fragmentos_codigo(nombre_categoria)

    prefijo = (tipo_tokens[0] if tipo_tokens else "CAT")[:3]
    ultimo = categoria_tokens[-1] if categoria_tokens else ""
    principal = categoria_tokens[0] if categoria_tokens else ""
    candidatos: list[str] = []

    def agregar(valor: str) -> None:
        candidato = re.sub(r"[^A-Z0-9]", "", valor.upper())[:5]
        if 2 <= len(candidato) <= 5 and candidato not in candidatos:
            candidatos.append(candidato)

    if ultimo:
        agregar(prefijo + ultimo[:2])
        agregar(prefijo + ultimo[:1])
    if principal:
        agregar(prefijo + principal[:2])
        agregar(prefijo + principal[:1])
    if len(categoria_tokens) >= 2:
        iniciales = "".join(token[0] for token in categoria_tokens[:2])
        agregar(prefijo[:2] + iniciales)
        agregar(prefijo + categoria_tokens[1][:1])
    if principal:
        for longitud in range(2, min(len(principal), 5) + 1):
            agregar(principal[:longitud])
    for token in categoria_tokens[1:]:
        for longitud in range(2, min(len(token), 5) + 1):
            agregar(token[:longitud])
    if not candidatos:
        agregar("CAT")

    return candidatos


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


def capitalizar_razon_social(texto: Optional[str]) -> str:
    """
    Title Case para razones sociales preservando abreviaturas comunes.

    Ejemplo:
        >>> capitalizar_razon_social("PLETORICA SERVICIOS DE NOMINA S.A. DE C.V.")
        'Pletorica Servicios de Nomina S.A. de C.V.'
    """
    texto_capitalizado = capitalizar_con_preposiciones(texto)
    reemplazos = (
        (r"\bS\.a\. de C\.v\.\b", "S.A. de C.V."),
        (r"\bS\.a\. de R\.l\. de C\.v\.\b", "S.A. de R.L. de C.V."),
        (r"\bS\. de R\.l\. de C\.v\.\b", "S. de R.L. de C.V."),
        (r"\bA\.c\.\b", "A.C."),
        (r"\bS\.c\.\b", "S.C."),
    )
    for patron, reemplazo in reemplazos:
        texto_capitalizado = re.sub(
            patron,
            reemplazo,
            texto_capitalizado,
            flags=re.IGNORECASE,
        )
    return texto_capitalizado


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


def construir_mailto_href(email: Optional[str]) -> str:
    """Genera un href mailto a partir de un email normalizado."""
    email_normalizado = normalizar_email(email)
    if not email_normalizado:
        return ""
    return f"mailto:{email_normalizado}"


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
    digitos = re.sub(r"[\s\-\(\)\+]", "", texto.strip())
    if len(digitos) == 10:
        return f"{digitos[:3]} {digitos[3:6]} {digitos[6:]}"
    return digitos


def formatear_url_display(url: Optional[str]) -> str:
    """Limpia una URL para mostrarla sin protocolo ni slash final."""
    if not url:
        return ""
    limpio = limpiar_espacios(url)
    limpio = re.sub(r"^https?://", "", limpio, flags=re.IGNORECASE)
    return limpio.rstrip("/")


def construir_url_publica(url: Optional[str]) -> str:
    """Asegura que una URL tenga protocolo para usarla como href."""
    if not url:
        return ""
    limpio = limpiar_espacios(url)
    if not limpio:
        return ""
    if re.match(r"^https?://", limpio, flags=re.IGNORECASE):
        return limpio
    return f"https://{limpio}"


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


def obtener_iniciales(
    texto: Optional[str], max_palabras: int = 2, fallback: str = "?"
) -> str:
    """Obtiene iniciales a partir de un nombre o texto libre."""
    palabras = [p for p in limpiar_espacios(texto).split() if p]
    if not palabras:
        return fallback
    return "".join(p[0].upper() for p in palabras[:max_palabras])


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


def formatear_moneda(
    valor: Optional[str],
    con_simbolo: bool = True,
    *,
    decimales_fijos: int | None = None,
    espacio_simbolo: bool = True,
) -> str:
    """
    Formatea un valor como moneda con separadores de miles.

    Args:
        valor: Valor a formatear (puede contener $, comas, espacios)
        con_simbolo: Si incluir "$" al inicio
        decimales_fijos: Si se define, fuerza ese numero de decimales
        espacio_simbolo: Si True deja un espacio despues del simbolo "$"

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
    if not re.fullmatch(r"-?\d+(\.\d+)?", limpio):
        return limpio

    if decimales_fijos is not None:
        try:
            numero = Decimal(limpio)
        except (InvalidOperation, ValueError):
            return limpio
        formateado = f"{numero:,.{max(decimales_fijos, 0)}f}"
    else:
        # Separar parte entera y decimal preservando el valor recibido.
        partes = limpio.split(".")
        entero = int(partes[0])
        decimal = partes[1] if len(partes) > 1 else ""

        # Formatear con comas
        formateado = f"{entero:,}"
        if decimal:
            formateado += f".{decimal}"

    # Agregar símbolo si se requiere
    if con_simbolo:
        prefijo = "$ " if espacio_simbolo else "$"
        return f"{prefijo}{formateado}"
    return formateado


def formatear_porcentaje(
    valor: Optional[Union[Decimal, float, str]],
    sufijo: str = "%",
    valor_vacio: str = "",
) -> str:
    """
    Formatea porcentajes preservando decimales significativos.

    Ejemplo:
        >>> formatear_porcentaje("2.5980")
        '2.598%'
    """
    if valor in (None, ""):
        return valor_vacio

    try:
        decimal_valor = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return str(valor)

    texto = format(decimal_valor.normalize(), "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return f"{texto}{sufijo}"


def formatear_fecha(
    fecha: Optional[Union[date, datetime, str]],
    formato: str = "%d/%m/%Y",
    valor_vacio: str = "-",
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

    fecha_normalizada = _parse_fecha_ui(fecha)
    if fecha_normalizada is None:
        return valor_vacio
    return fecha_normalizada.strftime(formato)


def _parse_fecha_ui(
    fecha: Optional[Union[date, datetime, str]],
) -> Optional[Union[date, datetime]]:
    """Normaliza fechas ISO simples o con hora para render en UI."""
    if not fecha:
        return None

    if isinstance(fecha, datetime):
        return fecha

    if isinstance(fecha, date):
        return fecha

    if not isinstance(fecha, str):
        return None

    texto = fecha.strip()
    if not texto:
        return None

    candidatos = [texto]
    if texto.endswith("Z"):
        candidatos.append(texto.replace("Z", "+00:00"))
    if "T" in texto:
        candidatos.append(texto.split("T", 1)[0])

    for candidato in candidatos:
        try:
            if len(candidato) <= 10:
                return date.fromisoformat(candidato)
            return datetime.fromisoformat(candidato)
        except ValueError:
            continue

    return None


def formatear_fecha_hora(
    fecha: Optional[Union[date, datetime, str]],
    formato: str = "%d/%m/%Y %H:%M",
    formato_fecha: str = "%d/%m/%Y",
    valor_vacio: str = "",
) -> str:
    """
    Formatea fecha/hora para UI.

    Si recibe una fecha sin hora, conserva el formato corto de fecha.
    Si recibe un datetime o un string ISO con hora, incluye HH:MM.
    """
    fecha_normalizada = _parse_fecha_ui(fecha)
    if fecha_normalizada is None:
        return valor_vacio

    if isinstance(fecha_normalizada, datetime):
        return fecha_normalizada.strftime(formato)

    return fecha_normalizada.strftime(formato_fecha)


_MESES_ES = [
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

_MESES_CORTOS_ES = [
    "",
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
]


def formatear_fecha_es(fecha: Optional[Union[date, datetime, str]]) -> str:
    """
    Formatea una fecha en espanol: '10 de julio de 2025'.

    Args:
        fecha: Fecha a formatear (date, datetime, string ISO, o None)

    Returns:
        Fecha en espanol o cadena vacia si es None
    """
    if not fecha:
        return ""
    fecha_normalizada = _parse_fecha_ui(fecha)
    if fecha_normalizada is None:
        return ""
    try:
        return (
            f"{fecha_normalizada.day} de "
            f"{_MESES_ES[fecha_normalizada.month]} de "
            f"{fecha_normalizada.year}"
        )
    except (AttributeError, IndexError):
        return ""


def formatear_vigencia_meses(
    fecha_inicio: Optional[Union[date, datetime, str]],
    fecha_fin: Optional[Union[date, datetime, str]],
    *,
    valor_vacio: str = "Sin vigencia",
) -> str:
    """
    Formatea una vigencia corta por meses para tablas operativas.

    Ejemplos:
        Mar - Dic 2026
        Nov 2025 - Mar 2026
        Desde Mar 2026
    """
    inicio = _parse_fecha_ui(fecha_inicio)
    fin = _parse_fecha_ui(fecha_fin)

    if inicio and fin:
        inicio_mes = _MESES_CORTOS_ES[inicio.month]
        fin_mes = _MESES_CORTOS_ES[fin.month]
        if inicio.year == fin.year:
            return f"{inicio_mes} - {fin_mes} {fin.year}"
        return f"{inicio_mes} {inicio.year} - {fin_mes} {fin.year}"

    if inicio:
        return f"Desde {_MESES_CORTOS_ES[inicio.month]} {inicio.year}"

    if fin:
        return f"Hasta {_MESES_CORTOS_ES[fin.month]} {fin.year}"

    return valor_vacio
