
"""
Interfaz del repositorio de Empresa.
Define el contrato que debe cumplir cualquier implementación.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from app.domain.entities.empresa_entity import (
    EmpresaEntity, 
    EmpresaResumenEntity,
    TipoEmpresa,
    EstatusEmpresa
)


class IEmpresaRepository(ABC):
    """
    Interfaz para el repositorio de Empresa.
    """
    
    @abstractmethod
    async def obtener_por_id(self, empresa_id: int) -> Optional[EmpresaEntity]:
        """Obtiene una empresa por su ID"""
        pass
    
    @abstractmethod
    async def obtener_todas(
        self, 
        incluir_inactivas: bool = False,
        limite: int = None,
        offset: int = 0
    ) -> List[EmpresaEntity]:
        """Obtiene todas las empresas con paginación opcional"""
        pass
    
    @abstractmethod
    async def crear(self, empresa: EmpresaEntity) -> EmpresaEntity:
        """Crea una nueva empresa"""
        pass
    
    @abstractmethod
    async def actualizar(self, empresa: EmpresaEntity) -> EmpresaEntity:
        """Actualiza una empresa existente"""
        pass
    
    @abstractmethod
    async def eliminar(self, empresa_id: int) -> bool:
        """Elimina una empresa (soft delete)"""
        pass
    
    @abstractmethod
    async def buscar_por_rfc(self, rfc: str) -> Optional[EmpresaEntity]:
        """Busca una empresa por su RFC"""
        pass
    
    @abstractmethod
    async def buscar_por_nombre(
        self, 
        termino: str,
        limite: int = 10
    ) -> List[EmpresaEntity]:
        """Busca empresas por nombre"""
        pass
    
    @abstractmethod
    async def buscar_por_tipo(
        self,
        tipo: TipoEmpresa,
        incluir_inactivas: bool = False
    ) -> List[EmpresaEntity]:
        """Obtiene empresas de un tipo específico"""
        pass
    
    @abstractmethod
    async def obtener_resumen(
        self,
        filtros: Dict[str, Any] = None,
        limite: int = 100,
        offset: int = 0
    ) -> List[EmpresaResumenEntity]:
        """Obtiene resumen de empresas para listados"""
        pass
    
    @abstractmethod
    async def contar(
        self,
        filtros: Dict[str, Any] = None
    ) -> int:
        """Cuenta empresas según filtros"""
        pass
    
    @abstractmethod
    async def existe_rfc(self, rfc: str, excluir_id: int = None) -> bool:
        """Verifica si existe un RFC"""
        pass
    
    @abstractmethod
    async def cambiar_estatus(
        self,
        empresa_id: int,
        nuevo_estatus: EstatusEmpresa
    ) -> EmpresaEntity:
        """Cambia el estatus de una empresa"""
        pass
    
    @abstractmethod
    async def puede_eliminar(self, empresa_id: int) -> tuple[bool, str]:
        """Verifica si una empresa puede ser eliminada"""
        pass
    
    @abstractmethod
    async def tiene_empleados(self, empresa_id: int) -> bool:
        """Verifica si una empresa tiene empleados"""
        pass
    
    @abstractmethod
    async def tiene_sedes(self, empresa_id: int) -> bool:
        """Verifica si una empresa tiene sedes"""
        pass