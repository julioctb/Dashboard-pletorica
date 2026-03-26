"""Evita que states y páginas vuelvan a depender de wrappers de validación legacy."""

from pathlib import Path


FORBIDDEN_IMPORT_FRAGMENTS = (
    "core.presentation.pages.backoffice.categorias_puesto.categorias_puesto_validators",
    "core.presentation.pages.backoffice.contratos.contrato_categorias_validators",
    "core.presentation.pages.backoffice.contratos.contratos_validators",
    "core.presentation.pages.backoffice.contratos.pagos_validators",
    "core.presentation.pages.backoffice.empleados.empleados_validators",
    "core.presentation.pages.backoffice.empresas.empresas_validators",
    "core.presentation.pages.backoffice.sedes.sedes_validators",
    "core.presentation.pages.backoffice.tipo_servicio.tipo_servicio_validators",
    "core.presentation.pages.backoffice.admin.usuarios.usuarios_validators",
)

LEGACY_WRAPPER_PATHS = (
    "core/presentation/pages/backoffice/admin/usuarios/usuarios_validators.py",
    "core/presentation/pages/backoffice/categorias_puesto/categorias_puesto_validators.py",
    "core/presentation/pages/backoffice/contratos/contrato_categorias_validators.py",
    "core/presentation/pages/backoffice/contratos/contratos_validators.py",
    "core/presentation/pages/backoffice/contratos/pagos_validators.py",
    "core/presentation/pages/backoffice/empleados/empleados_validators.py",
    "core/presentation/pages/backoffice/empresas/empresas_validators.py",
    "core/presentation/pages/backoffice/sedes/sedes_validators.py",
    "core/presentation/pages/backoffice/tipo_servicio/tipo_servicio_validators.py",
)


def test_presentation_no_importa_wrappers_validacion_legacy():
    root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []

    for path in sorted(root.rglob("*.py")):
        if "tests" in path.parts:
            continue

        text = path.read_text(encoding="utf-8")
        if any(fragment in text for fragment in FORBIDDEN_IMPORT_FRAGMENTS):
            offenders.append(str(path.relative_to(root.parent)))

    assert offenders == [], f"Imports legacy detectados: {offenders}"


def test_wrappers_legacy_ya_no_existen():
    repo_root = Path(__file__).resolve().parents[2]
    existentes = [
        path
        for path in LEGACY_WRAPPER_PATHS
        if (repo_root / path).exists()
    ]
    assert existentes == [], f"Wrappers legacy presentes: {existentes}"
