"""
Entidades de dominio del sistema.

Este módulo exporta todas las entidades de negocio para facilitar imports:
    from core.domain.models import Empresa, AreaServicio, etc.
"""

# Enums centralizados
from core.core.enums import (
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
from core.domain.models.empresa import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
)

# Perfil de Usuario
from core.domain.models.user_profile import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResumen
)

# Relacion Usuario/ Empresa
from core.domain.models.user_company import(
    UserCompany,
    UserCompanyCreate,
    UserCompanyResumen,
    UserCompanyAsignacionInicial,
)

# Institucion
from core.domain.models.institucion import (
    Institucion,
    InstitucionCreate,
    InstitucionUpdate,
    InstitucionResumen,
    InstitucionEmpresa,
)

# Tipo de Servicio
from core.domain.models.tipo_servicio import (
    TipoServicio,
    TipoServicioCreate,
    TipoServicioUpdate,
)

# Categoría de Puesto
from core.domain.models.categoria_puesto import (
    CategoriaPuesto,
    CategoriaPuestoCreate,
    CategoriaPuestoUpdate,
)

# Contrato
from core.domain.models.contrato import (
    Contrato,
    ContratoCreate,
    ContratoUpdate,
    ContratoResumen,
)

# Pago
from core.domain.models.pago import (
    Pago,
    PagoCreate,
    PagoUpdate,
    PagoResumen,
    ResumenPagosContrato,
)

# ContratoCategoria
from core.domain.models.contrato_categoria import (
    ContratoCategoria,
    ContratoCategoriaCreate,
    ContratoCategoriaUpdate,
    ContratoCategoriaResumen,
    ResumenPersonalContrato,
)

# Plaza
from core.domain.models.plaza import (
    Plaza,
    PlazaCreate,
    PlazaUpdate,
    PlazaResumen,
    ResumenPlazasContrato,
    ResumenPlazasCategoria,
)

# Empleado
from core.domain.models.empleado import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
)
from core.domain.models.empleado_descuento_recurrente import (
    EmpleadoDescuentoRecurrente,
    EmpleadoDescuentoRecurrenteCreate,
)

# Empresa Documento
from core.domain.models.empresa_documento import (
    EmpresaDocumento,
    EmpresaDocumentoCreate,
    EmpresaDocumentoResumen,
    EmpresaDocumentoRequisito,
    EmpresaDocumentoRequisitoCreate,
    EmpresaDocumentoShareLink,
    EmpresaDocumentoShareLinkCreate,
)

# Historial Laboral
from core.domain.models.historial_laboral import (
    HistorialLaboral,
    HistorialLaboralInterno,
    HistorialLaboralResumen,
)

# Baja Empleado
from core.domain.models.baja_empleado import (
    BajaEmpleado,
    BajaEmpleadoCreate,
    BajaEmpleadoResumen,
)

# Archivo
from core.domain.models.archivo import (
    EntidadArchivo,
    TipoArchivo,
    OrigenArchivo,
    ArchivoSistema,
    ArchivoSistemaUpdate,
    ArchivoUploadResponse,
)

# Contrato Item
from core.domain.models.contrato_item import (
    ContratoItem,
    ContratoItemCreate,
)

# Requisicion
from core.domain.models.requisicion import (
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
from core.domain.models.sede import (
    Sede,
    SedeCreate,
    SedeUpdate,
    SedeResumen,
)

# Restriccion de Empleado
from core.domain.models.empleado_restriccion_log import (
    EmpleadoRestriccionLog,
    EmpleadoRestriccionLogCreate,
    EmpleadoRestriccionLogResumen,
)

# Contacto BUAP
from core.domain.models.contacto_buap import (
    ContactoBuap,
    ContactoBuapCreate,
    ContactoBuapUpdate,
)

# Alta Masiva
from core.domain.models.alta_masiva import (
    ResultadoFila,
    RegistroValidado,
    ResultadoValidacion,
    ResultadoProcesamiento,
    DetalleResultado,
)

# Dashboard
from core.domain.models.dashboard import DashboardMetricas

# Notificacion
from core.domain.models.notificacion import (
    Notificacion,
    NotificacionCreate,
)

# Entregables
from core.domain.models.entregable import (
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
    from core.domain.models.costo_patronal import (
        ConfiguracionEmpresa,
        Trabajador,
        ResultadoCuotas,
    )
except ImportError:
    pass  # El módulo puede no existir aún

# Empleado Documento
from core.domain.models.empleado_documento import (
    EmpleadoDocumento,
    EmpleadoDocumentoCreate,
    EmpleadoDocumentoResumen,
)

# Cuenta Bancaria Historial
from core.domain.models.cuenta_bancaria_historial import (
    CuentaBancariaHistorial,
    CuentaBancariaHistorialCreate,
)

# Asistencia
from core.domain.models.asistencia import (
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
from core.domain.models.configuracion_operativa_empresa import (
    ConfiguracionOperativaEmpresa,
    ConfiguracionOperativaEmpresaCreate,
    ConfiguracionOperativaEmpresaUpdate,
)

# CURP Validación
from core.domain.models.curp_validacion import (
    CurpValidacionResponse,
    CurpRenapoResponse,
)

# Onboarding
from core.domain.models.onboarding import (
    AltaEmpleadoBuap,
    CompletarDatosEmpleado,
    ExpedienteStatus,
)

# Concepto Nómina
from core.domain.models.concepto_nomina import (
    ConceptoNomina,
    ConceptoNominaCreate,
    ConceptoNominaResumen,
    ConceptoNominaEmpresa,
    ConceptoNominaEmpresaCreate,
    ConceptoNominaEmpresaResumen,
)

# Período de Nómina
from core.domain.models.periodo_nomina import (
    PeriodoNomina,
    PeriodoNominaCreate,
    PeriodoNominaUpdate,
    PeriodoNominaResumen,
)

# Nómina Empleado
from core.domain.models.nomina_empleado import (
    NominaEmpleado,
    NominaEmpleadoCreate,
    NominaEmpleadoUpdate,
    NominaEmpleadoResumen,
)

# Nómina Movimiento
from core.domain.models.nomina_movimiento import (
    NominaMovimiento,
    NominaMovimientoCreate,
    NominaMovimientoResumen,
)
from core.domain.models.configuracion_dispersion import (
    ConfiguracionBancoEmpresa,
    ConfiguracionBancoEmpresaCreate,
    DispersionLayout,
    ResultadoDispersion,
)

# Configuración Fiscal Empresa
from core.domain.models.configuracion_fiscal_empresa import (
    ConfiguracionFiscalEmpresa,
    ConfiguracionFiscalEmpresaCreate,
    ConfiguracionFiscalEmpresaUpdate,
)

# Cotización
from core.domain.models.cotizacion import (
    Cotizacion,
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionResumen,
)

# Cotización Partida
from core.domain.models.cotizacion_partida import (
    CotizacionPartida,
    CotizacionPartidaCreate,
    CotizacionPartidaResumen,
)

# Cotización Partida Categoría
from core.domain.models.cotizacion_partida_categoria import (
    CotizacionPartidaCategoria,
    CotizacionPartidaCategoriaCreate,
    CotizacionPartidaCategoriaResumen,
)

# Cotización Concepto
from core.domain.models.cotizacion_concepto import (
    CotizacionConcepto,
    CotizacionConceptoCreate,
)

# Cotización Item
from core.domain.models.cotizacion_item import (
    CotizacionItem,
    CotizacionItemCreate,
)

# Cotización Concepto Valor
from core.domain.models.cotizacion_concepto_valor import (
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
