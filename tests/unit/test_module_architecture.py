"""Architecture checks for the new modular entrypoints."""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = REPO_ROOT / "core"
APP_SHIM_ROOT = REPO_ROOT / "app"
MODULES_ROOT = CORE_ROOT / "modules"
FORBIDDEN_UI_IMPORT_PREFIXES = ("core.database", "core.domain.repositories")


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


def test_core_entrypoint_is_a_thin_composition_root():
    app_py = (CORE_ROOT / "app.py").read_text(encoding="utf-8")
    assert "from core.bootstrap import create_app" in app_py
    assert "app = create_app()" in app_py
    assert "add_page(" not in app_py


def test_legacy_app_shim_supports_entrypoints():
    package_text = (APP_SHIM_ROOT / "__init__.py").read_text(encoding="utf-8")
    module_text = (APP_SHIM_ROOT / "app.py").read_text(encoding="utf-8")
    assert "from core import app" in package_text
    assert "from core.app import app" in module_text


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


def test_no_app_imports_outside_compat_shim():
    offenders: list[str] = []
    shim_files = {
        APP_SHIM_ROOT / "__init__.py",
        APP_SHIM_ROOT / "app.py",
    }

    for root in (CORE_ROOT, REPO_ROOT / "tests"):
        if not root.exists():
            continue
        for path in _iter_python_files(root):
            if path in shim_files:
                continue
            imports = _imports_for(path)
            if any(imported == "app" or imported.startswith("app.") for imported in imports):
                offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == [], f"Legacy app imports found outside shim: {offenders}"
