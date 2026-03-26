"""
Servicios de aplicación (lógica de negocio).

Este módulo exporta todos los servicios para facilitar imports:
    from core.domain.services import empresa_service, area_servicio_service
"""

# Empresa
from core.domain.services.empresa_service import (
    EmpresaService,
    empresa_service,
)

# Tipo de Servicio
from core.domain.services.tipo_servicio_service import (
    TipoServicioService,
    tipo_servicio_service,
)

# Categoría de Puesto
from core.domain.services.categoria_puesto_service import (
    CategoriaPuestoService,
    categoria_puesto_service,
)

# Contrato
from core.domain.services.contratos import (
    ContratoItemService,
    ContratoMutationService,
    ContratoQueryService,
)
from core.domain.services.contrato_service import (
    ContratoService,
    contrato_service,
)

# Pago
from core.domain.services.pago_service import (
    PagoService,
    pago_service,
)

# ContratoCategoria
from core.domain.services.contrato_categoria_service import (
    ContratoCategoriaService,
    contrato_categoria_service,
)

# Plaza
from core.domain.services.plaza_service import (
    PlazaService,
    plaza_service,
)

# Empleado
from core.domain.services.empleados import (
    EmpleadoMutationService,
    EmpleadoQueryService,
    EmpleadoRestrictionService,
)
from core.domain.services.empleado_service import (
    EmpleadoService,
    empleado_service,
)
from core.domain.services.empleado_descuento_recurrente_service import (
    EmpleadoDescuentoRecurrenteService,
    empleado_descuento_recurrente_service,
)

# Historial Laboral
from core.domain.services.historial_laboral_service import (
    HistorialLaboralService,
    historial_laboral_service,
)


# Archivo
from core.domain.services.archivo_service import (
    ArchivoService,
    archivo_service,
)

# Requisicion
from core.domain.services.requisicion_service import (
    RequisicionService,
    requisicion_service,
)

# Requisicion PDF
from core.domain.services.requisicion_pdf_service import (
    RequisicionPDFService,
    requisicion_pdf_service,
)

# Sede
from core.domain.services.sede_service import (
    SedeService,
    sede_service,
)

# Contacto BUAP
from core.domain.services.contacto_buap_service import (
    ContactoBuapService,
    contacto_buap_service,
)

# User (Autenticación y Perfiles)
from core.domain.services.users import (
    UserAuthService,
    UserCompanyService,
    UserProfileService,
)
from core.domain.services.user_service import user_service

# Institucion
from core.domain.services.institucion_service import (
    InstitucionService,
    institucion_service,
)

# Alta Masiva
from core.domain.services.alta_masiva_parser import (
    AltaMasivaParser,
    alta_masiva_parser,
)

from core.domain.services.alta_masiva_service import (
    AltaMasivaService,
    alta_masiva_service,
)

from core.domain.services.plantilla_service import (
    PlantillaService,
    plantilla_service,
)

from core.domain.services.reporte_alta_masiva_service import (
    ReporteAltaMasivaService,
    reporte_alta_masiva_service,
)

# Entregable
from core.domain.services.entregable_service import (
    EntregableService,
    entregable_service,
)

# Dashboard
from core.domain.services.dashboard_service import (
    DashboardService,
    dashboard_service
)

# Notificacion
from core.domain.services.notificacion_service import (
    NotificacionService,
    notificacion_service,
)

# CURP
from core.domain.services.curp_service import (
    CurpService,
    curp_service,
)

# Cuenta Bancaria Historial
from core.domain.services.cuenta_bancaria_historial_service import (
    CuentaBancariaHistorialService,
    cuenta_bancaria_historial_service,
)

# Configuracion Operativa
from core.domain.services.configuracion_operativa_service import (
    ConfiguracionOperativaService,
    configuracion_operativa_service,
)

# Empleado Documento
from core.domain.services.empleado_documento_service import (
    EmpleadoDocumentoService,
    empleado_documento_service,
)

# Empresa Documento
from core.domain.services.empresa_documento_service import (
    EmpresaDocumentoService,
    empresa_documento_service,
)

# Baja Empleado
from core.domain.services.baja_service import (
    BajaService,
    baja_service,
)

# Onboarding
from core.domain.services.onboarding_service import (
    OnboardingService,
    onboarding_service,
)

# Asistencia
from core.domain.services.asistencias import (
    AsistenciaConfigService,
    AsistenciaIncidenciaService,
    AsistenciaJornadaService,
    AsistenciaPanelService,
)
from core.domain.services.asistencia_service import (
    AsistenciaService,
    asistencia_service,
)

