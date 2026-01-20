"""
Validadores frontend para el módulo de Categorías de Contrato.

Funciones de validación que se ejecutan en tiempo real (on_blur)
y antes de enviar el formulario.

Usa validadores centralizados de app.core.validation para operaciones comunes.
"""
from app.core.validation import (
    validar_select_requerido,
    validar_entero_requerido,
    validar_enteros_min_max,
    validar_monto_opcional,
    validar_texto_opcional,
)


def validar_categoria_puesto_id(categoria_id: str) -> str:
    """Valida que se haya seleccionado una categoría"""
    return validar_select_requerido(categoria_id, "categoría de puesto")


def validar_cantidad_minima(cantidad: str) -> str:
    """Valida la cantidad mínima de personal"""
    return validar_entero_requerido(cantidad, "cantidad mínima", permitir_cero=True)


def validar_cantidad_maxima(cantidad: str, cantidad_minima: str = "0") -> str:
    """Valida la cantidad máxima de personal"""
    # Primero validar que sea un entero válido
    error_entero = validar_entero_requerido(cantidad, "cantidad máxima", permitir_cero=True)
    if error_entero:
        return error_entero

    # Luego validar coherencia con cantidad mínima
    error_rango = validar_enteros_min_max(
        cantidad_minima, cantidad,
        nombre_min="mínimo",
        nombre_max="máximo"
    )
    if error_rango:
        try:
            valor_min = int(cantidad_minima.strip()) if cantidad_minima else 0
            return f"Debe ser mayor o igual a la cantidad mínima ({valor_min})"
        except ValueError:
            pass

    return ""


def validar_costo_unitario(costo: str) -> str:
    """Valida el costo unitario (opcional)"""
    return validar_monto_opcional(costo, "costo")


def validar_notas(notas: str) -> str:
    """Valida las notas (opcional, máximo 1000 caracteres)"""
    return validar_texto_opcional(notas, "notas", max_length=1000)
