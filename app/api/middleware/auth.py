"""
Middleware de autenticacion para la API.

Comportamiento:
- API_AUTH_ENABLED=false: Permite todas las peticiones (desarrollo)
- API_AUTH_ENABLED=true: Exige header Authorization: Bearer <token>

Rutas excluidas (siempre permitidas):
- Rutas de Reflex: /ping/, /_event, /_upload
- Documentacion: /api/docs, /api/redoc, /api/openapi.json
- Rutas que no empiezan con /api/
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.config import APIConfig

logger = logging.getLogger(__name__)

# Rutas que nunca requieren autenticacion
RUTAS_EXCLUIDAS = {
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
}

# Prefijos que no son parte de la API
PREFIJOS_EXCLUIDOS = (
    "/ping",
    "/_event",
    "/_upload",
)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware de autenticacion con bypass configurable.

    Si API_AUTH_ENABLED=false, no interviene.
    Si API_AUTH_ENABLED=true, valida que exista Bearer token
    en las rutas /api/*.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Si auth esta deshabilitado, pasar todo
        if not APIConfig.AUTH_ENABLED:
            return await call_next(request)

        # No interceptar rutas que no son de la API
        if not path.startswith("/api/"):
            return await call_next(request)

        # No interceptar rutas excluidas (docs, etc.)
        if path in RUTAS_EXCLUIDAS:
            return await call_next(request)

        # No interceptar rutas internas de Reflex
        if path.startswith(PREFIJOS_EXCLUIDOS):
            return await call_next(request)

        # Validar Authorization header
        auth_header = request.headers.get("authorization", "")

        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "data": None,
                    "total": 0,
                    "message": "Header Authorization requerido",
                },
            )

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "data": None,
                    "total": 0,
                    "message": "Formato invalido. Usar: Bearer <token>",
                },
            )

        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "data": None,
                    "total": 0,
                    "message": "Token vacio",
                },
            )

        # TODO: Validar JWT con Supabase en fase futura
        logger.debug(f"Token recibido para {path} (validacion JWT pendiente)")

        return await call_next(request)
