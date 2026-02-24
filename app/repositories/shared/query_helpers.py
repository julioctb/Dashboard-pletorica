"""Helpers reutilizables para componer queries de Supabase."""


def apply_eq_filters(query, filters: dict | None):
    """Aplica filtros eq cuando el valor no es None/empty."""
    if not filters:
        return query

    for field, value in filters.items():
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        query = query.eq(field, value)
    return query


def apply_order(query, field: str, *, desc: bool = True):
    """Aplica orden estándar."""
    return query.order(field, desc=desc)


def apply_pagination(query, limit: int | None, offset: int = 0):
    """Aplica paginación basada en range de Supabase."""
    if not limit:
        return query
    return query.range(offset, offset + limit - 1)


def apply_date_range_filter(query, field: str, start: str | None = None, end: str | None = None):
    """Aplica filtros de rango de fecha opcionales."""
    if start:
        query = query.gte(field, start)
    if end:
        query = query.lte(field, end)
    return query


def build_ilike_or(term: str, fields: list[str]) -> str:
    """Construye OR para búsquedas ILIKE en múltiples campos."""
    term = term.strip()
    return ",".join([f"{field}.ilike.%{term}%" for field in fields if field])
