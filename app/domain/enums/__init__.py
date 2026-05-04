"""Domain enum surface decoupled from the legacy ``core.core`` package."""

from app.core import enums as legacy_enums


def _export_public_names(module) -> list[str]:
    names = list(getattr(module, "__all__", []))
    if not names:
        names = [name for name in dir(module) if not name.startswith("_")]
    for name in names:
        globals()[name] = getattr(module, name)
    return names


__all__ = _export_public_names(legacy_enums)
