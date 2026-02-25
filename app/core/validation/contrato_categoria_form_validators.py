"""Validadores de formulario (UI) para Categorías de Contrato."""
from .common_validators import (
    validar_select_requerido,
    validar_entero_requerido,
    validar_enteros_min_max,
    validar_monto_opcional,
    validar_texto_opcional,
)
from .constants import NOTAS_PAGO_MAX


def validar_categoria_puesto_id_contrato_categoria(categoria_id: str) -> str:
    return validar_select_requerido(categoria_id, "categoría de puesto")


def validar_cantidad_minima_contrato_categoria(cantidad: str) -> str:
    return validar_entero_requerido(cantidad, "cantidad mínima", permitir_cero=True)


def validar_cantidad_maxima_contrato_categoria(cantidad: str, cantidad_minima: str = "0") -> str:
    error_entero = validar_entero_requerido(cantidad, "cantidad máxima", permitir_cero=True)
    if error_entero:
        return error_entero
    error_rango = validar_enteros_min_max(cantidad_minima, cantidad, nombre_min="mínimo", nombre_max="máximo")
    if error_rango:
        try:
            valor_min = int(cantidad_minima.strip()) if cantidad_minima else 0
            return f"Debe ser mayor o igual a la cantidad mínima ({valor_min})"
        except ValueError:
            return error_rango
    return ""


def validar_costo_unitario_contrato_categoria(costo: str) -> str:
    return validar_monto_opcional(costo, "costo")


def validar_notas_contrato_categoria(notas: str) -> str:
    return validar_texto_opcional(notas, "notas", max_length=NOTAS_PAGO_MAX)


__all__ = [
    "validar_categoria_puesto_id_contrato_categoria",
    "validar_cantidad_minima_contrato_categoria",
    "validar_cantidad_maxima_contrato_categoria",
    "validar_costo_unitario_contrato_categoria",
    "validar_notas_contrato_categoria",
]
