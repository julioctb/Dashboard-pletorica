"""Tests de compatibilidad para rutas canónicas de subpaquetes de servicios."""

from app.services import (
    AsistenciaConfigService as InitAsistenciaConfigService,
    AsistenciaIncidenciaService as InitAsistenciaIncidenciaService,
    AsistenciaJornadaService as InitAsistenciaJornadaService,
    AsistenciaPanelService as InitAsistenciaPanelService,
    UserAuthService as InitUserAuthService,
    UserCompanyService as InitUserCompanyService,
    UserProfileService as InitUserProfileService,
)
from app.services.asistencia_config_service import AsistenciaConfigService as LegacyAsistenciaConfigService
from app.services.asistencia_incidencia_service import AsistenciaIncidenciaService as LegacyAsistenciaIncidenciaService
from app.services.asistencia_jornada_service import AsistenciaJornadaService as LegacyAsistenciaJornadaService
from app.services.asistencia_panel_service import AsistenciaPanelService as LegacyAsistenciaPanelService
from app.services.asistencias.config import AsistenciaConfigService
from app.services.asistencias.incidencias import AsistenciaIncidenciaService
from app.services.asistencias.jornadas import AsistenciaJornadaService
from app.services.asistencias.panel import AsistenciaPanelService
from app.services.user_auth_service import UserAuthService as LegacyUserAuthService
from app.services.user_company_service import UserCompanyService as LegacyUserCompanyService
from app.services.user_profile_service import UserProfileService as LegacyUserProfileService
from app.services.users.auth import UserAuthService
from app.services.users.companies import UserCompanyService
from app.services.users.profiles import UserProfileService


def test_user_subpackages_reexportan_clases_canonicas():
    assert UserAuthService is LegacyUserAuthService
    assert UserProfileService is LegacyUserProfileService
    assert UserCompanyService is LegacyUserCompanyService


def test_asistencia_subpackages_reexportan_clases_canonicas():
    assert AsistenciaPanelService is LegacyAsistenciaPanelService
    assert AsistenciaConfigService is LegacyAsistenciaConfigService
    assert AsistenciaJornadaService is LegacyAsistenciaJornadaService
    assert AsistenciaIncidenciaService is LegacyAsistenciaIncidenciaService


def test_app_services_expone_subdominios_canonicos():
    assert InitUserAuthService is UserAuthService
    assert InitUserProfileService is UserProfileService
    assert InitUserCompanyService is UserCompanyService
    assert InitAsistenciaPanelService is AsistenciaPanelService
    assert InitAsistenciaConfigService is AsistenciaConfigService
    assert InitAsistenciaJornadaService is AsistenciaJornadaService
    assert InitAsistenciaIncidenciaService is AsistenciaIncidenciaService
