#Importar servicios separados
from .empresa_service import empresa_service, EmpresaService

#Exportar para uso externo
__all__ = [
    "empresa_service",
    "EmpresaService"
]