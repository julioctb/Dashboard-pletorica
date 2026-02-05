import os
import logging
from dotenv import load_dotenv

#cargar las variables de entorno .env
load_dotenv()


class Config:

    SUPABASE_URL= os.getenv("SUPABASE_URL")
    SUPABASE_KEY =os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

    # Control de autenticación
    SKIP_AUTH = os.getenv("SKIP_AUTH", "FALSE").lower() == "true"

    #CONFIGURACION DE LA APLICACION
    APP_NAME= os.getenv("APP_NAME","Sistema de Administración de Personal")
    APP_VERSION = os.getenv("APP_VERSION","0.0.1")
    DEBUG = os.getenv("DEBUG","FALSE").lower() == "true"

    #Validar que todas las clases criticas esten presentes

    @classmethod
    def validate_config(cls):
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL no esta configurada")
        if not cls.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY no esta configurada")
        # Advertencia si no hay service key (no es crítico)
        if not cls.SUPABASE_SERVICE_KEY:
            logging.warning(
                "SUPABASE_SERVICE_KEY no configurada. "
                "Las operaciones administrativas (crear usuarios) no funcionarán."
            )
        return True

    @classmethod
    def configurar_logging(cls):
        """
        Configura el nivel de logging segun DEBUG.

        - DEBUG=true → level=DEBUG solo para app.* (codigo propio)
        - DEBUG=false → level=WARNING para todo
        - Librerias externas siempre en WARNING (evita ruido de Reflex, websockets, etc.)
        """
        nivel = logging.DEBUG if cls.DEBUG else logging.WARNING
        logging.basicConfig(
            level=nivel,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
            force=True,
        )
        if cls.DEBUG:
            # Solo codigo propio en DEBUG, librerias externas en WARNING
            logging.getLogger("app").setLevel(logging.DEBUG)
            for lib in [
                "httpx", "httpcore", "hpack", "websockets",
                "watchfiles", "uvicorn", "starlette", "fastapi",
                "tokio_tungstenite", "tungstenite",
                "reflex", "sqlmodel", "alembic",
            ]:
                logging.getLogger(lib).setLevel(logging.WARNING)

    @classmethod
    def requiere_autenticacion(cls) -> bool:
        """
        Determina si el sistema debe exigir login.

        Solo SKIP_AUTH controla autenticacion.
        DEBUG controla logging y detalle de errores.
        """
        if cls.SKIP_AUTH:
            return False
        return True


#validar configuración y configurar logging al importar
Config.validate_config()
Config.configurar_logging()