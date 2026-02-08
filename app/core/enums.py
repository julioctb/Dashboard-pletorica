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


class AccionRestriccion(str, Enum):
    """Tipos de accion en el log de restricciones de empleados"""
    RESTRICCION = 'RESTRICCION'
    LIBERACION = 'LIBERACION'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'RESTRICCION': 'Restriccion aplicada',
            'LIBERACION': 'Restriccion liberada'
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

class TipoMovimiento(str, Enum):
    """Tipos de movimiento en historial laboral"""
    ALTA = 'ALTA'
    ASIGNACION = 'ASIGNACION'
    CAMBIO_PLAZA = 'CAMBIO_PLAZA'
    SUSPENSION = 'SUSPENSION'
    REACTIVACION = 'REACTIVACION'
    BAJA = 'BAJA'
    REINGRESO = 'REINGRESO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del tipo"""
        descripciones = {
            'ALTA': 'Alta en sistema',
            'ASIGNACION': 'Asignación a plaza',
            'CAMBIO_PLAZA': 'Cambio de plaza',
            'SUSPENSION': 'Suspensión',
            'REACTIVACION': 'Reactivación',
            'BAJA': 'Baja del sistema',
            'REINGRESO': 'Reingreso a otra empresa'
        }
        return descripciones.get(self.value, self.value)


# =============================================================================
# ENUMS DE REQUISICIÓN
# =============================================================================

class EstadoRequisicion(str, Enum):
    """Estados posibles de una requisición"""
    BORRADOR = 'BORRADOR'
    ENVIADA = 'ENVIADA'
    EN_REVISION = 'EN REVISION'
    APROBADA = 'APROBADA'
    ADJUDICADA = 'ADJUDICADA'
    CONTRATADA = 'CONTRATADA'
    CANCELADA = 'CANCELADA'

    @property
    def descripcion(self) -> str:
        """Descripción legible del estado"""
        descripciones = {
            'BORRADOR': 'Borrador',
            'ENVIADA': 'Enviada',
            'EN_REVISION': 'En revisión',
            'APROBADA': 'Aprobada',
            'ADJUDICADA': 'Adjudicada',
            'CONTRATADA': 'Contratada',
            'CANCELADA': 'Cancelada',
        }
        return descripciones.get(self.value, self.value)

    @property
    def es_estado_final(self) -> bool:
        """Indica si el estado es final (no permite más transiciones)"""
        return self in (EstadoRequisicion.CONTRATADA, EstadoRequisicion.CANCELADA)


class TipoContratacion(str, Enum):
    """Tipos de contratación para requisiciones"""
    ADQUISICION = 'ADQUISICION'
    ARRENDAMIENTO = 'ARRENDAMIENTO'
    SERVICIO = 'SERVICIO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del tipo"""
        descripciones = {
            'ADQUISICION': 'Adquisición',
            'ARRENDAMIENTO': 'Arrendamiento',
            'SERVICIO': 'Servicio',
        }
        return descripciones.get(self.value, self.value)


class GrupoConfiguracion(str, Enum):
    """Grupos de configuración para valores default de requisiciones"""
    AREA_REQUIRENTE = 'AREA_REQUIRENTE'
    FIRMAS = 'FIRMAS'
    ENTREGA = 'ENTREGA'

    @property
    def descripcion(self) -> str:
        """Descripción legible del grupo"""
        descripciones = {
            'AREA_REQUIRENTE': 'Área Requirente',
            'FIRMAS': 'Firmas',
            'ENTREGA': 'Entrega',
        }
        return descripciones.get(self.value, self.value)


# =============================================================================
# ENUMS DE SEDE
# =============================================================================

