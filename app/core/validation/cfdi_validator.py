"""
Validador de XML CFDI (Comprobante Fiscal Digital por Internet).

Valida que un XML CFDI contenga los datos esperados:
- RFC emisor y receptor
- Monto total dentro de tolerancia
- Folio fiscal (UUID del timbrado)

Usa defusedxml para parsing seguro (previene XXE attacks).
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# RFC de la BUAP (receptor esperado en todas las facturas)
RFC_BUAP = "BUA520801GS2"

# Namespace CFDI 4.0 (SAT)
NS_CFDI = "http://www.sat.gob.mx/cfd/4"
NS_TFD = "http://www.sat.gob.mx/TimbreFiscalDigital"


class ResultadoValidacionCFDI(BaseModel):
    """Resultado de la validacion de un XML CFDI."""
    es_valido: bool = False
    rfc_emisor: Optional[str] = None
    rfc_receptor: Optional[str] = None
    monto_total: Optional[Decimal] = None
    folio_fiscal: Optional[str] = None
    errores: List[str] = []


def validar_cfdi(
    xml_bytes: bytes,
    rfc_emisor_esperado: str,
    rfc_receptor_esperado: str = RFC_BUAP,
    monto_esperado: Optional[Decimal] = None,
    tolerancia_monto: Decimal = Decimal("1"),
) -> ResultadoValidacionCFDI:
    """
    Valida un XML CFDI contra los datos esperados.

    Args:
        xml_bytes: Contenido del XML en bytes
        rfc_emisor_esperado: RFC de la empresa que emite la factura
        rfc_receptor_esperado: RFC del receptor (default: BUAP)
        monto_esperado: Monto total esperado (opcional, si se pasa se valida)
        tolerancia_monto: Diferencia aceptable en el monto (default: $1)

    Returns:
        ResultadoValidacionCFDI con los datos extraidos y errores encontrados
    """
    try:
        import defusedxml.ElementTree as ET
    except ImportError:
        return ResultadoValidacionCFDI(
            errores=["defusedxml no esta instalado. Ejecute: pip install defusedxml"]
        )

    errores = []
    rfc_emisor = None
    rfc_receptor = None
    monto_total = None
    folio_fiscal = None

    try:
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        logger.error(f"Error parseando XML CFDI: {e}")
        return ResultadoValidacionCFDI(
            errores=[f"El archivo XML no es valido: {str(e)}"]
        )

    # Extraer datos del comprobante
    # Intentar con namespace CFDI 4.0 primero, luego sin namespace
    comprobante = root
    if comprobante.tag != f"{{{NS_CFDI}}}Comprobante" and "Comprobante" not in comprobante.tag:
        errores.append("El XML no parece ser un CFDI valido (falta nodo Comprobante)")
        return ResultadoValidacionCFDI(errores=errores)

    # Total del comprobante
    total_str = comprobante.get("Total")
    if total_str:
        try:
            monto_total = Decimal(total_str)
        except (InvalidOperation, ValueError):
            errores.append(f"Monto total invalido en el CFDI: {total_str}")

    # Emisor
    emisor = _buscar_nodo(root, "Emisor")
    if emisor is not None:
        rfc_emisor = emisor.get("Rfc")
    else:
        errores.append("No se encontro el nodo Emisor en el CFDI")

    # Receptor
    receptor = _buscar_nodo(root, "Receptor")
    if receptor is not None:
        rfc_receptor = receptor.get("Rfc")
    else:
        errores.append("No se encontro el nodo Receptor en el CFDI")

    # Timbre Fiscal Digital (folio fiscal)
    complemento = _buscar_nodo(root, "Complemento")
    if complemento is not None:
        tfd = None
        for child in complemento:
            if "TimbreFiscalDigital" in child.tag:
                tfd = child
                break
        if tfd is not None:
            folio_fiscal = tfd.get("UUID")
        else:
            errores.append("No se encontro el TimbreFiscalDigital (sin timbrar)")
    else:
        errores.append("No se encontro el nodo Complemento en el CFDI")

    # Validaciones de negocio
    if rfc_emisor and rfc_emisor_esperado:
        if rfc_emisor.upper() != rfc_emisor_esperado.upper():
            errores.append(
                f"RFC emisor no coincide: esperado {rfc_emisor_esperado}, "
                f"encontrado {rfc_emisor}"
            )

    if rfc_receptor and rfc_receptor_esperado:
        if rfc_receptor.upper() != rfc_receptor_esperado.upper():
            errores.append(
                f"RFC receptor no coincide: esperado {rfc_receptor_esperado}, "
                f"encontrado {rfc_receptor}"
            )

    if monto_esperado is not None and monto_total is not None:
        diferencia = abs(monto_total - monto_esperado)
        if diferencia > tolerancia_monto:
            errores.append(
                f"Monto total no coincide: esperado ${monto_esperado}, "
                f"encontrado ${monto_total} (diferencia: ${diferencia})"
            )

    return ResultadoValidacionCFDI(
        es_valido=len(errores) == 0,
        rfc_emisor=rfc_emisor,
        rfc_receptor=rfc_receptor,
        monto_total=monto_total,
        folio_fiscal=folio_fiscal,
        errores=errores,
    )


def _buscar_nodo(root, nombre_local: str):
    """Busca un nodo por nombre local, con o sin namespace."""
    # Con namespace CFDI 4.0
    nodo = root.find(f"{{{NS_CFDI}}}{nombre_local}")
    if nodo is not None:
        return nodo

    # Sin namespace (fallback)
    nodo = root.find(nombre_local)
    if nodo is not None:
        return nodo

    # Busqueda recursiva por nombre local
    for child in root.iter():
        if child.tag.endswith(f"}}{nombre_local}") or child.tag == nombre_local:
            return child

    return None
