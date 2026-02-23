"""
Servicios de aplicación (lógica de negocio).

Este módulo exporta todos los servicios para facilitar imports:
    from app.services import empresa_service, area_servicio_service
"""

# Empresa
from app.services.empresa_service import (
    EmpresaService,
    empresa_service,
)

# Tipo de Servicio
from app.services.tipo_servicio_service import (
    TipoServicioService,
    tipo_servicio_service,
)

# Categoría de Puesto
from app.services.categoria_puesto_service import (
    CategoriaPuestoService,
    categoria_puesto_service,
)

# Contrato
from app.services.contrato_service import (
    ContratoService,
    contrato_service,
)

# Pago
from app.services.pago_service import (
    PagoService,
    pago_service,
)

# ContratoCategoria
from app.services.contrato_categoria_service import (
    ContratoCategoriaService,
    contrato_categoria_service,
)

# Plaza
from app.services.plaza_service import (
    PlazaService,
    plaza_service,
)

# Empleado
from app.services.empleado_service import (
    EmpleadoService,
    empleado_service,
)

# Historial Laboral
from app.services.historial_laboral_service import (
    HistorialLaboralService,
    historial_laboral_service,
)


# Archivo
from app.services.archivo_service import (
    ArchivoService,
    archivo_service,
)

# Requisicion
from app.services.requisicion_service import (
    RequisicionService,
    requisicion_service,
)

# Requisicion PDF
from app.services.requisicion_pdf_service import (
    RequisicionPDFService,
    requisicion_pdf_service,
)

# Sede
from app.services.sede_service import (
    SedeService,
    sede_service,
)

# Contacto BUAP
from app.services.contacto_buap_service import (
    ContactoBuapService,
    contacto_buap_service,
)

# User (Autenticación y Perfiles)
from app.services.user_service import user_service

# Alta Masiva
from app.services.alta_masiva_parser import (
    AltaMasivaParser,
    alta_masiva_parser,
)

from app.services.alta_masiva_service import (
    AltaMasivaService,
    alta_masiva_service,
)

from app.services.plantilla_service import (
    PlantillaService,
    plantilla_service,
)

from app.services.reporte_alta_masiva_service import (
    ReporteAltaMasivaService,
    reporte_alta_masiva_service,
)

# Entregable
from app.services.entregable_service import (
    EntregableService,
    entregable_service,
)

# Dashboard
from app.services.dashboard_service import (
    DashboardService,
    dashboard_service
)

# Notificacion
from app.services.notificacion_service import (
    NotificacionService,
    notificacion_service,
)

# CURP
from app.services.curp_service import (
    CurpService,
    curp_service,
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
    "EmpleadoService",
    "empleado_service",
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
    "user_service",
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
]