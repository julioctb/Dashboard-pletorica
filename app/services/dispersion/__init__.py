"""
Generadores de layout bancario para dispersión de nómina.

Exporta:
    LayoutBancario    — clase base abstracta
    LayoutBanregio    — TXT posiciones fijas
    LayoutHSBC        — TXT delimitado por pipes
    LayoutFondeadora  — CSV estándar
    GENERADORES       — mapa formato → clase
"""
from .base import LayoutBancario
from .layout_banregio import LayoutBanregio
from .layout_hsbc import LayoutHSBC
from .layout_fondeadora import LayoutFondeadora

# Mapa de formato → generador (usado por DispersionService)
GENERADORES: dict[str, type[LayoutBancario]] = {
    'TXT_POSICIONES': LayoutBanregio,
    'TXT_CSV':        LayoutHSBC,
    'CSV':            LayoutFondeadora,
}

__all__ = [
    'LayoutBancario',
    'LayoutBanregio',
    'LayoutHSBC',
    'LayoutFondeadora',
    'GENERADORES',
]
