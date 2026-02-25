"""Compatibilidad de validadores de Categorías de Contrato (wrapper sobre core.validation)."""
from app.core.validation.contrato_categoria_form_validators import (
    validar_categoria_puesto_id_contrato_categoria as validar_categoria_puesto_id,
    validar_cantidad_minima_contrato_categoria as validar_cantidad_minima,
    validar_cantidad_maxima_contrato_categoria as validar_cantidad_maxima,
    validar_costo_unitario_contrato_categoria as validar_costo_unitario,
    validar_notas_contrato_categoria as validar_notas,
)

__all__ = [
    "validar_categoria_puesto_id",
    "validar_cantidad_minima",
    "validar_cantidad_maxima",
    "validar_costo_unitario",
    "validar_notas",
]
