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


class TipoJornadaPlaza(str, Enum):
    """Tipos de jornada permitidos para una plaza."""
    COMPLETA = 'COMPLETA'
    MEDIA_JORNADA = 'MEDIA_JORNADA'
    POR_HORAS = 'POR_HORAS'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'COMPLETA': 'Jornada completa',
            'MEDIA_JORNADA': 'Media jornada',
            'POR_HORAS': 'Por horas',
        }
        return descripciones.get(self.value, self.value)


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
# ENUMS DE BAJA DE EMPLEADO
# =============================================================================

class EstatusBaja(str, Enum):
    """Estados del proceso de baja de un empleado."""
    INICIADA = 'INICIADA'
    COMUNICADA = 'COMUNICADA'
    LIQUIDADA = 'LIQUIDADA'
    CERRADA = 'CERRADA'
    CANCELADA = 'CANCELADA'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'INICIADA': 'Baja registrada',
            'COMUNICADA': 'Comunicada a BUAP',
            'LIQUIDADA': 'Liquidacion entregada',
            'CERRADA': 'Proceso cerrado',
            'CANCELADA': 'Baja cancelada',
        }
        return descripciones.get(self.value, self.value)

    @property
    def es_proceso_activo(self) -> bool:
        return self in (EstatusBaja.INICIADA, EstatusBaja.COMUNICADA)


class EstatusLiquidacion(str, Enum):
    """Estados de la liquidacion/finiquito."""
    NO_APLICA = 'NO_APLICA'
    PENDIENTE = 'PENDIENTE'
    EN_PROCESO = 'EN_PROCESO'
    ENTREGADA = 'ENTREGADA'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'NO_APLICA': 'No aplica',
            'PENDIENTE': 'Pendiente',
            'EN_PROCESO': 'En proceso',
            'ENTREGADA': 'Entregada',
        }
        return descripciones.get(self.value, self.value)


# =============================================================================
# ENUMS DE ASISTENCIAS
# =============================================================================

class EstatusJornada(str, Enum):
    """Estados del ciclo de una jornada de asistencia."""
    ABIERTA = 'ABIERTA'
    CERRADA = 'CERRADA'
    CONSOLIDADA = 'CONSOLIDADA'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'ABIERTA': 'Jornada abierta',
            'CERRADA': 'Jornada cerrada',
            'CONSOLIDADA': 'Jornada consolidada',
        }
        return descripciones.get(self.value, self.value)


class TipoIncidencia(str, Enum):
    """Tipos de incidencia que impactan asistencia y nomina."""
    FALTA = 'FALTA'
    FALTA_JUSTIFICADA = 'FALTA_JUSTIFICADA'
    RETARDO = 'RETARDO'
    SALIDA_ANTICIPADA = 'SALIDA_ANTICIPADA'
    HORA_EXTRA = 'HORA_EXTRA'
    PERMISO_CON_GOCE = 'PERMISO_CON_GOCE'
    PERMISO_SIN_GOCE = 'PERMISO_SIN_GOCE'
    INCAPACIDAD_ENFERMEDAD = 'INCAPACIDAD_ENFERMEDAD'
    INCAPACIDAD_RIESGO_TRABAJO = 'INCAPACIDAD_RIESGO_TRABAJO'
    INCAPACIDAD_MATERNIDAD = 'INCAPACIDAD_MATERNIDAD'
    VACACIONES = 'VACACIONES'
    DIA_FESTIVO = 'DIA_FESTIVO'
    COMISION = 'COMISION'
    OTRO = 'OTRO'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'FALTA': 'Falta injustificada',
            'FALTA_JUSTIFICADA': 'Falta justificada',
            'RETARDO': 'Retardo',
            'SALIDA_ANTICIPADA': 'Salida anticipada',
            'HORA_EXTRA': 'Hora extra',
            'PERMISO_CON_GOCE': 'Permiso con goce',
            'PERMISO_SIN_GOCE': 'Permiso sin goce',
            'INCAPACIDAD_ENFERMEDAD': 'Incapacidad por enfermedad',
            'INCAPACIDAD_RIESGO_TRABAJO': 'Incapacidad por riesgo de trabajo',
            'INCAPACIDAD_MATERNIDAD': 'Incapacidad por maternidad',
            'VACACIONES': 'Vacaciones',
            'DIA_FESTIVO': 'Dia festivo',
            'COMISION': 'Comision',
            'OTRO': 'Otro',
        }
        return descripciones.get(self.value, self.value)


