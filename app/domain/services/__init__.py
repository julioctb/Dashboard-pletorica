"""
Servicios de aplicación (lógica de negocio).

Este módulo exporta todos los servicios para facilitar imports:
    from app.domain.services import empresa_service, area_servicio_service
"""

# Empresa
from app.domain.services.empresa_service import (
    EmpresaService,
    empresa_service,
)

# Tipo de Servicio
from app.domain.services.tipo_servicio_service import (
    TipoServicioService,
    tipo_servicio_service,
)

# Categoría de Puesto
from app.domain.services.categoria_puesto_service import (
    CategoriaPuestoService,
    categoria_puesto_service,
)

# Contrato
from app.domain.services.contratos import (
    ContratoItemService,
    ContratoMutationService,
    ContratoQueryService,
)
from app.domain.services.contrato_service import (
    ContratoService,
    contrato_service,
)

# Pago
from app.domain.services.pago_service import (
    PagoService,
    pago_service,
)

# ContratoCategoria
from app.domain.services.contrato_categoria_service import (
    ContratoCategoriaService,
    contrato_categoria_service,
)

# Plaza
from app.domain.services.plaza_service import (
    PlazaService,
    plaza_service,
)

# Empleado
from app.domain.services.empleados import (
    EmpleadoMutationService,
    EmpleadoQueryService,
    EmpleadoRestrictionService,
)
from app.domain.services.empleado_service import (
    EmpleadoService,
    empleado_service,
)
from app.domain.services.empleado_descuento_recurrente_service import (
    EmpleadoDescuentoRecurrenteService,
    empleado_descuento_recurrente_service,
)

# Historial Laboral
from app.domain.services.historial_laboral_service import (
    HistorialLaboralService,
    historial_laboral_service,
)


# Archivo
from app.domain.services.archivo_service import (
    ArchivoService,
    archivo_service,
)

# Requisicion
from app.domain.services.requisicion_service import (
    RequisicionService,
    requisicion_service,
)

# Requisicion PDF
from app.domain.services.requisicion_pdf_service import (
    RequisicionPDFService,
    requisicion_pdf_service,
)

# Sede
from app.domain.services.sede_service import (
    SedeService,
    sede_service,
)

# Contacto BUAP
from app.domain.services.contacto_buap_service import (
    ContactoBuapService,
    contacto_buap_service,
)

# User (Autenticación y Perfiles)
from app.domain.services.users import (
    UserAuthService,
    UserCompanyService,
    UserProfileService,
)
from app.domain.services.user_service import user_service

# Institucion
from app.domain.services.institucion_service import (
    InstitucionService,
    institucion_service,
)

# Alta Masiva
from app.domain.services.alta_masiva_parser import (
    AltaMasivaParser,
    alta_masiva_parser,
)

from app.domain.services.alta_masiva_service import (
    AltaMasivaService,
    alta_masiva_service,
)

from app.domain.services.plantilla_service import (
    PlantillaService,
    plantilla_service,
)

from app.domain.services.reporte_alta_masiva_service import (
    ReporteAltaMasivaService,
    reporte_alta_masiva_service,
)

# Entregable
from app.domain.services.entregable_service import (
    EntregableService,
    entregable_service,
)

# Dashboard
from app.domain.services.dashboard_service import (
    DashboardService,
    dashboard_service
)

# Notificacion
from app.domain.services.notificacion_service import (
    NotificacionService,
    notificacion_service,
)

# CURP
from app.domain.services.curp_service import (
    CurpService,
    curp_service,
)

# Cuenta Bancaria Historial
from app.domain.services.cuenta_bancaria_historial_service import (
    CuentaBancariaHistorialService,
    cuenta_bancaria_historial_service,
)

# Configuracion Operativa
from app.domain.services.configuracion_operativa_service import (
    ConfiguracionOperativaService,
    configuracion_operativa_service,
)

# Empleado Documento
from app.domain.services.empleado_documento_service import (
    EmpleadoDocumentoService,
    empleado_documento_service,
)

# Empresa Documento
from app.domain.services.empresa_documento_service import (
    EmpresaDocumentoService,
    empresa_documento_service,
)

# Baja Empleado
from app.domain.services.baja_service import (
    BajaService,
    baja_service,
)

# Onboarding
from app.domain.services.onboarding_service import (
    OnboardingService,
    onboarding_service,
)

# Asistencia
from app.domain.services.asistencias import (
    AsistenciaConfigService,
    AsistenciaIncidenciaService,
    AsistenciaJornadaService,
    AsistenciaPanelService,
)
from app.domain.services.asistencia_service import (
    AsistenciaService,
    asistencia_service,
)

# Concepto Nómina
from app.domain.services.concepto_nomina_service import (
    ConceptoNominaService,
    concepto_nomina_service,
)

# Nómina — Período
from app.domain.services.nomina_periodo_service import (
    NominaPeriodoService,
    nomina_periodo_service,
)

# Nómina — Cálculo
from app.domain.services.nomina_calculo_service import (
    NominaCalculoService,
    nomina_calculo_service,
)

# Dispersión Bancaria
from app.domain.services.dispersion_service import (
    DispersionService,
    dispersion_service,
)

# Configuración Fiscal Empresa
from app.domain.services.configuracion_fiscal_service import (
    ConfiguracionFiscalService,
    configuracion_fiscal_service,
)

# Cotizador
from app.domain.services.cotizacion_service import (
    CotizacionService,
    cotizacion_service,
)

# Cotizador PDF
from app.domain.services.cotizacion_pdf_service import (
    CotizacionPdfService,
    cotizacion_pdf_service,
)

# Incapacidad
from app.domain.services.incapacidad_service import (
    IncapacidadService,
    incapacidad_service,
)
from app.domain.services.presentation_bridge_service import (
    PresentationBridgeService,
    presentation_bridge_service,
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
    # Presentation Bridge
    "PresentationBridgeService",
    "presentation_bridge_service",
]
