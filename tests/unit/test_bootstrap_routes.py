"""Route registry checks for the modular bootstrap layer."""

from app.bootstrap.routes_backoffice import BACKOFFICE_PAGE_ROUTES
from app.bootstrap.routes_core import CORE_ROUTES
from app.bootstrap.routes_portal import PORTAL_PAGE_ROUTES


def _route_paths(route_specs: tuple[tuple[str, object], ...]) -> set[str]:
    return {route for route, _ in route_specs}


def test_core_routes_keep_public_entrypoints():
    assert _route_paths(CORE_ROUTES) == {
        "/",
        "/login",
        "/share/empresa-documentacion/[share_token]",
    }


def test_backoffice_routes_include_modular_hotspots():
    paths = _route_paths(BACKOFFICE_PAGE_ROUTES)
    assert "/empleados" in paths
    assert "/nominas" in paths
    assert "/nominas/calculo" in paths
    assert "/admin" in paths


def test_portal_routes_include_modular_hotspots():
    paths = _route_paths(PORTAL_PAGE_ROUTES)
    assert "/portal/empleados" in paths
    assert "/portal/empleados/[id]" in paths
    assert "/portal/cotizador" in paths
    assert "/portal/nominas" in paths
    assert "/portal/contratos/[id]/plazas" in paths