class OrigenIncidencia(str, Enum):
    """Origen de la captura de una incidencia."""
    SUPERVISOR = 'SUPERVISOR'
    RH = 'RH'
    AUTOREGISTRO = 'AUTOREGISTRO'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'SUPERVISOR': 'Supervisor',
            'RH': 'Recursos Humanos',
            'AUTOREGISTRO': 'Autoregistro',
        }
        return descripciones.get(self.value, self.value)


class TipoRegistroAsistencia(str, Enum):
    """Resultado final consolidado del dia."""
    ASISTENCIA = 'ASISTENCIA'
    FALTA = 'FALTA'
    FALTA_JUSTIFICADA = 'FALTA_JUSTIFICADA'
    RETARDO = 'RETARDO'
    SALIDA_ANTICIPADA = 'SALIDA_ANTICIPADA'
    HORA_EXTRA = 'HORA_EXTRA'
    PERMISO_CON_GOCE = 'PERMISO_CON_GOCE'
    PERMISO_SIN_GOCE = 'PERMISO_SIN_GOCE'
    INCAPACIDAD_ENFERMEDAD = 'INCAPACIDAD_ENFERMEDAD'
    INCAPACIDAD_RIESGO_TRABAJO = 'INCAPACIDAD_RIESGO_TRABAJO'
    INCAPACIDAD_MATERNIDAD = 'INCAPACIDAD_MATERNIDAD'
    VACACIONES = 'VACACIONES'
    DIA_FESTIVO = 'DIA_FESTIVO'
    COMISION = 'COMISION'
    OTRO = 'OTRO'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'ASISTENCIA': 'Asistencia normal',
            'FALTA': 'Falta injustificada',
            'FALTA_JUSTIFICADA': 'Falta justificada',
            'RETARDO': 'Retardo',
            'SALIDA_ANTICIPADA': 'Salida anticipada',
            'HORA_EXTRA': 'Hora extra',
            'PERMISO_CON_GOCE': 'Permiso con goce',
            'PERMISO_SIN_GOCE': 'Permiso sin goce',
            'INCAPACIDAD_ENFERMEDAD': 'Incapacidad por enfermedad',
            'INCAPACIDAD_RIESGO_TRABAJO': 'Incapacidad por riesgo de trabajo',
            'INCAPACIDAD_MATERNIDAD': 'Incapacidad por maternidad',
            'VACACIONES': 'Vacaciones',
            'DIA_FESTIVO': 'Dia festivo',
            'COMISION': 'Comision',
            'OTRO': 'Otro',
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


class RolPlataforma(str, Enum):
    """
    Tipo de organización que representa el usuario en la plataforma.

    Define QUÉ TIPO de actor es, no qué puede hacer.
    Los permisos específicos se definen en RolEmpresa (user_companies).

    Valores de compatibilidad:
    - 'admin' equivale a 'superadmin' (usuarios existentes)
    - 'client' equivale a 'proveedor' (usuarios existentes)
    """
    SUPERADMIN = 'superadmin'
    ADMIN = 'admin'
    INSTITUCION = 'institucion'
    PROVEEDOR = 'proveedor'
    CLIENT = 'client'
    EMPLEADO = 'empleado'

    @property
    def descripcion(self) -> str:
        """Descripción legible del rol"""
        descripciones = {
            'superadmin': 'Super Administrador (Plataforma)',
            'admin': 'Administrador (Compatibilidad)',
            'institucion': 'Institución Cliente',
            'proveedor': 'Empresa Proveedora',
            'client': 'Cliente (Compatibilidad)',
            'empleado': 'Empleado',
        }
        return descripciones.get(self.value, self.value)

    @property
    def es_superadmin(self) -> bool:
        """True para superadmin y admin (compatibilidad)."""
        return self.value in ('superadmin', 'admin')

    @property
    def es_proveedor(self) -> bool:
        """True para proveedor y client (compatibilidad)."""
        return self.value in ('proveedor', 'client')

    @property
    def es_institucion(self) -> bool:
        """True solo para institucion."""
        return self == RolPlataforma.INSTITUCION

    @property
    def es_empleado(self) -> bool:
        """True solo para empleado."""
        return self == RolPlataforma.EMPLEADO


