"""
State para la pagina Mis Empleados del portal.
"""
import asyncio
import logging
from datetime import date
from decimal import Decimal
from typing import List

import reflex as rx

from core.core.text_utils import (
    capitalizar_con_preposiciones,
    capitalizar_palabras,
    formatear_fecha,
    formatear_fecha_hora,
    formatear_moneda,
    formatear_telefono,
    normalizar_mayusculas,
    obtener_iniciales,
)
from core.core.utils import normalize_date_input, parse_date_input
from core.modules.empleados.domain.enums import (
    EstatusEmpleado,
    EstatusPlaza,
    GeneroEmpleado,
    MotivoBaja,
)
from core.presentation.components.shared import (
    EMPLOYEE_BULK_UPLOAD_ID,
    EmployeeBulkUploadStateMixin,
)
from core.presentation.pages.portal.state.portal_state import PortalState
from core.presentation.components.shared.employee_form_state_mixin import EmployeeFormStateMixin
from core.domain.services import (
    categoria_puesto_service,
    contrato_categoria_service,
    plaza_service,
    sede_service,
)
from core.modules.empleados.application import (
    baja_service,
    cuenta_bancaria_historial_service,
    empleado_descuento_recurrente_service,
    empleado_service,
    onboarding_service,
)
from core.domain.models import EmpleadoCreate, EmpleadoUpdate, PlazaUpdate
from core.core.exceptions import DuplicateError, BusinessRuleError, NotFoundError
from core.core.ui_helpers import opciones_desde_enum, rango_paginacion
from core.core.validation import (
    normalizar_clabe_interbancaria,
    normalizar_cuenta_bancaria,
    validar_rfc_empleado_requerido,
    validar_nss_empleado_requerido,
    validar_telefono_empleado_requerido,
    validar_apellido_materno_empleado,
    validar_genero_empleado_requerido,
    validar_fecha_nacimiento_empleado,
    validar_contacto_emergencia_nombre,
    validar_contacto_emergencia_telefono,
    normalizar_nombre_banco as normalizar_banco,
    validar_banco_empleado as validar_banco,
    validar_clabe_empleado as validar_clabe,
    validar_cuenta_bancaria_empleado as validar_cuenta_bancaria,
    validar_curp_empleado as validar_curp,
    validar_nombre_empleado as validar_nombre,
    validar_apellido_paterno_empleado as validar_apellido_paterno,
    validar_email_empleado as validar_email,
)


# =============================================================================
# STATE
# =============================================================================

logger = logging.getLogger(__name__)

_BANCOS_EMPLEADO_OPTIONS: List[dict] = [
    {"label": "BBVA", "value": "BBVA"},
    {"label": "Banamex", "value": "BANAMEX"},
    {"label": "Banorte", "value": "BANORTE"},
    {"label": "Santander", "value": "SANTANDER"},
    {"label": "HSBC", "value": "HSBC"},
    {"label": "Scotiabank", "value": "SCOTIABANK"},
    {"label": "Inbursa", "value": "INBURSA"},
    {"label": "Banco Azteca", "value": "BANCO AZTECA"},
    {"label": "BanCoppel", "value": "BANCOPPEL"},
    {"label": "Banregio", "value": "BANREGIO"},
]

FILTRO_CONTRATO_TODOS = "__todos__"
FILTRO_PANEL_TODOS = "TODOS"
FILTRO_PANEL_ACTIVOS = "ACTIVO"
FILTRO_PANEL_INACTIVOS = "INACTIVO"
FILTROS_PANEL_PERSONAL_VALIDOS = {
    FILTRO_PANEL_TODOS,
    FILTRO_PANEL_ACTIVOS,
    FILTRO_PANEL_INACTIVOS,
}
ESTATUS_ONBOARDING_COMPLETOS = {"ACTIVO_COMPLETO"}
VISTA_PERSONAL_EMPLEADO = "empleado"
VISTA_PERSONAL_PLAZA = "plaza"
QUERY_STATUS_MAP = {
    "todos": FILTRO_PANEL_TODOS,
    "activos": FILTRO_PANEL_ACTIVOS,
    "activo": FILTRO_PANEL_ACTIVOS,
    "inactivos": FILTRO_PANEL_INACTIVOS,
    "inactivo": FILTRO_PANEL_INACTIVOS,
}

ACCION_PLAZA_ASIGNAR_EMPLEADO = "ASIGNAR_EMPLEADO"
ACCION_PLAZA_ASIGNAR_CATEGORIA = "ASIGNAR_CATEGORIA"
ACCION_PLAZA_ASIGNAR_SEDE = "ASIGNAR_SEDE"
ACCION_PLAZA_CAMBIAR_CATEGORIA = "CAMBIAR_CATEGORIA"
ACCION_PLAZA_ACTUALIZAR_SALARIO = "ACTUALIZAR_SALARIO"
ACCION_PLAZA_LIBERAR = "LIBERAR"
ACCION_PLAZA_REACTIVAR = "REACTIVAR"
ACCION_PLAZA_REASIGNAR_CATEGORIA = "REASIGNAR_CATEGORIA"
ACCION_PLAZA_REASIGNAR_PLAZA = "REASIGNAR_PLAZA"
ACCION_PLAZA_REASIGNAR_SEDE = "REASIGNAR_SEDE"


def _empty_empleado_detalle() -> dict:
    """Payload base del detalle para evitar claves ausentes en render."""
    return {
        "id": 0,
        "uuid": "",
        "empresa_id": 0,
        "user_id": "",
        "clave": "",
        "nombre_completo": "",
        "estatus": "",
        "estatus_portal": "",
        "es_activo_portal": False,
        "estatus_personal": "",
        "contrato_codigo": "",
        "is_restricted": False,
        "curp": "",
        "rfc": "",
        "nss": "",
        "telefono": "",
        "email": "",
        "direccion": "",
        "notas": "",
        "fecha_ingreso": "",
        "fecha_ingreso_vigente": "",
        "contacto_nombre": "",
        "contacto_telefono": "",
        "contacto_parentesco": "",
        "banco": "",
        "cuenta_bancaria": "",
        "clabe_interbancaria": "",
        "documentos_aprobados_expediente": 0,
        "documentos_requeridos_expediente": 0,
        "descuentos_configurados": [],
        "descuentos_activos_hoy": [],
    }


