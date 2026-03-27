"""Application services for the nomina module."""

from core.modules.nomina.application import calculo as calculo_module
from core.modules.nomina.application import catalogos as catalogos_module
from core.modules.nomina.application import dispersion as dispersion_module
from core.modules.nomina.application import periodos as periodos_module


def _export_public_names(module) -> list[str]:
    names = list(getattr(module, "__all__", []))
    for name in names:
        globals()[name] = getattr(module, name)
    return names

__all__ = []
__all__ += _export_public_names(periodos_module)
__all__ += _export_public_names(calculo_module)
__all__ += _export_public_names(dispersion_module)
__all__ += _export_public_names(catalogos_module)
