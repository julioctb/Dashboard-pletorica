"""
Entidades de dominio del sistema.

Este módulo exporta todas las entidades de negocio para facilitar imports:
    from app.entities import Empresa, AreaServicio, etc.
"""

# Enums centralizados
from app.core.enums import (
    Estatus,
    EstatusEmpresa,
    TipoEmpresa,
    # Enums de Usuario
    RolUsuario,
    RolPlataforma,
    RolEmpresa,
    # Enums de Contrato
    TipoContrato,
    ModalidadAdjudicacion,
    TipoDuracion,
    EstatusContrato,
    # Enums de Plaza
    EstatusPlaza,
    # Enums de Empleado
    EstatusEmpleado,
    GeneroEmpleado,
    MotivoBaja,
    AccionRestriccion,
    # Enums de Historial Laboral
    TipoMovimiento,
    # Enums de Requisicion
    EstadoRequisicion,
    TipoContratacion,
    GrupoConfiguracion,
    # Enums de Sede
    TipoSede,
    NivelContacto,
    # Enums de Entregable y Pago
    EstatusEntregable,
    EstatusPago,
    # Enums de Onboarding
    EstatusOnboarding,
    TipoDocumentoEmpleado,
    EstatusDocumento,
)

# Empresa
from app.entities.empresa import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
)

# Perfil de Usuario
from app.entities.user_profile import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResumen
)

# Relacion Usuario/ Empresa
from app.entities.user_company import(
    UserCompany,
    UserCompanyCreate,
    UserCompanyResumen,
    UserCompanyAsignacionInicial,
)

# Institucion
from app.entities.institucion import (
    Institucion,
    InstitucionCreate,
    InstitucionUpdate,
    InstitucionResumen,
    InstitucionEmpresa,
)

# Tipo de Servicio
from app.entities.tipo_servicio import (
    TipoServicio,
    TipoServicioCreate,
    TipoServicioUpdate,
)

# Categoría de Puesto
from app.entities.categoria_puesto import (
    CategoriaPuesto,
    CategoriaPuestoCreate,
    CategoriaPuestoUpdate,
)

# Contrato
from app.entities.contrato import (
    Contrato,
    ContratoCreate,
    ContratoUpdate,
    ContratoResumen,
)

# Pago
from app.entities.pago import (
    Pago,
    PagoCreate,
    PagoUpdate,
    PagoResumen,
    ResumenPagosContrato,
)

# ContratoCategoria
from app.entities.contrato_categoria import (
    ContratoCategoria,
    ContratoCategoriaCreate,
    ContratoCategoriaUpdate,
    ContratoCategoriaResumen,
    ResumenPersonalContrato,
)

# Plaza
from app.entities.plaza import (
    Plaza,
    PlazaCreate,
    PlazaUpdate,
    PlazaResumen,
    ResumenPlazasContrato,
    ResumenPlazasCategoria,
)

# Empleado
from app.entities.empleado import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
)

# Historial Laboral
from app.entities.historial_laboral import (
    HistorialLaboral,
    HistorialLaboralInterno,
    HistorialLaboralResumen,
)

# Archivo
from app.entities.archivo import (
    EntidadArchivo,
    TipoArchivo,
    OrigenArchivo,
    ArchivoSistema,
    ArchivoSistemaUpdate,
    ArchivoUploadResponse,
)

# Contrato Item
from app.entities.contrato_item import (
    ContratoItem,
    ContratoItemCreate,
)

# Requisicion
from app.entities.requisicion import (
    LugarEntrega,
    ConfiguracionRequisicion,
    Requisicion,
    RequisicionCreate,
    RequisicionUpdate,
    RequisicionResumen,
    RequisicionAdjudicar,
    RequisicionItem,
    RequisicionItemCreate,
    RequisicionItemUpdate,
    TRANSICIONES_VALIDAS,
)

# Sede
from app.entities.sede import (
    Sede,
    SedeCreate,
    SedeUpdate,
    SedeResumen,
)

# Restriccion de Empleado
from app.entities.empleado_restriccion_log import (
    EmpleadoRestriccionLog,
    EmpleadoRestriccionLogCreate,
    EmpleadoRestriccionLogResumen,
)

# Contacto BUAP
from app.entities.contacto_buap import (
    ContactoBuap,
    ContactoBuapCreate,
    ContactoBuapUpdate,
)

# Alta Masiva
from app.entities.alta_masiva import (
    ResultadoFila,
    RegistroValidado,
    ResultadoValidacion,
    ResultadoProcesamiento,
    DetalleResultado,
)

# Dashboard
from app.entities.dashboard import DashboardMetricas

# Notificacion
from app.entities.notificacion import (
    Notificacion,
    NotificacionCreate,
)

# Entregables
from app.entities.entregable import (
    Entregable,
    EntregableCreate,
    EntregableUpdate,
    EntregableResumen,
    ContratoTipoEntregable,
    ContratoTipoEntregableCreate,
    ContratoTipoEntregableUpdate,
    AlertaEntregables,
)

# Costo Patronal (si existe)
try:
    from app.entities.costo_patronal import (
        ConfiguracionEmpresa,
        Trabajador,
        ResultadoCuotas,
    )
except ImportError:
    pass  # El módulo puede no existir aún

# Empleado Documento
from app.entities.empleado_documento import (
    EmpleadoDocumento,
    EmpleadoDocumentoCreate,
    EmpleadoDocumentoResumen,
)

# Cuenta Bancaria Historial
from app.entities.cuenta_bancaria_historial import (
    CuentaBancariaHistorial,
    CuentaBancariaHistorialCreate,
)

