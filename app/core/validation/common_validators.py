"""
Validadores comunes reutilizables para formularios.

Este módulo centraliza validaciones repetitivas como:
- Selects/dropdowns requeridos
- Fechas (requeridas, no futuras, rangos)
- Montos/moneda (requeridos, opcionales, rangos)
- Enteros (requeridos, rangos)
- Texto (longitud máxima, requerido)

Uso:
    from app.core.validation import (
        validar_select_requerido,
        validar_fecha_requerida,
        validar_monto_requerido,
        limpiar_moneda,
    )

    error = validar_select_requerido(valor, "empresa")
    error = validar_fecha_requerida(fecha, "fecha de inicio")
    error = validar_monto_requerido(monto, "monto máximo")
"""
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional


# ============================================================================
# UTILIDADES
# ============================================================================

def limpiar_moneda(valor: str) -> str:
    """
    Limpia un string de moneda eliminando símbolos y separadores.

    Args:
        valor: String con formato de moneda (ej: "$ 1,234.56")

    Returns:
        String limpio (ej: "1234.56")

    Ejemplo:
        >>> limpiar_moneda("$ 1,234.56")
        "1234.56"
        >>> limpiar_moneda("")
        ""
    """
    if not valor:
        return ""
    return valor.replace(",", "").replace("$", "").replace(" ", "").strip()


def _es_valor_vacio(valor: str) -> bool:
    """Verifica si un valor de select está vacío o es placeholder."""
    return not valor or valor == "" or valor == "0"


# ============================================================================
# VALIDADORES DE SELECT/DROPDOWN
# ============================================================================

def validar_select_requerido(valor: str, nombre_campo: str) -> str:
    """
    Valida que se haya seleccionado un valor en un dropdown.

    Args:
        valor: Valor seleccionado (generalmente un ID como string)
        nombre_campo: Nombre del campo para el mensaje de error

    Returns:
        Mensaje de error o cadena vacía si es válido

    Ejemplo:
        >>> validar_select_requerido("", "empresa")
        "Debe seleccionar una empresa"
        >>> validar_select_requerido("1", "empresa")
        ""
    """
    if _es_valor_vacio(valor):
        # Determinar artículo correcto (una/un)
        articulo = "una" if nombre_campo.endswith("a") else "un"
        return f"Debe seleccionar {articulo} {nombre_campo}"
    return ""