class MisEmpleadosState(
    PortalState,
    EmployeeFormStateMixin,
    EmployeeBulkUploadStateMixin,
):
    """State para la lista de empleados del portal."""

    _campos_error_formulario: List[str] = [
        "curp",
        "nombre",
        "apellido_paterno",
        "apellido_materno",
        "rfc",
        "nss",
        "fecha_ingreso",
        "genero",
        "fecha_nacimiento",
        "email",
        "telefono",
        "contacto_nombre",
        "contacto_telefono",
        "contacto_parentesco",
        "cuenta_bancaria",
        "banco",
        "clabe",
        "descuentos_recurrentes",
    ]

    empleados: List[dict] = []
    total_empleados_lista: int = 0
    onboarding_empleados: List[dict] = []
    bajas_activas: List[dict] = []
    resumen_contratos_rrhh: List[dict] = []
    plazas_por_contrato: List[dict] = []
    sedes_catalogo_rrhh: List[dict] = []
    plazas_contrato_expandido: List[dict] = []
    seleccion_plazas_por_contrato: dict[str, list[int]] = {}
    sedes_masivas_por_contrato: dict[str, str] = {}
    categorias_masivas_por_contrato: dict[str, str] = {}
    opciones_categorias_masivas_por_contrato: dict[str, list[dict[str, str]]] = {}
    cargando_plazas_contrato_actual: bool = False
    contrato_accion_masiva_activo: str = ""
    contrato_expandido_plaza_id: int = 0
    pagina_plaza_actual: int = 1
    plaza_por_pagina: int = 20
    plaza_busqueda: str = ""
    plaza_filtro_categoria: str = "all"
    plaza_filtro_sede: str = "all"
    plaza_filtro_estado: str = "all"

    # Filtros
    filtro_busqueda_emp: str = ""
    filtro_contrato_id: str = FILTRO_CONTRATO_TODOS
    filtro_sede: str = "all"
    filtro_categoria: str = "all"
    filtro_panel_personal: str = FILTRO_PANEL_TODOS
    vista_personal: str = VISTA_PERSONAL_EMPLEADO
    pagina: int = 1
    por_pagina: int = 20

    # Alta masiva inline
    mostrar_panel_alta_masiva: bool = False
    alta_masiva_paso_actual: int = 1
    alta_masiva_archivo_nombre: str = ""
    alta_masiva_archivo_error: str = ""
    alta_masiva_validando_archivo: bool = False
    alta_masiva_validacion_total: int = 0
    alta_masiva_validacion_validos: List[dict] = []
    alta_masiva_validacion_reingresos: List[dict] = []
    alta_masiva_validacion_errores: List[dict] = []
    alta_masiva_procesando: bool = False
    alta_masiva_resultado_creados: int = 0
    alta_masiva_resultado_reingresados: int = 0
    alta_masiva_resultado_errores_count: int = 0
    alta_masiva_resultado_detalles: List[dict] = []
    _alta_masiva_cache_validos: List[dict] = []
    _alta_masiva_cache_reingresos: List[dict] = []

    # ========================
    # FORMULARIO
    # ========================
    mostrar_modal_empleado: bool = False
    es_edicion: bool = False
    empleado_editando_id: int = 0
    form_curp: str = ""
    form_nombre: str = ""
    form_apellido_paterno: str = ""
    form_apellido_materno: str = ""
    form_rfc: str = ""
    form_nss: str = ""
    form_fecha_ingreso: str = ""
    form_fecha_nacimiento: str = ""
    form_genero: str = ""
    form_telefono: str = ""
    form_email: str = ""
    form_direccion: str = ""
    form_cuenta_bancaria: str = ""
    form_banco: str = ""
    form_clabe: str = ""
    form_notas: str = ""
    editar_datos_bancarios: bool = False
    snapshot_bancario_base_edicion: dict = {}

    # Contacto de emergencia (3 campos)
    form_contacto_nombre: str = ""
    form_contacto_telefono: str = ""
    form_contacto_parentesco: str = ""
    form_descuento_infonavit_monto: str = ""
    form_descuento_infonavit_inicio: str = ""
    form_descuento_infonavit_fin: str = ""
    form_descuento_infonavit_notas: str = ""
    form_descuento_infonavit_activo: bool = False
    form_descuento_fonacot_monto: str = ""
    form_descuento_fonacot_inicio: str = ""
    form_descuento_fonacot_fin: str = ""
    form_descuento_fonacot_notas: str = ""
    form_descuento_fonacot_activo: bool = False
    form_descuento_prestamo_empresa_monto: str = ""
    form_descuento_prestamo_empresa_inicio: str = ""
    form_descuento_prestamo_empresa_fin: str = ""
    form_descuento_prestamo_empresa_notas: str = ""
    form_descuento_prestamo_empresa_activo: bool = False
    form_descuento_pension_alimenticia_monto: str = ""
    form_descuento_pension_alimenticia_inicio: str = ""
    form_descuento_pension_alimenticia_fin: str = ""
    form_descuento_pension_alimenticia_notas: str = ""
    form_descuento_pension_alimenticia_activo: bool = False

    # ========================
    # DETALLE DE EMPLEADO
    # ========================
    mostrar_modal_detalle: bool = False
    mostrar_modal_historial_bancario: bool = False
    loading_detalle_empleado: bool = False
    empleado_detalle: dict = _empty_empleado_detalle()
    historial_bancario: List[dict] = []
    mostrar_modal_asignacion_plaza: bool = False
    plaza_seleccionada: dict = {}
    empleados_disponibles_plaza: List[dict] = []
    empleado_seleccionado_plaza_id: str = ""
    cargando_empleados_plaza: bool = False
    modo_asignacion_plaza: str = "asignar"
    mostrar_modal_categoria_plaza: bool = False
    plaza_categoria_seleccionada: dict = {}
    categoria_seleccionada_plaza_id: str = ""
    categorias_disponibles_plaza: List[dict] = []
    cargando_categorias_plaza: bool = False
    mostrar_modal_salario_plaza: bool = False
    plaza_salario_seleccionada: dict = {}
    form_salario_plaza: str = ""
    error_salario_plaza: str = ""
    salario_base_categoria_plaza_referencia: str = ""
    mostrar_modal_sede_plaza: bool = False
    plaza_sede_seleccionada: dict = {}
    sede_seleccionada_plaza_id: str = ""
    mostrar_modal_reasignacion_plaza: bool = False
    plaza_reasignacion_seleccionada: dict = {}
    plaza_destino_reasignacion_id: str = ""
    plazas_disponibles_reasignacion: List[dict] = []

    # ========================
    # BAJA DE EMPLEADO
    # ========================
    mostrar_modal_baja: bool = False
    empleado_baja_seleccionado: dict = {}
    form_motivo_baja: str = ""
    form_fecha_efectiva_baja: str = ""
    form_notas_baja: str = ""
    error_motivo_baja: str = ""
    error_fecha_efectiva_baja: str = ""

    # ========================
    # ERRORES DE VALIDACION
    # ========================
    error_curp: str = ""
    error_nombre: str = ""
    error_apellido_paterno: str = ""
    error_apellido_materno: str = ""
    error_rfc: str = ""
    error_nss: str = ""
    error_fecha_ingreso: str = ""
    error_genero: str = ""
    error_fecha_nacimiento: str = ""
    error_email: str = ""
    error_telefono: str = ""
    error_contacto_nombre: str = ""
    error_contacto_telefono: str = ""
    error_contacto_parentesco: str = ""
    error_cuenta_bancaria: str = ""
    error_banco: str = ""
    error_clabe: str = ""
    error_descuentos_recurrentes: str = ""

    # ========================
    # SETTERS DE FILTROS
    # ========================
    def set_filtro_busqueda_emp(self, value: str):
        self.filtro_busqueda_emp = value
        self.pagina = 1

    def set_filtro_contrato_id(self, value: str):
        self.filtro_contrato_id = value or FILTRO_CONTRATO_TODOS
        self.pagina = 1

    def set_filtro_sede(self, value: str):
        self.filtro_sede = value or "all"
        self.pagina = 1

    def set_filtro_categoria(self, value: str):
        self.filtro_categoria = value or "all"
        self.pagina = 1

    def limpiar_busqueda(self):
        self.set_filtro_busqueda_emp("")

    def set_filtro_panel_personal(self, value: str):
        filtro = value or FILTRO_PANEL_TODOS
        if filtro not in FILTROS_PANEL_PERSONAL_VALIDOS:
            filtro = FILTRO_PANEL_TODOS
        self.filtro_panel_personal = filtro
        self.pagina = 1

    async def set_vista_personal(self, value: str):
        self.vista_personal = (
            VISTA_PERSONAL_PLAZA if value == VISTA_PERSONAL_PLAZA else VISTA_PERSONAL_EMPLEADO
        )
        self.pagina = 1
        if self.vista_es_plaza:
            await self._asegurar_contrato_plaza_seleccionado(autoselect_if_empty=True)

    def set_plaza_busqueda(self, value: str):
        self.plaza_busqueda = value
        self.pagina_plaza_actual = 1
        self._sincronizar_seleccion_contrato_actual()

    def limpiar_plaza_busqueda(self):
        self.set_plaza_busqueda("")

    def set_plaza_filtro_categoria(self, value: str):
        self.plaza_filtro_categoria = value or "all"
        self.pagina_plaza_actual = 1
        self._sincronizar_seleccion_contrato_actual()

    def set_plaza_filtro_sede(self, value: str):
        self.plaza_filtro_sede = value or "all"
        self.pagina_plaza_actual = 1
        self._sincronizar_seleccion_contrato_actual()

    def set_plaza_filtro_estado(self, value: str):
        self.plaza_filtro_estado = value or "all"
        self.pagina_plaza_actual = 1
        self._sincronizar_seleccion_contrato_actual()

    def set_empleado_seleccionado_plaza_id(self, value: str):
        self.empleado_seleccionado_plaza_id = value or ""

    def set_categoria_seleccionada_plaza_id(self, value: str):
        self.categoria_seleccionada_plaza_id = value or ""

    def set_form_salario_plaza(self, value: str):
        self.form_salario_plaza = formatear_moneda(value) if value else ""
        self.error_salario_plaza = ""

    def validar_salario_plaza_campo(self):
        self.error_salario_plaza = ""
        salario = self._parse_decimal_seguro(self.form_salario_plaza)
        if not self.form_salario_plaza.strip():
            self.error_salario_plaza = "Capture un salario"
            return
        if salario <= 0:
            self.error_salario_plaza = "El salario debe ser mayor a 0"

    def set_sede_seleccionada_plaza_id(self, value: str):
        self.sede_seleccionada_plaza_id = value or ""

    def set_plaza_destino_reasignacion_id(self, value: str):
        self.plaza_destino_reasignacion_id = value or ""

    # ========================
    # SETTERS DE FORMULARIO
    # ========================
    def set_form_curp(self, value: str):
        self._set_form_upper_field("form_curp", value)

    def set_form_nombre(self, value: str):
        self._set_form_upper_field("form_nombre", value)

    def set_form_apellido_paterno(self, value: str):
        self._set_form_upper_field("form_apellido_paterno", value)

    def set_form_apellido_materno(self, value: str):
        self._set_form_upper_field("form_apellido_materno", value)

    def set_form_rfc(self, value: str):
        self._set_form_upper_field("form_rfc", value)

    def set_form_nss(self, value: str):
        self._set_form_plain_field("form_nss", value)

    def set_form_fecha_ingreso(self, value: str):
        self._set_form_fecha_ingreso_value(value)

    def set_form_fecha_nacimiento(self, value: str):
        self._set_form_plain_field("form_fecha_nacimiento", normalize_date_input(value))

    def set_form_genero(self, value: str):
        self._set_form_plain_field("form_genero", value)

    def set_form_telefono(self, value: str):
        self._set_form_plain_field("form_telefono", value)

    def set_form_email(self, value: str):
        self._set_form_lower_field("form_email", value)

    def set_form_direccion(self, value: str):
        self._set_form_plain_field("form_direccion", value)

    def set_form_cuenta_bancaria(self, value: str):
        self.form_cuenta_bancaria = normalizar_cuenta_bancaria(value)
        self.error_cuenta_bancaria = validar_cuenta_bancaria(self.form_cuenta_bancaria)

    def set_form_banco(self, value: str):
        self.form_banco = normalizar_banco(value)
        self.error_banco = validar_banco(self.form_banco)

    def set_form_clabe(self, value: str):
        self.form_clabe = normalizar_clabe_interbancaria(value)
        self.error_clabe = validar_clabe(self.form_clabe)

    def set_form_notas(self, value: str):
        self._set_form_plain_field("form_notas", value)

    def set_form_contacto_nombre(self, value: str):
        self._set_form_plain_field("form_contacto_nombre", value)

    def set_form_contacto_telefono(self, value: str):
        self._set_form_plain_field("form_contacto_telefono", value)

    def set_form_contacto_parentesco(self, value: str):
        self._set_form_plain_field("form_contacto_parentesco", value)

    def set_form_descuento_monto(self, form_key: str, value: str):
        self._set_form_descuento_recurrente_field(form_key, "monto", value)

    def set_form_descuento_inicio(self, form_key: str, value: str):
        self._set_form_descuento_recurrente_field(form_key, "inicio", value)

    def set_form_descuento_fin(self, form_key: str, value: str):
        self._set_form_descuento_recurrente_field(form_key, "fin", value)

    def set_form_descuento_notas(self, form_key: str, value: str):
        self._set_form_descuento_recurrente_field(form_key, "notas", value)

    def set_form_descuento_activo(self, form_key: str, value) -> None:
        """Activa o limpia la captura visual de un descuento recurrente."""
        checked = self._valor_switch_a_bool(value)
        activo_attr = f"form_descuento_{form_key}_activo"
        if not hasattr(self, activo_attr):
            return

        setattr(self, activo_attr, checked)
        if hasattr(self, "error_descuentos_recurrentes"):
            self.error_descuentos_recurrentes = ""

        if checked:
            inicio_attr = f"form_descuento_{form_key}_inicio"
            if hasattr(self, inicio_attr) and not getattr(self, inicio_attr, "").strip():
                setattr(
                    self,
                    inicio_attr,
                    self.form_fecha_ingreso or date.today().isoformat(),
                )
            return

        for field_name in ("monto", "inicio", "fin", "notas"):
            attr = f"form_descuento_{form_key}_{field_name}"
            if hasattr(self, attr):
                setattr(self, attr, "")

    def set_form_motivo_baja(self, value: str):
        self._set_form_plain_field("form_motivo_baja", value)
        self.error_motivo_baja = ""

    def set_form_fecha_efectiva_baja(self, value: str):
        self._set_form_plain_field("form_fecha_efectiva_baja", normalize_date_input(value))
        self.error_fecha_efectiva_baja = ""

    def set_form_notas_baja(self, value: str):
        self._set_form_plain_field("form_notas_baja", value)

    # ========================
    # VALIDADORES ON_BLUR
    # ========================
    def validar_curp_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_curp,
            validador=validar_curp,
            error_attr="error_curp",
        )

    def validar_nombre_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_nombre,
            validador=validar_nombre,
            error_attr="error_nombre",
        )

    def validar_apellido_paterno_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_apellido_paterno,
            validador=validar_apellido_paterno,
            error_attr="error_apellido_paterno",
        )

    def validar_apellido_materno_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_apellido_materno,
            validador=validar_apellido_materno_empleado,
            error_attr="error_apellido_materno",
        )

    def validar_rfc_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_rfc,
            validador=validar_rfc_empleado_requerido,
            error_attr="error_rfc",
        )

    def validar_nss_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_nss,
            validador=validar_nss_empleado_requerido,
            error_attr="error_nss",
        )

    def validar_fecha_ingreso_blur(self):
        self._validar_fecha_ingreso_form()

    def validar_fecha_nacimiento_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_fecha_nacimiento,
            validador=lambda v: validar_fecha_nacimiento_empleado(v, requerida=True, edad_min=18),
            error_attr="error_fecha_nacimiento",
        )

    def validar_genero_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_genero,
            validador=validar_genero_empleado_requerido,
            error_attr="error_genero",
        )

    def validar_email_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_email,
            validador=validar_email,
            error_attr="error_email",
        )

    def validar_telefono_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_telefono,
            validador=validar_telefono_empleado_requerido,
            error_attr="error_telefono",
        )

    def validar_contacto_nombre_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_contacto_nombre,
            validador=validar_contacto_emergencia_nombre,
            error_attr="error_contacto_nombre",
        )

    def validar_contacto_telefono_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_contacto_telefono,
            validador=validar_contacto_emergencia_telefono,
            error_attr="error_contacto_telefono",
        )

    def validar_contacto_parentesco_blur(self):
        # Parentesco es opcional y viene de un select
        self.error_contacto_parentesco = ""

    def validar_cuenta_bancaria_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_cuenta_bancaria,
            validador=validar_cuenta_bancaria,
            error_attr="error_cuenta_bancaria",
        )

    def validar_banco_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_banco,
            validador=validar_banco,
            error_attr="error_banco",
        )

    def validar_clabe_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_clabe,
            validador=validar_clabe,
            error_attr="error_clabe",
        )

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def opciones_genero(self) -> List[dict]:
        """Opciones para el select de genero."""
        return opciones_desde_enum(GeneroEmpleado)

    @rx.var
    def opciones_parentesco(self) -> List[dict]:
        """Opciones para el select de parentesco."""
        return [
            {"value": "Padre/Madre", "label": "Padre/Madre"},
            {"value": "Esposo(a)", "label": "Esposo(a)"},
            {"value": "Hermano(a)", "label": "Hermano(a)"},
            {"value": "Hijo(a)", "label": "Hijo(a)"},
            {"value": "Tio(a)", "label": "Tio(a)"},
            {"value": "Otro", "label": "Otro"},
        ]

    @rx.var
    def opciones_banco_empleado(self) -> List[dict]:
        """Opciones visibles para el select de banco, preservando el valor actual."""
        opciones = list(_BANCOS_EMPLEADO_OPTIONS)
        actual = str(self.form_banco or "").strip()
        if not actual:
            return opciones

        valores_existentes = {str(opt.get("value", "")).strip() for opt in opciones}
        if actual not in valores_existentes:
            return [{"label": actual, "value": actual}, *opciones]
        return opciones

    @rx.var
    def datos_bancarios_bloqueados(self) -> bool:
        """En edición, los datos bancarios se muestran en lectura hasta desbloquearlos."""
        return self.es_edicion and not self.editar_datos_bancarios

    @rx.var
    def mostrar_accion_editar_datos_bancarios(self) -> bool:
        """Muestra la acción para desbloquear captura bancaria solo en edición."""
        return self.es_edicion and not self.editar_datos_bancarios

    @rx.var
    def texto_accion_datos_bancarios(self) -> str:
        """Texto del CTA según exista o no un snapshot bancario previo."""
        snapshot = self.snapshot_bancario_base_edicion or {}
        tiene_datos = any([
            str(snapshot.get("cuenta_bancaria", "") or ""),
            str(snapshot.get("banco", "") or ""),
            str(snapshot.get("clabe_interbancaria", "") or ""),
        ])
        return "Editar datos bancarios" if tiene_datos else "Capturar datos bancarios"

    @rx.var
    def descripcion_datos_bancarios(self) -> str:
        """Ayuda contextual para el modo lectura/edición de datos bancarios."""
        if not self.es_edicion:
            return ""
        if self.editar_datos_bancarios:
            return (
                "Capture los nuevos datos bancarios. Al guardar se registrará "
                "un nuevo cambio en el historial."
            )
        return (
            "Se muestran los últimos datos bancarios guardados. Use el botón "
            "para capturar nuevos datos."
        )

    @staticmethod
    def _texto_contacto_secundario(payload: dict) -> str:
        telefono = formatear_telefono(str(payload.get("telefono") or ""))
        if telefono:
            return telefono
        return str(
            payload.get("email")
            or ""
        ).strip()

    @staticmethod
    def _normalizar_nombre_visual(nombre: str) -> str:
        return capitalizar_palabras(nombre)

    @staticmethod
    def _normalizar_sede_visual(nombre: str) -> str:
        sede = str(nombre or "").strip()
        if not sede or sede.lower() == "sin sede":
            return ""
        return normalizar_mayusculas(sede)

    @staticmethod
    def _normalizar_telefono_visual(telefono: str) -> str:
        return formatear_telefono(str(telefono or "").strip())

    @staticmethod
    def _campos_tabla_empleado_ui(
        *,
        nombre: str,
        curp: str = "",
        telefono: str = "",
    ) -> dict[str, str]:
        nombre_ui = capitalizar_palabras(nombre)
        return {
            "nombre_completo_ui": nombre_ui,
            "avatar_iniciales_ui": obtener_iniciales(nombre_ui),
            "curp_ui": normalizar_mayusculas(curp),
            "telefono_ui": formatear_telefono(str(telefono or "").strip()),
        }

    @staticmethod
    def _resumen_docs(aprobados: int, requeridos: int) -> dict:
        porcentaje = 0
        if requeridos > 0:
            porcentaje = int(round((aprobados / requeridos) * 100))
            porcentaje = max(0, min(100, porcentaje))

        tone = "muted"
        if requeridos > 0 and aprobados >= requeridos:
            tone = "success"
        elif aprobados > 0:
            tone = "warning"

        return {
            "docs_aprobados": aprobados,
            "docs_requeridos": requeridos,
            "docs_porcentaje": porcentaje,
            "docs_porcentaje_ui": f"{porcentaje}%",
            "docs_resumen_ui": f"{aprobados}/{requeridos}",
            "docs_tone": tone,
        }

    def _resolver_nombre_empleado_visual(self, empleado) -> str:
        """Resuelve nombre visible desde modelos/dicts sin serializar métodos."""
        if empleado is None:
            return ""
        if isinstance(empleado, dict):
            nombre = (
                empleado.get("nombre_completo")
                or empleado.get("nombre_completo_ui")
                or ""
            )
            return self._normalizar_nombre_visual(str(nombre or ""))

        nombre_completo = getattr(empleado, "nombre_completo", None)
        if callable(nombre_completo):
            return self._normalizar_nombre_visual(nombre_completo())

        if nombre_completo:
            return self._normalizar_nombre_visual(str(nombre_completo))

        nombre = str(getattr(empleado, "nombre", "") or "")
        apellido_paterno = str(getattr(empleado, "apellido_paterno", "") or "")
        apellido_materno = str(getattr(empleado, "apellido_materno", "") or "")
        return self._normalizar_nombre_visual(
            " ".join(
                part for part in [nombre, apellido_paterno, apellido_materno] if part
            ).strip()
        )

    @staticmethod
    def _clave_contrato(contrato_id: int | str) -> str:
        return str(int(contrato_id or 0))

    def _opciones_categoria_masiva_contrato(self, contrato_id: int | str) -> list[dict[str, str]]:
        clave = self._clave_contrato(contrato_id)
        return list(self.opciones_categorias_masivas_por_contrato.get(clave, []) or [])

    @staticmethod
    def _pluralizar(cantidad: int, singular: str, plural: str) -> str:
        return singular if cantidad == 1 else plural

    def _texto_resumen_cantidad(self, cantidad: int, singular: str, plural: str) -> str:
        return f"{cantidad} {self._pluralizar(cantidad, singular, plural)}"

    def _texto_resumen_plazas_sedes(self, plazas: int, sedes: int) -> str:
        return (
            f"{self._texto_resumen_cantidad(plazas, 'plaza', 'plazas')} · "
            f"{self._texto_resumen_cantidad(sedes, 'sede', 'sedes')}"
        )

    def _reset_filtros_internos_plaza(self) -> None:
        self.plaza_busqueda = ""
        self.plaza_filtro_categoria = "all"
        self.plaza_filtro_sede = "all"
        self.plaza_filtro_estado = "all"
        self.pagina_plaza_actual = 1

    def _reset_contexto_plazas_ui(self) -> None:
        """Limpia el contexto de la vista por plaza y reinicia el contrato activo."""
        self.plazas_contrato_expandido = []
        self.seleccion_plazas_por_contrato = {}
        self.sedes_masivas_por_contrato = {}
        self.categorias_masivas_por_contrato = {}
        self.opciones_categorias_masivas_por_contrato = {}
        self.cargando_plazas_contrato_actual = False
        self.contrato_accion_masiva_activo = ""
        self.contrato_expandido_plaza_id = 0
        self._reset_filtros_internos_plaza()

    def _sincronizar_seleccion_contrato_actual(self) -> None:
        contrato_id = int(self.contrato_expandido_plaza_id or 0)
        if contrato_id <= 0:
            return

        clave = self._clave_contrato(contrato_id)
        seleccion_actual = self.seleccion_plazas_por_contrato.get(clave, [])
        visibles_ids = {
            int(plaza.get("id") or 0)
            for plaza in self.plazas_pagina_actual
            if int(plaza.get("id") or 0) > 0
        }
        nuevas_selecciones = dict(self.seleccion_plazas_por_contrato)
        nuevas_selecciones[clave] = [
            plaza_id for plaza_id in seleccion_actual if plaza_id in visibles_ids
        ]
        self.seleccion_plazas_por_contrato = nuevas_selecciones
        if nuevas_selecciones[clave]:
            self.contrato_accion_masiva_activo = clave
        elif self.contrato_accion_masiva_activo == clave:
            self.contrato_accion_masiva_activo = ""

    def _listar_contratos_plaza_filtrados(self) -> List[dict]:
        contratos = list(self.plazas_por_contrato)
        if self.filtro_estatus_plaza == EstatusPlaza.OCUPADA.value:
            return [
                contrato
                for contrato in contratos
                if int(contrato.get("plazas_ocupadas") or 0) > 0
            ]
        if self.filtro_estatus_plaza == EstatusPlaza.VACANTE.value:
            return [
                contrato
                for contrato in contratos
                if int(contrato.get("plazas_vacantes") or 0) > 0
            ]
        return contratos

    def _resolver_contrato_plaza_seleccionado(
        self,
        preferred_contract_id: int = 0,
        *,
        autoselect_if_empty: bool = False,
    ) -> int:
        contratos = self._listar_contratos_plaza_filtrados()
        if not contratos:
            return 0

        contratos_ids = [
            int(contrato.get("contrato_id") or 0)
            for contrato in contratos
            if int(contrato.get("contrato_id") or 0) > 0
        ]
        if not contratos_ids:
            return 0

        preferido = int(preferred_contract_id or 0)
        if preferido > 0 and preferido in contratos_ids:
            return preferido

        actual = int(self.contrato_expandido_plaza_id or 0)
        if actual > 0 and actual in contratos_ids:
            return actual

        if autoselect_if_empty:
            return contratos_ids[0]
        return 0

    async def _asegurar_contrato_plaza_seleccionado(
        self,
        preferred_contract_id: int = 0,
        *,
        autoselect_if_empty: bool = False,
        pagina: int | None = None,
        force_reload: bool = False,
    ) -> None:
        contrato_id = self._resolver_contrato_plaza_seleccionado(
            preferred_contract_id,
            autoselect_if_empty=autoselect_if_empty,
        )
        if contrato_id <= 0:
            self._reset_contexto_plazas_ui()
            return

        pagina_segura = max(1, int(pagina or self.pagina_plaza_actual or 1))
        contrato_actual = int(self.contrato_expandido_plaza_id or 0)
        contrato_cambio = contrato_id != contrato_actual

        if contrato_cambio:
            self._reset_contexto_plazas_ui()

        if (
            not force_reload
            and not contrato_cambio
            and self.plazas_contrato_expandido
        ):
            self.pagina_plaza_actual = min(pagina_segura, self.total_paginas_plaza_actual)
            self._sincronizar_seleccion_contrato_actual()
            return

        await self._cargar_pagina_plazas_contrato(contrato_id, pagina=pagina_segura)

    @staticmethod
    def _estado_expediente(
        aprobados: int,
        requeridos: int,
        *,
        pendiente: bool = False,
    ) -> dict:
        porcentaje = 0
        if requeridos > 0:
            porcentaje = int(round((aprobados / requeridos) * 100))
            porcentaje = max(0, min(100, porcentaje))

        if pendiente or (requeridos > 0 and aprobados <= 0):
            return {
                "expediente_resumen_ui": f"{aprobados}/{requeridos}",
                "expediente_tone": "warning",
                "expediente_completo": False,
                "expediente_requiere_accion": True,
                "expediente_porcentaje": porcentaje,
            }
        if requeridos > 0 and aprobados >= requeridos:
            return {
                "expediente_resumen_ui": f"{aprobados}/{requeridos}",
                "expediente_tone": "success",
                "expediente_completo": True,
                "expediente_requiere_accion": False,
                "expediente_porcentaje": porcentaje,
            }
        return {
            "expediente_resumen_ui": f"{aprobados}/{requeridos}",
            "expediente_tone": "warning" if aprobados > 0 else "secondary",
            "expediente_completo": False,
            "expediente_requiere_accion": requeridos > 0 and aprobados < requeridos,
            "expediente_porcentaje": porcentaje,
        }

    @staticmethod
    def _tiene_plaza_portal_activa(plaza: dict) -> bool:
        if not isinstance(plaza, dict):
            return False
        return (
            int(plaza.get("contrato_id") or 0) > 0
            and int(plaza.get("categoria_puesto_id") or 0) > 0
        )

    def _resolver_estatus_portal_empleado(self, empleado_data: dict, plaza: dict) -> str:
        estatus_actual = str(empleado_data.get("estatus", "") or "").strip().upper()
        if estatus_actual == EstatusEmpleado.SUSPENDIDO.value:
            return FILTRO_PANEL_INACTIVOS
        if self._tiene_plaza_portal_activa(plaza):
            return FILTRO_PANEL_ACTIVOS
        return FILTRO_PANEL_INACTIVOS

    def _aplicar_estatus_portal(self, row: dict, plaza: dict) -> dict:
        estatus_portal = self._resolver_estatus_portal_empleado(row, plaza)
        row["estatus_portal"] = estatus_portal
        row["es_activo_portal"] = estatus_portal == FILTRO_PANEL_ACTIVOS
        return row

    def _normalizar_resumen_empleado(self, empleado, plazas_por_empleado: dict[int, dict]) -> dict:
        data = (
            empleado.model_dump(mode="json")
            if hasattr(empleado, "model_dump")
            else dict(empleado)
        )
        data["uuid"] = str(data.get("uuid", "") or "")
        empleado_id = int(data.get("id") or 0)
        plaza = plazas_por_empleado.get(empleado_id, {})
        aprobados = int(data.get("documentos_aprobados_expediente", 0) or 0)
        requeridos = int(data.get("documentos_requeridos_expediente", 0) or 0)
        data.update(
            self._campos_tabla_empleado_ui(
                nombre=str(data.get("nombre_completo", "") or ""),
                curp=str(data.get("curp", "") or ""),
                telefono=str(data.get("telefono", "") or ""),
            )
        )
        data["contacto_secundario_ui"] = self._texto_contacto_secundario(data)
        data["contrato_id"] = plaza.get("contrato_id")
        data["contrato_codigo"] = str(plaza.get("contrato_codigo", "") or "").strip().upper()
        data["categoria_puesto_id"] = int(plaza.get("categoria_puesto_id") or 0)
        data["categoria_nombre"] = self._normalizar_nombre_visual(
            str(plaza.get("categoria_nombre", "") or "")
        )
        data["categoria_clave"] = str(plaza.get("categoria_clave", "") or "").strip().upper()
        data["sede_nombre_ui"] = self._normalizar_sede_visual(str(plaza.get("sede_nombre", "") or ""))
        data["expediente_resumen"] = (
            str(aprobados)
            + "/"
            + str(requeridos)
        )
        data.update(self._resumen_docs(aprobados, requeridos))
        data.update(self._estado_expediente(aprobados, requeridos))
        return self._aplicar_estatus_portal(data, plaza)

    def _normalizar_resumen_onboarding(self, onboarding: dict, plazas_por_empleado: dict[int, dict]) -> dict:
        empleado_id = int(onboarding.get("id") or 0)
        plaza = plazas_por_empleado.get(empleado_id, {})
        row = {
            "id": empleado_id,
            "uuid": str(onboarding.get("uuid", "") or ""),
            "clave": str(onboarding.get("clave", "") or "").strip().upper(),
            "curp": onboarding.get("curp", ""),
            "contacto_secundario_ui": str(onboarding.get("email", "") or ""),
            "telefono": "",
            "email": onboarding.get("email", ""),
            "estatus": FILTRO_PANEL_INACTIVOS,
            "estatus_personal": "",
            "estatus_onboarding": onboarding.get("estatus_onboarding", ""),
            "contrato_id": plaza.get("contrato_id"),
            "contrato_codigo": str(plaza.get("contrato_codigo", "") or "").strip().upper(),
            "categoria_puesto_id": int(plaza.get("categoria_puesto_id") or 0),
            "categoria_nombre": self._normalizar_nombre_visual(
                str(plaza.get("categoria_nombre", "") or "")
            ),
            "categoria_clave": str(plaza.get("categoria_clave", "") or "").strip().upper(),
            "sede_nombre_ui": self._normalizar_sede_visual(str(plaza.get("sede_nombre", "") or "")),
            "documentos_aprobados_expediente": 0,
            "documentos_requeridos_expediente": 0,
            "expediente_resumen": "Pendiente",
            "expediente_pendiente": True,
            **self._campos_tabla_empleado_ui(
                nombre=str(onboarding.get("nombre_completo", "") or ""),
                curp=str(onboarding.get("curp", "") or ""),
                telefono="",
            ),
            **self._resumen_docs(0, 0),
            **self._estado_expediente(0, 0, pendiente=True),
        }
        return self._aplicar_estatus_portal(row, plaza)

    @staticmethod
    def _opcion_accion_plaza(value: str, label: str) -> dict[str, str]:
        return {"value": value, "label": label}

    @classmethod
    def _label_accion_salario_plaza(cls, plaza: dict) -> str:
        salario = cls._parse_decimal_seguro(plaza.get("salario_mensual"))
        if salario > 0:
            return "Actualizar salario"
        return "Asignar salario"

    @classmethod
    def _resolver_acciones_plaza(cls, plaza: dict) -> list[dict[str, str]]:
        if not isinstance(plaza, dict):
            return []

        estatus = str(plaza.get("estatus", "") or "")
        tiene_categoria = int(plaza.get("categoria_puesto_id") or 0) > 0
        tiene_sede = int(plaza.get("sede_id") or 0) > 0
        tiene_empleado = int(plaza.get("empleado_id") or 0) > 0
        puede_actualizar_salario = estatus in {
            EstatusPlaza.VACANTE.value,
            EstatusPlaza.OCUPADA.value,
        }
        accion_salario = cls._opcion_accion_plaza(
            ACCION_PLAZA_ACTUALIZAR_SALARIO,
            cls._label_accion_salario_plaza(plaza),
        )

        if estatus == EstatusPlaza.SUSPENDIDA.value:
            return [
                cls._opcion_accion_plaza(
                    ACCION_PLAZA_REACTIVAR,
                    "Reactivar plaza",
                ),
            ]

        if not tiene_categoria:
            acciones = [
                cls._opcion_accion_plaza(
                    ACCION_PLAZA_ASIGNAR_CATEGORIA,
                    "Asignar categoria",
                ),
            ]
            if puede_actualizar_salario:
                acciones.append(accion_salario)
            return acciones

        acciones = [
            cls._opcion_accion_plaza(
                ACCION_PLAZA_CAMBIAR_CATEGORIA if tiene_empleado else ACCION_PLAZA_REASIGNAR_CATEGORIA,
                "Cambiar de categoria" if tiene_empleado else "Reasignar categoria",
            ),
        ]

        if not tiene_sede:
            acciones.append(
                cls._opcion_accion_plaza(
                    ACCION_PLAZA_ASIGNAR_SEDE,
                    "Asignar sede",
                ),
            )
            if puede_actualizar_salario:
                acciones.append(accion_salario)
            return acciones

        if not tiene_empleado:
            acciones.extend(
                [
                    cls._opcion_accion_plaza(
                        ACCION_PLAZA_REASIGNAR_SEDE,
                        "Reasignar sede",
                    ),
                    cls._opcion_accion_plaza(
                        ACCION_PLAZA_ASIGNAR_EMPLEADO,
                        "Asignar empleado",
                    ),
                ]
            )
            if puede_actualizar_salario:
                acciones.append(accion_salario)
            return acciones

        acciones[:0] = [
            cls._opcion_accion_plaza(
                ACCION_PLAZA_REASIGNAR_PLAZA,
                "Reasignar plaza",
            ),
            cls._opcion_accion_plaza(
                ACCION_PLAZA_LIBERAR,
                "Liberar plaza",
            ),
        ]
        if puede_actualizar_salario:
            acciones.append(accion_salario)
        return acciones

    @classmethod
    def _placeholder_acciones_plaza(cls, plaza: dict) -> str:
        acciones = cls._resolver_acciones_plaza(plaza)
        if len(acciones) == 1:
            return str(acciones[0].get("label", "Acciones") or "Acciones")
        return "Acciones"

    def _serializar_plaza_portal(self, plaza) -> dict:
        plaza_dict = plaza.model_dump(mode="json")
        plaza_dict["contrato_codigo"] = str(plaza_dict.get("contrato_codigo", "") or "").strip().upper()
        plaza_dict["categoria_nombre"] = self._normalizar_nombre_visual(
            str(plaza_dict.get("categoria_nombre") or "sin categoria")
        )
        plaza_dict["categoria_clave"] = str(plaza_dict.get("categoria_clave") or "").strip().upper()
        plaza_dict["sede_nombre"] = self._normalizar_sede_visual(
            str(plaza_dict.get("sede_nombre") or "")
        )
        plaza_dict["sede_codigo"] = str(plaza_dict.get("sede_codigo") or "").strip().upper()
        plaza_dict["empleado_nombre"] = self._normalizar_nombre_visual(
            str(plaza_dict.get("empleado_nombre", "") or "")
        )
        plaza_dict["empleado_uuid"] = str(plaza_dict.get("empleado_uuid", "") or "").strip()
        plaza_dict["sede_display"] = (
            f"{plaza_dict['sede_codigo']} - {plaza_dict['sede_nombre']}".strip(" -")
            if plaza_dict["sede_codigo"]
            else str(plaza_dict["sede_nombre"] or "SIN SEDE")
        )
        plaza_dict["acciones_disponibles"] = self._resolver_acciones_plaza(plaza_dict)
        plaza_dict["acciones_placeholder"] = self._placeholder_acciones_plaza(plaza_dict)
        return plaza_dict

    def _normalizar_resumen_contrato_plaza(self, contrato: dict) -> dict:
        total_plazas = int(contrato.get("total_plazas") or 0)
        plazas_ocupadas = int(contrato.get("plazas_ocupadas") or 0)
        plazas_vacantes = int(contrato.get("plazas_vacantes") or 0)
        plazas_suspendidas = int(contrato.get("plazas_suspendidas") or 0)
        total_sedes = int(contrato.get("total_sedes") or 0)
        return {
            "contrato_id": int(contrato.get("contrato_id") or 0),
            "contrato_codigo": str(contrato.get("contrato_codigo", "") or "").strip().upper(),
            "contrato_estatus": str(contrato.get("contrato_estatus", "") or ""),
            "tipo_servicio_clave": str(contrato.get("tipo_servicio_clave", "") or "").strip().upper(),
            "tipo_servicio_nombre": self._normalizar_nombre_visual(
                str(contrato.get("tipo_servicio_nombre", "") or "")
            ),
            "total_plazas": total_plazas,
            "plazas_ocupadas": plazas_ocupadas,
            "plazas_vacantes": plazas_vacantes,
            "plazas_suspendidas": plazas_suspendidas,
            "total_sedes": total_sedes,
            "tiene_plazas": total_plazas > 0,
            "resumen_plazas": self._texto_resumen_plazas_sedes(total_plazas, total_sedes),
        }

    def _aplicar_query_inicial(self) -> None:
        query = self.router_data.get("query", {}) or {}
        status = str(query.get("status", "") or "").strip().lower()
        view = str(query.get("view", "") or "").strip().lower()
        contrato_id = str(query.get("contrato_id", "") or "").strip()

        self.vista_personal = (
            VISTA_PERSONAL_PLAZA if view == VISTA_PERSONAL_PLAZA else VISTA_PERSONAL_EMPLEADO
        )
        self.filtro_panel_personal = QUERY_STATUS_MAP.get(status, FILTRO_PANEL_TODOS)

        if contrato_id:
            try:
                self.filtro_contrato_id = str(int(contrato_id))
            except (TypeError, ValueError):
                self.filtro_contrato_id = FILTRO_CONTRATO_TODOS
        else:
            self.filtro_contrato_id = FILTRO_CONTRATO_TODOS

    @rx.var
    def subtitulo_empleados(self) -> str:
        empresa = str(self.nombre_empresa_actual or "Empresa actual").strip()
        return f"{empresa} - Plantilla y gestion de personal"

    @rx.var
    def vista_es_empleado(self) -> bool:
        return self.vista_personal != VISTA_PERSONAL_PLAZA

    @rx.var
    def vista_es_plaza(self) -> bool:
        return self.vista_personal == VISTA_PERSONAL_PLAZA

    @rx.var
    def opciones_contratos_activos(self) -> List[dict]:
        opciones = [
            {
                "value": FILTRO_CONTRATO_TODOS,
                "label": "Todos los contratos",
            }
        ]
        for contrato in self.resumen_contratos_rrhh:
            opciones.append(
                {
                    "value": str(contrato.get("contrato_id", "")),
                    "label": str(contrato.get("contrato_codigo", "") or "Sin contrato"),
                }
            )
        return opciones

    @rx.var
    def opciones_sedes_plaza(self) -> List[dict]:
        return [
            {
                "value": str(sede.get("id")),
                "label": (
                    f"{str(sede.get('codigo', '') or '').strip().upper()} - "
                    f"{self._normalizar_nombre_visual(str(sede.get('nombre_corto') or sede.get('nombre', '') or ''))}"
                ).strip(" -"),
            }
            for sede in self.sedes_catalogo_rrhh
        ]

    @rx.var
    def contratos_activos_filtrados(self) -> List[dict]:
        if self.filtro_contrato_id == FILTRO_CONTRATO_TODOS:
            return self.resumen_contratos_rrhh

        contrato_id = int(self.filtro_contrato_id) if self.filtro_contrato_id else 0
        return [
            item
            for item in self.resumen_contratos_rrhh
            if int(item.get("contrato_id") or 0) == contrato_id
        ]

    @rx.var
    def empleados_por_contrato(self) -> List[dict]:
        if self.filtro_contrato_id == FILTRO_CONTRATO_TODOS:
            return self.empleados

        contrato_id = int(self.filtro_contrato_id) if self.filtro_contrato_id else 0
        return [
            empleado
            for empleado in self.empleados
            if int(empleado.get("contrato_id") or 0) == contrato_id
        ]

    @rx.var
    def total_empleados(self) -> int:
        return len(self.empleados_por_contrato)

    @rx.var
    def total_activos(self) -> int:
        return len(
            [
                item for item in self.empleados_por_contrato
                if item.get("estatus_portal") == FILTRO_PANEL_ACTIVOS
            ]
        )

    @rx.var
    def total_inactivos(self) -> int:
        return len(
            [
                item for item in self.empleados_por_contrato
                if item.get("estatus_portal") == FILTRO_PANEL_INACTIVOS
            ]
        )

    @rx.var
    def total_plazas(self) -> int:
        return self.metrica_plazas_totales

    @rx.var
    def plazas_ocupadas(self) -> int:
        return self.metrica_plazas_ocupadas

    @rx.var
    def plazas_vacantes(self) -> int:
        return self.metrica_plazas_vacantes

    @rx.var
    def docs_pendientes(self) -> int:
        return len([item for item in self.empleados_por_contrato if bool(item.get("expediente_requiere_accion"))])

    @rx.var
    def total_contratos_label(self) -> str:
        return self.metrica_hint_plazas

    @rx.var
    def cobertura_label(self) -> str:
        return self.metrica_hint_cobertura

    @rx.var
    def nombre_empresa(self) -> str:
        return str(self.nombre_empresa_actual or "Empresa actual").strip()

    @rx.var
    def contratos_opciones(self) -> List[dict]:
        return self.opciones_contratos_activos

    @rx.var
    def sedes_opciones(self) -> List[dict]:
        sedes = sorted({str(item.get("sede_nombre_ui", "") or "").strip() for item in self.empleados if str(item.get("sede_nombre_ui", "") or "").strip()})
        return [{"value": sede, "label": sede} for sede in sedes]

    @rx.var
    def categorias_opciones(self) -> List[dict]:
        categorias = sorted({str(item.get("categoria_nombre", "") or "").strip() for item in self.empleados if str(item.get("categoria_nombre", "") or "").strip()})
        return [{"value": categoria, "label": categoria} for categoria in categorias]

    @rx.var
    def filtro_es_todos(self) -> bool:
        return self.filtro_panel_personal == FILTRO_PANEL_TODOS

    @rx.var
    def filtro_es_activos(self) -> bool:
        return self.filtro_panel_personal == FILTRO_PANEL_ACTIVOS

    @rx.var
    def filtro_es_inactivos(self) -> bool:
        return self.filtro_panel_personal == FILTRO_PANEL_INACTIVOS

    @rx.var
    def empleados_filtrados(self) -> List[dict]:
        empleados = self.empleados_por_contrato

        if self.filtro_panel_personal != FILTRO_PANEL_TODOS:
            empleados = [
                item
                for item in empleados
                if item.get("estatus_portal") == self.filtro_panel_personal
            ]

        if self.filtro_sede != "all":
            empleados = [
                item for item in empleados
                if str(item.get("sede_nombre_ui", "") or "").strip() == self.filtro_sede
            ]

        if self.filtro_categoria != "all":
            empleados = [
                item for item in empleados
                if str(item.get("categoria_nombre", "") or "").strip() == self.filtro_categoria
            ]

        if not self.filtro_busqueda_emp:
            return empleados

        termino = self.filtro_busqueda_emp.lower()
        return [
            item
            for item in empleados
            if termino in str(item.get("nombre_completo_ui", "")).lower()
            or termino in str(item.get("curp", "")).lower()
        ]

    @rx.var
    def total_empleados_filtrados(self) -> int:
        return len(self.empleados_filtrados)

    @rx.var
    def total_paginas_empleados(self) -> int:
        return self.calcular_total_paginas(
            self.total_empleados_filtrados,
            self.por_pagina,
        )

    @rx.var
    def pagina_empleados_actual(self) -> int:
        if self.pagina < 1:
            return 1
        if self.pagina > self.total_paginas_empleados:
            return self.total_paginas_empleados
        return self.pagina

    @rx.var
    def empleados_paginados(self) -> List[dict]:
        inicio = (self.pagina_empleados_actual - 1) * self.por_pagina
        fin = inicio + self.por_pagina
        return self.empleados_filtrados[inicio:fin]

    @rx.var
    def paginas_visibles_empleados(self) -> List[int]:
        return rango_paginacion(
            self.pagina_empleados_actual,
            self.total_paginas_empleados,
            visible=5,
        )

    @rx.var
    def resumen_paginacion_empleados(self) -> str:
        return f"Mostrando {self.total_empleados_filtrados} empleado(s)"

    @rx.var
    def contratos_plaza_filtrados(self) -> List[dict]:
        return self._listar_contratos_plaza_filtrados()

    @rx.var
    def titulo_modal_asignacion_plaza(self) -> str:
        if self.modo_asignacion_plaza == "reasignar":
            return "Reasignar empleado"
        return "Asignar empleado"

    @rx.var
    def texto_guardar_asignacion_plaza(self) -> str:
        if self.modo_asignacion_plaza == "reasignar":
            return "Reasignar"
        return "Asignar"

    @rx.var
    def descripcion_modal_asignacion_plaza(self) -> str:
        numero_plaza = self._texto_seguro_modal_plaza(
            self.plaza_seleccionada.get("numero_plaza"),
        )
        contrato_codigo = self._texto_seguro_modal_plaza(
            self.plaza_seleccionada.get("contrato_codigo", ""),
        )
        if not numero_plaza:
            return "Seleccione un empleado disponible para esta plaza."
        return (
            f"Plaza #{numero_plaza} del contrato {contrato_codigo}. "
            "Seleccione un empleado disponible sin otra plaza activa."
        )

    @rx.var
    def placeholder_empleado_plaza(self) -> str:
        if self.cargando_empleados_plaza:
            return "Cargando empleados..."
        return "Seleccionar empleado"

    @rx.var
    def tiene_empleados_disponibles_plaza(self) -> bool:
        return len(self.empleados_disponibles_plaza) > 0

    @rx.var
    def total_contratos_plazas_visibles(self) -> int:
        return len(self.contratos_plaza_filtrados)

    @rx.var
    def total_plazas_visibles(self) -> int:
        return sum(int(grupo.get("total_plazas") or 0) for grupo in self.contratos_plaza_filtrados)

    @rx.var
    def resumen_paginacion_plazas(self) -> str:
        return (
            "Mostrando "
            f"{self.total_contratos_plazas_visibles} contrato(s) · "
            f"{self.total_plazas_visibles} plaza(s)"
        )

    @rx.var
    def tiene_plazas_visibles(self) -> bool:
        return self.total_contratos_plazas_visibles > 0

    @rx.var
    def contratos_plaza_selector_opciones(self) -> List[dict]:
        return [
            {
                "value": str(contrato.get("contrato_id") or ""),
                "label": (
                    f"{str(contrato.get('contrato_codigo', '') or 'Sin contrato')} · "
                    f"{str(contrato.get('tipo_servicio_nombre', '') or 'Sin servicio')} · "
                    f"{str(contrato.get('resumen_plazas', '') or 'Sin plazas')}"
                ),
            }
            for contrato in self.contratos_plaza_filtrados
            if int(contrato.get("contrato_id") or 0) > 0
        ]

    @rx.var
    def contrato_plaza_seleccionado_value(self) -> str:
        contrato_id = self._resolver_contrato_plaza_seleccionado(autoselect_if_empty=True)
        return str(contrato_id) if contrato_id > 0 else ""

    @rx.var
    def contrato_plaza_activo(self) -> dict:
        contrato_id = int(self._resolver_contrato_plaza_seleccionado() or 0)
        if contrato_id <= 0:
            return {}

        contrato = next(
            (
                item
                for item in self.contratos_plaza_filtrados
                if int(item.get("contrato_id") or 0) == contrato_id
            ),
            {},
        )
        if not contrato:
            return {}

        clave = self._clave_contrato(contrato_id)
        seleccion_ids = list(self.seleccion_plazas_por_contrato.get(clave, []) or [])
        return {
            **contrato,
            "seleccion_ids": seleccion_ids,
            "seleccion_count": len(seleccion_ids),
            "tiene_seleccion": len(seleccion_ids) > 0,
            "seleccion_label": self._texto_resumen_cantidad(
                len(seleccion_ids),
                "plaza seleccionada",
                "plazas seleccionadas",
            ),
            "seleccion_todas_visibles": self.seleccion_todas_plazas_visibles_actual,
            "sede_masiva_value": str(self.sedes_masivas_por_contrato.get(clave, "") or ""),
            "categoria_masiva_value": str(self.categorias_masivas_por_contrato.get(clave, "") or ""),
            "opciones_categorias_masivas": self._opciones_categoria_masiva_contrato(clave),
            "mostrar_badge_suspendidas": int(contrato.get("plazas_suspendidas") or 0) > 0,
        }

    @rx.var
    def tiene_contrato_plaza_activo(self) -> bool:
        return bool(self.contrato_plaza_activo)

    @rx.var
    def puede_confirmar_asignacion_plaza(self) -> bool:
        return bool(self.empleado_seleccionado_plaza_id) and not self.saving

    @rx.var
    def titulo_modal_categoria_plaza(self) -> str:
        if int(self.plaza_categoria_seleccionada.get("empleado_id") or 0) > 0:
            return "Cambiar categoria"
        if int(self.plaza_categoria_seleccionada.get("categoria_puesto_id") or 0) > 0:
            return "Reasignar categoria"
        return "Asignar categoria"

    @rx.var
    def texto_guardar_categoria_plaza(self) -> str:
        if int(self.plaza_categoria_seleccionada.get("categoria_puesto_id") or 0) > 0:
            return "Guardar categoria"
        return "Asignar categoria"

    @rx.var
    def descripcion_modal_categoria_plaza(self) -> str:
        numero_plaza = self._texto_seguro_modal_plaza(
            self.plaza_categoria_seleccionada.get("numero_plaza"),
        )
        contrato_codigo = self._texto_seguro_modal_plaza(
            self.plaza_categoria_seleccionada.get("contrato_codigo", ""),
        )
        if not numero_plaza:
            return "Seleccione una categoria para la plaza."
        return f"Plaza #{numero_plaza} del contrato {contrato_codigo}."

    @rx.var
    def puede_confirmar_categoria_plaza(self) -> bool:
        return bool(self.categoria_seleccionada_plaza_id) and not self.saving

    @rx.var
    def opciones_categoria_plaza(self) -> List[dict]:
        return [
            {
                "value": str(categoria.get("id")),
                "label": str(categoria.get("label", "") or ""),
            }
            for categoria in self.categorias_disponibles_plaza
        ]

    @rx.var
    def hint_categoria_plaza(self) -> str:
        if self.cargando_categorias_plaza:
            return "Cargando categorias..."
        if self.categorias_disponibles_plaza:
            return ""
        return "No hay categorias disponibles para esta operacion."

    @rx.var
    def titulo_modal_salario_plaza(self) -> str:
        salario_actual = self._parse_decimal_seguro(
            self.plaza_salario_seleccionada.get("salario_mensual"),
        )
        if salario_actual > 0:
            return "Actualizar salario"
        return "Asignar salario"

    @rx.var
    def texto_guardar_salario_plaza(self) -> str:
        salario_actual = self._parse_decimal_seguro(
            self.plaza_salario_seleccionada.get("salario_mensual"),
        )
        if salario_actual > 0:
            return "Guardar salario"
        return "Asignar salario"

    @rx.var
    def descripcion_modal_salario_plaza(self) -> str:
        numero_plaza = self._texto_seguro_modal_plaza(
            self.plaza_salario_seleccionada.get("numero_plaza"),
        )
        contrato_codigo = self._texto_seguro_modal_plaza(
            self.plaza_salario_seleccionada.get("contrato_codigo", ""),
        )
        if not numero_plaza:
            return "Capture el salario de la plaza."
        return f"Plaza #{numero_plaza} del contrato {contrato_codigo}."

    @rx.var
    def hint_salario_plaza(self) -> str:
        salario_base = self._parse_decimal_seguro(
            self.salario_base_categoria_plaza_referencia,
        )
        if salario_base <= 0:
            return ""

        categoria = self._texto_seguro_modal_plaza(
            self.plaza_salario_seleccionada.get("categoria_nombre", ""),
        )
        salario_texto = formatear_moneda(str(salario_base))
        if categoria and categoria.lower() != "sin categoria":
            return f"Referencia de {categoria}: {salario_texto}"
        return f"Sueldo base de referencia: {salario_texto}"

    @rx.var
    def puede_confirmar_salario_plaza(self) -> bool:
        return bool(self.form_salario_plaza.strip()) and not self.saving

    @rx.var
    def titulo_modal_sede_plaza(self) -> str:
        if int(self.plaza_sede_seleccionada.get("sede_id") or 0) > 0:
            return "Reasignar sede"
        return "Asignar sede"

    @rx.var
    def texto_guardar_sede_plaza(self) -> str:
        if int(self.plaza_sede_seleccionada.get("sede_id") or 0) > 0:
            return "Guardar sede"
        return "Asignar sede"

    @rx.var
    def descripcion_modal_sede_plaza(self) -> str:
        numero_plaza = self._texto_seguro_modal_plaza(
            self.plaza_sede_seleccionada.get("numero_plaza"),
        )
        contrato_codigo = self._texto_seguro_modal_plaza(
            self.plaza_sede_seleccionada.get("contrato_codigo", ""),
        )
        if not numero_plaza:
            return "Seleccione una sede para la plaza."
        return f"Plaza #{numero_plaza} del contrato {contrato_codigo}."

    @rx.var
    def puede_confirmar_sede_plaza(self) -> bool:
        return bool(self.sede_seleccionada_plaza_id) and not self.saving

    @rx.var
    def titulo_modal_reasignacion_plaza(self) -> str:
        return "Reasignar plaza"

    @rx.var
    def descripcion_modal_reasignacion_plaza(self) -> str:
        numero_plaza = self._texto_seguro_modal_plaza(
            self.plaza_reasignacion_seleccionada.get("numero_plaza"),
        )
        empleado = self._texto_seguro_modal_plaza(
            self.plaza_reasignacion_seleccionada.get("empleado_nombre", ""),
        )
        if not numero_plaza:
            return "Seleccione la nueva plaza de destino."
        return (
            f"Mueva al empleado {empleado or 'asignado'} desde la plaza #{numero_plaza} "
            "hacia otra plaza vacante con sede y categoria configuradas."
        )

    @rx.var
    def puede_confirmar_reasignacion_plaza(self) -> bool:
        return bool(self.plaza_destino_reasignacion_id) and not self.saving

    @rx.var
    def opciones_reasignacion_plaza(self) -> List[dict]:
        return [
            {
                "value": str(plaza.get("id")),
                "label": str(plaza.get("label", "") or ""),
            }
            for plaza in self.plazas_disponibles_reasignacion
        ]

    @rx.var
    def hint_reasignacion_plaza(self) -> str:
        if self.plazas_disponibles_reasignacion:
            return ""
        return "No hay otra plaza vacante compatible para reasignar."

    @rx.var
    def opciones_categorias_masivas_actuales(self) -> List[dict[str, str]]:
        return self._opciones_categoria_masiva_contrato(self.contrato_accion_masiva_activo)

    @rx.var
    def plaza_categorias_opciones(self) -> List[dict]:
        categorias: dict[str, str] = {}
        for plaza in self.plazas_contrato_expandido:
            categoria_id = str(plaza.get("categoria_puesto_id") or "").strip()
            if not categoria_id:
                continue
            categorias[categoria_id] = str(plaza.get("categoria_nombre", "") or "Sin categoria")
        return [
            {"value": categoria_id, "label": nombre}
            for categoria_id, nombre in sorted(
                categorias.items(),
                key=lambda item: item[1],
            )
        ]

    @rx.var
    def plaza_sedes_opciones(self) -> List[dict]:
        sedes: dict[str, str] = {}
        for plaza in self.plazas_contrato_expandido:
            sede_id = str(plaza.get("sede_id") or "").strip()
            if not sede_id:
                continue
            sedes[sede_id] = str(
                plaza.get("sede_display")
                or plaza.get("sede_nombre")
                or "Sin sede"
            )
        return [
            {"value": sede_id, "label": nombre}
            for sede_id, nombre in sorted(
                sedes.items(),
                key=lambda item: item[1],
            )
        ]

    @rx.var
    def plazas_filtradas_contrato_actual(self) -> List[dict]:
        plazas = list(self.plazas_contrato_expandido)
        termino = self.plaza_busqueda.lower().strip()
        if termino:
            plazas = self._filtrar_plazas_por_busqueda(plazas, termino)

        if self.plaza_filtro_categoria != "all":
            plazas = [
                plaza
                for plaza in plazas
                if str(plaza.get("categoria_puesto_id") or "") == self.plaza_filtro_categoria
            ]

        if self.plaza_filtro_sede != "all":
            plazas = [
                plaza
                for plaza in plazas
                if str(plaza.get("sede_id") or "") == self.plaza_filtro_sede
            ]

        if self.plaza_filtro_estado != "all":
            plazas = [
                plaza
                for plaza in plazas
                if str(plaza.get("estatus") or "") == self.plaza_filtro_estado
            ]

        return plazas

    @rx.var
    def plaza_total_filtradas(self) -> int:
        return len(self.plazas_filtradas_contrato_actual)

    @rx.var
    def total_plazas_contrato_actual(self) -> int:
        return self.plaza_total_filtradas

    @rx.var
    def total_paginas_plaza_actual(self) -> int:
        return self.calcular_total_paginas(
            self.plaza_total_filtradas,
            self.plaza_por_pagina,
        )

    @rx.var
    def page_numbers_plaza_actual(self) -> List[int]:
        return rango_paginacion(
            self.pagina_plaza_actual,
            self.total_paginas_plaza_actual,
            visible=5,
        )

    @rx.var
    def plazas_pagina_actual(self) -> List[dict]:
        inicio = (self.pagina_plaza_actual - 1) * self.plaza_por_pagina
        fin = inicio + self.plaza_por_pagina
        clave = self._clave_contrato(self.contrato_expandido_plaza_id)
        seleccionadas = set(self.seleccion_plazas_por_contrato.get(clave, []) or [])
        return [
            {
                **plaza,
                "seleccionada": int(plaza.get("id") or 0) in seleccionadas,
            }
            for plaza in self.plazas_filtradas_contrato_actual[inicio:fin]
        ]

    @rx.var
    def plazas_visibles_contrato_actual(self) -> List[dict]:
        return self.plazas_pagina_actual

    @rx.var
    def seleccion_todas_plazas_visibles_actual(self) -> bool:
        visibles_ids = [
            int(plaza.get("id") or 0)
            for plaza in self.plazas_pagina_actual
            if int(plaza.get("id") or 0) > 0
        ]
        if not visibles_ids:
            return False
        seleccionadas = set(
            self.seleccion_plazas_por_contrato.get(
                self._clave_contrato(self.contrato_expandido_plaza_id),
                [],
            )
            or []
        )
        return all(plaza_id in seleccionadas for plaza_id in visibles_ids)

    @rx.var
    def resumen_pagina_contrato_actual(self) -> str:
        total = self.plaza_total_filtradas
        if total <= 0:
            return "Sin plazas disponibles"
        inicio = ((self.pagina_plaza_actual - 1) * self.plaza_por_pagina) + 1
        fin = min(self.pagina_plaza_actual * self.plaza_por_pagina, total)
        return f"Mostrando {inicio}-{fin} de {total} plazas"

    @rx.var
    def opciones_empleados_disponibles_plaza(self) -> List[dict]:
        return [
            {
                "value": str(empleado.get("id")),
                "label": f"{empleado.get('clave', '')} - {empleado.get('nombre_completo', '')}",
            }
            for empleado in self.empleados_disponibles_plaza
        ]

    @rx.var
    def metrica_plazas_totales(self) -> int:
        return sum(int(item.get("total_plazas") or 0) for item in self.contratos_activos_filtrados)

    @rx.var
    def metrica_plazas_ocupadas(self) -> int:
        return sum(int(item.get("plazas_ocupadas") or 0) for item in self.contratos_activos_filtrados)

    @rx.var
    def metrica_plazas_vacantes(self) -> int:
        return sum(int(item.get("plazas_vacantes") or 0) for item in self.contratos_activos_filtrados)

    @rx.var
    def metrica_hint_plazas(self) -> str:
        total = len(self.contratos_activos_filtrados)
        return f"{total} contrato(s) activos"

    @rx.var
    def metrica_porcentaje_cobertura(self) -> int:
        total = self.metrica_plazas_totales
        if total <= 0:
            return 0
        return int(round((self.metrica_plazas_ocupadas / total) * 100))

    @rx.var
    def metrica_hint_cobertura(self) -> str:
        return f"{self.metrica_porcentaje_cobertura}% cobertura"

    @rx.var
    def nombre_empleado_baja(self) -> str:
        """Nombre del empleado seleccionado para baja."""
        emp = self.empleado_baja_seleccionado
        if not emp:
            return ""
        return str(
            emp.get("nombre_completo", "")
            or emp.get("nombre_completo_ui", "")
            or ""
        )

    @rx.var
    def clave_empleado_baja(self) -> str:
        """Clave del empleado seleccionado para baja."""
        emp = self.empleado_baja_seleccionado
        if not emp:
            return ""
        return str(emp.get("clave", "") or "")

    @rx.var
    def detalle_nombre_empleado(self) -> str:
        """Nombre del empleado visible en el modal de detalle."""
        return str(self.empleado_detalle.get("nombre_completo", "") or "")

    @rx.var
    def detalle_clave_empleado(self) -> str:
        """Clave del empleado visible en el modal de detalle."""
        return str(self.empleado_detalle.get("clave", "") or "")

    @rx.var
    def detalle_expediente_resumen(self) -> str:
        """Progreso del expediente visible en el detalle."""
        aprobados = int(self.empleado_detalle.get("documentos_aprobados_expediente", 0) or 0)
        requeridos = int(self.empleado_detalle.get("documentos_requeridos_expediente", 0) or 0)
        return f"{aprobados}/{requeridos}"

    @rx.var
    def detalle_ficha_href(self) -> str:
        """URL de la ficha del empleado visible en el modal de detalle."""
        empleado_uuid = str(self.empleado_detalle.get("uuid", "") or "").strip()
        if empleado_uuid:
            return f"/portal/empleados/{empleado_uuid}"

        empleado_id = self.empleado_detalle.get("id")
        if not empleado_id:
            return ""
        return f"/portal/empleados/{empleado_id}"

    @rx.var
    def detalle_banco_actual(self) -> str:
        """Banco actual del empleado seleccionado."""
        return str(self.empleado_detalle.get("banco", "") or "")

    @rx.var
    def detalle_cuenta_bancaria_mascara(self) -> str:
        """Cuenta bancaria actual enmascarada."""
        return self._enmascarar_digitos(self.empleado_detalle.get("cuenta_bancaria"))

    @rx.var
    def detalle_clabe_mascara(self) -> str:
        """CLABE actual enmascarada."""
        return self._enmascarar_digitos(self.empleado_detalle.get("clabe_interbancaria"))

    @rx.var
    def detalle_tiene_bancarios(self) -> bool:
        """Indica si el detalle actual tiene datos bancarios."""
        return any(
            [
                self.empleado_detalle.get("banco"),
                self.empleado_detalle.get("cuenta_bancaria"),
                self.empleado_detalle.get("clabe_interbancaria"),
            ]
        )

    @rx.var
    def historial_bancario_total(self) -> int:
        """Total de cambios bancarios cargados para el detalle."""
        return len(self.historial_bancario)

    @rx.var
    def tiene_historial_bancario(self) -> bool:
        """Indica si hay historial bancario cargado."""
        return len(self.historial_bancario) > 0

    @rx.var
    def ultima_actualizacion_bancaria(self) -> str:
        """Fecha de la última actualización bancaria visible."""
        if not self.historial_bancario:
            return ""
        return str(self.historial_bancario[0].get("fecha_cambio", "") or "")

    @rx.var
    def origen_ultima_actualizacion_bancaria(self) -> str:
        """Origen del último cambio bancario."""
        if not self.historial_bancario:
            return ""
        return str(self.historial_bancario[0].get("origen", "") or "")

    @rx.var
    def puede_editar_detalle(self) -> bool:
        """Permite editar desde el modal de detalle."""
        is_restricted = bool(self.empleado_detalle.get("is_restricted", False))
        return bool(self.empleado_detalle.get("es_activo_portal", False)) and not is_restricted

    @rx.var
    def puede_dar_baja_detalle(self) -> bool:
        """Permite dar de baja desde el modal de detalle."""
        return bool(self.empleado_detalle.get("es_activo_portal", False))

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_empleados(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.mostrar_seccion_rrhh or not (
            self.puede_gestionar_personal or self.puede_registrar_personal
        ):
            yield rx.redirect("/portal")
            return
        self._aplicar_query_inicial()
        self.vista_personal = VISTA_PERSONAL_EMPLEADO
        self._reset_contexto_plazas_ui()
        async for _ in self._montar_pagina(self._fetch_empleados):
            yield
        if self._query_solicita_alta_masiva():
            self.abrir_panel_alta_masiva()

    # ========================
    # CARGA DE DATOS
    # ========================
    def _mapear_plazas_ocupadas_por_empleado(self, plazas_ocupadas) -> dict[int, dict]:
        plazas_por_empleado: dict[int, dict] = {}
        for plaza in plazas_ocupadas:
            plaza_dict = self._serializar_plaza_portal(plaza)
            empleado_id = int(plaza_dict.get("empleado_id") or 0)
            if empleado_id <= 0:
                continue
            plazas_por_empleado[empleado_id] = {
                "contrato_id": plaza_dict.get("contrato_id"),
                "contrato_codigo": plaza_dict.get("contrato_codigo", ""),
                "categoria_puesto_id": int(plaza_dict.get("categoria_puesto_id") or 0),
                "categoria_nombre": plaza_dict.get("categoria_nombre", ""),
                "categoria_clave": plaza_dict.get("categoria_clave", ""),
                "sede_nombre": plaza_dict.get("sede_nombre", ""),
            }
        return plazas_por_empleado

    def _filtrar_plazas_por_busqueda(self, plazas: list[dict], termino: str) -> list[dict]:
        termino_normalizado = termino.lower().strip()
        if not termino_normalizado:
            return plazas
        return [
            plaza
            for plaza in plazas
            if termino_normalizado in str(plaza.get("numero_plaza", "")).lower()
            or termino_normalizado in str(plaza.get("categoria_nombre", "")).lower()
            or termino_normalizado in str(plaza.get("sede_nombre", "")).lower()
            or termino_normalizado in str(plaza.get("empleado_nombre", "")).lower()
            or termino_normalizado in str(plaza.get("codigo", "")).lower()
            or termino_normalizado in str(plaza.get("contrato_codigo", "")).lower()
        ]

    async def _cargar_opciones_categoria_masiva(self, contrato_id: int) -> None:
        clave = self._clave_contrato(contrato_id)
        if self.opciones_categorias_masivas_por_contrato.get(clave):
            return

        resumenes, conteos = await asyncio.gather(
            contrato_categoria_service.obtener_resumen_de_contrato(contrato_id),
            plaza_service.obtener_cantidad_esperada_por_categoria(contrato_id),
        )

        opciones: list[dict] = []
        for resumen in resumenes:
            categoria_id = int(getattr(resumen, "categoria_puesto_id", 0) or 0)
            if categoria_id <= 0:
                continue
            maximo = int(getattr(resumen, "cantidad_maxima", 0) or 0)
            if maximo <= 0:
                continue
            asignadas = int(conteos.get(categoria_id) or 0)
            disponibles = max(0, maximo - asignadas)
            nombre_categoria = self._normalizar_nombre_visual(
                str(getattr(resumen, "categoria_nombre", "") or "")
            )
            opciones.append(
                {
                    "value": str(categoria_id),
                    "label": f"{nombre_categoria} ({disponibles} disp.)",
                }
            )

        opciones_por_contrato = dict(self.opciones_categorias_masivas_por_contrato)
        opciones_por_contrato[clave] = opciones
        self.opciones_categorias_masivas_por_contrato = opciones_por_contrato

    async def _cargar_pagina_plazas_contrato(self, contrato_id: int, pagina: int = 1) -> None:
        pagina_segura = max(1, int(pagina or 1))
        self.cargando_plazas_contrato_actual = True
        self.contrato_expandido_plaza_id = int(contrato_id or 0)
        try:
            plazas = await plaza_service.obtener_resumen_de_contrato(contrato_id)
            self.plazas_contrato_expandido = [
                self._serializar_plaza_portal(plaza)
                for plaza in plazas
                if str(getattr(plaza.estatus, "value", plaza.estatus) or "")
                != EstatusPlaza.CANCELADA.value
            ]
            self.pagina_plaza_actual = pagina_segura
            if self.pagina_plaza_actual > self.total_paginas_plaza_actual:
                self.pagina_plaza_actual = self.total_paginas_plaza_actual
            self._sincronizar_seleccion_contrato_actual()
            await self._cargar_opciones_categoria_masiva(contrato_id)
        finally:
            self.cargando_plazas_contrato_actual = False

    async def _recargar_contrato_expandido(self, contrato_id: int, pagina: int = 1) -> None:
        contrato_id_int = int(contrato_id or 0)
        if contrato_id_int <= 0:
            self._reset_contexto_plazas_ui()
            return
        await self._cargar_pagina_plazas_contrato(contrato_id_int, pagina=pagina)

    async def _fetch_empleados(self):
        """Carga y unifica empleados, onboarding, bajas y resumen de plazas."""
        if not self.id_empresa_actual:
            return

        try:
            resumen_contratos, plazas_ocupadas, empleados_resumen, onboarding_resumen, bajas_activas, sedes = await asyncio.gather(
                plaza_service.obtener_resumen_contratos_con_plazas(
                    empresa_id=self.id_empresa_actual,
                    solo_activos=True,
                ),
                plaza_service.obtener_resumen_ocupadas_por_empresa(
                    self.id_empresa_actual,
                ),
                empleado_service.obtener_resumen_por_empresa(
                    empresa_id=self.id_empresa_actual,
                    incluir_inactivos=True,
                    limite=200,
                ),
                onboarding_service.obtener_empleados_onboarding(
                    empresa_id=self.id_empresa_actual,
                ),
                baja_service.obtener_bajas_empresa(
                    empresa_id=self.id_empresa_actual,
                    solo_activas=True,
                ),
                sede_service.obtener_todas(
                    incluir_inactivas=False,
                    limite=500,
                ),
            )

            plazas_por_empleado = self._mapear_plazas_ocupadas_por_empleado(plazas_ocupadas)

            onboarding_lookup = {
                int(item.get("id") or 0): item
                for item in onboarding_resumen
                if item.get("estatus_onboarding")
                and item.get("estatus_onboarding") not in ESTATUS_ONBOARDING_COMPLETOS
            }
            bajas_lookup = {
                int(item.empleado_id if hasattr(item, "empleado_id") else item.get("empleado_id") or 0): (
                    item.model_dump(mode="json")
                    if hasattr(item, "model_dump")
                    else dict(item)
                )
                for item in bajas_activas
                if int(item.empleado_id if hasattr(item, "empleado_id") else item.get("empleado_id") or 0) > 0
            }
            bajas_ids = set(bajas_lookup.keys())

            filas_por_empleado_id: dict[int, dict] = {}
            for empleado in empleados_resumen:
                row = self._normalizar_resumen_empleado(empleado, plazas_por_empleado)
                empleado_id = int(row.get("id") or 0)
                if empleado_id in bajas_ids:
                    continue
                row["expediente_pendiente"] = False
                filas_por_empleado_id[empleado_id] = row

            for empleado_id, onboarding in onboarding_lookup.items():
                if empleado_id in bajas_ids:
                    continue
                base_row = filas_por_empleado_id.get(empleado_id)
                if base_row is None:
                    filas_por_empleado_id[empleado_id] = self._normalizar_resumen_onboarding(
                        onboarding,
                        plazas_por_empleado,
                    )
                    continue

                base_row["estatus_onboarding"] = onboarding.get("estatus_onboarding", "")
                base_row["expediente_resumen"] = "Pendiente"
                base_row["expediente_pendiente"] = True
                base_row.update(self._estado_expediente(0, 0, pendiente=True))
                base_row["contacto_secundario_ui"] = (
                    str(onboarding.get("email", "") or "")
                    or base_row.get("contacto_secundario_ui", "")
                )

            contratos_normalizados = [
                self._normalizar_resumen_contrato_plaza(
                    item.model_dump(mode="json") if hasattr(item, "model_dump") else dict(item)
                )
                for item in resumen_contratos
            ]
            contratos_normalizados.sort(key=lambda item: str(item.get("contrato_codigo", "")))

            contrato_expandido_previo = int(self.contrato_expandido_plaza_id or 0)
            pagina_plaza_previa = int(self.pagina_plaza_actual or 1)
            self.resumen_contratos_rrhh = list(contratos_normalizados)
            self.onboarding_empleados = list(onboarding_lookup.values())
            self.bajas_activas = list(bajas_lookup.values())
            self.sedes_catalogo_rrhh = [
                sede.model_dump(mode="json") if hasattr(sede, "model_dump") else dict(sede)
                for sede in sedes
            ]
            self.plazas_por_contrato = list(contratos_normalizados)
            self.empleados = sorted(
                filas_por_empleado_id.values(),
                key=lambda item: str(item.get("nombre_completo_ui", "")),
            )
            self.total_empleados_lista = len(self.empleados)
            contratos_validos = {
                str(item.get("contrato_id"))
                for item in self.resumen_contratos_rrhh
                if int(item.get("contrato_id") or 0) > 0
            }
            if (
                self.filtro_contrato_id != FILTRO_CONTRATO_TODOS
                and self.filtro_contrato_id not in contratos_validos
            ):
                self.filtro_contrato_id = FILTRO_CONTRATO_TODOS
            self._ajustar_pagina_empleados()
            if self.vista_es_plaza or contrato_expandido_previo > 0:
                await self._asegurar_contrato_plaza_seleccionado(
                    preferred_contract_id=contrato_expandido_previo,
                    autoselect_if_empty=self.vista_es_plaza,
                    pagina=pagina_plaza_previa,
                    force_reload=True,
                )
            else:
                self._reset_contexto_plazas_ui()
        except Exception as e:
            self.mostrar_mensaje(f"Error cargando empleados: {e}", "error")
            self.resumen_contratos_rrhh = []
            self.onboarding_empleados = []
            self.bajas_activas = []
            self.sedes_catalogo_rrhh = []
            self.plazas_por_contrato = []
            self._reset_contexto_plazas_ui()
            self.empleados = []
            self.total_empleados_lista = 0
            self.pagina = 1

    async def cargar_empleados(self):
        """Recarga la vista unificada con skeleton."""
        async for _ in self._recargar_datos(self._fetch_empleados):
            yield

    async def aplicar_filtros_emp(self):
        return None

    async def limpiar_filtros_emp(self):
        self.filtro_busqueda_emp = ""
        self.filtro_contrato_id = FILTRO_CONTRATO_TODOS
        self.filtro_sede = "all"
        self.filtro_categoria = "all"
        self.filtro_panel_personal = FILTRO_PANEL_TODOS
        self.pagina = 1

    def filtrar_todos(self):
        self.set_filtro_panel_personal(FILTRO_PANEL_TODOS)

    def filtrar_activos(self):
        self.set_filtro_panel_personal(FILTRO_PANEL_ACTIVOS)

    def filtrar_inactivos(self):
        self.set_filtro_panel_personal(FILTRO_PANEL_INACTIVOS)

    # --- Filtros vista plaza ---

    filtro_estatus_plaza: str = "all"

    async def set_filtro_estatus_plaza(self, value: str):
        self.filtro_estatus_plaza = value or "all"
        await self._asegurar_contrato_plaza_seleccionado(autoselect_if_empty=True)

    @rx.var
    def filtro_plaza_es_todas(self) -> bool:
        return self.filtro_estatus_plaza == "all"

    @rx.var
    def filtro_plaza_es_ocupadas(self) -> bool:
        return self.filtro_estatus_plaza == "OCUPADA"

    @rx.var
    def filtro_plaza_es_vacantes(self) -> bool:
        return self.filtro_estatus_plaza == "VACANTE"

    async def filtrar_plazas_todas(self):
        await self.set_filtro_estatus_plaza("all")

    async def filtrar_plazas_ocupadas(self):
        await self.set_filtro_estatus_plaza("OCUPADA")

    async def filtrar_plazas_vacantes(self):
        await self.set_filtro_estatus_plaza("VACANTE")

    def ir_a_pagina(self, pagina: int):
        """Navega a una página específica del listado."""
        self.pagina = int(pagina) if pagina else 1
        self._ajustar_pagina_empleados()

    def pagina_anterior(self):
        """Retrocede una página del listado."""
        self.ir_a_pagina(self.pagina_empleados_actual - 1)

    def pagina_siguiente(self):
        """Avanza una página del listado."""
        self.ir_a_pagina(self.pagina_empleados_actual + 1)

    async def set_contrato_plaza_seleccionado(self, value: str):
        contrato_id_int = int(value or 0)
        if contrato_id_int <= 0:
            self._reset_contexto_plazas_ui()
            return
        await self._asegurar_contrato_plaza_seleccionado(
            preferred_contract_id=contrato_id_int,
            autoselect_if_empty=False,
            pagina=1,
        )

    def ir_a_pagina_plaza_contrato(self, contrato_id: int, pagina: int):
        contrato_id_int = int(contrato_id or 0)
        if contrato_id_int <= 0:
            return
        if contrato_id_int != int(self.contrato_expandido_plaza_id or 0):
            return
        pagina_segura = max(1, min(int(pagina or 1), self.total_paginas_plaza_actual))
        self.pagina_plaza_actual = pagina_segura
        self._sincronizar_seleccion_contrato_actual()

    def pagina_anterior_plaza_contrato(self, contrato_id: int):
        self.ir_a_pagina_plaza_contrato(int(contrato_id or 0), self.pagina_plaza_actual - 1)

    def pagina_siguiente_plaza_contrato(self, contrato_id: int):
        self.ir_a_pagina_plaza_contrato(int(contrato_id or 0), self.pagina_plaza_actual + 1)

    def toggle_plaza_seleccionada(self, contrato_id: int, plaza_id: int, checked) -> None:
        contrato_id_int = int(contrato_id or 0)
        plaza_id_int = int(plaza_id or 0)
        if contrato_id_int <= 0 or plaza_id_int <= 0:
            return

        clave = self._clave_contrato(contrato_id_int)
        seleccionadas = list(self.seleccion_plazas_por_contrato.get(clave, []) or [])
        marcado = self._valor_switch_a_bool(checked)
        if marcado and plaza_id_int not in seleccionadas:
            seleccionadas.append(plaza_id_int)
        if not marcado:
            seleccionadas = [item for item in seleccionadas if item != plaza_id_int]

        nuevas_selecciones = {
            item_clave: ([] if item_clave != clave else list(valores))
            for item_clave, valores in self.seleccion_plazas_por_contrato.items()
        }
        nuevas_selecciones[clave] = seleccionadas
        self.seleccion_plazas_por_contrato = nuevas_selecciones
        self.contrato_accion_masiva_activo = clave if seleccionadas else ""

    def seleccionar_todas_plazas_visibles(self, contrato_id: int, checked) -> None:
        contrato_id_int = int(contrato_id or 0)
        if contrato_id_int <= 0:
            return
        clave = self._clave_contrato(contrato_id_int)
        visibles = [
            int(plaza.get("id") or 0)
            for plaza in self.plazas_pagina_actual
            if int(plaza.get("id") or 0) > 0
        ]
        nuevas_selecciones = {
            item_clave: ([] if item_clave != clave else list(valores))
            for item_clave, valores in self.seleccion_plazas_por_contrato.items()
        }
        nuevas_selecciones[clave] = visibles if self._valor_switch_a_bool(checked) else []
        self.seleccion_plazas_por_contrato = nuevas_selecciones
        self.contrato_accion_masiva_activo = clave if nuevas_selecciones[clave] else ""

    def limpiar_seleccion_plazas(self, contrato_id: int) -> None:
        contrato_id_int = int(contrato_id or 0)
        if contrato_id_int <= 0:
            return
        clave = self._clave_contrato(contrato_id_int)
        nuevas_selecciones = dict(self.seleccion_plazas_por_contrato)
        nuevas_selecciones[clave] = []
        self.seleccion_plazas_por_contrato = nuevas_selecciones
        if self.contrato_accion_masiva_activo == clave:
            self.contrato_accion_masiva_activo = ""

    def set_sede_masiva_contrato(self, contrato_id: int, value: str) -> None:
        clave = self._clave_contrato(contrato_id)
        nuevos_valores = dict(self.sedes_masivas_por_contrato)
        nuevos_valores[clave] = value or ""
        self.sedes_masivas_por_contrato = nuevos_valores

    def set_categoria_masiva_contrato(self, contrato_id: int, value: str) -> None:
        clave = self._clave_contrato(contrato_id)
        nuevos_valores = dict(self.categorias_masivas_por_contrato)
        nuevos_valores[clave] = value or ""
        self.categorias_masivas_por_contrato = nuevos_valores

    async def aplicar_sede_masiva_contrato(self, contrato_id: int):
        contrato_id_int = int(contrato_id or 0)
        clave = self._clave_contrato(contrato_id_int)
        plaza_ids = list(self.seleccion_plazas_por_contrato.get(clave, []) or [])
        sede_id = self.parse_id(self.sedes_masivas_por_contrato.get(clave, ""))
        if contrato_id_int <= 0 or not plaza_ids:
            return rx.toast.error("Seleccione al menos una plaza")
        if sede_id is None:
            return rx.toast.error("Seleccione una sede para aplicar")

        self.saving = True
        try:
            for plaza_id in plaza_ids:
                await plaza_service.actualizar(
                    plaza_id,
                    PlazaUpdate(sede_id=sede_id),
                )
            await self._fetch_empleados()
            return rx.toast.success(
                f"Se actualizo la sede en {len(plaza_ids)} plaza(s)"
            )
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "aplicando sede masiva")
        finally:
            self.saving = False

    async def aplicar_categoria_masiva_contrato(self, contrato_id: int):
        contrato_id_int = int(contrato_id or 0)
        clave = self._clave_contrato(contrato_id_int)
        plaza_ids = list(self.seleccion_plazas_por_contrato.get(clave, []) or [])
        categoria_id = self.parse_id(self.categorias_masivas_por_contrato.get(clave, ""))
        if contrato_id_int <= 0 or not plaza_ids:
            return rx.toast.error("Seleccione al menos una plaza")
        if categoria_id is None:
            return rx.toast.error("Seleccione una categoria para aplicar")

        self.saving = True
        try:
            for plaza_id in plaza_ids:
                await plaza_service.actualizar(
                    plaza_id,
                    PlazaUpdate(categoria_puesto_id=categoria_id),
                )
            await self._fetch_empleados()
            return rx.toast.success(
                f"Se actualizo la categoria en {len(plaza_ids)} plaza(s)"
            )
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "aplicando categoria masiva")
        finally:
            self.saving = False

    def abrir_panel_alta_masiva(self):
        """Abre la sección inline de alta masiva desde el listado."""
        for attr, value in EmployeeBulkUploadStateMixin.build_alta_masiva_reset_values(
            mantener_panel_abierto=True,
        ).items():
            setattr(self, attr, value)

    def cerrar_panel_alta_masiva(self):
        """Cierra la sección inline y limpia archivos seleccionados."""
        for attr, value in EmployeeBulkUploadStateMixin.build_alta_masiva_reset_values(
            mantener_panel_abierto=False,
        ).items():
            setattr(self, attr, value)

        eventos = [rx.clear_selected_files(EMPLOYEE_BULK_UPLOAD_ID)]
        if EmployeeBulkUploadStateMixin._query_solicita_alta_masiva(self):
            eventos.append(rx.redirect("/portal/empleados", replace=True))
        return eventos

    def reiniciar_alta_masiva(self):
        """Regresa el panel inline al paso inicial."""
        for attr, value in EmployeeBulkUploadStateMixin.build_alta_masiva_reset_values(
            mantener_panel_abierto=True,
        ).items():
            setattr(self, attr, value)
        return rx.clear_selected_files(EMPLOYEE_BULK_UPLOAD_ID)

    async def handle_upload_alta_masiva(self, files: list[rx.UploadFile]):
        """Wrapper de Reflex para validación de archivo desde el state concreto."""
        async for event in EmployeeBulkUploadStateMixin.handle_upload_alta_masiva(
            self,
            files,
        ):
            yield event

    async def confirmar_alta_masiva(self):
        """Wrapper de Reflex para procesamiento de alta masiva."""
        async for event in EmployeeBulkUploadStateMixin.confirmar_alta_masiva(self):
            yield event

    def descargar_plantilla_excel_alta_masiva(self):
        """Wrapper de Reflex para descarga de plantilla Excel."""
        return EmployeeBulkUploadStateMixin.descargar_plantilla_excel_alta_masiva(
            self,
        )

    def descargar_plantilla_csv_alta_masiva(self):
        """Wrapper de Reflex para descarga de plantilla CSV."""
        return EmployeeBulkUploadStateMixin.descargar_plantilla_csv_alta_masiva(
            self,
        )

    def descargar_reporte_alta_masiva(self):
        """Wrapper de Reflex para descarga del reporte final."""
        return EmployeeBulkUploadStateMixin.descargar_reporte_alta_masiva(self)

    @rx.event
    def ver_baja_empleado(self, empleado: dict):
        if not isinstance(empleado, dict):
            return

        empleado_id = int(empleado.get("id") or 0)
        if empleado_id <= 0:
            return rx.redirect("/portal/bajas")

        return rx.redirect(
            f"/portal/bajas?empleado_id={empleado_id}",
        )

    @rx.event
    def ver_ficha_empleado(self, empleado: dict):
        """Navega a la ficha del empleado usando UUID (fallback por ID)."""
        puede_ver_ficha = (
            self.puede_acceder_rrhh
            or self.puede_registrar_personal
            or self.es_institucion
        )
        if not puede_ver_ficha or not isinstance(empleado, dict):
            return

        empleado_uuid = str(empleado.get("uuid", "") or "").strip()
        if empleado_uuid:
            return rx.redirect(f"/portal/empleados/{empleado_uuid}")

        empleado_id = empleado.get("id")
        if empleado_id:
            return rx.redirect(f"/portal/empleados/{empleado_id}")
        return

    @rx.event
    def ver_perfil_plaza(self, plaza: dict):
        """Abre perfil desde vista por plaza (prioriza UUID cuando esté disponible)."""
        puede_ver_ficha = (
            self.puede_acceder_rrhh
            or self.puede_registrar_personal
            or self.es_institucion
        )
        if not puede_ver_ficha or not isinstance(plaza, dict):
            return

        empleado_uuid = str(plaza.get("empleado_uuid", "") or "").strip()
        if empleado_uuid:
            return rx.redirect(f"/portal/empleados/{empleado_uuid}")

        empleado_id = int(plaza.get("empleado_id") or 0)
        if empleado_id <= 0:
            return

        for emp in self.empleados:
            if int(emp.get("id") or 0) != empleado_id:
                continue
            empleado_uuid = str(emp.get("uuid", "") or "").strip()
            if empleado_uuid:
                return rx.redirect(f"/portal/empleados/{empleado_uuid}")
            break

        return rx.redirect(f"/portal/empleados/{empleado_id}")

    @staticmethod
    def _parse_decimal_seguro(value: object) -> Decimal:
        if value in (None, ""):
            return Decimal("0")
        try:
            return Decimal(str(value).replace(",", "").replace("$", "").strip())
        except Exception:
            return Decimal("0")

    def _obtener_salario_base_categoria(self, categoria_id: int) -> Decimal | None:
        categoria_id_str = str(categoria_id)
        for categoria in self.categorias_disponibles_plaza:
            if str(categoria.get("id") or "") != categoria_id_str:
                continue
            salario = categoria.get("salario_base_mensual")
            if salario in (None, ""):
                return None
            return self._parse_decimal_seguro(salario)
        return None

    async def _cargar_categorias_disponibles_plaza(self) -> list[dict]:
        categorias = await categoria_puesto_service.obtener_todas(
            incluir_inactivas=False,
            limite=500,
        )
        return [
            {
                "id": int(categoria.id or 0),
                "label": (
                    f"{str(categoria.clave or '').strip().upper()} - "
                    f"{self._normalizar_nombre_visual(str(categoria.nombre or ''))}"
                ).strip(" -"),
                "salario_base_mensual": (
                    str(categoria.salario_base_mensual)
                    if getattr(categoria, "salario_base_mensual", None) is not None
                    else ""
                ),
            }
            for categoria in categorias
            if int(categoria.id or 0) > 0
        ]

    def _construir_plazas_reasignacion_disponibles(self, plaza_origen: dict) -> list[dict]:
        origen_id = int(plaza_origen.get("id") or 0)
        categoria_id = int(plaza_origen.get("categoria_puesto_id") or 0)
        contrato_id = int(plaza_origen.get("contrato_id") or 0)
        opciones: list[dict] = []

        for plaza in self.plazas_contrato_expandido:
            plaza_id = int(plaza.get("id") or 0)
            if plaza_id <= 0 or plaza_id == origen_id:
                continue
            if int(plaza.get("contrato_id") or 0) != contrato_id:
                continue
            if str(plaza.get("estatus", "") or "") != EstatusPlaza.VACANTE.value:
                continue
            if int(plaza.get("empleado_id") or 0) > 0:
                continue
            if int(plaza.get("categoria_puesto_id") or 0) != categoria_id:
                continue
            if int(plaza.get("sede_id") or 0) <= 0:
                continue

            opciones.append(
                {
                    "id": plaza_id,
                    "label": (
                        f"Plaza #{plaza.get('numero_plaza', '')} · "
                        f"{plaza.get('sede_display', 'Sin sede')} · "
                        f"{plaza.get('contrato_codigo', '')}"
                    ).strip(" ·"),
                }
            )

        opciones.sort(key=lambda item: str(item.get("label", "")))
        return opciones

    async def abrir_modal_asignacion_plaza(self, plaza: dict):
        """Abre el selector para asignar o reasignar una plaza."""
        if not isinstance(plaza, dict):
            yield rx.toast.error("Plaza inválida")
            return

        plaza_id = int(plaza.get("id") or 0)
        if plaza_id <= 0:
            yield rx.toast.error("No se pudo identificar la plaza")
            return

        estatus = str(plaza.get("estatus", "") or "")
        if estatus == EstatusPlaza.SUSPENDIDA.value:
            yield rx.toast.error("Reactive la plaza antes de asignar personal")
            return
        if not plaza.get("categoria_puesto_id"):
            yield rx.toast.error("La plaza debe tener categoría antes de asignar un empleado")
            return
        if not plaza.get("sede_id"):
            yield rx.toast.error("La plaza debe tener sede antes de asignar un empleado")
            return
        if int(plaza.get("empleado_id") or 0) > 0:
            yield rx.toast.error(
                "Primero libere o reasigne la plaza para conservar el historial del empleado actual"
            )
            return

        self.plaza_seleccionada = dict(plaza)
        self.modo_asignacion_plaza = "asignar"
        self.empleado_seleccionado_plaza_id = ""
        self.empleados_disponibles_plaza = []
        self.cargando_empleados_plaza = True
        self.mostrar_modal_asignacion_plaza = True
        yield

        try:
            empleados = await empleado_service.obtener_por_empresa(
                empresa_id=self.id_empresa_actual,
                incluir_inactivos=True,
                limite=200,
            )
            empleados_asignados = await plaza_service.obtener_empleados_asignados(
                empresa_id=self.id_empresa_actual,
            )
            empleados_asignados_set = set(empleados_asignados)
            bajas_activas_ids = {
                int(item.get("empleado_id") or 0)
                for item in self.bajas_activas
                if int(item.get("empleado_id") or 0) > 0
            }

            opciones = []
            for empleado in empleados:
                if empleado.id in bajas_activas_ids:
                    continue
                if (
                    str(getattr(empleado, "estatus", "") or "").upper()
                    == EstatusEmpleado.SUSPENDIDO.value
                ):
                    continue
                if empleado.id in empleados_asignados_set:
                    continue
                opciones.append(
                    {
                        "id": empleado.id,
                        "clave": empleado.clave,
                        "nombre_completo": self._resolver_nombre_empleado_visual(empleado),
                    }
                )
            self.empleados_disponibles_plaza = sorted(
                opciones,
                key=lambda item: (item.get("nombre_completo", ""), item.get("clave", "")),
            )
        except Exception as e:
            self.manejar_error(e, "cargar empleados disponibles para plaza")
            self.mostrar_modal_asignacion_plaza = False
            self.plaza_seleccionada = {}
            self.empleados_disponibles_plaza = []
            yield rx.toast.error("No se pudo cargar la disponibilidad de empleados")
        finally:
            self.cargando_empleados_plaza = False

    def cerrar_modal_asignacion_plaza(self):
        self.mostrar_modal_asignacion_plaza = False
        self.plaza_seleccionada = {}
        self.empleados_disponibles_plaza = []
        self.empleado_seleccionado_plaza_id = ""
        self.cargando_empleados_plaza = False
        self.modo_asignacion_plaza = "asignar"

    async def confirmar_asignacion_plaza(self):
        """Confirma la asignación de una plaza vacante."""
        plaza_id = int(self.plaza_seleccionada.get("id") or 0)
        empleado_nuevo_id = self.parse_id(self.empleado_seleccionado_plaza_id)
        empleado_actual_id = int(self.plaza_seleccionada.get("empleado_id") or 0)

        if plaza_id <= 0:
            yield rx.toast.error("No hay plaza seleccionada")
            return
        if empleado_nuevo_id is None:
            yield rx.toast.error("Seleccione un empleado")
            return

        self.saving = True
        yield
        try:
            if empleado_actual_id > 0:
                yield rx.toast.error(
                    "Primero libere o reasigne la plaza para conservar el historial del empleado actual"
                )
                return

            await plaza_service.asignar_empleado(plaza_id, empleado_nuevo_id)
            self.cerrar_modal_asignacion_plaza()
            await self._fetch_empleados()
            yield rx.toast.success("Empleado asignado correctamente")
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "asignando plaza")
        finally:
            self.saving = False

    async def abrir_modal_categoria_plaza(self, plaza: dict):
        """Abre el selector para asignar o cambiar la categoría de una plaza."""
        if not isinstance(plaza, dict):
            yield rx.toast.error("Plaza inválida")
            return

        plaza_id = int(plaza.get("id") or 0)
        if plaza_id <= 0:
            yield rx.toast.error("No se pudo identificar la plaza")
            return

        if str(plaza.get("estatus", "") or "") == EstatusPlaza.SUSPENDIDA.value:
            yield rx.toast.error("Reactive la plaza antes de actualizar la categoria")
            return

        self.plaza_categoria_seleccionada = dict(plaza)
        self.categoria_seleccionada_plaza_id = str(plaza.get("categoria_puesto_id") or "")
        self.categorias_disponibles_plaza = []
        self.cargando_categorias_plaza = True
        self.mostrar_modal_categoria_plaza = True
        yield

        try:
            self.categorias_disponibles_plaza = await self._cargar_categorias_disponibles_plaza()
        except Exception as e:
            self.manejar_error(e, "cargando categorias disponibles para plaza")
            self.cerrar_modal_categoria_plaza()
            yield rx.toast.error("No se pudieron cargar las categorias disponibles")
        finally:
            self.cargando_categorias_plaza = False

    def cerrar_modal_categoria_plaza(self):
        self.mostrar_modal_categoria_plaza = False
        self.plaza_categoria_seleccionada = {}
        self.categoria_seleccionada_plaza_id = ""
        self.categorias_disponibles_plaza = []
        self.cargando_categorias_plaza = False

    async def confirmar_categoria_plaza(self):
        plaza_id = int(self.plaza_categoria_seleccionada.get("id") or 0)
        categoria_nueva_id = self.parse_id(self.categoria_seleccionada_plaza_id)
        categoria_actual_id = int(self.plaza_categoria_seleccionada.get("categoria_puesto_id") or 0)

        if plaza_id <= 0:
            yield rx.toast.error("No hay plaza seleccionada")
            return
        if categoria_nueva_id is None:
            yield rx.toast.error("Seleccione una categoria")
            return

        self.saving = True
        yield
        try:
            if categoria_actual_id == categoria_nueva_id:
                self.cerrar_modal_categoria_plaza()
                yield rx.toast.success("La plaza conserva la categoria actual")
                return

            salario_actual = self._parse_decimal_seguro(
                self.plaza_categoria_seleccionada.get("salario_mensual"),
            )
            salario_base = self._obtener_salario_base_categoria(categoria_nueva_id)
            payload_kwargs = {
                "categoria_puesto_id": categoria_nueva_id,
            }
            if (
                int(self.plaza_categoria_seleccionada.get("empleado_id") or 0) <= 0
                and salario_base is not None
                and salario_actual <= 0
            ):
                payload_kwargs["salario_mensual"] = salario_base

            await plaza_service.actualizar(plaza_id, PlazaUpdate(**payload_kwargs))
            self.cerrar_modal_categoria_plaza()
            await self._fetch_empleados()
            yield rx.toast.success(
                "Categoria actualizada correctamente"
                if categoria_actual_id > 0
                else "Categoria asignada correctamente"
            )
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "actualizando categoria de plaza")
        finally:
            self.saving = False

    async def abrir_modal_salario_plaza(self, plaza: dict):
        """Abre el modal para asignar o actualizar el salario de una plaza."""
        if not isinstance(plaza, dict):
            yield rx.toast.error("Plaza inválida")
            return

        plaza_id = int(plaza.get("id") or 0)
        if plaza_id <= 0:
            yield rx.toast.error("No se pudo identificar la plaza")
            return

        estatus = str(plaza.get("estatus", "") or "")
        if estatus not in {
            EstatusPlaza.VACANTE.value,
            EstatusPlaza.OCUPADA.value,
        }:
            yield rx.toast.error("Solo puede actualizar el salario de plazas activas")
            return

        salario_actual = self._parse_decimal_seguro(plaza.get("salario_mensual"))
        self.plaza_salario_seleccionada = dict(plaza)
        self.form_salario_plaza = (
            formatear_moneda(str(salario_actual))
            if salario_actual > 0
            else ""
        )
        self.error_salario_plaza = ""
        self.salario_base_categoria_plaza_referencia = ""
        self.mostrar_modal_salario_plaza = True
        yield

        categoria_id = int(plaza.get("categoria_puesto_id") or 0)
        if categoria_id <= 0:
            return

        salario_base = self._parse_decimal_seguro(
            plaza.get("categoria_salario_base_mensual"),
        )
        if salario_base <= 0:
            salario_base_cache = self._obtener_salario_base_categoria(categoria_id)
            if salario_base_cache is not None:
                salario_base = salario_base_cache

        if salario_base <= 0:
            try:
                categoria = await categoria_puesto_service.obtener_por_id(categoria_id)
            except Exception:
                logger.debug(
                    "No se pudo cargar el sueldo base de categoria para la plaza %s",
                    plaza_id,
                    exc_info=True,
                )
                return

            salario_categoria = getattr(categoria, "salario_base_mensual", None)
            if salario_categoria is None:
                return
            salario_base = self._parse_decimal_seguro(salario_categoria)

        if salario_base > 0:
            self.salario_base_categoria_plaza_referencia = str(salario_base)

    def cerrar_modal_salario_plaza(self):
        self.mostrar_modal_salario_plaza = False
        self.plaza_salario_seleccionada = {}
        self.form_salario_plaza = ""
        self.error_salario_plaza = ""
        self.salario_base_categoria_plaza_referencia = ""

    async def confirmar_salario_plaza(self):
        plaza_id = int(self.plaza_salario_seleccionada.get("id") or 0)
        if plaza_id <= 0:
            yield rx.toast.error("No hay plaza seleccionada")
            return

        self.validar_salario_plaza_campo()
        if self.error_salario_plaza:
            yield rx.toast.error(self.error_salario_plaza)
            return

        salario_actual = self._parse_decimal_seguro(
            self.plaza_salario_seleccionada.get("salario_mensual"),
        )
        salario_nuevo = self._parse_decimal_seguro(self.form_salario_plaza)

        self.saving = True
        yield
        try:
            if salario_nuevo == salario_actual:
                self.cerrar_modal_salario_plaza()
                yield rx.toast.success("La plaza conserva el salario actual")
                return

            await plaza_service.actualizar(
                plaza_id,
                PlazaUpdate(salario_mensual=salario_nuevo),
            )
            self.cerrar_modal_salario_plaza()
            await self._fetch_empleados()
            yield rx.toast.success("Salario actualizado correctamente")
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "actualizando salario de plaza")
        finally:
            self.saving = False

    def abrir_modal_reasignacion_plaza(self, plaza: dict):
        """Prepara el cambio del empleado actual a otra plaza compatible."""
        if not isinstance(plaza, dict):
            return rx.toast.error("Plaza inválida")

        plaza_id = int(plaza.get("id") or 0)
        if plaza_id <= 0:
            return rx.toast.error("No se pudo identificar la plaza")
        if str(plaza.get("estatus", "") or "") != EstatusPlaza.OCUPADA.value:
            return rx.toast.error("Solo puede reasignar plazas ocupadas")

        opciones = self._construir_plazas_reasignacion_disponibles(plaza)
        if not opciones:
            return rx.toast.error(
                "No hay otra plaza vacante con sede y categoria compatible para reasignar"
            )

        self.plaza_reasignacion_seleccionada = dict(plaza)
        self.plaza_destino_reasignacion_id = ""
        self.plazas_disponibles_reasignacion = opciones
        self.mostrar_modal_reasignacion_plaza = True

    def cerrar_modal_reasignacion_plaza(self):
        self.mostrar_modal_reasignacion_plaza = False
        self.plaza_reasignacion_seleccionada = {}
        self.plaza_destino_reasignacion_id = ""
        self.plazas_disponibles_reasignacion = []

    async def confirmar_reasignacion_plaza(self):
        plaza_origen_id = int(self.plaza_reasignacion_seleccionada.get("id") or 0)
        plaza_destino_id = self.parse_id(self.plaza_destino_reasignacion_id)

        if plaza_origen_id <= 0:
            yield rx.toast.error("No hay plaza origen seleccionada")
            return
        if plaza_destino_id is None:
            yield rx.toast.error("Seleccione una plaza destino")
            return

        self.saving = True
        yield
        try:
            await plaza_service.reasignar_empleado_a_plaza(
                plaza_origen_id=plaza_origen_id,
                plaza_destino_id=plaza_destino_id,
            )
            self.cerrar_modal_reasignacion_plaza()
            await self._fetch_empleados()
            yield rx.toast.success("Plaza reasignada correctamente")
        except BusinessRuleError as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "reasignando plaza")
        finally:
            self.saving = False

    def abrir_modal_sede_plaza(self, plaza: dict):
        """Abre el modal compacto para asignar o actualizar la sede de una plaza."""
        if not isinstance(plaza, dict):
            return rx.toast.error("Plaza inválida")

        plaza_id = int(plaza.get("id") or 0)
        if plaza_id <= 0:
            return rx.toast.error("No se pudo identificar la plaza")

        if str(plaza.get("estatus", "") or "") == EstatusPlaza.SUSPENDIDA.value:
            return rx.toast.error("Reactive la plaza antes de actualizar la sede")
        if int(plaza.get("empleado_id") or 0) > 0:
            return rx.toast.error(
                "No se puede cambiar la sede de una plaza ocupada; use reasignar plaza"
            )

        self.plaza_sede_seleccionada = dict(plaza)
        self.sede_seleccionada_plaza_id = str(plaza.get("sede_id") or "")
        self.mostrar_modal_sede_plaza = True

    def cerrar_modal_sede_plaza(self):
        self.mostrar_modal_sede_plaza = False
        self.plaza_sede_seleccionada = {}
        self.sede_seleccionada_plaza_id = ""

    async def confirmar_sede_plaza(self):
        plaza_id = int(self.plaza_sede_seleccionada.get("id") or 0)
        if plaza_id <= 0:
            return rx.toast.error("No hay plaza seleccionada")
        return await self.actualizar_sede_plaza(
            plaza_id,
            self.sede_seleccionada_plaza_id,
        )

    async def actualizar_sede_plaza(self, plaza_id: int, sede_id: str):
        """Actualiza la sede de una plaza desde la tabla agrupada."""
        plaza_id_int = int(plaza_id or 0)
        sede_id_int = self.parse_id(sede_id)
        if plaza_id_int <= 0 or sede_id_int is None:
            return rx.toast.error("Seleccione una sede válida")

        self.saving = True
        try:
            await plaza_service.actualizar(
                plaza_id_int,
                PlazaUpdate(sede_id=sede_id_int),
            )
            await self._fetch_empleados()
            if int(self.plaza_sede_seleccionada.get("id") or 0) == plaza_id_int:
                self.cerrar_modal_sede_plaza()
            return rx.toast.success("Sede asignada correctamente")
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "actualizando sede de plaza")
        finally:
            self.saving = False

    async def liberar_plaza_portal(self, plaza: dict):
        """Libera la asignación actual de una plaza desde la vista por plaza."""
        plaza_id = int(plaza.get("id") or 0) if isinstance(plaza, dict) else 0
        if plaza_id <= 0:
            return rx.toast.error("No se pudo identificar la plaza")

        if str(plaza.get("estatus", "") or "") != EstatusPlaza.OCUPADA.value:
            return rx.toast.error("Solo puede liberar plazas ocupadas")

        self.saving = True
        try:
            await plaza_service.liberar_plaza(plaza_id)
            await self._fetch_empleados()
            return rx.toast.success("Plaza liberada correctamente")
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "liberando plaza")
        finally:
            self.saving = False

    def ejecutar_accion_plaza(self, plaza: dict, accion: str):
        """Despacha la acción elegida desde el selector de la fila."""
        accion_normalizada = str(accion or "").strip().upper()
        if not isinstance(plaza, dict) or not accion_normalizada:
            return None

        if accion_normalizada == ACCION_PLAZA_ASIGNAR_EMPLEADO:
            return type(self).abrir_modal_asignacion_plaza(plaza)
        if accion_normalizada in {
            ACCION_PLAZA_ASIGNAR_CATEGORIA,
            ACCION_PLAZA_REASIGNAR_CATEGORIA,
            ACCION_PLAZA_CAMBIAR_CATEGORIA,
        }:
            return type(self).abrir_modal_categoria_plaza(plaza)
        if accion_normalizada == ACCION_PLAZA_ACTUALIZAR_SALARIO:
            return type(self).abrir_modal_salario_plaza(plaza)
        if accion_normalizada in {
            ACCION_PLAZA_ASIGNAR_SEDE,
            ACCION_PLAZA_REASIGNAR_SEDE,
        }:
            return type(self).abrir_modal_sede_plaza(plaza)
        if accion_normalizada == ACCION_PLAZA_REASIGNAR_PLAZA:
            return type(self).abrir_modal_reasignacion_plaza(plaza)
        if accion_normalizada == "VER_PERFIL":
            return type(self).ver_perfil_plaza(plaza)
        if accion_normalizada == ACCION_PLAZA_LIBERAR:
            return type(self).liberar_plaza_portal(plaza)
        if accion_normalizada == ACCION_PLAZA_REACTIVAR:
            return type(self).reactivar_plaza_portal(plaza)
        return None

    async def reactivar_plaza_portal(self, plaza: dict):
        """Reactiva una plaza suspendida desde la vista agrupada."""
        plaza_id = int(plaza.get("id") or 0) if isinstance(plaza, dict) else 0
        if plaza_id <= 0:
            return rx.toast.error("No se pudo identificar la plaza")

        self.saving = True
        try:
            await plaza_service.reactivar_plaza(plaza_id)
            await self._fetch_empleados()
            return rx.toast.success("Plaza reactivada correctamente")
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "reactivando plaza")
        finally:
            self.saving = False

    async def abrir_modal_detalle(self, empleado: dict):
        """Abre el modal de detalle y carga datos completos del empleado."""
        if not isinstance(empleado, dict):
            yield rx.toast.error("Empleado inválido")
            return

        empleado_id = empleado.get("id")
        if not empleado_id:
            yield rx.toast.error("No se pudo abrir el detalle del empleado")
            return

        self.empleado_detalle = self._detalle_empleado_placeholder(empleado)
        self.historial_bancario = []
        self.mostrar_modal_historial_bancario = False
        self.mostrar_modal_detalle = True
        self.loading_detalle_empleado = True
        yield

        try:
            empleado_entidad = await empleado_service.obtener_por_id(int(empleado_id))
            if (
                self.id_empresa_actual
                and int(empleado_entidad.empresa_id or 0) != int(self.id_empresa_actual)
            ):
                raise BusinessRuleError("No tiene acceso a este empleado")

            historial = await cuenta_bancaria_historial_service.obtener_historial(
                empleado_entidad.id,
                limite=50,
            )
            self.empleado_detalle = self._serializar_empleado_detalle_modal(
                empleado_entidad,
                empleado,
            )
            self.historial_bancario = self._serializar_historial_bancario(
                historial,
                empleado_entidad.user_id,
            )
        except NotFoundError:
            self.cerrar_modal_detalle()
            yield rx.toast.error("Empleado no encontrado")
            return
        except BusinessRuleError as e:
            self.cerrar_modal_detalle()
            yield rx.toast.error(str(e))
            return
        except Exception as e:
            self.cerrar_modal_detalle()
            yield self.manejar_error_con_toast(e, "cargando detalle del empleado")
            return
        finally:
            self.loading_detalle_empleado = False

    def cerrar_modal_detalle(self):
        """Cierra el modal de detalle y limpia su estado asociado."""
        self.mostrar_modal_detalle = False
        self.mostrar_modal_historial_bancario = False
        self.loading_detalle_empleado = False
        self.empleado_detalle = _empty_empleado_detalle()
        self.historial_bancario = []

    def abrir_modal_historial_bancario(self):
        """Abre el modal secundario con el historial bancario del empleado."""
        self.mostrar_modal_historial_bancario = True

    def cerrar_modal_historial_bancario(self):
        """Cierra el modal secundario de historial bancario."""
        self.mostrar_modal_historial_bancario = False

    async def _post_procesamiento_alta_masiva(self):
        """Recarga el listado después de una alta masiva exitosa."""
        await self._fetch_empleados()

    # ========================
    # ACCIONES DE MODAL
    # ========================
    def abrir_modal_crear(self):
        """Abre el modal para crear un nuevo empleado."""
        self._limpiar_formulario()
        self.editar_datos_bancarios = True
        self.snapshot_bancario_base_edicion = {}
        self.mostrar_modal_empleado = True

    def cerrar_modal_empleado(self):
        """Cierra el modal de empleado."""
        self.mostrar_modal_empleado = False
        self._limpiar_formulario()

    def habilitar_edicion_datos_bancarios(self):
        """Desbloquea la captura bancaria en el modal de edición."""
        self.editar_datos_bancarios = True

    def abrir_modal_baja(self, empleado: dict):
        """Abre modal de baja para un empleado especifico."""
        if not empleado or not isinstance(empleado, dict):
            return
        self.empleado_baja_seleccionado = empleado
        self._limpiar_formulario_baja()
        self.mostrar_modal_baja = True

    def cerrar_modal_baja(self):
        """Cierra modal de baja y limpia estado asociado."""
        self.mostrar_modal_baja = False
        self.empleado_baja_seleccionado = {}
        self._limpiar_formulario_baja()

    async def abrir_modal_editar_desde_detalle(self):
        """Cierra el detalle y delega el flujo al modal de edición."""
        empleado = dict(self.empleado_detalle)
        if not empleado:
            return
        self.cerrar_modal_detalle()
        return await self.abrir_modal_editar(empleado)

    def abrir_modal_baja_desde_detalle(self):
        """Cierra el detalle y abre la baja para el empleado actual."""
        empleado = dict(self.empleado_detalle)
        if not empleado:
            return
        self.cerrar_modal_detalle()
        self.abrir_modal_baja(empleado)

    # ========================
    # CREAR EMPLEADO
    # ========================
    async def crear_empleado(self):
        """Crea un nuevo empleado asignado a la empresa del portal."""
        if not self._validar_formulario():
            return rx.toast.error("Por favor corrija los errores del formulario")

        descuentos_form = self._construir_descuentos_recurrentes_form()
        if descuentos_form is None:
            return rx.toast.error(
                self.error_descuentos_recurrentes or "Revise los descuentos recurrentes"
            )

        self.saving = True
        try:
            snapshot_bancario = self._snapshot_bancario_form()
            payload = self._payload_base_empleado()
            payload.update(
                {
                    "empresa_id": self.id_empresa_actual,
                    "curp": self.form_curp,
                    "nombre": self.form_nombre,
                    "apellido_paterno": self.form_apellido_paterno,
                    "fecha_nacimiento": parse_date_input(self.form_fecha_nacimiento),
                    "genero": self.form_genero,
                    "telefono": self.form_telefono,
                }
            )
            empleado_create = EmpleadoCreate(**payload)

            empleado = await empleado_service.crear(empleado_create)
            await empleado_descuento_recurrente_service.reemplazar_descuentos_empleado(
                empleado.id,
                [
                    descuento.model_copy(update={"empleado_id": empleado.id})
                    for descuento in descuentos_form
                ],
            )
            await self._registrar_historial_bancario(
                empleado.id,
                snapshot_bancario,
                registrar_vacio=False,
            )

            self.cerrar_modal_empleado()
            await self._fetch_empleados()
            return rx.toast.success(f"Empleado {empleado.clave} creado correctamente")

        except DuplicateError as e:
            if "curp" in str(e).lower():
                self.error_curp = "Este CURP ya esta registrado"
            return rx.toast.error(str(e))
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "creando empleado")
        finally:
            self.saving = False

    # ========================
    # EDITAR EMPLEADO
    # ========================
    async def abrir_modal_editar(self, emp: dict):
        """Abre el modal en modo edicion con los datos del empleado."""
        self._limpiar_formulario()
        try:
            empleado = await empleado_service.obtener_por_id(emp["id"])
        except NotFoundError:
            return rx.toast.error("Empleado no encontrado")
        except Exception as e:
            return self.manejar_error_con_toast(e, "cargando empleado")

        self.es_edicion = True
        self.empleado_editando_id = empleado.id
        snapshot_bancario_inicial = await self._obtener_snapshot_bancario_base_edicion(
            empleado
        )
        descuentos_resumen = (
            await empleado_descuento_recurrente_service.obtener_resumenes_ui_por_empleados(
                [empleado.id]
            )
        ).get(empleado.id, {})
        self.snapshot_bancario_base_edicion = snapshot_bancario_inicial
        self.editar_datos_bancarios = False
        self._llenar_formulario_empleado_compartido(
            {
                "curp": empleado.curp,
                "nombre": empleado.nombre,
                "apellido_paterno": empleado.apellido_paterno,
                "apellido_materno": empleado.apellido_materno,
                "rfc": empleado.rfc,
                "nss": empleado.nss,
                "fecha_ingreso": str(empleado.fecha_ingreso) if empleado.fecha_ingreso else "",
                "fecha_ingreso_vigente": (
                    str(empleado.fecha_ingreso_vigente)
                    if empleado.fecha_ingreso_vigente else ""
                ),
                "fecha_nacimiento": str(empleado.fecha_nacimiento) if empleado.fecha_nacimiento else "",
                "genero": empleado.genero,
                "telefono": empleado.telefono,
                "email": empleado.email,
                "direccion": empleado.direccion,
                "notas": empleado.notas,
                "contacto_emergencia": empleado.contacto_emergencia,
                "cuenta_bancaria": snapshot_bancario_inicial["cuenta_bancaria"],
                "banco": snapshot_bancario_inicial["banco"],
                "clabe_interbancaria": snapshot_bancario_inicial["clabe_interbancaria"],
                "descuentos_configurados": descuentos_resumen.get(
                    "descuentos_configurados",
                    [],
                ),
            }
        )
        self._sincronizar_descuentos_activos_form()

        self.mostrar_modal_empleado = True

    async def actualizar_empleado(self):
        """Actualiza un empleado existente."""
        if not self._validar_formulario():
            return rx.toast.error("Por favor corrija los errores del formulario")

        descuentos_form = self._construir_descuentos_recurrentes_form(
            empleado_id=self.empleado_editando_id
        )
        if descuentos_form is None:
            return rx.toast.error(
                self.error_descuentos_recurrentes or "Revise los descuentos recurrentes"
            )

        self.saving = True
        try:
            snapshot_bancario_original = self._normalizar_snapshot_bancario(
                self.snapshot_bancario_base_edicion
            )
            snapshot_bancario_nuevo = self._snapshot_bancario_form()
            empleado_update = EmpleadoUpdate(**self._payload_base_empleado())

            empleado = await empleado_service.actualizar(self.empleado_editando_id, empleado_update)
            await empleado_descuento_recurrente_service.reemplazar_descuentos_empleado(
                empleado.id,
                descuentos_form,
            )
            if snapshot_bancario_nuevo != snapshot_bancario_original:
                await self._registrar_historial_bancario(
                    empleado.id,
                    snapshot_bancario_nuevo,
                    registrar_vacio=True,
                )

            self.cerrar_modal_empleado()
            await self._fetch_empleados()
            return rx.toast.success(f"Empleado {empleado.clave} actualizado correctamente")

        except NotFoundError:
            return rx.toast.error("Empleado no encontrado")
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "actualizando empleado")
        finally:
            self.saving = False

    async def guardar_empleado(self):
        """Dispatcher: crea o actualiza segun el modo."""
        if self.es_edicion:
            return await self.actualizar_empleado()
        return await self.crear_empleado()

    async def confirmar_baja(self):
        """Ejecuta la baja usando BajaService."""
        emp = self.empleado_baja_seleccionado
        if not emp:
            yield rx.toast.error("No hay empleado seleccionado")
            return

        empleado_id = emp.get("id")
        if not empleado_id:
            yield rx.toast.error("Error: no se pudo obtener el ID del empleado")
            return

        self.error_motivo_baja = ""
        self.error_fecha_efectiva_baja = ""

        if not self.form_motivo_baja:
            self.error_motivo_baja = "Debe seleccionar un motivo de baja"
            yield rx.toast.error("Debe seleccionar un motivo de baja")
            return

        from core.domain.models.baja_empleado import BajaEmpleadoCreate

        fecha_efectiva = date.today()
        if self.form_fecha_efectiva_baja:
            try:
                fecha_efectiva = parse_date_input(self.form_fecha_efectiva_baja)
            except ValueError:
                self.error_fecha_efectiva_baja = "Fecha efectiva inválida"
                yield rx.toast.error("Fecha efectiva inválida")
                return

        registrado_por = self.obtener_uuid_usuario_actual()

        self.saving = True
        try:
            if (
                bool(emp.get("es_activo_portal", False))
                and str(emp.get("estatus", "") or "").strip().upper()
                != EstatusEmpleado.ACTIVO.value
            ):
                await empleado_service.sincronizar_estatus_por_plazas(
                    empleado_id,
                    tiene_plaza_activa=True,
                )

            await baja_service.registrar_baja(
                BajaEmpleadoCreate(
                    empleado_id=empleado_id,
                    empresa_id=emp.get("empresa_id") or self.id_empresa_actual,
                    motivo=MotivoBaja(self.form_motivo_baja),
                    fecha_efectiva=fecha_efectiva,
                    notas=self.form_notas_baja or None,
                    registrado_por=registrado_por,
                )
            )

            self.cerrar_modal_baja()
            await self._fetch_empleados()

            yield rx.toast.success(
                "Baja registrada. Se generó una alerta de liquidación en Bajas (15 días hábiles)."
            )
        except (BusinessRuleError, ValueError) as e:
            yield rx.toast.error(str(e))
        except Exception as e:
            yield self.manejar_error_con_toast(e, "registrando baja")
        finally:
            self.saving = False

    # ========================
    # METODOS PRIVADOS
    # ========================
    def _construir_contacto_emergencia(self) -> str | None:
        """Construye el string de contacto de emergencia desde los campos del form."""
        return self._construir_contacto_emergencia_compartido()

    def _snapshot_bancario_form(self) -> dict[str, str]:
        """Snapshot normalizado de los datos bancarios capturados en el formulario."""
        return {
            "cuenta_bancaria": normalizar_cuenta_bancaria(self.form_cuenta_bancaria),
            "banco": normalizar_banco(self.form_banco),
            "clabe_interbancaria": normalizar_clabe_interbancaria(self.form_clabe),
        }

    def _snapshot_bancario_empleado(self, empleado) -> dict[str, str]:
        """Snapshot normalizado de los datos bancarios actuales del empleado."""
        return {
            "cuenta_bancaria": normalizar_cuenta_bancaria(empleado.cuenta_bancaria),
            "banco": normalizar_banco(empleado.banco),
            "clabe_interbancaria": normalizar_clabe_interbancaria(
                empleado.clabe_interbancaria
            ),
        }

    @staticmethod
    def _normalizar_snapshot_bancario(snapshot: dict | None) -> dict[str, str]:
        """Normaliza un snapshot externo al contrato bancario usado por el modal."""
        snapshot = snapshot or {}
        return {
            "cuenta_bancaria": normalizar_cuenta_bancaria(snapshot.get("cuenta_bancaria")),
            "banco": normalizar_banco(snapshot.get("banco")),
            "clabe_interbancaria": normalizar_clabe_interbancaria(
                snapshot.get("clabe_interbancaria")
            ),
        }

    async def _obtener_snapshot_bancario_base_edicion(self, empleado) -> dict[str, str]:
        """Obtiene el último snapshot bancario guardado o cae al dato actual del empleado."""
        snapshot_empleado = self._snapshot_bancario_empleado(empleado)
        try:
            historial = await cuenta_bancaria_historial_service.obtener_historial(
                empleado.id,
                limite=1,
            )
            if historial:
                registro = historial[0]
                return self._normalizar_snapshot_bancario(
                    {
                        "cuenta_bancaria": registro.cuenta_bancaria,
                        "banco": registro.banco,
                        "clabe_interbancaria": registro.clabe_interbancaria,
                    }
                )
        except Exception as exc:
            logger.warning(
                "No se pudo cargar el último snapshot bancario del empleado %s: %s",
                empleado.id,
                exc,
            )
        return snapshot_empleado

    async def _registrar_historial_bancario(
        self,
        empleado_id: int,
        snapshot_bancario: dict[str, str],
        *,
        registrar_vacio: bool,
    ) -> None:
        """Registra el snapshot bancario cuando el alta/edición lo amerita."""
        if not registrar_vacio and not any(snapshot_bancario.values()):
            return

        actor = self.obtener_uuid_usuario_actual()
        if not actor:
            logger.warning(
                "Se omitió historial bancario del empleado %s por falta de actor",
                empleado_id,
            )
            return

        try:
            from core.domain.models.cuenta_bancaria_historial import CuentaBancariaHistorialCreate

            await cuenta_bancaria_historial_service.registrar_cambio(
                CuentaBancariaHistorialCreate(
                    empleado_id=empleado_id,
                    cuenta_bancaria=snapshot_bancario["cuenta_bancaria"] or None,
                    banco=snapshot_bancario["banco"] or None,
                    clabe_interbancaria=snapshot_bancario["clabe_interbancaria"] or None,
                    cambiado_por=actor,
                )
            )
        except Exception as exc:
            logger.warning(
                "No se pudo registrar historial bancario del empleado %s: %s",
                empleado_id,
                exc,
            )

    @staticmethod
    def _enmascarar_digitos(valor: str | None, visibles: int = 4) -> str:
        """Enmascara una cuenta/CLABE conservando sólo los últimos dígitos."""
        if not valor:
            return ""
        valor_limpio = str(valor).strip()
        if not valor_limpio:
            return ""
        if len(valor_limpio) <= visibles:
            return valor_limpio
        return ("*" * (len(valor_limpio) - visibles)) + valor_limpio[-visibles:]

    @staticmethod
    def _formatear_fecha_hora(valor) -> str:
        """Formatea fechas de auditoría bancaria para UI."""
        return formatear_fecha_hora(valor, valor_vacio="")

    @staticmethod
    def _detalle_empleado_placeholder(resumen: dict) -> dict:
        """Construye un placeholder ligero mientras carga el detalle completo."""
        detalle = _empty_empleado_detalle()
        detalle.update({
            "id": resumen.get("id"),
            "uuid": str(resumen.get("uuid", "") or ""),
            "empresa_id": resumen.get("empresa_id"),
            "clave": resumen.get("clave", "") or "",
            "nombre_completo": (
                resumen.get("nombre_completo", "")
                or resumen.get("nombre_completo_ui", "")
                or ""
            ),
            "estatus": resumen.get("estatus", "") or "",
            "estatus_portal": resumen.get("estatus_portal", "") or FILTRO_PANEL_INACTIVOS,
            "es_activo_portal": bool(
                resumen.get("es_activo_portal", False)
                or resumen.get("estatus_portal", "") == FILTRO_PANEL_ACTIVOS
            ),
            "estatus_personal": resumen.get("estatus_personal", "") or "",
            "contrato_codigo": resumen.get("contrato_codigo", "") or "",
            "fecha_ingreso": resumen.get("fecha_ingreso", "") or "",
            "fecha_ingreso_vigente": resumen.get("fecha_ingreso_vigente", "") or "",
            "telefono": resumen.get("telefono", "") or "",
            "email": resumen.get("email", "") or "",
            "is_restricted": bool(resumen.get("is_restricted", False)),
            "documentos_aprobados_expediente": int(
                resumen.get("documentos_aprobados_expediente", 0) or 0
            ),
            "documentos_requeridos_expediente": int(
                resumen.get("documentos_requeridos_expediente", 0) or 0
            ),
            "descuentos_configurados": list(
                resumen.get("descuentos_configurados", []) or []
            ),
            "descuentos_activos_hoy": list(
                resumen.get("descuentos_activos_hoy", []) or []
            ),
        })
        return detalle

    def _serializar_empleado_detalle_modal(self, empleado, resumen: dict) -> dict:
        """Normaliza el detalle del empleado a un payload seguro para Reflex."""
        contacto_nombre, contacto_telefono, contacto_parentesco = self._split_contacto_emergencia(
            empleado.contacto_emergencia
        )
        estatus_portal = (
            str(resumen.get("estatus_portal", "") or "").strip()
            or FILTRO_PANEL_INACTIVOS
        )
        detalle = _empty_empleado_detalle()
        detalle.update({
            "id": empleado.id,
            "uuid": str(empleado.uuid) if getattr(empleado, "uuid", None) else "",
            "empresa_id": empleado.empresa_id,
            "user_id": str(empleado.user_id) if empleado.user_id else "",
            "clave": empleado.clave,
            "nombre_completo": empleado.nombre_completo(),
            "estatus": str(empleado.estatus or ""),
            "estatus_portal": estatus_portal,
            "es_activo_portal": estatus_portal == FILTRO_PANEL_ACTIVOS,
            "estatus_personal": resumen.get("estatus_personal", "") or "",
            "contrato_codigo": resumen.get("contrato_codigo", "") or "",
            "is_restricted": bool(empleado.is_restricted),
            "curp": empleado.curp or "",
            "rfc": empleado.rfc or "",
            "nss": empleado.nss or "",
            "telefono": empleado.telefono or "",
            "email": empleado.email or "",
            "direccion": empleado.direccion or "",
            "notas": empleado.notas or "",
            "fecha_ingreso": formatear_fecha(empleado.fecha_ingreso) if empleado.fecha_ingreso else "",
            "fecha_ingreso_vigente": (
                formatear_fecha(empleado.fecha_ingreso_vigente)
                if empleado.fecha_ingreso_vigente else ""
            ),
            "contacto_nombre": contacto_nombre,
            "contacto_telefono": contacto_telefono,
            "contacto_parentesco": contacto_parentesco,
            "banco": empleado.banco or "",
            "cuenta_bancaria": empleado.cuenta_bancaria or "",
            "clabe_interbancaria": empleado.clabe_interbancaria or "",
            "documentos_aprobados_expediente": int(
                resumen.get("documentos_aprobados_expediente", 0) or 0
            ),
            "documentos_requeridos_expediente": int(
                resumen.get("documentos_requeridos_expediente", 0) or 0
            ),
            "descuentos_configurados": list(
                resumen.get("descuentos_configurados", []) or []
            ),
            "descuentos_activos_hoy": list(
                resumen.get("descuentos_activos_hoy", []) or []
            ),
        })
        return detalle

    def _serializar_historial_bancario(self, registros, user_id) -> List[dict]:
        """Normaliza historial bancario a un formato de lectura para la UI."""
        user_id_str = str(user_id) if user_id else ""
        historial: List[dict] = []
        for registro in registros:
            origen = (
                "Autoservicio"
                if user_id_str and str(registro.cambiado_por) == user_id_str
                else "Administracion"
            )
            historial.append(
                {
                    "id": registro.id,
                    "fecha_cambio": self._formatear_fecha_hora(registro.fecha_cambio),
                    "origen": origen,
                    "banco": registro.banco or "",
                    "cuenta_bancaria": self._enmascarar_digitos(registro.cuenta_bancaria),
                    "clabe_interbancaria": self._enmascarar_digitos(
                        registro.clabe_interbancaria
                    ),
                    "tiene_soporte": bool(registro.documento_id),
                }
            )
        return historial

    def _limpiar_formulario_baja(self) -> None:
        """Resetea el formulario de baja del portal."""
        self.form_motivo_baja = ""
        self.form_fecha_efectiva_baja = ""
        self.form_notas_baja = ""
        self.error_motivo_baja = ""
        self.error_fecha_efectiva_baja = ""

    def _ajustar_pagina_empleados(self) -> None:
        """Mantiene la página actual dentro del rango válido."""
        total_paginas = self.calcular_total_paginas(
            self.total_empleados_filtrados,
            self.por_pagina,
        )
        if self.pagina < 1:
            self.pagina = 1
        elif self.pagina > total_paginas:
            self.pagina = total_paginas

    def _limpiar_formulario(self):
        """Limpia el formulario."""
        self._reset_employee_form_fields(
            error_fields=self._campos_error_formulario,
            extra_defaults={
                "form_motivo_baja": "",
                "form_fecha_efectiva_baja": "",
                "form_notas_baja": "",
                "form_descuento_infonavit_activo": False,
                "form_descuento_fonacot_activo": False,
                "form_descuento_prestamo_empresa_activo": False,
                "form_descuento_pension_alimenticia_activo": False,
                "editar_datos_bancarios": False,
                "snapshot_bancario_base_edicion": {},
            },
        )

    def _limpiar_errores(self):
        """Limpia los errores de validacion."""
        self.limpiar_errores_campos(self._campos_error_formulario)

    def _sincronizar_descuentos_activos_form(self) -> None:
        """Alinea los toggles visuales de descuentos con el contenido cargado."""
        for form_key in (
            "infonavit",
            "fonacot",
            "prestamo_empresa",
            "pension_alimenticia",
        ):
            activo_attr = f"form_descuento_{form_key}_activo"
            if not hasattr(self, activo_attr):
                continue
            setattr(
                self,
                activo_attr,
                any(
                    [
                        getattr(self, f"form_descuento_{form_key}_monto", "").strip(),
                        getattr(self, f"form_descuento_{form_key}_inicio", "").strip(),
                        getattr(self, f"form_descuento_{form_key}_fin", "").strip(),
                        getattr(self, f"form_descuento_{form_key}_notas", "").strip(),
                    ]
                ),
            )

    def _validar_formulario(self) -> bool:
        """Valida el formulario completo. Retorna True si es valido."""
        es_valido = self._validar_formulario_empleado_compartido(
            error_fields=self._campos_error_formulario,
            curp_validator=validar_curp,
            required_validations=[
                ("error_nombre", self.form_nombre, validar_nombre),
                ("error_apellido_paterno", self.form_apellido_paterno, validar_apellido_paterno),
                ("error_apellido_materno", self.form_apellido_materno, validar_apellido_materno_empleado),
                ("error_rfc", self.form_rfc, validar_rfc_empleado_requerido),
                ("error_nss", self.form_nss, validar_nss_empleado_requerido),
                ("error_genero", self.form_genero, validar_genero_empleado_requerido),
                ("error_fecha_nacimiento", self.form_fecha_nacimiento, lambda v: validar_fecha_nacimiento_empleado(v, requerida=True, edad_min=18)),
                ("error_telefono", self.form_telefono, validar_telefono_empleado_requerido),
            ],
            optional_validations=[
                ("error_email", self.form_email, validar_email),
                ("error_contacto_nombre", self.form_contacto_nombre, validar_contacto_emergencia_nombre),
                ("error_contacto_telefono", self.form_contacto_telefono, validar_contacto_emergencia_telefono),
                ("error_cuenta_bancaria", self.form_cuenta_bancaria, validar_cuenta_bancaria),
                ("error_banco", self.form_banco, validar_banco),
                ("error_clabe", self.form_clabe, validar_clabe),
            ],
        )
        if not self._validar_fecha_ingreso_form():
            es_valido = False
        return es_valido

    @staticmethod
    def _valor_switch_a_bool(value) -> bool:
        """Normaliza el valor de un switch de Reflex a bool."""
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() == "true"

    @staticmethod
    def _texto_seguro_modal_plaza(value) -> str:
        """Evita que valores callable se rendericen como `bound Method` en el modal."""
        if callable(value):
            return ""
        return str(value or "").strip()
