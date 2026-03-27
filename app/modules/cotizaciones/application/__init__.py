"""Application services for the cotizacion module."""

from app.modules.cotizaciones.application import (
    contract_conversion as contract_conversion_module,
)
from app.modules.cotizaciones.application import mutations as mutations_module
from app.modules.cotizaciones.application import pricing as pricing_module
from app.modules.cotizaciones.application import queries as queries_module
from app.modules.cotizaciones.application import versioning as versioning_module


def _export_public_names(module) -> list[str]:
    names = list(getattr(module, "__all__", []))
    for name in names:
        globals()[name] = getattr(module, name)
    return names

__all__ = []
__all__ += _export_public_names(queries_module)
__all__ += _export_public_names(mutations_module)
__all__ += _export_public_names(pricing_module)
__all__ += _export_public_names(versioning_module)
__all__ += _export_public_names(contract_conversion_module)
