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


# =============================================================================
# ENUMS DE PLAZA
# =============================================================================

class EstatusPlaza(str, Enum):
    """Estados posibles de una plaza"""
    VACANTE = 'VACANTE'
    OCUPADA = 'OCUPADA'
    SUSPENDIDA = 'SUSPENDIDA'
    CANCELADA = 'CANCELADA'

    @property
    def descripcion(self) -> str:
        """Descripción legible del estatus"""
        descripciones = {
            'VACANTE': 'Vacante',
            'OCUPADA': 'Ocupada',
            'SUSPENDIDA': 'Suspendida',
            'CANCELADA': 'Cancelada'
        }
        return descripciones.get(self.value, self.value)

    @property
    def es_asignable(self) -> bool:
        """Indica si la plaza puede ser asignada a un empleado"""
        return self == EstatusPlaza.VACANTE


# =============================================================================
# ENUMS DE EMPLEADO
# =============================================================================

class EstatusEmpleado(str, Enum):
    """Estados posibles de un empleado"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del estatus"""
        descripciones = {
            'ACTIVO': 'Activo',
            'INACTIVO': 'Inactivo',
            'SUSPENDIDO': 'Suspendido'
        }
        return descripciones.get(self.value, self.value)


class GeneroEmpleado(str, Enum):
    """Género del empleado"""
    MASCULINO = 'MASCULINO'
    FEMENINO = 'FEMENINO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del género"""
        descripciones = {
            'MASCULINO': 'Masculino',
            'FEMENINO': 'Femenino'
        }
        return descripciones.get(self.value, self.value)


class MotivoBaja(str, Enum):
    """Motivos de baja de empleado"""
    RENUNCIA = 'RENUNCIA'
    DESPIDO = 'DESPIDO'
    FIN_CONTRATO = 'FIN_CONTRATO'
    JUBILACION = 'JUBILACION'
    FALLECIMIENTO = 'FALLECIMIENTO'
    OTRO = 'OTRO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del motivo"""
        descripciones = {
            'RENUNCIA': 'Renuncia voluntaria',
            'DESPIDO': 'Despido',
            'FIN_CONTRATO': 'Fin de contrato',
            'JUBILACION': 'Jubilación',
            'FALLECIMIENTO': 'Fallecimiento',
            'OTRO': 'Otro motivo'
        }
        return descripciones.get(self.value, self.value)


# =============================================================================
# ENUMS DE HISTORIAL LABORAL
# =============================================================================

class EstatusHistorial(str, Enum):
    """Estados del empleado en historial laboral (refleja estatus del empleado)"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del estatus"""
        descripciones = {
            'ACTIVO': 'Activo',
            'INACTIVO': 'Inactivo',
            'SUSPENDIDO': 'Suspendido'
        }
        return descripciones.get(self.value, self.value)


class TipoMovimiento(str, Enum):
    """Tipos de movimiento en historial laboral"""
    ALTA = 'ALTA'
    ASIGNACION = 'ASIGNACION'
    CAMBIO_PLAZA = 'CAMBIO_PLAZA'
    SUSPENSION = 'SUSPENSION'
    REACTIVACION = 'REACTIVACION'
    BAJA = 'BAJA'

    @property
    def descripcion(self) -> str:
        """Descripción legible del tipo"""
        descripciones = {
            'ALTA': 'Alta en sistema',
            'ASIGNACION': 'Asignación a plaza',
            'CAMBIO_PLAZA': 'Cambio de plaza',
            'SUSPENSION': 'Suspensión',
            'REACTIVACION': 'Reactivación',
            'BAJA': 'Baja del sistema'
        }
        return descripciones.get(self.value, self.value)


# Alias para compatibilidad (deprecated)
MotivoFinHistorial = TipoMovimiento