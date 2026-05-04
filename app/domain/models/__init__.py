"""
Entidades de dominio del sistema.

Este módulo exporta todas las entidades de negocio para facilitar imports:
    from app.domain.models import Empresa, AreaServicio, etc.
"""

# Enums centralizados
from app.domain.enums import (
    Estatus,
    EstatusEmpresa,
    TipoEmpresa,
    # Enums de Usuario
    RolUsuario,
    RolPlataforma,
    RolEmpresa,
    # Enums de Cotización
    TipoCotizacion,
    TipoSueldo,
    EstatusCotizacion,
    EstatusPartidaCotizacion,
    TipoConceptoCotizacion,
    TipoValorConcepto,
    # Enums de Contrato
    TipoContrato,
    ModalidadAdjudicacion,
    TipoDuracion,
    EstatusContrato,
    # Enums de Plaza
    EstatusPlaza,
    TipoJornadaPlaza,
    # Enums de Empleado
    EstatusEmpleado,
    GeneroEmpleado,
    MotivoBaja,
    AccionRestriccion,
    # Enums de Historial Laboral
    TipoMovimiento,
    # Enums de Baja
    EstatusBaja,
    EstatusLiquidacion,
    # Enums de Asistencia
    EstatusJornada,
    TipoIncidencia,
    OrigenIncidencia,
    TipoRegistroAsistencia,
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
    TipoDocumentoEmpresa,
    EstatusDocumento,
    # Enums de Nómina — Catálogo
    TipoConcepto,
    TratamientoISR,
    OrigenCaptura,
    # Enums de Nómina — Operación
    EstatusPeriodoNomina,
    PeriodicidadNomina,
    ReglaCalculoQuincenal,
    TipoPeriodoNomina,
    ModoCalculoAguinaldo,
    OrigenMovimiento,
    EstatusNominaEmpleado,
)

# Empresa
from app.domain.models.empresa import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
)

# Perfil de Usuario
from app.domain.models.user_profile import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResumen
)

# Relacion Usuario/ Empresa
from app.domain.models.user_company import(
    UserCompany,
    UserCompanyCreate,
    UserCompanyResumen,
    UserCompanyAsignacionInicial,
)

# Institucion
from app.domain.models.institucion import (
    Institucion,
    InstitucionCreate,
    InstitucionUpdate,
    InstitucionResumen,
    InstitucionEmpresa,
)

# Tipo de Servicio
from app.domain.models.tipo_servicio import (
    TipoServicio,
    TipoServicioCreate,
    TipoServicioUpdate,
)

# Categoría de Puesto
from app.domain.models.categoria_puesto import (
    CategoriaPuesto,
    CategoriaPuestoCreate,
    CategoriaPuestoUpdate,
)

# Contrato
from app.domain.models.contrato import (
    Contrato,
    ContratoCreate,
    ContratoUpdate,
    ContratoResumen,
)

# Pago
from app.domain.models.pago import (
    Pago,
    PagoCreate,
    PagoUpdate,
    PagoResumen,
    ResumenPagosContrato,
)

# ContratoCategoria
from app.domain.models.contrato_categoria import (
    ContratoCategoria,
    ContratoCategoriaCreate,
    ContratoCategoriaUpdate,
    ContratoCategoriaResumen,
    ResumenPersonalContrato,
)

# Plaza
from app.domain.models.plaza import (
    Plaza,
    PlazaCreate,
    PlazaUpdate,
    PlazaResumen,
    ResumenPlazasContrato,
    ResumenPlazasCategoria,
)

# Empleado
from app.domain.models.empleado import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
)
from app.domain.models.empleado_descuento_recurrente import (
    EmpleadoDescuentoRecurrente,
    EmpleadoDescuentoRecurrenteCreate,
)

# Empresa Documento
from app.domain.models.empresa_documento import (
    EmpresaDocumento,
    EmpresaDocumentoCreate,
    EmpresaDocumentoResumen,
    EmpresaDocumentoRequisito,
    EmpresaDocumentoRequisitoCreate,
    EmpresaDocumentoShareLink,
    EmpresaDocumentoShareLinkCreate,
)

# Historial Laboral
from app.domain.models.historial_laboral import (
    HistorialLaboral,
    HistorialLaboralInterno,
    HistorialLaboralResumen,
)

