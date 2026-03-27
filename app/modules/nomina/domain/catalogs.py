"""Nomina reference catalogs grouped under the feature namespace."""

from app.core.catalogs import fiscal as fiscal_catalogs
from app.core.catalogs import laboral as laboral_catalogs
from app.core.catalogs import nomina as nomina_catalogs
from app.core.catalogs import sistema as sistema_catalogs


def _export_public_names(module) -> list[str]:
    names = list(getattr(module, "__all__", []))
    for name in names:
        globals()[name] = getattr(module, name)
    return names

catalogs___all__: list[str] = []
catalogs___all__ += _export_public_names(fiscal_catalogs)
catalogs___all__ += _export_public_names(laboral_catalogs)
catalogs___all__ += _export_public_names(nomina_catalogs)
catalogs___all__ += _export_public_names(sistema_catalogs)

__all__ = catalogs___all__
