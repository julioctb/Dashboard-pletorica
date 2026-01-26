"""
Dependencias compartidas de FastAPI.

Inyeccion de dependencias para endpoints:
- Servicios singleton
- Validacion de autenticacion
"""
from fastapi import Depends, HTTPException, Header
from typing import Optional

from app.api.config import APIConfig


async def verificar_auth(
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    """
    Verifica el header Authorization.

    Si API_AUTH_ENABLED=false, permite todo.
    Si API_AUTH_ENABLED=true, exige Bearer token (sin validar JWT aun).

    Returns:
        Token extraido o None si auth deshabilitado
    """
    if not APIConfig.AUTH_ENABLED:
        return None

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Header Authorization requerido",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Formato invalido. Usar: Bearer <token>",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Token vacio",
        )

    # TODO: Validar JWT con Supabase en fase futura
    return token
