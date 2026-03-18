"""Validadores de formulario reutilizados por multiples modulos."""

from .common_validators import validar_select_requerido, validar_texto_opcional
from .constants import NOTAS_PAGO_MAX


def validar_tipo_servicio_id_form(valor: str) -> str:
    """Valida la selección obligatoria de tipo de servicio."""
    return validar_select_requerido(valor, "tipo de servicio")


def validar_notas_form(notas: str) -> str:
    """Valida notas opcionales con el tope estándar compartido."""
    return validar_texto_opcional(notas, "notas", max_length=NOTAS_PAGO_MAX)


__all__ = [
    "validar_tipo_servicio_id_form",
    "validar_notas_form",
]