# Baja Empleado
from app.domain.models.baja_empleado import (
    BajaEmpleado,
    BajaEmpleadoCreate,
    BajaEmpleadoResumen,
)

# Archivo
from app.domain.models.archivo import (
    EntidadArchivo,
    TipoArchivo,
    OrigenArchivo,
    ArchivoSistema,
    ArchivoSistemaUpdate,
    ArchivoUploadResponse,
)

# Contrato Item
from app.domain.models.contrato_item import (
    ContratoItem,
    ContratoItemCreate,
)

# Requisicion
from app.domain.models.requisicion import (
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
from app.domain.models.sede import (
    Sede,
    SedeCreate,
    SedeUpdate,
    SedeResumen,
)

# Restriccion de Empleado
from app.domain.models.empleado_restriccion_log import (
    EmpleadoRestriccionLog,
    EmpleadoRestriccionLogCreate,
    EmpleadoRestriccionLogResumen,
)

# Contacto BUAP
from app.domain.models.contacto_buap import (
    ContactoBuap,
    ContactoBuapCreate,
    ContactoBuapUpdate,
)

# Alta Masiva
from app.domain.models.alta_masiva import (
    ResultadoFila,
    RegistroValidado,
    ResultadoValidacion,
    ResultadoProcesamiento,
    DetalleResultado,
)

# Dashboard
from app.domain.models.dashboard import DashboardMetricas

# Notificacion
from app.domain.models.notificacion import (
    Notificacion,
    NotificacionCreate,
)

# Entregables
from app.domain.models.entregable import (
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
    from app.domain.models.costo_patronal import (
        ConfiguracionEmpresa,
        Trabajador,
        ResultadoCuotas,
    )
except ImportError:
    pass  # El módulo puede no existir aún

# Empleado Documento
from app.domain.models.empleado_documento import (
    EmpleadoDocumento,
    EmpleadoDocumentoCreate,
    EmpleadoDocumentoResumen,
)

# Cuenta Bancaria Historial
from app.domain.models.cuenta_bancaria_historial import (
    CuentaBancariaHistorial,
    CuentaBancariaHistorialCreate,
)

# Asistencia
from app.domain.models.asistencia import (
    Horario,
    SupervisorSede,
    JornadaAsistencia,
    JornadaAsistenciaCreate,
    IncidenciaAsistencia,
    IncidenciaAsistenciaCreate,
    RegistroAsistencia,
    EmpleadoAsistenciaEsperado,
)

# Configuración Operativa Empresa
from app.domain.models.configuracion_operativa_empresa import (
    ConfiguracionOperativaEmpresa,
    ConfiguracionOperativaEmpresaCreate,
    ConfiguracionOperativaEmpresaUpdate,
)

# CURP Validación
from app.domain.models.curp_validacion import (
    CurpValidacionResponse,
    CurpRenapoResponse,
)

# Onboarding
from app.domain.models.onboarding import (
    AltaEmpleadoBuap,
    CompletarDatosEmpleado,
    ExpedienteStatus,
)

# Concepto Nómina
from app.domain.models.concepto_nomina import (
    ConceptoNomina,
    ConceptoNominaCreate,
    ConceptoNominaResumen,
    ConceptoNominaEmpresa,
    ConceptoNominaEmpresaCreate,
    ConceptoNominaEmpresaResumen,
)

# Período de Nómina
from app.domain.models.periodo_nomina import (
    PeriodoNomina,
    PeriodoNominaCreate,
    PeriodoNominaUpdate,
    PeriodoNominaResumen,
)

# Nómina Empleado
from app.domain.models.nomina_empleado import (
    NominaEmpleado,
    NominaEmpleadoCreate,
    NominaEmpleadoUpdate,
    NominaEmpleadoResumen,
)

# Nómina Movimiento
from app.domain.models.nomina_movimiento import (
    NominaMovimiento,
    NominaMovimientoCreate,
    NominaMovimientoResumen,
)
from app.domain.models.configuracion_dispersion import (
    ConfiguracionBancoEmpresa,
    ConfiguracionBancoEmpresaCreate,
    DispersionLayout,
    ResultadoDispersion,
)

# Configuración Fiscal Empresa
from app.domain.models.configuracion_fiscal_empresa import (
    ConfiguracionFiscalEmpresa,
    ConfiguracionFiscalEmpresaCreate,
    ConfiguracionFiscalEmpresaUpdate,
)

# Cotización
from app.domain.models.cotizacion import (
    Cotizacion,
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionResumen,
)

# Cotización Partida
from app.domain.models.cotizacion_partida import (
    CotizacionPartida,
    CotizacionPartidaCreate,
    CotizacionPartidaResumen,
)

# Cotización Partida Categoría
from app.domain.models.cotizacion_partida_categoria import (
    CotizacionPartidaCategoria,
    CotizacionPartidaCategoriaCreate,
    CotizacionPartidaCategoriaResumen,
)

# Cotización Concepto
from app.domain.models.cotizacion_concepto import (
    CotizacionConcepto,
    CotizacionConceptoCreate,
)

# Cotización Item
from app.domain.models.cotizacion_item import (
    CotizacionItem,
    CotizacionItemCreate,
)

# Cotización Concepto Valor
from app.domain.models.cotizacion_concepto_valor import (
    CotizacionConceptoValor,
    CotizacionConceptoValorCreate,
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
    "TipoDocumentoEmpresa",
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
    # Baja Empleado
    "EstatusBaja",
    "EstatusLiquidacion",
    "BajaEmpleado",
    "BajaEmpleadoCreate",
    "BajaEmpleadoResumen",
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
    # Empresa Documento
    "EmpresaDocumento",
    "EmpresaDocumentoCreate",
    "EmpresaDocumentoResumen",
    "EmpresaDocumentoShareLink",
    "EmpresaDocumentoShareLinkCreate",
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
    # Enums Nómina — Catálogo
    "TipoConcepto",
    "TratamientoISR",
    "OrigenCaptura",
    # Enums Nómina — Operación
    "EstatusPeriodoNomina",
    "PeriodicidadNomina",
    "ReglaCalculoQuincenal",
    "OrigenMovimiento",
    "EstatusNominaEmpleado",
    # Concepto Nómina
    "ConceptoNomina",
    "ConceptoNominaCreate",
    "ConceptoNominaResumen",
    "ConceptoNominaEmpresa",
    "ConceptoNominaEmpresaCreate",
    "ConceptoNominaEmpresaResumen",
    # Período de Nómina
    "PeriodoNomina",
    "PeriodoNominaCreate",
    "PeriodoNominaUpdate",
    "PeriodoNominaResumen",
    # Nómina Empleado
    "NominaEmpleado",
    "NominaEmpleadoCreate",
    "NominaEmpleadoUpdate",
    "NominaEmpleadoResumen",
    # Nómina Movimiento
    "NominaMovimiento",
    "NominaMovimientoCreate",
    "NominaMovimientoResumen",
    # Dispersión Bancaria
    "ConfiguracionBancoEmpresa",
    "ConfiguracionBancoEmpresaCreate",
    "DispersionLayout",
    "ResultadoDispersion",
    # Enums Cotización
    "TipoCotizacion",
    "TipoSueldo",
    "EstatusCotizacion",
    "EstatusPartidaCotizacion",
    "TipoConceptoCotizacion",
    "TipoValorConcepto",
    # Configuración Fiscal Empresa
    "ConfiguracionFiscalEmpresa",
    "ConfiguracionFiscalEmpresaCreate",
    "ConfiguracionFiscalEmpresaUpdate",
    # Cotización
    "Cotizacion",
    "CotizacionCreate",
    "CotizacionUpdate",
    "CotizacionResumen",
    # Cotización Partida
    "CotizacionPartida",
    "CotizacionPartidaCreate",
    "CotizacionPartidaResumen",
    # Cotización Partida Categoría
    "CotizacionPartidaCategoria",
    "CotizacionPartidaCategoriaCreate",
    "CotizacionPartidaCategoriaResumen",
    # Cotización Concepto
    "CotizacionConcepto",
    "CotizacionConceptoCreate",
    # Cotización Item
    "CotizacionItem",
    "CotizacionItemCreate",
    # Cotización Concepto Valor
    "CotizacionConceptoValor",
    "CotizacionConceptoValorCreate",
]