# Configuración Operativa Empresa
from app.entities.configuracion_operativa_empresa import (
    ConfiguracionOperativaEmpresa,
    ConfiguracionOperativaEmpresaCreate,
    ConfiguracionOperativaEmpresaUpdate,
)

# CURP Validación
from app.entities.curp_validacion import (
    CurpValidacionResponse,
    CurpRenapoResponse,
)

# Onboarding
from app.entities.onboarding import (
    AltaEmpleadoBuap,
    CompletarDatosEmpleado,
    ExpedienteStatus,
)


__all__ = [
    # Enums
    "Estatus",
    "EstatusEmpresa",
    "TipoEmpresa",
    "TipoContrato",
    "ModalidadAdjudicacion",
    "TipoDuracion",
    "EstatusContrato",
    "EstatusPlaza",
    "EstatusEmpleado",
    "GeneroEmpleado",
    "MotivoBaja",
    "TipoMovimiento",
    "EstadoRequisicion",
    "TipoContratacion",
    "GrupoConfiguracion",
    "RolUsuario",
    "RolPlataforma",
    "RolEmpresa",
    "EstatusEntregable",
    "EstatusPago",
    # Enums de Onboarding
    "EstatusOnboarding",
    "TipoDocumentoEmpleado",
    "EstatusDocumento",
    # Empresa
    "Empresa",
    "EmpresaCreate",
    "EmpresaUpdate",
    "EmpresaResumen",
    # Usuarios
    "UserProfile",
    "UserProfileCreate",
    "UserProfileUpdate",
    "UserProfileResumen",
    # Usuario Empresa
    "UserCompany",
    "UserCompanyCreate",
    "UserCompanyResumen",
    # Institucion
    "Institucion",
    "InstitucionCreate",
    "InstitucionUpdate",
    "InstitucionResumen",
    "InstitucionEmpresa",
    # Tipo de Servicio
    "TipoServicio",
    "TipoServicioCreate",
    "TipoServicioUpdate",
    # Categoría de Puesto
    "CategoriaPuesto",
    "CategoriaPuestoCreate",
    "CategoriaPuestoUpdate",
    # Contrato
    "Contrato",
    "ContratoCreate",
    "ContratoUpdate",
    "ContratoResumen",
    # Pago
    "Pago",
    "PagoCreate",
    "PagoUpdate",
    "PagoResumen",
    "ResumenPagosContrato",
    # ContratoCategoria
    "ContratoCategoria",
    "ContratoCategoriaCreate",
    "ContratoCategoriaUpdate",
    "ContratoCategoriaResumen",
    "ResumenPersonalContrato",
    # Plaza
    "Plaza",
    "PlazaCreate",
    "PlazaUpdate",
    "PlazaResumen",
    "ResumenPlazasContrato",
    "ResumenPlazasCategoria",
    # Empleado
    "Empleado",
    "EmpleadoCreate",
    "EmpleadoUpdate",
    "EmpleadoResumen",
    # Historial Laboral
    "HistorialLaboral",
    "HistorialLaboralInterno",
    "HistorialLaboralResumen",
    # Archivo
    "EntidadArchivo",
    "TipoArchivo",
    "OrigenArchivo",
    "ArchivoSistema",
    "ArchivoSistemaUpdate",
    "ArchivoUploadResponse",
    # Contrato Item
    "ContratoItem",
    "ContratoItemCreate",
    # Requisicion
    "LugarEntrega",
    "ConfiguracionRequisicion",
    "Requisicion",
    "RequisicionCreate",
    "RequisicionUpdate",
    "RequisicionResumen",
    "RequisicionAdjudicar",
    "RequisicionItem",
    "RequisicionItemCreate",
    "RequisicionItemUpdate",
    "TRANSICIONES_VALIDAS",
    # Sede
    "TipoSede",
    "NivelContacto",
    "Sede",
    "SedeCreate",
    "SedeUpdate",
    "SedeResumen",
    # Restriccion de Empleado
    "AccionRestriccion",
    "EmpleadoRestriccionLog",
    "EmpleadoRestriccionLogCreate",
    "EmpleadoRestriccionLogResumen",
    # Contacto BUAP
    "ContactoBuap",
    "ContactoBuapCreate",
    "ContactoBuapUpdate",
    # Costo Patronal
    "ConfiguracionEmpresa",
    "Trabajador",
    "ResultadoCuotas",
    # Alta Masiva
    "ResultadoFila",
    "RegistroValidado",
    "ResultadoValidacion",
    "ResultadoProcesamiento",
    "DetalleResultado",
    # Entregables
    "Entregable",
    "EntregableCreate",
    "EntregableUpdate",
    "EntregableResumen",
    "ContratoTipoEntregable",
    "ContratoTipoEntregableCreate",
    "ContratoTipoEntregableUpdate",
    "AlertaEntregables",
    # Dashboard
    "DashboardMetricas",
    # Notificacion
    "Notificacion",
    "NotificacionCreate",
    # Empleado Documento
    "EmpleadoDocumento",
    "EmpleadoDocumentoCreate",
    "EmpleadoDocumentoResumen",
    # Cuenta Bancaria Historial
    "CuentaBancariaHistorial",
    "CuentaBancariaHistorialCreate",
    # Configuración Operativa Empresa
    "ConfiguracionOperativaEmpresa",
    "ConfiguracionOperativaEmpresaCreate",
    "ConfiguracionOperativaEmpresaUpdate",
    # CURP Validación
    "CurpValidacionResponse",
    "CurpRenapoResponse",
    # Onboarding
    "AltaEmpleadoBuap",
    "CompletarDatosEmpleado",
    "ExpedienteStatus",
]
