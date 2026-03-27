"""Canonical application surface for UI orchestration imports."""

from app.domain import services as legacy_services
from app.domain.services.archivo_service import ArchivoValidationError
from app.domain.services.empresa_documento_service import empresa_documento_service
from app.domain.services.super_admin_dashboard_service import super_admin_dashboard_service


def _export_public_names(module) -> list[str]:
    names = list(getattr(module, "__all__", []))
    for name in names:
        globals()[name] = getattr(module, name)
    return names


__all__ = _export_public_names(legacy_services)
if "ArchivoValidationError" not in __all__:
    __all__.append("ArchivoValidationError")
if "empresa_documento_service" not in __all__:
    __all__.append("empresa_documento_service")
if "super_admin_dashboard_service" not in __all__:
    __all__.append("super_admin_dashboard_service")
