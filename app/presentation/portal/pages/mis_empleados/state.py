"""
State para la pagina Mis Empleados del portal.
"""
import logging
from datetime import date, datetime
from typing import List

import reflex as rx

from app.core.text_utils import formatear_fecha
from app.core.enums import GeneroEmpleado
from app.presentation.components.shared import (
    EMPLOYEE_BULK_UPLOAD_ID,
    EmployeeBulkUploadStateMixin,
)
from app.presentation.portal.state.portal_state import PortalState
from app.presentation.components.shared.employee_form_state_mixin import EmployeeFormStateMixin
from app.services import cuenta_bancaria_historial_service, empleado_service
from app.entities import EmpleadoCreate, EmpleadoUpdate
from app.core.exceptions import DuplicateError, BusinessRuleError, NotFoundError
from app.core.ui_helpers import opciones_desde_enum, rango_paginacion
from app.core.validation import (
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
)

from app.presentation.pages.empleados.empleados_validators import (
    normalizar_banco,
    validar_banco,
    validar_clabe,
    validar_cuenta_bancaria,
    validar_curp,
    validar_nombre,
    validar_apellido_paterno,
    validar_email,
)


# =============================================================================
# STATE
# =============================================================================

logger = logging.getLogger(__name__)

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
    ]

    empleados: List[dict] = []
    total_empleados_lista: int = 0

    # Filtros
    filtro_busqueda_emp: str = ""
    filtro_estatus_emp: str = "ACTIVO"
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

    # ========================
    # DETALLE DE EMPLEADO
    # ========================
    mostrar_modal_detalle: bool = False
    mostrar_modal_historial_bancario: bool = False
    loading_detalle_empleado: bool = False
    empleado_detalle: dict = {}
    historial_bancario: List[dict] = []

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

    # ========================
    # SETTERS DE FILTROS
    # ========================
    def set_filtro_busqueda_emp(self, value: str):
        self.filtro_busqueda_emp = value
        self.pagina = 1

    def set_filtro_estatus_emp(self, value: str):
        self.filtro_estatus_emp = value
        self.pagina = 1

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

    def set_form_fecha_nacimiento(self, value: str):
        self._set_form_plain_field("form_fecha_nacimiento", value)

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

    def set_form_motivo_baja(self, value: str):
        self._set_form_plain_field("form_motivo_baja", value)
        self.error_motivo_baja = ""

    def set_form_fecha_efectiva_baja(self, value: str):
        self._set_form_plain_field("form_fecha_efectiva_baja", value)
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

    @rx.var
    def empleados_filtrados(self) -> List[dict]:
        """Filtra empleados por texto de busqueda."""
        if not self.filtro_busqueda_emp:
            return self.empleados
        termino = self.filtro_busqueda_emp.lower()
        return [
            e for e in self.empleados
            if termino in (e.get("nombre_completo") or "").lower()
            or termino in (e.get("clave") or "").lower()
            or termino in (e.get("curp") or "").lower()
        ]

    @rx.var
    def total_empleados_filtrados(self) -> int:
        """Total visible en la tabla tras aplicar la búsqueda local."""
        return len(self.empleados_filtrados)

    @rx.var
    def total_paginas_empleados(self) -> int:
        """Total de páginas del listado actual."""
        return self.calcular_total_paginas(
            self.total_empleados_filtrados,
            self.por_pagina,
        )

    @rx.var
    def pagina_empleados_actual(self) -> int:
        """Página actual acotada al rango válido."""
        if self.pagina < 1:
            return 1
        if self.pagina > self.total_paginas_empleados:
            return self.total_paginas_empleados
        return self.pagina

    @rx.var
    def empleados_paginados(self) -> List[dict]:
        """Slice visible de empleados para la página actual."""
        inicio = (self.pagina_empleados_actual - 1) * self.por_pagina
        fin = inicio + self.por_pagina
        return self.empleados_filtrados[inicio:fin]

    @rx.var
    def paginas_visibles_empleados(self) -> List[int]:
        """Rango de páginas visibles para el paginador."""
        return rango_paginacion(
            self.pagina_empleados_actual,
            self.total_paginas_empleados,
            visible=5,
        )

    @rx.var
    def resumen_paginacion_empleados(self) -> str:
        """Texto resumen del rango mostrado en la tabla."""
        total = self.total_empleados_filtrados
        if total <= 0:
            return "Sin empleados registrados"

        inicio = ((self.pagina_empleados_actual - 1) * self.por_pagina) + 1
        fin = min(
            inicio + len(self.empleados_paginados) - 1,
            total,
        )
        return f"Mostrando {inicio}-{fin} de {total} empleado(s)"

    @rx.var
    def nombre_empleado_baja(self) -> str:
        """Nombre del empleado seleccionado para baja."""
        emp = self.empleado_baja_seleccionado
        if not emp:
            return ""
        return str(emp.get("nombre_completo", "") or "")

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
    def detalle_expediente_href(self) -> str:
        """URL del expediente del empleado visible en el modal de detalle."""
        empleado_id = self.empleado_detalle.get("id")
        if not empleado_id:
            return ""
        return f"/portal/empleados/expedientes?empleado_id={empleado_id}"

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
        estatus = str(self.empleado_detalle.get("estatus", "") or "")
        is_restricted = bool(self.empleado_detalle.get("is_restricted", False))
        return estatus == "ACTIVO" and not is_restricted

    @rx.var
    def puede_dar_baja_detalle(self) -> bool:
        """Permite dar de baja desde el modal de detalle."""
        return str(self.empleado_detalle.get("estatus", "") or "") == "ACTIVO"

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_empleados(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.mostrar_seccion_rrhh or not self.puede_gestionar_personal:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_empleados):
            yield
        if self._query_solicita_alta_masiva():
            self.abrir_panel_alta_masiva()

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_empleados(self):
        """Carga empleados de la empresa del usuario (sin manejo de loading)."""
        if not self.id_empresa_actual:
            return

        self.empleados = await self.cargar_y_asignar_lista(
            "empleados",
            lambda: empleado_service.obtener_resumen_por_empresa(
                empresa_id=self.id_empresa_actual,
                incluir_inactivos=self.filtro_estatus_emp != "ACTIVO",
                limite=200,
            ),
            contexto_error="cargando empleados",
        )
        self.total_empleados_lista = len(self.empleados)
        self._ajustar_pagina_empleados()

    async def cargar_empleados(self):
        """Recarga empleados con skeleton (filtros)."""
        async for _ in self._recargar_datos(self._fetch_empleados):
            yield

    async def aplicar_filtros_emp(self):
        async for _ in self.cargar_empleados():
            yield

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
    def ver_expediente(self, empleado: dict):
        """Navega al detalle de expediente del empleado en la pagina dedicada."""
        if not self.es_rrhh or not isinstance(empleado, dict):
            return

        empleado_id = empleado.get("id")
        if not empleado_id:
            return

        return rx.redirect(f"/portal/empleados/expedientes?empleado_id={empleado_id}")

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
        self.empleado_detalle = {}
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
                    "fecha_nacimiento": date.fromisoformat(self.form_fecha_nacimiento),
                    "genero": self.form_genero,
                    "telefono": self.form_telefono,
                }
            )
            empleado_create = EmpleadoCreate(**payload)

            empleado = await empleado_service.crear(empleado_create)
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
            }
        )

        self.mostrar_modal_empleado = True

    async def actualizar_empleado(self):
        """Actualiza un empleado existente."""
        if not self._validar_formulario():
            return rx.toast.error("Por favor corrija los errores del formulario")

        self.saving = True
        try:
            snapshot_bancario_original = self._normalizar_snapshot_bancario(
                self.snapshot_bancario_base_edicion
            )
            snapshot_bancario_nuevo = self._snapshot_bancario_form()
            empleado_update = EmpleadoUpdate(**self._payload_base_empleado())

            empleado = await empleado_service.actualizar(self.empleado_editando_id, empleado_update)
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

        from app.services.baja_service import baja_service
        from app.entities.baja_empleado import BajaEmpleadoCreate
        from app.core.enums import MotivoBaja

        fecha_efectiva = date.today()
        if self.form_fecha_efectiva_baja:
            try:
                fecha_efectiva = date.fromisoformat(self.form_fecha_efectiva_baja)
            except ValueError:
                self.error_fecha_efectiva_baja = "Fecha efectiva inválida"
                yield rx.toast.error("Fecha efectiva inválida")
                return

        registrado_por = self.obtener_uuid_usuario_actual()

        self.saving = True
        try:
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
            from app.entities.cuenta_bancaria_historial import CuentaBancariaHistorialCreate

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
        if not valor:
            return ""
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M")
        if isinstance(valor, date):
            return formatear_fecha(valor)
        if isinstance(valor, str):
            try:
                valor_dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
                return valor_dt.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                return valor
        return str(valor)

    @staticmethod
    def _detalle_empleado_placeholder(resumen: dict) -> dict:
        """Construye un placeholder ligero mientras carga el detalle completo."""
        return {
            "id": resumen.get("id"),
            "empresa_id": resumen.get("empresa_id"),
            "clave": resumen.get("clave", "") or "",
            "nombre_completo": resumen.get("nombre_completo", "") or "",
            "estatus": resumen.get("estatus", "") or "",
            "telefono": resumen.get("telefono", "") or "",
            "email": resumen.get("email", "") or "",
            "is_restricted": bool(resumen.get("is_restricted", False)),
            "documentos_aprobados_expediente": int(
                resumen.get("documentos_aprobados_expediente", 0) or 0
            ),
            "documentos_requeridos_expediente": int(
                resumen.get("documentos_requeridos_expediente", 0) or 0
            ),
        }

    def _serializar_empleado_detalle_modal(self, empleado, resumen: dict) -> dict:
        """Normaliza el detalle del empleado a un payload seguro para Reflex."""
        contacto_nombre, contacto_telefono, contacto_parentesco = self._split_contacto_emergencia(
            empleado.contacto_emergencia
        )
        return {
            "id": empleado.id,
            "empresa_id": empleado.empresa_id,
            "user_id": str(empleado.user_id) if empleado.user_id else "",
            "clave": empleado.clave,
            "nombre_completo": empleado.nombre_completo(),
            "estatus": str(empleado.estatus or ""),
            "is_restricted": bool(empleado.is_restricted),
            "curp": empleado.curp or "",
            "rfc": empleado.rfc or "",
            "nss": empleado.nss or "",
            "telefono": empleado.telefono or "",
            "email": empleado.email or "",
            "direccion": empleado.direccion or "",
            "notas": empleado.notas or "",
            "fecha_ingreso": formatear_fecha(empleado.fecha_ingreso) if empleado.fecha_ingreso else "",
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
        }

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
                "editar_datos_bancarios": False,
                "snapshot_bancario_base_edicion": {},
            },
        )

    def _limpiar_errores(self):
        """Limpia los errores de validacion."""
        self.limpiar_errores_campos(self._campos_error_formulario)

    def _validar_formulario(self) -> bool:
        """Valida el formulario completo. Retorna True si es valido."""
        return self._validar_formulario_empleado_compartido(
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
