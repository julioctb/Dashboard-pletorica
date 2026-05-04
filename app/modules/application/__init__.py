"""Canonical application surface for UI orchestration imports."""

from app.domain import services as legacy_services
from app.domain.services.archivo_service import ArchivoValidationError
from app.domain.services.empresa_documento_service import empresa_documento_service
from app.domain.services.super_admin_dashboard_service import super_admin_dashboard_service

FORBIDDEN_EMPLOYEE_EXPORTS = {
    # Query/mutation orchestration for employees.
    "EmpleadoMutationService",
    "EmpleadoQueryService",
    "EmpleadoRestrictionService",
    # Main employee services.
    "EmpleadoService",
    "empleado_service",
    "EmpleadoDocumentoService",
    "empleado_documento_service",
    "HistorialLaboralService",
    "historial_laboral_service",
    "IncapacidadService",
    "incapacidad_service",
    "BajaService",
    "baja_service",
    "OnboardingService",
    "onboarding_service",
    # Employee satellite services.
    "AltaMasivaParser",
    "alta_masiva_parser",
    "AltaMasivaService",
    "alta_masiva_service",
    "PlantillaService",
    "plantilla_service",
    "ReporteAltaMasivaService",
    "reporte_alta_masiva_service",
    "EmpleadoDescuentoRecurrenteService",
    "empleado_descuento_recurrente_service",
    "CuentaBancariaHistorialService",
    "cuenta_bancaria_historial_service",
}


def _export_public_names(module, excluded: set[str] | None = None) -> list[str]:
    excluded = excluded or set()
    names = list(getattr(module, "__all__", []))
    exported_names: list[str] = []
    for name in names:
        if name in excluded:
            continue
        globals()[name] = getattr(module, name)
        exported_names.append(name)
    return exported_names


__all__ = _export_public_names(
    legacy_services,
    excluded=FORBIDDEN_EMPLOYEE_EXPORTS,
)
if "ArchivoValidationError" not in __all__:
    __all__.append("ArchivoValidationError")
if "empresa_documento_service" not in __all__:
    __all__.append("empresa_documento_service")
if "super_admin_dashboard_service" not in __all__:
    __all__.append("super_admin_dashboard_service")
