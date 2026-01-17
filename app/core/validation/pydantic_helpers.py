"""
Helpers para integrar FieldConfig con Pydantic.

Estos helpers eliminan la duplicación entre el catálogo de campos
y las definiciones de entidades Pydantic.

Uso:
    from app.core.validation import CAMPO_RFC, CAMPO_EMAIL
    from app.core.validation.pydantic_helpers import pydantic_field, campo_validador

    class Empleado(BaseModel):
        # Field generado desde FieldConfig
        rfc: str = pydantic_field(CAMPO_RFC)
        email: Optional[str] = pydantic_field(CAMPO_EMAIL)

        # Validador generado desde FieldConfig
        validar_rfc = campo_validador('rfc', CAMPO_RFC)
        validar_email = campo_validador('email', CAMPO_EMAIL)
"""
from typing import Any, Optional
from pydantic import Field, field_validator

from .field_config import FieldConfig
from .validator_factory import validar_con_config


def pydantic_field(config: FieldConfig, **override) -> Any:
    """
    Genera un Pydantic Field() desde FieldConfig.

    Extrae las constraints del FieldConfig (min_length, max_length, pattern)
    y genera el Field correspondiente.

    Args:
        config: FieldConfig con las reglas de validación
        **override: Kwargs para sobrescribir valores del config

    Returns:
        Pydantic Field configurado

    Ejemplo:
        class Empleado(BaseModel):
            rfc: str = pydantic_field(CAMPO_RFC)
            email: Optional[str] = pydantic_field(CAMPO_EMAIL)

            # Con override
            nombre: str = pydantic_field(CAMPO_NOMBRE, min_length=10)
    """
    kwargs = {}

    # Longitud mínima
    if config.min_len is not None:
        kwargs['min_length'] = config.min_len

    # Longitud máxima
    if config.max_len is not None:
        kwargs['max_length'] = config.max_len

    # Default según si es requerido o no
    if config.requerido:
        kwargs['default'] = ...  # Ellipsis = requerido en Pydantic
    else:
        kwargs['default'] = None

    # Descripción para documentación/OpenAPI
    if config.hint:
        kwargs['description'] = config.hint

    # Aplicar overrides
    kwargs.update(override)

    return Field(**kwargs)


def campo_validador(nombre_campo: str, config: FieldConfig):
    """
    Genera un @field_validator desde FieldConfig.

    El validador generado:
    1. Permite None/vacío si el campo no es requerido
    2. Aplica transformaciones (ej: str.upper, str.lower)
    3. Valida según las reglas del FieldConfig
    4. Lanza ValueError si hay error

    Args:
        nombre_campo: Nombre del campo en el modelo Pydantic
        config: FieldConfig con las reglas de validación

    Returns:
        field_validator configurado

    Ejemplo:
        class Empleado(BaseModel):
            rfc: str = pydantic_field(CAMPO_RFC)

            validar_rfc = campo_validador('rfc', CAMPO_RFC)

    Nota:
        El nombre de la variable (validar_rfc) puede ser cualquiera,
        lo importante es el primer argumento (nombre_campo) que debe
        coincidir con el nombre del atributo en el modelo.
    """
    def validator(cls, v):
        # Si es None o vacío y no es requerido, permitir
        if not v and not config.requerido:
            return v

        # Aplicar validación y transformación usando FieldConfig
        valor_transformado, error = validar_con_config(v, config)

        if error:
            raise ValueError(error)

        return valor_transformado

    # Crear y retornar el field_validator de Pydantic
    # mode='before' para que las transformaciones se apliquen antes de las constraints
    return field_validator(nombre_campo, mode='before')(classmethod(validator))