class RolEmpresa(str, Enum):
    """
    Permisos de un usuario dentro de una empresa específica.

    Define QUÉ PUEDE HACER el usuario en el contexto de UNA empresa.
    Un mismo usuario puede tener roles diferentes en empresas diferentes.

    Solo aplica a usuarios 'proveedor' (y 'client' por compatibilidad):
        admin_empresa, rrhh, operaciones, contabilidad, lectura

    Y a usuarios 'empleado':
        empleado

    Usuarios 'institucion' NO usan user_companies — su acceso viene
    de instituciones_empresas y sus permisos son fijos en código.
    """
    # --- Roles de proveedor ---
    ADMIN_EMPRESA = 'admin_empresa'
    RRHH = 'rrhh'
    OPERACIONES = 'operaciones'
    CONTABILIDAD = 'contabilidad'
    LECTURA = 'lectura'

    # --- Roles de empleado ---
    EMPLEADO = 'empleado'

    @property
    def descripcion(self) -> str:
        """Descripción legible del rol"""
        descripciones = {
            'admin_empresa': 'Administrador de Empresa',
            'rrhh': 'Recursos Humanos',
            'operaciones': 'Operaciones',
            'contabilidad': 'Contabilidad',
            'lectura': 'Solo Lectura',
            'empleado': 'Empleado',
        }
        return descripciones.get(self.value, self.value)

    @property
    def es_gestion_personal(self) -> bool:
        """Indica si puede gestionar personal (empleados, expedientes)."""
        return self in (RolEmpresa.ADMIN_EMPRESA, RolEmpresa.RRHH)

    @property
    def puede_gestionar_empresa(self) -> bool:
        """Indica si puede cambiar configuración de la empresa."""
        return self == RolEmpresa.ADMIN_EMPRESA


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


# =============================================================================
# ENUMS DE ONBOARDING
# =============================================================================

class EstatusOnboarding(str, Enum):
    """Estados del proceso de onboarding de un empleado."""
    REGISTRADO = 'REGISTRADO'
    DATOS_PENDIENTES = 'DATOS_PENDIENTES'
    DOCUMENTOS_PENDIENTES = 'DOCUMENTOS_PENDIENTES'
    EN_REVISION = 'EN_REVISION'
    APROBADO = 'APROBADO'
    RECHAZADO = 'RECHAZADO'
    ACTIVO_COMPLETO = 'ACTIVO_COMPLETO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del estatus"""
        descripciones = {
            'REGISTRADO': 'Registrado por RRHH',
            'DATOS_PENDIENTES': 'Esperando datos del empleado',
            'DOCUMENTOS_PENDIENTES': 'Esperando documentos del empleado',
            'EN_REVISION': 'Expediente en revisión',
            'APROBADO': 'Expediente aprobado',
            'RECHAZADO': 'Expediente rechazado (requiere correcciones)',
            'ACTIVO_COMPLETO': 'Onboarding completado',
        }
        return descripciones.get(self.value, self.value)

    @property
    def requiere_accion_empleado(self) -> bool:
        """Indica si el empleado debe actuar en este estado."""
        return self in (
            EstatusOnboarding.DATOS_PENDIENTES,
            EstatusOnboarding.DOCUMENTOS_PENDIENTES,
            EstatusOnboarding.RECHAZADO,
        )


