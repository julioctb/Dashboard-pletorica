"""Tests de compatibilidad para rutas canónicas de subpaquetes de servicios."""

from app.domain.services import (
    AsistenciaConfigService as InitAsistenciaConfigService,
    AsistenciaIncidenciaService as InitAsistenciaIncidenciaService,
    AsistenciaJornadaService as InitAsistenciaJornadaService,
    AsistenciaPanelService as InitAsistenciaPanelService,
    ContratoItemService as InitContratoItemService,
    ContratoMutationService as InitContratoMutationService,
    ContratoQueryService as InitContratoQueryService,
    EmpleadoMutationService as InitEmpleadoMutationService,
    EmpleadoQueryService as InitEmpleadoQueryService,
    EmpleadoRestrictionService as InitEmpleadoRestrictionService,
    UserAuthService as InitUserAuthService,
    UserCompanyService as InitUserCompanyService,
    UserProfileService as InitUserProfileService,
)
from app.domain.services.contratos import ContratoItemService, ContratoMutationService, ContratoQueryService
from app.domain.services.empleados import (
    EmpleadoMutationService,
    EmpleadoQueryService,
    EmpleadoRestrictionService,
)
from app.domain.services.asistencia_config_service import AsistenciaConfigService as LegacyAsistenciaConfigService
from app.domain.services.asistencia_incidencia_service import AsistenciaIncidenciaService as LegacyAsistenciaIncidenciaService
from app.domain.services.asistencia_jornada_service import AsistenciaJornadaService as LegacyAsistenciaJornadaService
from app.domain.services.asistencia_panel_service import AsistenciaPanelService as LegacyAsistenciaPanelService
from app.domain.services.asistencias.config import AsistenciaConfigService
from app.domain.services.asistencias.incidencias import AsistenciaIncidenciaService
from app.domain.services.asistencias.jornadas import AsistenciaJornadaService
from app.domain.services.asistencias.panel import AsistenciaPanelService
from app.domain.services.user_auth_service import UserAuthService as LegacyUserAuthService
from app.domain.services.user_company_service import UserCompanyService as LegacyUserCompanyService
from app.domain.services.user_profile_service import UserProfileService as LegacyUserProfileService
from app.domain.services.users.auth import UserAuthService
from app.domain.services.users.companies import UserCompanyService
from app.domain.services.users.profiles import UserProfileService


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
    assert InitContratoQueryService is ContratoQueryService
    assert InitContratoMutationService is ContratoMutationService
    assert InitContratoItemService is ContratoItemService
    assert InitEmpleadoQueryService is EmpleadoQueryService
    assert InitEmpleadoMutationService is EmpleadoMutationService
    assert InitEmpleadoRestrictionService is EmpleadoRestrictionService
    assert InitAsistenciaPanelService is AsistenciaPanelService
    assert InitAsistenciaConfigService is AsistenciaConfigService
    assert InitAsistenciaJornadaService is AsistenciaJornadaService
    assert InitAsistenciaIncidenciaService is AsistenciaIncidenciaService
