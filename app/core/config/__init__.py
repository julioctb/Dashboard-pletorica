import os
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
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL no esta configurada")
        if not cls.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY no esta configurada")
        # Advertencia si no hay service key (no es crítico)
        if not cls.SUPABASE_SERVICE_KEY:
            import logging
            logging.warning(
                "SUPABASE_SERVICE_KEY no configurada. "
                "Las operaciones administrativas (crear usuarios) no funcionarán."
            )
        return True
    
    @classmethod
    def requiere_autenticacion(cls) -> bool:
        """
        Determina si el sistema debe exigir login.

        Reglas:
        - DEBUG=true → Nunca exige auth (desarrollo local)
        - SKIP_AUTH=true → No exige auth (testing/staging)
        - Ambos false → Exige auth (producción)
        """
        if cls.DEBUG:
            return False
        if cls.SKIP_AUTH:
            return False
        return True

#validar configuración al importar
Config.validate_config()