class TipoDocumentoEmpleado(str, Enum):
    """Tipos de documento del expediente de un empleado."""
    INE = 'INE'
    COMPROBANTE_DOMICILIO = 'COMPROBANTE_DOMICILIO'
    CARATULA_BANCARIA = 'CARATULA_BANCARIA'
    CURP_DOCUMENTO = 'CURP_DOCUMENTO'
    RFC_DOCUMENTO = 'RFC_DOCUMENTO'
    NSS_DOCUMENTO = 'NSS_DOCUMENTO'
    ACTA_NACIMIENTO = 'ACTA_NACIMIENTO'
    COMPROBANTE_ESTUDIOS = 'COMPROBANTE_ESTUDIOS'
    FOTOGRAFIA = 'FOTOGRAFIA'
    OTRO = 'OTRO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del tipo"""
        descripciones = {
            'INE': 'Identificación oficial (INE)',
            'COMPROBANTE_DOMICILIO': 'Comprobante de domicilio',
            'CARATULA_BANCARIA': 'Carátula bancaria',
            'CURP_DOCUMENTO': 'Documento CURP',
            'RFC_DOCUMENTO': 'Constancia de RFC',
            'NSS_DOCUMENTO': 'Documento IMSS',
            'ACTA_NACIMIENTO': 'Acta de nacimiento',
            'COMPROBANTE_ESTUDIOS': 'Comprobante de estudios',
            'FOTOGRAFIA': 'Fotografía',
            'OTRO': 'Otro documento',
        }
        return descripciones.get(self.value, self.value)

    @property
    def es_obligatorio(self) -> bool:
        """Indica si el documento es obligatorio para completar onboarding."""
        return self in (
            TipoDocumentoEmpleado.INE,
            TipoDocumentoEmpleado.COMPROBANTE_DOMICILIO,
            TipoDocumentoEmpleado.CARATULA_BANCARIA,
            TipoDocumentoEmpleado.CURP_DOCUMENTO,
            TipoDocumentoEmpleado.RFC_DOCUMENTO,
        )


