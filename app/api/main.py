"""
Configuracion principal de FastAPI.

Esta instancia se monta en Reflex usando api_transformer.
Proporciona endpoints REST bajo /api/v1/.

Rutas:
    /api/docs       - Swagger UI
    /api/redoc      - ReDoc
    /api/openapi.json - OpenAPI schema
    /api/v1/...     - Endpoints de la API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.config import APIConfig
from app.api.middleware.auth import AuthMiddleware
from app.api.v1.router import api_v1_router


def create_api_app() -> FastAPI:
    """Crea y configura la instancia de FastAPI."""

    app = FastAPI(
        title=APIConfig.TITLE,
        description=APIConfig.DESCRIPTION,
        version=APIConfig.VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS para Flutter y otros clientes externos
    app.add_middleware(
        CORSMiddleware,
        allow_origins=APIConfig.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware de autenticacion
    app.add_middleware(AuthMiddleware)

    # Router v1
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


# Instancia global de la API
api_app = create_api_app()
