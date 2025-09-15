import os
from dotenv import load_dotenv

#cargar las variables de entorno .env
load_dotenv()

class Config:

    SUPABASE_URL= os.getenv("SUPABASE_URL")
    SUPABASE_KEY =os.getenv("SUPABASE_KEY")

    #CONFIGURACION DE LA APLICACION
    APP_NAME= os.getenv("APP_NAME","Sistema de Administración de Personal")
    APP_VERSION = os.getenv("APP_VERSION","0.0.1")
    DEBUG = os.getenv("DEBUG","FALSE").lower == "true"

    #Validar que todas las clases criticas esten presentes

    @classmethod
    def validate_config(cls):
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL no esta configurada")
        if not cls.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY no esta configurada")
        return True

#validar configuración al importar
Config.validate_config()