class TipoDocumentoEmpresa(str, Enum):
    """Tipos de documento del expediente anual de una empresa."""

    ACTA_CONSTITUTIVA = "ACTA_CONSTITUTIVA"
    IDENTIFICACION_OFICIAL = "IDENTIFICACION_OFICIAL"
    CONSTANCIA_SITUACION_FISCAL = "CONSTANCIA_SITUACION_FISCAL"
    COMPROBANTE_DOMICILIO = "COMPROBANTE_DOMICILIO"
    OPINION_CUMPLIMIENTO_SAT = "OPINION_CUMPLIMIENTO_SAT"
    OPINION_POSITIVA_IMSS = "OPINION_POSITIVA_IMSS"
    ADEUDO_INFONAVIT = "ADEUDO_INFONAVIT"
    NO_ADEUDO_ESTADO = "NO_ADEUDO_ESTADO"
    PADRON_PROVEEDORES_BUAP = "PADRON_PROVEEDORES_BUAP"
    REPSE = "REPSE"
    MANIFESTACION_69B_CFF = "MANIFESTACION_69B_CFF"
    MANIFESTACION_77_LAASSP = "MANIFESTACION_77_LAASSP"
    MANIFESTACION_69B_77 = "MANIFESTACION_69B_77"
    DECLARACION_ANUAL = "DECLARACION_ANUAL"
    ACUSE_DECLARACION_ANUAL = "ACUSE_DECLARACION_ANUAL"
    DECLARACION_MENSUAL = "DECLARACION_MENSUAL"
    ACUSE_DECLARACION_MENSUAL = "ACUSE_DECLARACION_MENSUAL"
    CURRICULUM_EMPRESARIAL = "CURRICULUM_EMPRESARIAL"
    FACTURAS_CONTRATOS = "FACTURAS_CONTRATOS"
    COMPRANET = "COMPRANET"
    COTIZACION = "COTIZACION"
    DOCUMENTO_ADICIONAL = "DOCUMENTO_ADICIONAL"

    @property
    def numero(self) -> int:
        orden = {
            "ACTA_CONSTITUTIVA": 1,
            "IDENTIFICACION_OFICIAL": 2,
            "CONSTANCIA_SITUACION_FISCAL": 3,
            "COMPROBANTE_DOMICILIO": 4,
            "OPINION_CUMPLIMIENTO_SAT": 5,
            "OPINION_POSITIVA_IMSS": 6,
            "ADEUDO_INFONAVIT": 7,
            "NO_ADEUDO_ESTADO": 8,
            "PADRON_PROVEEDORES_BUAP": 9,
            "REPSE": 10,
            "MANIFESTACION_69B_CFF": 11,
            "MANIFESTACION_77_LAASSP": 12,
            "MANIFESTACION_69B_77": 13,
            "DECLARACION_ANUAL": 14,
            "ACUSE_DECLARACION_ANUAL": 15,
            "DECLARACION_MENSUAL": 16,
            "ACUSE_DECLARACION_MENSUAL": 17,
            "CURRICULUM_EMPRESARIAL": 18,
            "FACTURAS_CONTRATOS": 19,
            "COMPRANET": 20,
            "COTIZACION": 21,
            "DOCUMENTO_ADICIONAL": 22,
        }
        return orden[self.value]

    @property
    def es_obligatorio(self) -> bool:
        """REPSE y registros auxiliares no cuentan como requisito base obligatorio."""
        return self not in {
            TipoDocumentoEmpresa.REPSE,
            TipoDocumentoEmpresa.MANIFESTACION_69B_77,
            TipoDocumentoEmpresa.DOCUMENTO_ADICIONAL,
        }

    @property
    def es_anual(self) -> bool:
        """Documentos persistentes se reutilizan entre años hasta que se actualicen."""
        return self not in {
            TipoDocumentoEmpresa.ACTA_CONSTITUTIVA,
            TipoDocumentoEmpresa.IDENTIFICACION_OFICIAL,
            TipoDocumentoEmpresa.MANIFESTACION_69B_CFF,
            TipoDocumentoEmpresa.MANIFESTACION_77_LAASSP,
            TipoDocumentoEmpresa.MANIFESTACION_69B_77,
        }

    @property
    def es_visible_en_checklist(self) -> bool:
        """Valores auxiliares/legado no se renderizan como fila base del checklist."""
        return self not in {
            TipoDocumentoEmpresa.MANIFESTACION_69B_77,
            TipoDocumentoEmpresa.DOCUMENTO_ADICIONAL,
        }

    def etiqueta(self, anio: int | None = None) -> str:
        """Descripción legible del documento."""
        if self == TipoDocumentoEmpresa.DECLARACION_ANUAL and anio is not None:
            return (
                "Copia de la declaración anual de impuestos federales "
                f"del ejercicio fiscal {anio - 1}"
            )
        if self == TipoDocumentoEmpresa.ACUSE_DECLARACION_ANUAL and anio is not None:
            return (
                "Acuse de recibo de la declaración anual de impuestos federales "
                f"del ejercicio fiscal {anio - 1}"
            )
        if self == TipoDocumentoEmpresa.DECLARACION_MENSUAL and anio is not None:
            return (
                "Copia de la última declaración mensual de impuestos federales "
                f"del ejercicio fiscal {anio}"
            )
        if self == TipoDocumentoEmpresa.ACUSE_DECLARACION_MENSUAL and anio is not None:
            return (
                "Acuse de recibo de la última declaración mensual de impuestos federales "
                f"del ejercicio fiscal {anio}"
            )

        descripciones = {
            "ACTA_CONSTITUTIVA": "Acta constitutiva de la empresa",
            "IDENTIFICACION_OFICIAL": (
                "Identificación oficial vigente con fotografía del representante"
            ),
            "CONSTANCIA_SITUACION_FISCAL": "Constancia de situación fiscal",
            "COMPROBANTE_DOMICILIO": "Comprobante de domicilio",
            "OPINION_CUMPLIMIENTO_SAT": "Opinión de cumplimiento SAT",
            "OPINION_POSITIVA_IMSS": "Opinión positiva IMSS",
            "ADEUDO_INFONAVIT": "Constancia de no adeudo INFONAVIT",
            "NO_ADEUDO_ESTADO": "Constancia de no adeudo del Gobierno del Estado",
            "PADRON_PROVEEDORES_BUAP": "Constancia de inscripción al padrón BUAP",
            "REPSE": "Comprobante de registro REPSE",
            "MANIFESTACION_69B_CFF": "Manifestación legal art. 69-B del CFF",
            "MANIFESTACION_77_LAASSP": "Manifestación legal art. 77 de la LAASSP",
            "MANIFESTACION_69B_77": "Manifestación legal (legado 69-B / art. 77)",
            "CURRICULUM_EMPRESARIAL": "Currículum empresarial del proveedor",
            "FACTURAS_CONTRATOS": "Facturas y/o contratos celebrados",
            "COMPRANET": "Registro único de proveedores y contratistas (COMPRANET)",
            "COTIZACION": "Cotización",
            "DOCUMENTO_ADICIONAL": "Documento adicional configurable",
        }
        return descripciones.get(self.value, self.value)

    @property
    def descripcion(self) -> str:
        return self.etiqueta()

    def ayuda(self, anio: int | None = None) -> str:
        """Texto guía mostrado en la UI; no se valida automáticamente en v1."""
        ayudas = {
            "ACTA_CONSTITUTIVA": (
                "PDF legible del acta constitutiva vigente. Los complementos se pueden "
                "agregar como documentos adicionales por empresa."
            ),
            "IDENTIFICACION_OFICIAL": (
                "IFE/INE, pasaporte o cédula profesional del representante legal."
            ),
            "CONSTANCIA_SITUACION_FISCAL": (
                "Emitida por el SAT, con antigüedad no mayor a 30 días previos a la requisición."
            ),
            "COMPROBANTE_DOMICILIO": (
                "Recibo de luz, agua o predial con antigüedad no mayor a 3 meses. "
                "Si es arrendado, agregar contrato de arrendamiento."
            ),
            "OPINION_CUMPLIMIENTO_SAT": (
                "Emitida por el SAT en sentido positivo; debe estar vigente desde la "
                "presentación de la requisición hasta la firma del contrato."
            ),
            "OPINION_POSITIVA_IMSS": (
                "Opinión positiva del IMSS vigente desde antes de la adjudicación "
                "y hasta la fecha de firma del contrato."
            ),
            "ADEUDO_INFONAVIT": (
                "Constancia de adeudo INFONAVIT vigente desde la presentación de la "
                "requisición y hasta la firma del contrato."
            ),
            "NO_ADEUDO_ESTADO": (
                "Constancia de no adeudo vigente para proveedores del Gobierno del Estado."
            ),
            "PADRON_PROVEEDORES_BUAP": (
                "Constancia de inscripción al Padrón de Proveedores de la BUAP."
            ),
            "REPSE": (
                "Documento opcional en v1. Solo aplica para proveedores de servicios "
                "especializados u obras especializadas."
            ),
            "MANIFESTACION_69B_CFF": (
                "Manifestación legal firmada respecto al artículo 69-B del Código Fiscal "
                "de la Federación."
            ),
            "MANIFESTACION_77_LAASSP": (
                "Manifestación legal firmada respecto al artículo 77 de la Ley de "
                "Adquisiciones, Arrendamientos y Servicios del Sector Público."
            ),
            "MANIFESTACION_69B_77": (
                "Documento legado: la nueva carga separa 69-B y artículo 77 en dos archivos."
            ),
            "DECLARACION_ANUAL": (
                f"Declaración anual del ejercicio fiscal {anio - 1}."
                if anio is not None
                else "Declaración anual del ejercicio fiscal anterior."
            ),
            "ACUSE_DECLARACION_ANUAL": (
                f"Acuse de recibo de la declaración anual del ejercicio fiscal {anio - 1}."
                if anio is not None
                else "Acuse de la declaración anual del ejercicio fiscal anterior."
            ),
            "DECLARACION_MENSUAL": (
                f"Última declaración mensual del ejercicio fiscal {anio}."
                if anio is not None
                else "Última declaración mensual del ejercicio fiscal seleccionado."
            ),
            "ACUSE_DECLARACION_MENSUAL": (
                f"Acuse de la última declaración mensual del ejercicio fiscal {anio}."
                if anio is not None
                else "Acuse de la última declaración mensual del ejercicio fiscal seleccionado."
            ),
            "CURRICULUM_EMPRESARIAL": "Resumen del perfil y experiencia empresarial del proveedor.",
            "FACTURAS_CONTRATOS": "Copias simples de al menos dos facturas y/o contratos celebrados.",
            "COMPRANET": "Registro único de proveedores y contratistas (COMPRANET).",
            "COTIZACION": "Cotización emitida por la empresa proveedora.",
            "DOCUMENTO_ADICIONAL": "Documento configurable por empresa.",
        }
        return ayudas.get(self.value, self.etiqueta(anio))


