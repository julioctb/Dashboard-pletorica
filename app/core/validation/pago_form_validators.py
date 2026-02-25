"""Validadores de formulario (UI) para Pagos, centralizados en core.validation."""
from .common_validators import (
    validar_fecha_no_futura,
    validar_monto_requerido,
    validar_texto_requerido,
    validar_texto_opcional,
)
from .constants import CONCEPTO_PAGO_MAX, NUMERO_FACTURA_MAX, COMPROBANTE_MAX, NOTAS_PAGO_MAX


def validar_fecha_pago_form(fecha: str) -> str:
    return validar_fecha_no_futura(fecha, "fecha de pago")


def validar_monto_pago_form(monto: str) -> str:
    return validar_monto_requerido(monto, "monto", permitir_cero=False)


def validar_concepto_pago_form(concepto: str) -> str:
    return validar_texto_requerido(concepto, "concepto", min_length=3, max_length=CONCEPTO_PAGO_MAX)


def validar_numero_factura_pago_form(numero: str) -> str:
    return validar_texto_opcional(numero, "número de factura", max_length=NUMERO_FACTURA_MAX)


def validar_comprobante_pago_form(comprobante: str) -> str:
    return validar_texto_opcional(comprobante, "referencia del comprobante", max_length=COMPROBANTE_MAX)


def validar_notas_pago_form(notas: str) -> str:
    return validar_texto_opcional(notas, "notas", max_length=NOTAS_PAGO_MAX)


__all__ = [
    "validar_fecha_pago_form",
    "validar_monto_pago_form",
    "validar_concepto_pago_form",
    "validar_numero_factura_pago_form",
    "validar_comprobante_pago_form",
    "validar_notas_pago_form",
]
