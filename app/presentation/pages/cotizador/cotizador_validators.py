"""
Validadores de formulario para el módulo Cotizador.

Funciones puras (sin efectos secundarios) que se llaman
en on_blur y on_submit para dar feedback inmediato al usuario.
"""
from datetime import date
from typing import Optional


def validar_fecha_inicio(valor: str) -> Optional[str]:
    """Valida que la fecha de inicio sea una fecha válida."""
    if not valor or not valor.strip():
        return "La fecha de inicio es requerida"
    try:
        date.fromisoformat(valor)
    except ValueError:
        return "Fecha de inicio inválida"
    return None


def validar_fecha_fin(valor_fin: str, valor_inicio: str) -> Optional[str]:
    """Valida que la fecha de fin sea posterior a la de inicio."""
    if not valor_fin or not valor_fin.strip():
        return "La fecha de fin es requerida"
    try:
        fin = date.fromisoformat(valor_fin)
    except ValueError:
        return "Fecha de fin inválida"

    if valor_inicio:
        try:
            inicio = date.fromisoformat(valor_inicio)
            if fin <= inicio:
                return "La fecha de fin debe ser posterior a la de inicio"
        except ValueError:
            pass
    return None


def validar_salario_base(valor: str) -> Optional[str]:
    """Valida que el salario sea un número positivo."""
    if not valor or not valor.strip():
        return "El salario base es requerido"
    try:
        salario = float(valor.replace(',', ''))
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
        n = int(valor)
        if n < 0:
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
