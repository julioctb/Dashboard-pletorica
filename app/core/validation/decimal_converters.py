"""
Conversores de Decimal reutilizables para validadores Pydantic.

Evita duplicación del patrón de conversión string→Decimal
en múltiples modelos (Plaza, ContratoCategoria, etc.).

Uso como field_validator:
    from app.core.validation.decimal_converters import convertir_a_decimal

    @field_validator('salario_mensual', mode='before')
    @classmethod
    def convertir_salario(cls, v):
        return convertir_a_decimal(v)
"""

from decimal import Decimal
from typing import Optional


def convertir_a_decimal(v, default: Decimal = Decimal('0')) -> Decimal:
    """Convierte a Decimal, retorna default si es None o vacío."""
    if v is None:
        return default
    if isinstance(v, str):
        v = v.replace(',', '').replace('$', '').strip()
        if not v:
            return default
    return Decimal(str(v))


def convertir_a_decimal_opcional(v) -> Optional[Decimal]:
    """Convierte a Decimal, retorna None si es None o vacío."""
    if v is None:
        return None
    if isinstance(v, str):
        v = v.replace(',', '').replace('$', '').strip()
        if not v:
            return None
    return Decimal(str(v))
