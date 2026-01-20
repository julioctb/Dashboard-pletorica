"""
Validadores de frontend para el módulo de Pagos.

Estas funciones se usan para validación en tiempo real (on_blur)
y antes de enviar el formulario.

Usa validadores centralizados de app.core.validation para operaciones comunes.
"""
from app.core.validation import (
    validar_fecha_no_futura,
    validar_monto_requerido,
    validar_texto_requerido,
    validar_texto_opcional,
)


def validar_fecha_pago(fecha: str) -> str:
    """Valida la fecha del pago (requerida, no puede ser futura)"""
    return validar_fecha_no_futura(fecha, "fecha de pago")


def validar_monto(monto: str) -> str:
    """Valida el monto del pago (requerido, mayor a cero)"""
    return validar_monto_requerido(monto, "monto", permitir_cero=False)


def validar_concepto(concepto: str) -> str:
    """Valida el concepto del pago (requerido, 3-500 caracteres)"""
    return validar_texto_requerido(concepto, "concepto", min_length=3, max_length=500)


def validar_numero_factura(numero: str) -> str:
    """Valida el número de factura (opcional, max 50 caracteres)"""
    return validar_texto_opcional(numero, "número de factura", max_length=50)


def validar_comprobante(comprobante: str) -> str:
    """Valida la referencia del comprobante (opcional, max 200 caracteres)"""
    return validar_texto_opcional(comprobante, "referencia del comprobante", max_length=200)


def validar_notas(notas: str) -> str:
    """Valida las notas (opcional, max 1000 caracteres)"""
    return validar_texto_opcional(notas, "notas", max_length=1000)
