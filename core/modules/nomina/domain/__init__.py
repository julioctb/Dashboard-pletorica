"""Domain surface for the nomina module."""

from core.modules.nomina.domain import catalogs as catalogs_module
from core.modules.nomina.domain import enums as enums_module
from core.modules.nomina.domain import models as models_module


def _export_public_names(module) -> list[str]:
    names = list(getattr(module, "__all__", []))
    for name in names:
        globals()[name] = getattr(module, name)
    return names

__all__ = []
__all__ += _export_public_names(models_module)
__all__ += _export_public_names(enums_module)
__all__ += _export_public_names(catalogs_module)