def validar_select_opcional(valor: str, valores_validos: Optional[list] = None) -> str:
    """
    Valida un select opcional, verificando que el valor sea válido si está presente.

    Args:
        valor: Valor seleccionado
        valores_validos: Lista de valores permitidos (opcional)

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if _es_valor_vacio(valor):
        return ""  # Es opcional, vacío es válido

    if valores_validos and valor not in valores_validos:
        return "Valor seleccionado no válido"

    return ""


# ============================================================================
# VALIDADORES DE FECHA
# ============================================================================

def validar_fecha_requerida(fecha: str, nombre_campo: str = "fecha") -> str:
    """
    Valida que una fecha requerida esté presente y tenga formato válido.

    Args:
        fecha: Fecha en formato ISO (YYYY-MM-DD)
        nombre_campo: Nombre del campo para el mensaje de error

    Returns:
        Mensaje de error o cadena vacía si es válida
    """
    if not fecha or not fecha.strip():
        return f"La {nombre_campo} es obligatoria"

    try:
        date.fromisoformat(fecha)
        return ""
    except ValueError:
        return f"Formato de {nombre_campo} inválido (use AAAA-MM-DD)"


def validar_fecha_no_futura(fecha: str, nombre_campo: str = "fecha") -> str:
    """
    Valida que una fecha no sea futura (requerida).

    Args:
        fecha: Fecha en formato ISO (YYYY-MM-DD)
        nombre_campo: Nombre del campo para el mensaje de error

    Returns:
        Mensaje de error o cadena vacía si es válida
    """
    if not fecha or not fecha.strip():
        return f"La {nombre_campo} es obligatoria"

    try:
        fecha_date = date.fromisoformat(fecha)
        if fecha_date > date.today():
            return f"La {nombre_campo} no puede ser futura"
        return ""
    except ValueError:
        return f"Formato de {nombre_campo} inválido"


def validar_fecha_rango(
    fecha_inicio: str,
    fecha_fin: str,
    nombre_inicio: str = "fecha de inicio",
    nombre_fin: str = "fecha de fin"
) -> str:
    """
    Valida que fecha_fin no sea anterior a fecha_inicio.

    Args:
        fecha_inicio: Fecha de inicio en formato ISO
        fecha_fin: Fecha de fin en formato ISO
        nombre_inicio: Nombre del campo de inicio para mensajes
        nombre_fin: Nombre del campo de fin para mensajes

    Returns:
        Mensaje de error o cadena vacía si es válida
    """
    if not fecha_inicio or not fecha_fin:
        return ""  # Si falta alguna, no se puede validar rango

    try:
        inicio = date.fromisoformat(fecha_inicio)
        fin = date.fromisoformat(fecha_fin)

        if fin < inicio:
            return f"La {nombre_fin} no puede ser anterior a la {nombre_inicio}"
        return ""
    except ValueError:
        return ""  # Errores de formato se manejan en validadores individuales


# ============================================================================
# VALIDADORES DE MONTO/MONEDA
# ============================================================================

def validar_monto_requerido(
    monto: str,
    nombre_campo: str = "monto",
    permitir_cero: bool = False
) -> str:
    """
    Valida un monto requerido.

    Args:
        monto: Monto como string (puede tener formato de moneda)
        nombre_campo: Nombre del campo para el mensaje de error
        permitir_cero: Si True, acepta cero como valor válido

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if not monto or not monto.strip():
        return f"El {nombre_campo} es obligatorio"

    limpio = limpiar_moneda(monto)
    if not limpio:
        return f"El {nombre_campo} es obligatorio"

    try:
        valor = Decimal(limpio)
        if valor < 0:
            return f"El {nombre_campo} no puede ser negativo"
        if not permitir_cero and valor == 0:
            return f"El {nombre_campo} debe ser mayor a cero"
        return ""
    except InvalidOperation:
        return f"El {nombre_campo} debe ser un número válido"


def validar_monto_opcional(monto: str, nombre_campo: str = "monto") -> str:
    """
    Valida un monto opcional (solo valida formato si tiene valor).

    Args:
        monto: Monto como string (puede tener formato de moneda)
        nombre_campo: Nombre del campo para el mensaje de error

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if not monto or not monto.strip():
        return ""  # Es opcional

    limpio = limpiar_moneda(monto)
    if not limpio:
        return ""  # Vacío después de limpiar es válido

    try:
        valor = Decimal(limpio)
        if valor < 0:
            return f"El {nombre_campo} no puede ser negativo"
        return ""
    except InvalidOperation:
        return f"El {nombre_campo} debe ser un número válido"


def validar_montos_min_max(
    monto_min: str,
    monto_max: str,
    nombre_min: str = "monto mínimo",
    nombre_max: str = "monto máximo"
) -> str:
    """
    Valida que monto_max >= monto_min.

    Args:
        monto_min: Monto mínimo como string
        monto_max: Monto máximo como string
        nombre_min: Nombre del campo mínimo para mensajes
        nombre_max: Nombre del campo máximo para mensajes

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if not monto_min or not monto_max:
        return ""

    limpio_min = limpiar_moneda(monto_min)
    limpio_max = limpiar_moneda(monto_max)

    if not limpio_min or not limpio_max:
        return ""

    try:
        valor_min = Decimal(limpio_min)
        valor_max = Decimal(limpio_max)

        if valor_max < valor_min:
            return f"El {nombre_max} no puede ser menor al {nombre_min}"
        return ""
    except InvalidOperation:
        return ""  # Errores de formato se manejan en validadores individuales


# ============================================================================
# VALIDADORES DE ENTEROS
# ============================================================================

