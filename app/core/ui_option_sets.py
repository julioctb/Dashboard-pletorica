"""Factories de opciones UI reutilizables."""

from typing import Iterable


_ONBOARDING_LABELS = {
    "REGISTRADO": "Registrado",
    "DATOS_PENDIENTES": "Datos Pendientes",
    "DOCUMENTOS_PENDIENTES": "Docs Pendientes",
    "EN_REVISION": "En Revision",
    "APROBADO": "Aprobado",
    "RECHAZADO": "Rechazado",
    "ACTIVO_COMPLETO": "Activo Completo",
}


def _build_options(values: Iterable[str], include_todos: bool = True) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if include_todos:
        items.append({"value": "TODOS", "label": "Todos"})
    for value in values:
        items.append({"value": value, "label": _ONBOARDING_LABELS.get(value, value.title())})
    return items


def opciones_estatus_onboarding(
    *,
    include_registrado: bool = True,
    include_activo_completo: bool = True,
    include_todos: bool = True,
) -> list[dict[str, str]]:
    """Genera variantes de opciones de estatus onboarding por contexto."""
    base = [
        "REGISTRADO",
        "DATOS_PENDIENTES",
        "DOCUMENTOS_PENDIENTES",
        "EN_REVISION",
        "APROBADO",
        "RECHAZADO",
        "ACTIVO_COMPLETO",
    ]
    if not include_registrado:
        base.remove("REGISTRADO")
    if not include_activo_completo:
        base.remove("ACTIVO_COMPLETO")
    return _build_options(base, include_todos=include_todos)
