"""Infrastructure adapters for the employee module."""

from core.modules.empleados.infrastructure import repositories as repositories_module


def _export_public_names(module) -> list[str]:
    names = list(getattr(module, "__all__", []))
    for name in names:
        globals()[name] = getattr(module, name)
    return names

__all__ = _export_public_names(repositories_module)
