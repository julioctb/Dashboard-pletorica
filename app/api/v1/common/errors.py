"""Traduccion de excepciones de dominio a HTTPException."""

import logging

from fastapi import HTTPException

from app.core.exceptions import NotFoundError, DatabaseError, ValidationError, DuplicateError, BusinessRuleError


def raise_http_from_exc(exc: Exception, logger: logging.Logger, context: str) -> None:
    """Registra y lanza una HTTPException apropiada para errores comunes."""
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, (ValidationError, DuplicateError, BusinessRuleError)):
        raise HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, DatabaseError):
        logger.error("Error de BD %s: %s", context, exc)
        raise HTTPException(status_code=500, detail="Error de base de datos")

    logger.error("Error inesperado %s: %s", context, exc)
    raise HTTPException(status_code=500, detail="Error interno del servidor")
