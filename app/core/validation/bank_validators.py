"""Validadores y normalizadores bancarios compartidos."""

from __future__ import annotations

from typing import Optional

from app.core.text_utils import normalizar_mayusculas


_PESOS_CLABE = (3, 7, 1)
_CEROS_CLABE = "0" * 18


def normalizar_cuenta_bancaria(valor: Optional[str]) -> str:
    """Normaliza número de cuenta sin alterar dígitos internos."""
    return str(valor or "").strip()


def normalizar_clabe_interbancaria(valor: Optional[str]) -> str:
    """Normaliza CLABE sin alterar dígitos internos."""
    return str(valor or "").strip()


def normalizar_nombre_banco(valor: Optional[str]) -> str:
    """Normaliza nombre del banco a mayúsculas."""
    return normalizar_mayusculas(valor)


def calcular_digito_verificador_clabe(clabe_17: str) -> int:
    """Calcula el dígito verificador de una CLABE a partir de sus primeros 17 dígitos."""
    suma = 0
    for indice, digito in enumerate(clabe_17):
        producto = int(digito) * _PESOS_CLABE[indice % 3]
        suma += producto % 10
    return (10 - (suma % 10)) % 10


def verificar_clabe(clabe: Optional[str]) -> bool:
    """Verifica longitud, formato y dígito verificador de una CLABE."""
    clabe_limpia = normalizar_clabe_interbancaria(clabe)
    if len(clabe_limpia) != 18 or not clabe_limpia.isdigit():
        return False
    if clabe_limpia == _CEROS_CLABE:
        return False
    esperado = calcular_digito_verificador_clabe(clabe_limpia[:17])
    return esperado == int(clabe_limpia[17])


def cuenta_parece_clabe(cuenta: Optional[str]) -> bool:
    """Detecta cuando una CLABE válida fue capturada en el campo de número de cuenta."""
    cuenta_limpia = normalizar_cuenta_bancaria(cuenta)
    return len(cuenta_limpia) == 18 and verificar_clabe(cuenta_limpia)


__all__ = [
    "normalizar_cuenta_bancaria",
    "normalizar_clabe_interbancaria",
    "normalizar_nombre_banco",
    "calcular_digito_verificador_clabe",
    "verificar_clabe",
    "cuenta_parece_clabe",
]
