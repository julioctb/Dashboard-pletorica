"""
Configuracion de la API REST.

Variables de entorno:
    API_AUTH_ENABLED: Habilitar autenticacion (default: false)
    API_CORS_ORIGINS: Origenes permitidos separados por coma (default: *)
"""
import os
from dotenv import load_dotenv

load_dotenv()


class APIConfig:
    """Configuracion de la capa API."""

    # Autenticacion
    AUTH_ENABLED: bool = os.getenv("API_AUTH_ENABLED", "false").lower() == "true"

    # CORS
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("API_CORS_ORIGINS", "*").split(",")
    ]

    # Metadata de la API
    TITLE: str = "API SaaS Nomina BUAP"
    DESCRIPTION: str = "API REST para integracion con aplicaciones moviles"
    VERSION: str = os.getenv("API_VERSION", os.getenv("APP_VERSION", "0.6.0"))
