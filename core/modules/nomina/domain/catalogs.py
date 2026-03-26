"""Nomina reference catalogs grouped under the feature namespace."""

from core.core.catalogs import fiscal as fiscal_catalogs
from core.core.catalogs import laboral as laboral_catalogs
from core.core.catalogs import nomina as nomina_catalogs
from core.core.catalogs import sistema as sistema_catalogs
from core.core.catalogs.fiscal import *
from core.core.catalogs.laboral import *
from core.core.catalogs.nomina import *
from core.core.catalogs.sistema import *

catalogs___all__: list[str] = []
catalogs___all__ += list(getattr(fiscal_catalogs, "__all__", []))
catalogs___all__ += list(getattr(laboral_catalogs, "__all__", []))
catalogs___all__ += list(getattr(nomina_catalogs, "__all__", []))
catalogs___all__ += list(getattr(sistema_catalogs, "__all__", []))

__all__ = catalogs___all__