class EstatusDocumento(str, Enum):
    """Estados de revisión de un documento de empleado."""
    PENDIENTE_REVISION = 'PENDIENTE_REVISION'
    APROBADO = 'APROBADO'
    RECHAZADO = 'RECHAZADO'

    @property
    def descripcion(self) -> str:
        """Descripción legible del estatus"""
        descripciones = {
            'PENDIENTE_REVISION': 'Pendiente de revisión',
            'APROBADO': 'Aprobado',
            'RECHAZADO': 'Rechazado',
        }
        return descripciones.get(self.value, self.value)


# =============================================================================
# ENUMS DE NÓMINA
# =============================================================================

class TipoConcepto(str, Enum):
    """Tipo de concepto de nómina según clasificación SAT."""
    PERCEPCION = 'PERCEPCION'
    DEDUCCION = 'DEDUCCION'
    OTRO_PAGO = 'OTRO_PAGO'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'PERCEPCION': 'Percepción',
            'DEDUCCION': 'Deducción',
            'OTRO_PAGO': 'Otro pago',
        }
        return descripciones.get(self.value, self.value)


class TratamientoISR(str, Enum):
    """Tratamiento fiscal del concepto para ISR."""
    GRAVABLE = 'GRAVABLE'
    EXENTO = 'EXENTO'
    PARCIALMENTE_EXENTO = 'PARCIALMENTE_EXENTO'
    NO_APLICA = 'NO_APLICA'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'GRAVABLE': 'Gravable (100%)',
            'EXENTO': 'Exento (100%)',
            'PARCIALMENTE_EXENTO': 'Parcialmente exento',
            'NO_APLICA': 'No aplica',
        }
        return descripciones.get(self.value, self.value)


