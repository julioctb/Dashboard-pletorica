"""
Gestor de conexion a base de datos Supabase.

Usa service_role key para el cliente principal (bypass RLS).
La seguridad de acceso se maneja en la capa de servicios (AuthState, roles).
RLS protege contra acceso directo a la BD (API REST, client SDK).
"""
import logging
from supabase import create_client, Client
from app.core.config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manejador singleton de la conexion a Supabase"""

    def __init__(self):
        """
        Inicializa el cliente de Supabase.

        Usa service_role key si esta disponible (bypass RLS).
        Fallback a anon key si no hay service key.
        """
        # Preferir service_role key para operaciones backend
        key = Config.SUPABASE_SERVICE_KEY or Config.SUPABASE_KEY
        if Config.SUPABASE_SERVICE_KEY:
            logger.debug("DatabaseManager usando service_role key (bypass RLS)")
        else:
            logger.warning(
                "DatabaseManager usando anon key. "
                "Las queries seran filtradas por RLS."
            )

        self.supabase: Client = create_client(Config.SUPABASE_URL, key)

        # Cliente con anon key para operaciones de auth del usuario
        self._anon_client: Client = create_client(
            Config.SUPABASE_URL, Config.SUPABASE_KEY
        )

    def get_client(self) -> Client:
        """Retorna el cliente principal (service_role, bypass RLS)."""
        return self.supabase

    def get_anon_client(self) -> Client:
        """Retorna el cliente con anon key (para auth de usuario)."""
        return self._anon_client

    def test_connection(self) -> bool:
        """Prueba la conexion con la base de datos"""
        try:
            self.supabase.table("empresas").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Error de conexion: {e}")
            return False


# Instancia global del manejador de base de datos (singleton)
db_manager = DatabaseManager()
