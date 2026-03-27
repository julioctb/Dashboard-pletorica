"""Portal UI surface for the cotizacion module."""

from app.presentation.pages.backoffice.cotizador import cotizador_detalle_page, cotizador_page
from app.presentation.pages.backoffice.cotizador.cotizador_detalle_state import CotizadorDetalleState
from app.presentation.pages.backoffice.cotizador.cotizador_state import CotizadorState

__all__ = [
    "CotizadorDetalleState",
    "CotizadorState",
    "cotizador_detalle_page",
    "cotizador_page",
]
