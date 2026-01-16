"""
Fábrica de validadores y funciones auxiliares.

Contiene:
- crear_validador(): Factory que genera validadores desde FieldConfig
- validar_con_config(): Para usar FieldConfig en Pydantic validators
- Helpers reutilizables: validar_patron, validar_longitud, validar_requerido
"""
import re
from typing import Callable, Optional, Tuple

from .field_config import FieldConfig


# =============================================================================
# FUNCIONES HELPER REUTILIZABLES
# =============================================================================

def validar_patron(valor: str, patron: str, mensaje_error: str) -> str:
    """
    Valida un valor contra un patrón regex.

    Args:
        valor: Valor a validar
        patron: Patrón regex a usar
        mensaje_error: Mensaje si no coincide

    Returns:
        String vacío si es válido, mensaje de error si no
    """
    if not re.match(patron, valor):
        return mensaje_error
    return ""


def validar_longitud(
    valor: str,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
    nombre_campo: str = "Campo"
) -> str:
    """
    Valida la longitud de un valor.

    Args:
        valor: Valor a validar
        min_len: Longitud mínima (opcional)
        max_len: Longitud máxima (opcional)
        nombre_campo: Nombre para el mensaje de error

    Returns:
        String vacío si es válido, mensaje de error si no
    """
    longitud = len(valor)

    if min_len is not None and longitud < min_len:
        return f"{nombre_campo} debe tener al menos {min_len} caracteres"

    if max_len is not None and longitud > max_len:
        return f"{nombre_campo} no puede tener más de {max_len} caracteres"

    return ""


def validar_requerido(valor: Optional[str], nombre_campo: str = "Campo") -> str:
    """
    Valida que un campo requerido tenga valor.

    Args:
        valor: Valor a validar
        nombre_campo: Nombre para el mensaje de error

    Returns:
        String vacío si tiene valor, mensaje de error si no
    """
    if not valor or not valor.strip():
        return f"{nombre_campo} es obligatorio"
    return ""


# =============================================================================
# FACTORY DE VALIDADORES
# =============================================================================

def crear_validador(config: FieldConfig) -> Callable[[str], str]:
    """
    Crea una función validadora a partir de una configuración.

    Args:
        config: Configuración del campo (FieldConfig)

    Returns:
        Función que recibe valor y retorna mensaje de error o ""

    Example:
        >>> from app.core.validation import CAMPO_RFC, crear_validador
        >>> validar_rfc = crear_validador(CAMPO_RFC)
        >>> validar_rfc("XAXX010101AB1")  # "" = válido
    """
    def validar(valor: str) -> str:
        # Transformar si aplica (ej: str.upper)
        if config.transformar and valor:
            valor = config.transformar(valor)

        # Validar requerido
        if config.requerido:
            if not valor or not valor.strip():
                return f"{config.nombre} es obligatorio"
        elif not valor or not valor.strip():
            return ""  # Campo opcional vacío es válido

        valor = valor.strip()

        # Validar longitud mínima
        if config.min_len and len(valor) < config.min_len:
            return f"{config.nombre_display} debe tener al menos {config.min_len} caracteres"

        # Validar longitud máxima
        if config.max_len and len(valor) > config.max_len:
            return f"{config.nombre_display} no puede tener más de {config.max_len} caracteres"

        # Validar patrón regex
        if config.patron and not re.match(config.patron, valor):
            return config.patron_error or "Formato inválido"

        # Validador personalizado
        if config.validador_custom:
            error = config.validador_custom(valor)
            if error:
                return error

        return ""

    return validar


# =============================================================================
# VALIDACIÓN PARA PYDANTIC
# =============================================================================

def validar_con_config(valor: str, config: FieldConfig) -> Tuple[str, str]:
    """
    Valida un valor usando FieldConfig y retorna el valor transformado + error.

    Diseñado para usar en @field_validator de Pydantic:

    Example:
        @field_validator('nombre')
        def validar_nombre(cls, v):
            v, error = validar_con_config(v, CAMPO_NOMBRE_COMERCIAL)
            if error:
                raise ValueError(error)
            return v

    Args:
        valor: Valor a validar
        config: Configuración del campo

    Returns:
        Tuple[valor_transformado, error_message]
        - Si es válido: (valor_transformado, "")
        - Si hay error: (valor_original, "mensaje de error")
    """
    if not valor:
        if config.requerido:
            return valor, f"{config.nombre} es obligatorio"
        return valor, ""

    # Aplicar transformación
    valor_transformado = valor
    if config.transformar:
        valor_transformado = config.transformar(valor)

    valor_limpio = valor_transformado.strip() if isinstance(valor_transformado, str) else valor_transformado

    # Validar longitud mínima
    if config.min_len and len(valor_limpio) < config.min_len:
        return valor_transformado, f"{config.nombre} debe tener al menos {config.min_len} caracteres"

    # Validar longitud máxima
    if config.max_len and len(valor_limpio) > config.max_len:
        return valor_transformado, f"{config.nombre} no puede tener más de {config.max_len} caracteres"

    # Validar patrón
    if config.patron and not re.match(config.patron, valor_limpio):
        return valor_transformado, config.patron_error or "Formato inválido"

    # Validador custom
    if config.validador_custom:
        error = config.validador_custom(valor_limpio)
        if error:
            return valor_transformado, error

    return valor_transformado, ""


def pydantic_validator(config: FieldConfig):
    """
    Decorador que crea un validador Pydantic desde FieldConfig.

    Example:
        from app.core.validation import CAMPO_RFC, pydantic_validator

        class Empresa(BaseModel):
            rfc: str

            @field_validator('rfc')
            @classmethod
            @pydantic_validator(CAMPO_RFC)
            def validar_rfc(cls, v):
                return v  # El decorador ya validó y transformó
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(cls, v):
            if v is None:
                if config.requerido:
                    raise ValueError(f"{config.nombre} es obligatorio")
                return v

            v_transformado, error = validar_con_config(str(v), config)
            if error:
                raise ValueError(error)
            return v_transformado
        return wrapper
    return decorator
