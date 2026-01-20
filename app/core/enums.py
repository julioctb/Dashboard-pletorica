"""
Enums centralizados del sistema.

Este módulo contiene todos los enums compartidos entre módulos.
Centralizar enums evita duplicación y garantiza consistencia.
"""
from enum import Enum


# =============================================================================
# ENUMS DE ESTATUS
# =============================================================================

class Estatus(str, Enum):
    """Estatus genérico para entidades (activo/inactivo)"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'


class EstatusEmpresa(str, Enum):
    """Estados posibles de una empresa (incluye SUSPENDIDO)"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'


# =============================================================================
# ENUMS DE TIPO
# =============================================================================

class TipoEmpresa(str, Enum):
    """Tipos de empresa en el sistema"""
    NOMINA = 'NOMINA'
    MANTENIMIENTO = 'MANTENIMIENTO'

# =============================================================================
# ENUMS DE CONTRATO
# =============================================================================

class TipoContrato(str, Enum):
    """Tipos de contrato"""
    ADQUISICION = 'ADQUISICION'
    SERVICIOS = 'SERVICIOS'

    @property
    def descripcion(self) -> str:
        """Descripción legible del tipo"""
        descripciones = {
            'ADQUISICION': 'Adquisición',
            'SERVICIOS': 'Servicios'
        }
        return descripciones.get(self.value, self.value)


class ModalidadAdjudicacion(str, Enum):
    """Modalidades de adjudicación de contratos"""
    INVITACION_3 = 'INVITACION_3'
    ADJUDICACION_DIRECTA = 'ADJUDICACION_DIRECTA'
    LICITACION_PUBLICA = 'LICITACION_PUBLICA'
    
    @property
    def descripcion(self) -> str:
        """Descripción legible de la modalidad"""
        descripciones = {
            'INVITACION_3': 'Invitación a cuando menos 3 personas',
            'ADJUDICACION_DIRECTA': 'Adjudicación directa',
            'LICITACION_PUBLICA': 'Licitación pública'
        }
        return descripciones.get(self.value, self.value)


class TipoDuracion(str, Enum):
    """Tipos de duración de contratos"""
    TIEMPO_DETERMINADO = 'TIEMPO_DETERMINADO'
    TIEMPO_INDEFINIDO = 'TIEMPO_INDEFINIDO'
    OBRA_DETERMINADA = 'OBRA_DETERMINADA'
    
    @property
    def descripcion(self) -> str:
        """Descripción legible del tipo"""
        descripciones = {
            'TIEMPO_DETERMINADO': 'Tiempo determinado',
            'TIEMPO_INDEFINIDO': 'Tiempo indefinido',
            'OBRA_DETERMINADA': 'Obra determinada'
        }
        return descripciones.get(self.value, self.value)


class EstatusContrato(str, Enum):
    """Estados posibles de un contrato"""
    BORRADOR = 'BORRADOR'
    ACTIVO = 'ACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'
    VENCIDO = 'VENCIDO'
    CANCELADO = 'CANCELADO'
    CERRADO = 'CERRADO'  # Contrato pagado y finalizado