class OrigenCaptura(str, Enum):
    """Quién captura el concepto en el flujo de nómina."""
    SISTEMA = 'SISTEMA'
    RRHH = 'RRHH'
    CONTABILIDAD = 'CONTABILIDAD'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'SISTEMA': 'Calculado por el sistema',
            'RRHH': 'Capturado por RRHH',
            'CONTABILIDAD': 'Capturado por Contabilidad',
        }
        return descripciones.get(self.value, self.value)


# =============================================================================
# Nómina — Operación
# =============================================================================

class EstatusPeriodoNomina(str, Enum):
    """
    Workflow del período de nómina.

    BORRADOR → EN_PREPARACION_RRHH → ENVIADO_A_CONTABILIDAD
             → EN_PROCESO_CONTABILIDAD → CALCULADO → CERRADO
    """
    BORRADOR = 'BORRADOR'
    EN_PREPARACION_RRHH = 'EN_PREPARACION_RRHH'
    ENVIADO_A_CONTABILIDAD = 'ENVIADO_A_CONTABILIDAD'
    EN_PROCESO_CONTABILIDAD = 'EN_PROCESO_CONTABILIDAD'
    CALCULADO = 'CALCULADO'
    CERRADO = 'CERRADO'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'BORRADOR': 'Borrador',
            'EN_PREPARACION_RRHH': 'En preparación (RRHH)',
            'ENVIADO_A_CONTABILIDAD': 'Enviado a Contabilidad',
            'EN_PROCESO_CONTABILIDAD': 'En proceso (Contabilidad)',
            'CALCULADO': 'Calculado',
            'CERRADO': 'Cerrado',
        }
        return descripciones.get(self.value, self.value)


class PeriodicidadNomina(str, Enum):
    """Frecuencia de pago de la nómina."""
    SEMANAL = 'SEMANAL'
    QUINCENAL = 'QUINCENAL'
    MENSUAL = 'MENSUAL'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'SEMANAL': 'Semanal',
            'QUINCENAL': 'Quincenal',
            'MENSUAL': 'Mensual',
        }
        return descripciones.get(self.value, self.value)


class ReglaCalculoQuincenal(str, Enum):
    """Regla para calcular el sueldo base en periodos quincenales."""
    REAL = 'REAL'
    MIXTA = 'MIXTA'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'REAL': 'Real por días',
            'MIXTA': 'Base fija quincenal',
        }
        return descripciones.get(self.value, self.value)


class TipoPeriodoNomina(str, Enum):
    """Clasificación funcional del período de nómina."""
    ORDINARIA = 'ORDINARIA'
    AGUINALDO = 'AGUINALDO'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'ORDINARIA': 'Ordinaria',
            'AGUINALDO': 'Aguinaldo',
        }
        return descripciones.get(self.value, self.value)


class ModoCalculoAguinaldo(str, Enum):
    """Origen del monto bruto usado para el aguinaldo."""
    AUTO = 'AUTO'
    MANUAL = 'MANUAL'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'AUTO': 'Automático',
            'MANUAL': 'Manual',
        }
        return descripciones.get(self.value, self.value)


