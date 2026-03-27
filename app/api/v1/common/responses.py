"""Builders de respuestas API estandarizadas."""

from typing import Iterable, TypeVar, Sequence

from app.api.v1.schemas import APIResponse, APIListResponse

T = TypeVar("T")


def ok(data: T, total: int = 1, message: str | None = None) -> APIResponse[T]:
    """Crea respuesta APIResponse exitosa."""
    return APIResponse(success=True, data=data, total=total, message=message)


def ok_list(items: Sequence[T] | Iterable[T], total: int | None = None, message: str | None = None) -> APIListResponse[T]:
    """Crea respuesta APIListResponse exitosa."""
    data = list(items)
    return APIListResponse(
        success=True,
        data=data,
        total=len(data) if total is None else total,
        message=message,
    )
