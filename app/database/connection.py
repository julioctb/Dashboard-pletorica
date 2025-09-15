from supabase import create_client, Client
from app.config import Config

#Manejar la conexión y operaciones de supabase
class DatabaseManager:
    
    def __init__(self):
        self.supabase: Client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY
        )

#Retorna el cliente de Supabase
def get_client(self) -> Client:
    return self.supabase

#Prueba la conexion con la base de datos
def test_connection(self) -> bool:
    try:
        result = self.supabase.table("empresas").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"Error de conexion: {e}")
        return False
    
#instancia global del manejador de base de datos
db_manager = DatabaseManager()