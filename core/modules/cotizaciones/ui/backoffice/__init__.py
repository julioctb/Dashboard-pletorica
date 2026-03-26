"""Backoffice UI surface for the cotizacion module."""

from core.presentation.pages.backoffice.cotizador import cotizador_detalle_page, cotizador_page
from core.presentation.pages.backoffice.cotizador.cotizador_detalle_state import CotizadorDetalleState
from core.presentation.pages.backoffice.cotizador.cotizador_state import CotizadorState

__all__ = [
    "CotizadorDetalleState",
    "CotizadorState",
    "cotizador_detalle_page",
    "cotizador_page",
]
