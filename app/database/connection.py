"""
Gestor de conexión a base de datos Supabase.
Consolidado desde app/database/connection.py y app/modules/shared/database/connection.py
"""
from supabase import create_client, Client
from app.core.config import Config


class DatabaseManager:
    """Manejador singleton de la conexión a Supabase"""

    def __init__(self):
        """Inicializa el cliente de Supabase con credenciales de configuración"""
        self.supabase: Client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY
        )

    def get_client(self) -> Client:
        """Retorna el cliente de Supabase"""
        return self.supabase

    def test_connection(self) -> bool:
        """Prueba la conexión con la base de datos"""
        try:
            result = self.supabase.table("empresas").select("id").limit(1).execute()
            return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False


# Instancia global del manejador de base de datos (singleton)
db_manager = DatabaseManager()