class OrigenMovimiento(str, Enum):
    """Quién generó el movimiento en la nómina."""
    SISTEMA = 'SISTEMA'
    RRHH = 'RRHH'
    CONTABILIDAD = 'CONTABILIDAD'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'SISTEMA': 'Calculado por el sistema',
            'RRHH': 'Capturado por RRHH',
            'CONTABILIDAD': 'Capturado por Contabilidad',
        }
        return descripciones.get(self.value, self.value)


class EstatusNominaEmpleado(str, Enum):
    """Estatus del recibo individual de nómina."""
    PENDIENTE = 'PENDIENTE'
    EN_PROCESO = 'EN_PROCESO'
    CALCULADO = 'CALCULADO'
    APROBADO = 'APROBADO'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'PENDIENTE': 'Pendiente',
            'EN_PROCESO': 'En proceso',
            'CALCULADO': 'Calculado',
            'APROBADO': 'Aprobado',
        }
        return descripciones.get(self.value, self.value)


# =============================================================================
# ENUMS DE COTIZACIÓN
# =============================================================================

class TipoCotizacion(str, Enum):
    """Tipo de cotización."""
    PRODUCTOS_SERVICIOS = 'PRODUCTOS_SERVICIOS'
    PERSONAL = 'PERSONAL'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'PRODUCTOS_SERVICIOS': 'Productos/Servicios',
            'PERSONAL': 'Personal',
        }
        return descripciones.get(self.value, self.value)


class TipoSueldo(str, Enum):
    """Tipo de sueldo para cálculo patronal."""
    NETO = 'NETO'
    BRUTO = 'BRUTO'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'NETO': 'Neto',
            'BRUTO': 'Bruto',
        }
        return descripciones.get(self.value, self.value)


class EstatusCotizacion(str, Enum):
    """Estados del ciclo de vida de una cotización."""
    BORRADOR = 'BORRADOR'
    PREPARADA = 'PREPARADA'
    ENVIADA = 'ENVIADA'
    APROBADA = 'APROBADA'
    RECHAZADA = 'RECHAZADA'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'BORRADOR': 'Borrador',
            'PREPARADA': 'Preparada',
            'ENVIADA': 'Enviada',
            'APROBADA': 'Aprobada',
            'RECHAZADA': 'Rechazada',
        }
        return descripciones.get(self.value, self.value)

    @property
    def es_editable(self) -> bool:
        """Solo BORRADOR permite edición."""
        return self == EstatusCotizacion.BORRADOR

    @property
    def es_estado_final(self) -> bool:
        return self in (EstatusCotizacion.APROBADA, EstatusCotizacion.RECHAZADA)


class EstatusPartidaCotizacion(str, Enum):
    """Estados de una partida dentro de la cotización."""
    PENDIENTE = 'PENDIENTE'
    ACEPTADA = 'ACEPTADA'
    NO_ASIGNADA = 'NO_ASIGNADA'
    CONVERTIDA = 'CONVERTIDA'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'PENDIENTE': 'Pendiente',
            'ACEPTADA': 'Aceptada',
            'NO_ASIGNADA': 'No asignada',
            'CONVERTIDA': 'Convertida a contrato',
        }
        return descripciones.get(self.value, self.value)

    @property
    def puede_convertir(self) -> bool:
        return self == EstatusPartidaCotizacion.ACEPTADA


class TipoConceptoCotizacion(str, Enum):
    """Tipo de concepto en la matriz de costos."""
    PATRONAL = 'PATRONAL'
    INDIRECTO = 'INDIRECTO'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'PATRONAL': 'Costo patronal',
            'INDIRECTO': 'Gasto indirecto',
        }
        return descripciones.get(self.value, self.value)


class TipoValorConcepto(str, Enum):
    """Cómo se expresa el valor del concepto."""
    FIJO = 'FIJO'
    PORCENTAJE = 'PORCENTAJE'

    @property
    def descripcion(self) -> str:
        descripciones = {
            'FIJO': 'Importe fijo (pesos)',
            'PORCENTAJE': 'Porcentaje (%)',
        }
        return descripciones.get(self.value, self.value)