class TipoSede(str, Enum):
    """Clasificación de sedes BUAP"""
    # Ubicaciones físicas (típicamente es_ubicacion_fisica = True)
    CAMPUS = 'CAMPUS'
    COMPLEJO_REGIONAL = 'COMPLEJO_REGIONAL'
    FACULTAD = 'FACULTAD'
    PREPARATORIA = 'PREPARATORIA'
    INSTITUTO = 'INSTITUTO'
    HOSPITAL = 'HOSPITAL'
    CENTRO = 'CENTRO'
    BIBLIOTECA = 'BIBLIOTECA'
    LIBRERIA = 'LIBRERIA'
    MUSEO = 'MUSEO'
    EDIFICIO = 'EDIFICIO'
    # Unidades administrativas (típicamente es_ubicacion_fisica = False)
    DIRECCION = 'DIRECCION'
    COORDINACION = 'COORDINACION'
    SECRETARIA = 'SECRETARIA'
    VICERRECTORIA = 'VICERRECTORIA'
    PROYECTO = 'PROYECTO'
    UNIDAD = 'UNIDAD'
    OTRO = 'OTRO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del tipo"""
        descripciones = {
            'CAMPUS': 'Campus',
            'COMPLEJO_REGIONAL': 'Complejo Regional',
            'FACULTAD': 'Facultad',
            'PREPARATORIA': 'Preparatoria',
            'INSTITUTO': 'Instituto',
            'HOSPITAL': 'Hospital',
            'CENTRO': 'Centro',
            'BIBLIOTECA': 'Biblioteca',
            'LIBRERIA': 'Librería',
            'MUSEO': 'Museo',
            'EDIFICIO': 'Edificio',
            'DIRECCION': 'Dirección',
            'COORDINACION': 'Coordinación',
            'SECRETARIA': 'Secretaría',
            'VICERRECTORIA': 'Vicerrectoría',
            'PROYECTO': 'Proyecto',
            'UNIDAD': 'Unidad',
            'OTRO': 'Otro',
        }
        return descripciones.get(self.value, self.value)

    @property
    def prefijo_codigo(self) -> str:
        """Prefijo para códigos: CAM, FAC, DIR, etc."""
        prefijos = {
            'CAMPUS': 'CAM',
            'COMPLEJO_REGIONAL': 'CRE',
            'FACULTAD': 'FAC',
            'PREPARATORIA': 'PRE',
            'INSTITUTO': 'INS',
            'HOSPITAL': 'HOS',
            'CENTRO': 'CEN',
            'BIBLIOTECA': 'BIB',
            'LIBRERIA': 'LIB',
            'MUSEO': 'MUS',
            'EDIFICIO': 'EDI',
            'DIRECCION': 'DIR',
            'COORDINACION': 'COO',
            'SECRETARIA': 'SEC',
            'VICERRECTORIA': 'VIC',
            'PROYECTO': 'PRO',
            'UNIDAD': 'UNI',
            'OTRO': 'OTR',
        }
        return prefijos.get(self.value, 'OTR')


class NivelContacto(str, Enum):
    """Nivel jerárquico de contactos BUAP"""
    DIRECTOR = 'DIRECTOR'
    SUBDIRECTOR = 'SUBDIRECTOR'
    COORDINADOR = 'COORDINADOR'
    JEFE_DEPARTAMENTO = 'JEFE_DEPARTAMENTO'
    ADMINISTRATIVO = 'ADMINISTRATIVO'
    OPERATIVO = 'OPERATIVO'
    OTRO = 'OTRO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del nivel"""
        descripciones = {
            'DIRECTOR': 'Director',
            'SUBDIRECTOR': 'Subdirector',
            'COORDINADOR': 'Coordinador',
            'JEFE_DEPARTAMENTO': 'Jefe de Departamento',
            'ADMINISTRATIVO': 'Administrativo',
            'OPERATIVO': 'Operativo',
            'OTRO': 'Otro',
        }
        return descripciones.get(self.value, self.value)


# =============================================================================
# ENUMS DE USUARIO
# =============================================================================
# Agregar este bloque a app/core/enums.py antes del cierre del archivo

class RolUsuario(str, Enum):
    """
    Roles de usuario en el sistema.
    
    - ADMIN: Personal de BUAP con acceso completo
    - CLIENT: Usuario de empresa proveedora con acceso limitado a sus empresas
    """
    ADMIN = 'admin'
    CLIENT = 'client'

    @property
    def descripcion(self) -> str:
        """Descripción legible del rol"""
        descripciones = {
            'admin': 'Administrador (BUAP)',
            'client': 'Cliente (Empresa proveedora)'
        }
        return descripciones.get(self.value, self.value)

    @property
    def es_admin(self) -> bool:
        """Indica si el rol tiene privilegios de administrador"""
        return self == RolUsuario.ADMIN
    
# =============================================================================
# ENUMS DE ENTREGABLES
# =============================================================================

