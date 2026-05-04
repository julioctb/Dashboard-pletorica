"""Application services for the employee module."""

from app.modules.empleados.application import banking as banking_module
from app.modules.empleados.application import bulk_upload as bulk_upload_module
from app.modules.empleados.application import mutations as mutations_module
from app.modules.empleados.application import offboarding as offboarding_module
from app.modules.empleados.application import onboarding_sync as onboarding_sync_module
from app.modules.empleados.application import queries as queries_module
from app.modules.empleados.application import restrictions as restrictions_module


def _export_public_names(module) -> list[str]:
    names = list(getattr(module, "__all__", []))
    for name in names:
        globals()[name] = getattr(module, name)
    return names

__all__ = []
__all__ += _export_public_names(queries_module)
__all__ += _export_public_names(mutations_module)
__all__ += _export_public_names(restrictions_module)
__all__ += _export_public_names(offboarding_module)
__all__ += _export_public_names(banking_module)
__all__ += _export_public_names(bulk_upload_module)
__all__ += _export_public_names(onboarding_sync_module)
