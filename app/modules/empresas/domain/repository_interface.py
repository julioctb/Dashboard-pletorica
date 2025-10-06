"""Interfaz del repositorio de empresas"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Empresa

class IEmpresaRepository(ABC):
    """Define qué operaciones necesitamos, no cómo hacerlas"""
    
    @abstractmethod
    async def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        pass
    
    @abstractmethod
    async def obtener_todas(self, incluir_inactivas: bool = False) -> List[Empresa]:
        pass
    
    @abstractmethod
    async def crear(self, empresa: Empresa) -> Empresa:
        pass
    
    @abstractmethod
    async def actualizar(self, empresa: Empresa) -> Empresa:
        pass
    
    @abstractmethod
    async def eliminar(self, empresa_id: int) -> bool:
        pass
    
    @abstractmethod
    async def existe_rfc(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        pass
