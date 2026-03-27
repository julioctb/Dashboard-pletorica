"""Cotizacion domain validators."""

from typing import Optional

from core.core.utils import parse_date_input


def validar_fecha_inicio(valor: str) -> Optional[str]:
    """Valida que la fecha de inicio sea una fecha válida."""
    if not valor or not valor.strip():
        return "La fecha de inicio es requerida"
    if parse_date_input(valor) is None:
        return "Fecha de inicio inválida"
    return None


def validar_fecha_fin(valor_fin: str, valor_inicio: str) -> Optional[str]:
    """Valida que la fecha de fin sea posterior a la de inicio."""
    if not valor_fin or not valor_fin.strip():
        return "La fecha de fin es requerida"
    fin = parse_date_input(valor_fin)
    if fin is None:
        return "Fecha de fin inválida"

    if valor_inicio:
        inicio = parse_date_input(valor_inicio)
        if inicio is not None and fin <= inicio:
            return "La fecha de fin debe ser posterior a la de inicio"
    return None


def validar_salario_base(valor: str) -> Optional[str]:
    """Valida que el salario sea un número positivo."""
    if not valor or not valor.strip():
        return "El salario base es requerido"
    try:
        salario = float(valor.replace(",", ""))
        if salario <= 0:
            return "El salario debe ser mayor a cero"
    except ValueError:
        return "Ingresa un monto numérico válido"
    return None


def validar_cantidad(valor: str, campo: str = "Cantidad") -> Optional[str]:
    """Valida que la cantidad sea un entero no negativo."""
    if not valor or not valor.strip():
        return f"{campo} es requerida"
    try:
        numero = int(valor)
        if numero < 0:
            return f"{campo} no puede ser negativa"
    except ValueError:
        return f"{campo} debe ser un número entero"
    return None


def validar_nombre_concepto(valor: str) -> Optional[str]:
    """Valida que el nombre del concepto no esté vacío."""
    if not valor or not valor.strip():
        return "El nombre del concepto es requerido"
    if len(valor.strip()) > 200:
        return "El nombre no puede superar 200 caracteres"
    return None


def validar_precio_unitario(valor: str) -> Optional[str]:
    """Valida que el precio unitario sea un número no negativo."""
    if not valor or not valor.strip():
        return "El precio unitario es requerido"
    try:
        precio = float(valor.replace(",", ""))
        if precio < 0:
            return "El precio no puede ser negativo"
    except ValueError:
        return "Ingresa un monto numérico válido"
    return None


def validar_cantidad_meses(valor: str) -> Optional[str]:
    """Valida la cantidad de meses (>= 1)."""
    if not valor or not valor.strip():
        return "La cantidad de meses es requerida"
    try:
        numero = int(valor)
        if numero < 1:
            return "Mínimo 1 mes"
    except ValueError:
        return "Ingresa un número entero válido"
    return None


def validar_cantidad_items(items: list) -> Optional[str]:
    """Valida que haya al menos un item con descripción."""
    if not items:
        return "Agrega al menos un concepto"
    items_validos = [item for item in items if item.get("descripcion", "").strip()]
    if not items_validos:
        return "Al menos un concepto debe tener descripción"
    return None


__all__ = [
    "validar_fecha_inicio",
    "validar_fecha_fin",
    "validar_salario_base",
    "validar_cantidad",
    "validar_nombre_concepto",
    "validar_precio_unitario",
    "validar_cantidad_meses",
    "validar_cantidad_items",
]
