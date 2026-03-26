"""
Schemas compartidos para respuestas de la API.

Todas las respuestas usan el formato estandar APIResponse.
"""
from typing import TypeVar, Generic, Optional, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Respuesta estandar de la API."""
    success: bool
    data: Optional[T] = None
    total: int = 0
    message: Optional[str] = None


class APIListResponse(BaseModel, Generic[T]):
    """Respuesta estandar para listas."""
    success: bool
    data: List[T] = Field(default_factory=list)
    total: int = 0
    message: Optional[str] = None