# Concepto Nómina
from core.domain.services.concepto_nomina_service import (
    ConceptoNominaService,
    concepto_nomina_service,
)

# Nómina — Período
from core.domain.services.nomina_periodo_service import (
    NominaPeriodoService,
    nomina_periodo_service,
)

# Nómina — Cálculo
from core.domain.services.nomina_calculo_service import (
    NominaCalculoService,
    nomina_calculo_service,
)

# Dispersión Bancaria
from core.domain.services.dispersion_service import (
    DispersionService,
    dispersion_service,
)

# Configuración Fiscal Empresa
from core.domain.services.configuracion_fiscal_service import (
    ConfiguracionFiscalService,
    configuracion_fiscal_service,
)

# Cotizador
from core.domain.services.cotizacion_service import (
    CotizacionService,
    cotizacion_service,
)

# Cotizador PDF
from core.domain.services.cotizacion_pdf_service import (
    CotizacionPdfService,
    cotizacion_pdf_service,
)

# Incapacidad
from core.domain.services.incapacidad_service import (
    IncapacidadService,
    incapacidad_service,
)


__all__ = [
    # Empresa
    "EmpresaService",
    "empresa_service",
    # Tipo de Servicio
    "TipoServicioService",
    "tipo_servicio_service",
    # Categoría de Puesto
    "CategoriaPuestoService",
    "categoria_puesto_service",
    # Contrato
    "ContratoQueryService",
    "ContratoMutationService",
    "ContratoItemService",
    "ContratoService",
    "contrato_service",
    # Pago
    "PagoService",
    "pago_service",
    # ContratoCategoria
    "ContratoCategoriaService",
    "contrato_categoria_service",
    # Plaza
    "PlazaService",
    "plaza_service",
    # Empleado
    "EmpleadoQueryService",
    "EmpleadoMutationService",
    "EmpleadoRestrictionService",
    "EmpleadoService",
    "empleado_service",
    "EmpleadoDescuentoRecurrenteService",
    "empleado_descuento_recurrente_service",
    # Historial Laboral
    "HistorialLaboralService",
    "historial_laboral_service",
    # Archivo
    "ArchivoService",
    "archivo_service",
    # Requisicion
    "RequisicionService",
    "requisicion_service",
    # Requisicion PDF
    "RequisicionPDFService",
    "requisicion_pdf_service",
    # Sede
    "SedeService",
    "sede_service",
    # Contacto BUAP
    "ContactoBuapService",
    "contacto_buap_service",
    # User (Autenticación y Perfiles)
    "UserAuthService",
    "UserProfileService",
    "UserCompanyService",
    "user_service",
    # Institucion
    "InstitucionService",
    "institucion_service",
    # Alta Masiva
    "AltaMasivaParser",
    "alta_masiva_parser",
    "AltaMasivaService",
    "alta_masiva_service",
    "PlantillaService",
    "plantilla_service",
    "ReporteAltaMasivaService",
    "reporte_alta_masiva_service",
    # Entregable
    "EntregableService",
    "entregable_service",
    # Dasboard
    "DashboardService",
    "dashboard_service",
    # Notificacion
    "NotificacionService",
    "notificacion_service",
    # CURP
    "CurpService",
    "curp_service",
    # Cuenta Bancaria Historial
    "CuentaBancariaHistorialService",
    "cuenta_bancaria_historial_service",
    # Configuracion Operativa
    "ConfiguracionOperativaService",
    "configuracion_operativa_service",
    # Empleado Documento
    "EmpleadoDocumentoService",
    "empleado_documento_service",
    # Baja Empleado
    "BajaService",
    "baja_service",
    # Onboarding
    "OnboardingService",
    "onboarding_service",
    # Asistencia
    "AsistenciaPanelService",
    "AsistenciaConfigService",
    "AsistenciaJornadaService",
    "AsistenciaIncidenciaService",
    "AsistenciaService",
    "asistencia_service",
    # Concepto Nómina
    "ConceptoNominaService",
    "concepto_nomina_service",
    # Nómina — Período
    "NominaPeriodoService",
    "nomina_periodo_service",
    # Nómina — Cálculo
    "NominaCalculoService",
    "nomina_calculo_service",
    # Dispersión Bancaria
    "DispersionService",
    "dispersion_service",
    # Configuración Fiscal Empresa
    "ConfiguracionFiscalService",
    "configuracion_fiscal_service",
    # Cotizador
    "CotizacionService",
    "cotizacion_service",
    # Cotizador PDF
    "CotizacionPdfService",
    "cotizacion_pdf_service",
    # Incapacidad
    "IncapacidadService",
    "incapacidad_service",
]
