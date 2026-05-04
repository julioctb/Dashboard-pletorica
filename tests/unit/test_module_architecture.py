"""Architecture checks for the canonical app package topology."""

import ast
import importlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "app"
MODULES_ROOT = APP_ROOT / "modules"
FORBIDDEN_UI_IMPORT_PREFIXES = ("app.database", "app.domain.repositories")
FORBIDDEN_EMPLOYEE_GLOBAL_APPLICATION_IMPORTS = {
    "AltaMasivaParser",
    "AltaMasivaService",
    "BajaService",
    "CuentaBancariaHistorialService",
    "EmpleadoDescuentoRecurrenteService",
    "EmpleadoDocumentoService",
    "EmpleadoMutationService",
    "EmpleadoQueryService",
    "EmpleadoRestrictionService",
    "EmpleadoService",
    "HistorialLaboralService",
    "IncapacidadService",
    "OnboardingService",
    "PlantillaService",
    "ReporteAltaMasivaService",
    "alta_masiva_parser",
    "alta_masiva_service",
    "baja_service",
    "cuenta_bancaria_historial_service",
    "empleado_descuento_recurrente_service",
    "empleado_documento_service",
    "empleado_service",
    "historial_laboral_service",
    "incapacidad_service",
    "onboarding_service",
    "plantilla_service",
    "reporte_alta_masiva_service",
}
FORBIDDEN_EMPLOYEE_GLOBAL_APPLICATION_EXPORTS = set(
    FORBIDDEN_EMPLOYEE_GLOBAL_APPLICATION_IMPORTS
)


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _imports_for(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_app_entrypoint_is_a_thin_composition_root():
    app_py = (APP_ROOT / "app.py").read_text(encoding="utf-8")
    assert "from app.bootstrap import create_app" in app_py
    assert "app = create_app()" in app_py
    assert "add_page(" not in app_py


def test_package_root_exposes_lazy_app_proxy():
    package_text = (APP_ROOT / "__init__.py").read_text(encoding="utf-8")
    assert "_LazyAppProxy" in package_text
    assert "app = _LazyAppProxy()" in package_text


def test_modular_topology_exists_for_hotspots():
    expected_paths = (
        MODULES_ROOT / "empleados" / "application",
        MODULES_ROOT / "empleados" / "domain",
        MODULES_ROOT / "empleados" / "infrastructure",
        MODULES_ROOT / "empleados" / "ui" / "backoffice",
        MODULES_ROOT / "empleados" / "ui" / "portal",
        MODULES_ROOT / "cotizaciones" / "application",
        MODULES_ROOT / "cotizaciones" / "domain",
        MODULES_ROOT / "cotizaciones" / "ui" / "portal",
        MODULES_ROOT / "nomina" / "application",
        MODULES_ROOT / "nomina" / "domain",
        MODULES_ROOT / "nomina" / "ui" / "backoffice",
        MODULES_ROOT / "nomina" / "ui" / "portal",
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in expected_paths if not path.exists()]
    assert missing == [], f"Missing modular paths: {missing}"


def test_new_module_ui_does_not_import_legacy_db_layers_directly():
    offenders: list[str] = []
    for path in _iter_python_files(MODULES_ROOT):
        if "ui" not in path.parts:
            continue
        imports = _imports_for(path)
        if any(
            imported.startswith(prefix)
            for imported in imports
            for prefix in FORBIDDEN_UI_IMPORT_PREFIXES
        ):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == [], f"Forbidden UI imports detected: {offenders}"


def test_no_legacy_core_imports_remain():
    offenders: list[str] = []

    for root in (APP_ROOT, REPO_ROOT / "tests"):
        if not root.exists():
            continue
        for path in _iter_python_files(root):
            imports = _imports_for(path)
            if any(imported == "core" or imported.startswith("core.") for imported in imports):
                offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == [], f"Legacy core imports found: {offenders}"


def test_presentation_avoids_employee_services_from_global_application_surface():
    offenders: list[str] = []
    presentation_root = APP_ROOT / "presentation"

    for path in _iter_python_files(presentation_root):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != "app.modules.application":
                continue

            forbidden_names = sorted(
                alias.name
                for alias in node.names
                if alias.name in FORBIDDEN_EMPLOYEE_GLOBAL_APPLICATION_IMPORTS
            )
            if forbidden_names:
                offenders.append(
                    f"{path.relative_to(REPO_ROOT)} -> {', '.join(forbidden_names)}"
                )

    assert offenders == [], (
        "Employee services must be imported from app.modules.empleados.application: "
        f"{offenders}"
    )


def test_global_application_surface_does_not_export_employee_symbols():
    module = importlib.import_module("app.modules.application")
    exported = set(getattr(module, "__all__", []))

    leaked_exports = sorted(
        exported & FORBIDDEN_EMPLOYEE_GLOBAL_APPLICATION_EXPORTS
    )
    leaked_attributes = sorted(
        name
        for name in FORBIDDEN_EMPLOYEE_GLOBAL_APPLICATION_EXPORTS
        if hasattr(module, name)
    )

    assert leaked_exports == [], (
        "Employee symbols leaked in app.modules.application.__all__: "
        f"{leaked_exports}"
    )
    assert leaked_attributes == [], (
        "Employee symbols leaked as app.modules.application attributes: "
        f"{leaked_attributes}"
    )