class TipoEntregable(str, Enum):
    """Tipos de entregable según formato de archivo permitido"""
    FOTOGRAFICO = 'FOTOGRAFICO'
    REPORTE = 'REPORTE'
    LISTADO = 'LISTADO'
    DOCUMENTAL = 'DOCUMENTAL'

    @property
    def descripcion(self) -> str:
        """Descripción legible del tipo"""
        descripciones = {
            'FOTOGRAFICO': 'Evidencia fotográfica',
            'REPORTE': 'Reporte de actividades',
            'LISTADO': 'Listado de personal',
            'DOCUMENTAL': 'Documento oficial',
        }
        return descripciones.get(self.value, self.value)

    @property
    def formatos_permitidos(self) -> set:
        """MIME types permitidos para este tipo"""
        formatos = {
            'FOTOGRAFICO': {'image/jpeg', 'image/png', 'application/pdf'},
            'REPORTE': {'application/pdf'},
            'LISTADO': {
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/csv',
            },
            'DOCUMENTAL': {'application/pdf'},
        }
        return formatos.get(self.value, set())

    @property
    def extensiones_permitidas(self) -> set:
        """Extensiones de archivo permitidas"""
        extensiones = {
            'FOTOGRAFICO': {'.jpg', '.jpeg', '.png', '.pdf'},
            'REPORTE': {'.pdf'},
            'LISTADO': {'.xls', '.xlsx', '.csv'},
            'DOCUMENTAL': {'.pdf'},
        }
        return extensiones.get(self.value, set())


class PeriodicidadEntregable(str, Enum):
    """Periodicidad de entrega de entregables"""
    MENSUAL = 'MENSUAL'
    QUINCENAL = 'QUINCENAL'
    UNICO = 'UNICO'

    @property
    def descripcion(self) -> str:
        """Descripción legible de la periodicidad"""
        descripciones = {
            'MENSUAL': 'Mensual',
            'QUINCENAL': 'Quincenal',
            'UNICO': 'Único (al finalizar contrato)',
        }
        return descripciones.get(self.value, self.value)


class EstatusEntregable(str, Enum):
    """Estados del ciclo de vida de un entregable"""
    PENDIENTE = 'PENDIENTE'
    EN_REVISION = 'EN_REVISION'
    APROBADO = 'APROBADO'
    RECHAZADO = 'RECHAZADO'
    # --- Estados post-aprobacion (flujo de facturacion) ---
    PREFACTURA_ENVIADA = 'PREFACTURA_ENVIADA'
    PREFACTURA_RECHAZADA = 'PREFACTURA_RECHAZADA'
    PREFACTURA_APROBADA = 'PREFACTURA_APROBADA'
    FACTURADO = 'FACTURADO'
    PAGADO = 'PAGADO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del estatus"""
        descripciones = {
            'PENDIENTE': 'Pendiente de entrega',
            'EN_REVISION': 'En revisión',
            'APROBADO': 'Aprobado',
            'RECHAZADO': 'Rechazado',
            'PREFACTURA_ENVIADA': 'Prefactura enviada',
            'PREFACTURA_RECHAZADA': 'Prefactura rechazada',
            'PREFACTURA_APROBADA': 'Prefactura aprobada',
            'FACTURADO': 'Facturado',
            'PAGADO': 'Pagado',
        }
        return descripciones.get(self.value, self.value)

    @property
    def es_estado_final(self) -> bool:
        """Indica si es un estado final"""
        return self == EstatusEntregable.PAGADO

    @property
    def permite_edicion_cliente(self) -> bool:
        """Indica si el cliente puede editar/subir archivos de entregable"""
        return self in (EstatusEntregable.PENDIENTE, EstatusEntregable.RECHAZADO)

    @property
    def requiere_accion_cliente(self) -> bool:
        """Indica si el cliente debe actuar (subir prefactura, corregir, subir factura)"""
        return self in (
            EstatusEntregable.APROBADO,
            EstatusEntregable.PREFACTURA_RECHAZADA,
            EstatusEntregable.PREFACTURA_APROBADA,
        )


class EstatusPago(str, Enum):
    """Estados del pago"""
    PENDIENTE = 'PENDIENTE'
    EN_PROCESO = 'EN_PROCESO'
    PAGADO = 'PAGADO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del estatus"""
        descripciones = {
            'PENDIENTE': 'Pendiente (esperando factura)',
            'EN_PROCESO': 'En proceso de pago',
            'PAGADO': 'Pagado',
        }
        return descripciones.get(self.value, self.value)