def validar_entero_requerido(
    valor: str,
    nombre_campo: str = "valor",
    permitir_cero: bool = True
) -> str:
    """
    Valida un entero requerido.

    Args:
        valor: Valor como string
        nombre_campo: Nombre del campo para el mensaje de error
        permitir_cero: Si True, acepta cero como valor válido

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if not valor or not valor.strip():
        return f"El campo {nombre_campo} es obligatorio"

    try:
        num = int(valor.strip())
        if num < 0:
            return f"El campo {nombre_campo} no puede ser negativo"
        if not permitir_cero and num == 0:
            return f"El campo {nombre_campo} debe ser mayor a cero"
        return ""
    except ValueError:
        return f"El campo {nombre_campo} debe ser un número entero"


def validar_entero_opcional(valor: str, nombre_campo: str = "valor") -> str:
    """
    Valida un entero opcional (solo valida formato si tiene valor).

    Args:
        valor: Valor como string
        nombre_campo: Nombre del campo para el mensaje de error

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if not valor or not valor.strip():
        return ""  # Es opcional

    try:
        num = int(valor.strip())
        if num < 0:
            return f"El campo {nombre_campo} no puede ser negativo"
        return ""
    except ValueError:
        return f"El campo {nombre_campo} debe ser un número entero"


def validar_entero_rango(
    valor: str,
    nombre_campo: str = "valor",
    minimo: Optional[int] = None,
    maximo: Optional[int] = None,
    requerido: bool = True
) -> str:
    """
    Valida un entero con rango opcional.

    Args:
        valor: Valor como string
        nombre_campo: Nombre del campo para el mensaje de error
        minimo: Valor mínimo permitido (None = sin límite)
        maximo: Valor máximo permitido (None = sin límite)
        requerido: Si True, el campo es obligatorio

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if not valor or not valor.strip():
        if requerido:
            return f"El campo {nombre_campo} es obligatorio"
        return ""

    try:
        num = int(valor.strip())

        if minimo is not None and num < minimo:
            return f"El campo {nombre_campo} debe ser al menos {minimo}"

        if maximo is not None and num > maximo:
            return f"El campo {nombre_campo} no puede exceder {maximo}"

        return ""
    except ValueError:
        return f"El campo {nombre_campo} debe ser un número entero"


def validar_enteros_min_max(
    valor_min: str,
    valor_max: str,
    nombre_min: str = "mínimo",
    nombre_max: str = "máximo"
) -> str:
    """
    Valida que valor_max >= valor_min.

    Args:
        valor_min: Valor mínimo como string
        valor_max: Valor máximo como string
        nombre_min: Nombre del campo mínimo
        nombre_max: Nombre del campo máximo

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if not valor_min or not valor_max:
        return ""

    try:
        num_min = int(valor_min.strip())
        num_max = int(valor_max.strip())

        if num_max < num_min:
            return f"El {nombre_max} debe ser mayor o igual al {nombre_min}"
        return ""
    except ValueError:
        return ""  # Errores de formato se manejan en validadores individuales


# ============================================================================
# VALIDADORES DE TEXTO
# ============================================================================

def validar_texto_requerido(
    texto: str,
    nombre_campo: str = "campo",
    min_length: int = 1,
    max_length: Optional[int] = None
) -> str:
    """
    Valida un campo de texto requerido con restricciones de longitud.

    Args:
        texto: Texto a validar
        nombre_campo: Nombre del campo para el mensaje de error
        min_length: Longitud mínima requerida
        max_length: Longitud máxima permitida (None = sin límite)

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if not texto or not texto.strip():
        return f"El campo {nombre_campo} es obligatorio"

    texto_limpio = texto.strip()

    if len(texto_limpio) < min_length:
        return f"El campo {nombre_campo} debe tener al menos {min_length} caracteres"

    if max_length and len(texto_limpio) > max_length:
        return f"El campo {nombre_campo} no puede exceder {max_length} caracteres"

    return ""


def validar_texto_opcional(
    texto: str,
    nombre_campo: str = "campo",
    max_length: Optional[int] = None
) -> str:
    """
    Valida un campo de texto opcional con longitud máxima.

    Args:
        texto: Texto a validar
        nombre_campo: Nombre del campo para el mensaje de error
        max_length: Longitud máxima permitida (None = sin límite)

    Returns:
        Mensaje de error o cadena vacía si es válido
    """
    if not texto:
        return ""  # Es opcional

    if max_length and len(texto) > max_length:
        return f"El campo {nombre_campo} no puede exceder {max_length} caracteres"

    return ""
