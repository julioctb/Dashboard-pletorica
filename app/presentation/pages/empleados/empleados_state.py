"""
Estado de Reflex para el módulo de Empleados.
Maneja el estado de la UI y las operaciones del módulo.

Refactorizado para usar:
- CRUDStateMixin para operaciones CRUD genéricas
- ui_helpers para opciones de enums
- BaseState.limpiar_formulario para limpieza de formularios
"""
import reflex as rx
from typing import List, Optional, Dict, Any
from datetime import date

from app.presentation.components.shared.auth_state import AuthState
from app.presentation.components.shared.crud_state_mixin import CRUDStateMixin
from app.core.ui_helpers import (
    FILTRO_TODOS,
    FILTRO_TODAS,
    opciones_desde_enum,
)
from app.services import empleado_service, empresa_service
from app.core.text_utils import formatear_fecha
from app.core.enums import EstatusEmpleado, GeneroEmpleado, MotivoBaja

from app.entities import (
    EmpleadoCreate,
    EmpleadoUpdate,
)

from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    BusinessRuleError,
)

from .empleados_validators import (
    validar_curp,
    validar_rfc,
    validar_nss,
    validar_nombre,
    validar_apellido_paterno,
    validar_email,
    validar_telefono,
    validar_motivo_restriccion,
)


class EmpleadosState(AuthState, CRUDStateMixin):
    """Estado para el módulo de Empleados"""

    # ========================
    # CONFIGURACIÓN DEL MIXIN
    # ========================
    _entidad_nombre: str = "Empleado"
    _modal_principal: str = "mostrar_modal_empleado"
    _campos_formulario: Dict[str, Any] = {
        "empresa_id": "",
        "curp": "",
        "rfc": "",
        "nss": "",
        "nombre": "",
        "apellido_paterno": "",
        "apellido_materno": "",
        "fecha_nacimiento": "",
        "genero": "",
        "telefono": "",
        "email": "",
        "direccion": "",
        "contacto_emergencia": "",
        "notas": "",
        "motivo_baja": "",
        "motivo_restriccion": "",
        "notas_restriccion": "",
        "motivo_liberacion": "",
        "notas_liberacion": "",
    }
    _campos_error: List[str] = [
        "curp", "rfc", "nss", "nombre", "apellido_paterno",
        "email", "telefono", "empresa_id"
    ]

    # ========================
    # ESTADO DE VISTA
    # ========================
    view_mode: str = "table"  # "table" o "cards"

    # ========================
    # ESTADO DE DATOS
    # ========================
    empleados: List[dict] = []
    empleado_seleccionado: Optional[dict] = None
    total_empleados: int = 0

    # Paginación
    pagina: int = 1
    por_pagina: int = 50
    hay_mas: bool = False
    cargando_mas: bool = False

    # Catálogos
    empresas: List[dict] = []

    # ========================
    # FILTROS
    # ========================
    filtro_empresa_id: str = FILTRO_TODAS  # String para el select
    filtro_estatus: str = FILTRO_TODOS
    # filtro_busqueda heredado de BaseState

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_empleado: bool = False
    mostrar_modal_detalle: bool = False
    mostrar_modal_baja: bool = False
    mostrar_modal_restriccion: bool = False
    mostrar_modal_liberacion: bool = False
    mostrar_modal_historial: bool = False
    es_edicion: bool = False
    pestaña_activa: str = "datos"

    # ========================
    # FORMULARIO
    # ========================
    empleado_id_edicion: int = 0  # ID del empleado en edición
    form_empresa_id: str = ""
    form_curp: str = ""
    form_rfc: str = ""
    form_nss: str = ""
    form_nombre: str = ""
    form_apellido_paterno: str = ""
    form_apellido_materno: str = ""
    form_fecha_nacimiento: str = ""
    form_genero: str = ""
    form_telefono: str = ""
    form_email: str = ""
    form_direccion: str = ""
    form_contacto_emergencia: str = ""
    form_notas: str = ""
    form_motivo_baja: str = ""

    # Restricciones
    form_motivo_restriccion: str = ""
    form_notas_restriccion: str = ""
    form_motivo_liberacion: str = ""
    form_notas_liberacion: str = ""

    # Datos - Historial de restricciones
    historial_restricciones: List[dict] = []

    # ========================
    # ERRORES DE VALIDACIÓN
    # ========================
    error_curp: str = ""
    error_rfc: str = ""
    error_nss: str = ""
    error_nombre: str = ""
    error_apellido_paterno: str = ""
    error_email: str = ""
    error_telefono: str = ""
    error_empresa_id: str = ""

    # ========================
    # SETTERS DE VISTA
    # ========================
    def set_view_table(self):
        self.view_mode = "table"

    def set_view_cards(self):
        self.view_mode = "cards"

    @rx.var
    def is_table_view(self) -> bool:
        return self.view_mode == "table"

    # ========================
    # SETTERS DE FILTROS
    # ========================
    def set_filtro_empresa_id(self, value: str):
        self.filtro_empresa_id = value if value else FILTRO_TODAS

    def set_filtro_estatus(self, value: str):
        self.filtro_estatus = value if value else FILTRO_TODOS

    async def on_busqueda_change(self, value: str):
        """Actualiza busqueda. 3+ caracteres consulta la base de datos."""
        self.filtro_busqueda = value
        if len(value) >= 3:
            self.pagina = 1
            self.hay_mas = False
            try:
                empresa_id = None
                if self.filtro_empresa_id and self.filtro_empresa_id not in ("", FILTRO_TODAS):
                    empresa_id = int(self.filtro_empresa_id)

                empleados = await empleado_service.buscar(
                    texto=value,
                    empresa_id=empresa_id,
                    limite=200
                )
                self.empleados = await self._convertir_a_dicts(empleados)
                self.total_empleados = len(self.empleados)
            except Exception:
                pass  # Mantener lista actual si falla la busqueda
        elif not value:
            self.pagina = 1
            await self._fetch_empleados()

    # ========================
    # SETTERS DE FORMULARIO
    # ========================
    def set_form_empresa_id(self, value: str):
        self.form_empresa_id = value if value else ""
        self.error_empresa_id = ""

    def set_form_curp(self, value: str):
        self.form_curp = value.upper() if value else ""

    def set_form_rfc(self, value: str):
        self.form_rfc = value.upper() if value else ""

    def set_form_nss(self, value: str):
        self.form_nss = value if value else ""

    def set_form_nombre(self, value: str):
        self.form_nombre = value.upper() if value else ""

    def set_form_apellido_paterno(self, value: str):
        self.form_apellido_paterno = value.upper() if value else ""

    def set_form_apellido_materno(self, value: str):
        self.form_apellido_materno = value.upper() if value else ""

    def set_form_fecha_nacimiento(self, value: str):
        self.form_fecha_nacimiento = value if value else ""

    def set_form_genero(self, value: str):
        self.form_genero = value if value else ""

    def set_form_telefono(self, value: str):
        self.form_telefono = value if value else ""

    def set_form_email(self, value: str):
        self.form_email = value.lower() if value else ""

    def set_form_direccion(self, value: str):
        self.form_direccion = value if value else ""

    def set_form_contacto_emergencia(self, value: str):
        self.form_contacto_emergencia = value if value else ""

    def set_form_notas(self, value: str):
        self.form_notas = value if value else ""

    def set_form_motivo_baja(self, value: str):
        self.form_motivo_baja = value if value else ""

    def set_form_motivo_restriccion(self, value: str):
        self.form_motivo_restriccion = value

    def set_form_notas_restriccion(self, value: str):
        self.form_notas_restriccion = value

    def set_form_motivo_liberacion(self, value: str):
        self.form_motivo_liberacion = value

    def set_form_notas_liberacion(self, value: str):
        self.form_notas_liberacion = value

    def set_pestaña_activa(self, value: str):
        self.pestaña_activa = value if value else "datos"

    # ========================
    # VALIDADORES ON_BLUR
    # ========================
    def validar_curp_blur(self):
        self.error_curp = validar_curp(self.form_curp)

    def validar_rfc_blur(self):
        self.error_rfc = validar_rfc(self.form_rfc)

    def validar_nss_blur(self):
        self.error_nss = validar_nss(self.form_nss)

    def validar_nombre_blur(self):
        self.error_nombre = validar_nombre(self.form_nombre)

    def validar_apellido_paterno_blur(self):
        self.error_apellido_paterno = validar_apellido_paterno(self.form_apellido_paterno)

    def validar_email_blur(self):
        self.error_email = validar_email(self.form_email)

    def validar_telefono_blur(self):
        self.error_telefono = validar_telefono(self.form_telefono)

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def opciones_empresas(self) -> List[dict]:
        """Opciones para el select de empresas"""
        return [
            {"value": str(e.get("id")), "label": e.get("nombre_comercial", "")}
            for e in self.empresas
        ]

    @rx.var
    def opciones_estatus(self) -> List[dict]:
        """Opciones para el select de estatus"""
        return opciones_desde_enum(EstatusEmpleado, incluir_todos=True)

    @rx.var
    def opciones_genero(self) -> List[dict]:
        """Opciones para el select de género"""
        return opciones_desde_enum(GeneroEmpleado)

    @rx.var
    def opciones_motivo_baja(self) -> List[dict]:
        """Opciones para el select de motivo de baja"""
        return opciones_desde_enum(MotivoBaja)

    @rx.var
    def empleados_filtrados(self) -> List[dict]:
        """Empleados filtrados por búsqueda local (adicional al filtro de BD)"""
        if not self.filtro_busqueda:
            return self.empleados

        termino = self.filtro_busqueda.lower()
        return [
            e for e in self.empleados
            if termino in e.get("nombre_completo", "").lower()
            or termino in e.get("curp", "").lower()
            or termino in e.get("clave", "").lower()
        ]

    @rx.var
    def tiene_empleados(self) -> bool:
        return len(self.empleados) > 0

    @rx.var
    def titulo_modal(self) -> str:
        return "Editar Empleado" if self.es_edicion else "Nuevo Empleado"

    @rx.var
    def empleado_esta_activo(self) -> bool:
        if not self.empleado_seleccionado:
            return False
        return self.empleado_seleccionado.get("estatus") == "ACTIVO"

    @rx.var
    def empleado_esta_inactivo(self) -> bool:
        if not self.empleado_seleccionado:
            return False
        return self.empleado_seleccionado.get("estatus") == "INACTIVO"

    @rx.var
    def empleado_esta_suspendido(self) -> bool:
        if not self.empleado_seleccionado:
            return False
        return self.empleado_seleccionado.get("estatus") == "SUSPENDIDO"

    @rx.var
    def empleado_es_editable(self) -> bool:
        """Retorna True si el empleado puede ser editado (activo o suspendido)"""
        if not self.empleado_seleccionado:
            return False
        estatus = self.empleado_seleccionado.get("estatus")
        return estatus in ("ACTIVO", "SUSPENDIDO")

    @rx.var
    def nombre_completo_seleccionado(self) -> str:
        if not self.empleado_seleccionado:
            return ""
        return self.empleado_seleccionado.get("nombre_completo", "")

    # ========================
    # COMPUTED VARS - RESTRICCIONES
    # ========================

    @rx.var
    def empleado_esta_restringido(self) -> bool:
        """Verifica si el empleado seleccionado esta restringido."""
        if not self.empleado_seleccionado:
            return False
        return self.empleado_seleccionado.get("is_restricted", False)

    @rx.var
    def puede_restringir(self) -> bool:
        """True si es admin y empleado NO esta restringido."""
        if not self.empleado_seleccionado:
            return False
        if not self.es_admin:
            return False
        return not self.empleado_seleccionado.get("is_restricted", False)

    @rx.var
    def puede_liberar(self) -> bool:
        """True si es admin y empleado SI esta restringido."""
        if not self.empleado_seleccionado:
            return False
        if not self.es_admin:
            return False
        return self.empleado_seleccionado.get("is_restricted", False)

    @rx.var
    def puede_guardar_restriccion(self) -> bool:
        """Valida si el formulario de restriccion es valido."""
        return len(self.form_motivo_restriccion.strip()) >= 10 and not self.saving

    @rx.var
    def puede_guardar_liberacion(self) -> bool:
        """Valida si el formulario de liberacion es valido."""
        return len(self.form_motivo_liberacion.strip()) >= 10 and not self.saving

    @rx.var
    def motivo_restriccion_actual(self) -> str:
        """Motivo de restriccion del empleado seleccionado."""
        if not self.empleado_seleccionado:
            return ""
        return self.empleado_seleccionado.get("restriction_reason", "") or ""

    @rx.var
    def fecha_restriccion_actual(self) -> str:
        """Fecha de restriccion formateada."""
        if not self.empleado_seleccionado:
            return ""
        fecha = self.empleado_seleccionado.get("restricted_at", "")
        if not fecha:
            return ""
        try:
            from datetime import datetime
            if isinstance(fecha, str):
                dt = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
                return dt.strftime("%d/%m/%Y %H:%M")
            return str(fecha)
        except Exception:
            return str(fecha)

    @rx.var
    def tiene_historial_restricciones(self) -> bool:
        """Indica si hay historial de restricciones."""
        return len(self.historial_restricciones) > 0

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_empleados(self):
        """Carga la lista de empleados con filtros (sin manejo de loading)."""
        try:
            # Determinar empresa_id para filtro
            empresa_id = None
            if self.filtro_empresa_id and self.filtro_empresa_id not in ("", FILTRO_TODAS):
                empresa_id = int(self.filtro_empresa_id)

            # Determinar estatus para filtro
            estatus = None
            incluir_inactivos = False
            if self.filtro_estatus == FILTRO_TODOS:
                incluir_inactivos = True
            elif self.filtro_estatus:
                estatus = self.filtro_estatus

            # Buscar empleados
            if self.filtro_busqueda and len(self.filtro_busqueda) >= 2:
                empleados = await empleado_service.buscar(
                    texto=self.filtro_busqueda,
                    empresa_id=empresa_id,
                    limite=200
                )
                self.hay_mas = False
            elif empresa_id:
                empleados = await empleado_service.obtener_por_empresa(
                    empresa_id=empresa_id,
                    incluir_inactivos=incluir_inactivos,
                    limite=self.por_pagina,
                    offset=0
                )
                self.hay_mas = len(empleados) >= self.por_pagina
            else:
                empleados = await empleado_service.obtener_todos(
                    incluir_inactivos=incluir_inactivos,
                    limite=self.por_pagina,
                    offset=0
                )
                self.hay_mas = len(empleados) >= self.por_pagina

            # Convertir a diccionarios para la UI
            self.empleados = await self._convertir_a_dicts(empleados)
            self.total_empleados = len(self.empleados)

        except Exception as e:
            self.manejar_error(e, "cargando empleados")
            self.empleados = []

    async def cargar_empresas(self):
        """Carga el catálogo de empresas para el select"""
        try:
            empresas = await empresa_service.obtener_todas(incluir_inactivas=False)
            self.empresas = [
                {
                    "id": e.id,
                    "nombre_comercial": e.nombre_comercial,
                    "codigo_corto": e.codigo_corto or "",
                }
                for e in empresas
                if e.puede_tener_empleados()  # Solo empresas de tipo NOMINA
            ]
        except Exception as e:
            self.manejar_error(e, "cargando empresas")
            self.empresas = []

    async def cargar_detalle(self, empleado_id: int):
        """Carga el detalle de un empleado"""
        self.loading = True
        try:
            empleado = await empleado_service.obtener_por_id(empleado_id)

            # Obtener nombre de empresa
            empresa_nombre = "Sin asignar"
            if empleado.empresa_id is not None:
                try:
                    empresa = await empresa_service.obtener_por_id(empleado.empresa_id)
                    empresa_nombre = empresa.nombre_comercial
                except NotFoundError:
                    empresa_nombre = "N/A"

            self.empleado_seleccionado = {
                "id": empleado.id,
                "clave": empleado.clave,
                "curp": empleado.curp,
                "nombre_completo": empleado.nombre_completo(),
                "nombre": empleado.nombre,
                "apellido_paterno": empleado.apellido_paterno,
                "apellido_materno": empleado.apellido_materno or "",
                "empresa_id": empleado.empresa_id,
                "empresa_nombre": empresa_nombre,
                "estatus": empleado.estatus,
                "fecha_ingreso": formatear_fecha(empleado.fecha_ingreso) if empleado.fecha_ingreso else "",
                "fecha_ingreso_iso": empleado.fecha_ingreso.isoformat() if empleado.fecha_ingreso else "",
                "telefono": empleado.telefono or "",
                "email": empleado.email or "",
                "rfc": empleado.rfc or "",
                "nss": empleado.nss or "",
                "fecha_nacimiento": formatear_fecha(empleado.fecha_nacimiento) if empleado.fecha_nacimiento else "",
                "fecha_nacimiento_iso": empleado.fecha_nacimiento.isoformat() if empleado.fecha_nacimiento else "",
                "genero": empleado.genero or "",
                "direccion": empleado.direccion or "",
                "contacto_emergencia": empleado.contacto_emergencia or "",
                "notas": empleado.notas or "",
                "fecha_baja": formatear_fecha(empleado.fecha_baja) if empleado.fecha_baja else "",
                "motivo_baja": empleado.motivo_baja or "",
                "antiguedad_anios": empleado.antiguedad_anios(),
                "edad": empleado.edad(),
                "is_restricted": empleado.is_restricted,
                "restriction_reason": empleado.restriction_reason or "",
                "restricted_at": empleado.restricted_at.isoformat() if empleado.restricted_at else "",
                "restricted_by": str(empleado.restricted_by) if empleado.restricted_by else "",
            }

        except NotFoundError:
            self.mostrar_mensaje("Empleado no encontrado", "error")
            self.empleado_seleccionado = None
        except Exception as e:
            self.manejar_error(e, "cargando detalle")
            self.empleado_seleccionado = None
        finally:
            self.loading = False

    # ========================
    # ACCIONES DE MODAL
    # ========================
    def abrir_modal_crear(self):
        """Abre el modal para crear un nuevo empleado"""
        self._limpiar_formulario()
        self.es_edicion = False
        self.mostrar_modal_empleado = True

    def abrir_modal_editar(self, empleado: dict):
        """Abre el modal para editar un empleado existente"""
        if not empleado or not isinstance(empleado, dict):
            return
        emp_id = empleado.get("id", 0)
        if not emp_id:
            return
        self._limpiar_formulario()
        self.es_edicion = True
        self.empleado_seleccionado = empleado
        self.empleado_id_edicion = emp_id
        self._llenar_formulario_desde_empleado(empleado)
        self.mostrar_modal_empleado = True

    def abrir_modal_editar_desde_detalle(self):
        """Abre el modal de edición usando el empleado_seleccionado actual"""
        if not self.empleado_seleccionado:
            return
        self._limpiar_formulario()
        self.es_edicion = True
        self.empleado_id_edicion = self.empleado_seleccionado.get("id", 0)  # Guardar ID
        self._llenar_formulario_desde_empleado(self.empleado_seleccionado)
        self.mostrar_modal_empleado = True

    def _llenar_formulario_desde_empleado(self, empleado: dict):
        """Llena el formulario con datos del empleado"""
        empresa_id = empleado.get("empresa_id")
        self.form_empresa_id = str(empresa_id) if empresa_id else ""
        self.form_curp = empleado.get("curp", "")
        self.form_rfc = empleado.get("rfc", "")
        self.form_nss = empleado.get("nss", "")
        self.form_nombre = empleado.get("nombre", "")
        self.form_apellido_paterno = empleado.get("apellido_paterno", "")
        self.form_apellido_materno = empleado.get("apellido_materno", "")
        self.form_fecha_nacimiento = empleado.get("fecha_nacimiento_iso", "") or empleado.get("fecha_nacimiento", "")
        self.form_genero = empleado.get("genero", "")
        self.form_telefono = empleado.get("telefono", "")
        self.form_email = empleado.get("email", "")
        self.form_direccion = empleado.get("direccion", "")
        self.form_contacto_emergencia = empleado.get("contacto_emergencia", "")
        self.form_notas = empleado.get("notas", "")

    def abrir_modal_detalle(self, empleado: dict):
        """Abre el modal de detalle de un empleado"""
        if not empleado or not isinstance(empleado, dict):
            return
        self.empleado_seleccionado = empleado
        self.pestaña_activa = "datos"
        self.mostrar_modal_detalle = True

    def abrir_modal_baja(self):
        """Abre el modal para dar de baja"""
        self.form_motivo_baja = ""
        self.mostrar_modal_baja = True

    def cerrar_modal_empleado(self):
        """Cierra el modal de empleado"""
        self.mostrar_modal_empleado = False
        self._limpiar_formulario()

    def cerrar_modal_detalle(self):
        """Cierra el modal de detalle"""
        self.mostrar_modal_detalle = False
        self.empleado_seleccionado = None

    def cerrar_modal_baja(self):
        """Cierra el modal de baja"""
        self.mostrar_modal_baja = False
        self.form_motivo_baja = ""

    # ========================
    # ACCIONES DE MODAL - RESTRICCIONES
    # ========================

    def abrir_modal_restriccion(self):
        """Abre el modal para restringir empleado."""
        if not self.empleado_seleccionado:
            return
        self.form_motivo_restriccion = ""
        self.form_notas_restriccion = ""
        self.mostrar_modal_restriccion = True

    def abrir_modal_restriccion_desde_lista(self, empleado: dict):
        """Abre modal de restriccion desde la lista (sin abrir detalle)."""
        if not empleado or not isinstance(empleado, dict):
            return
        self.empleado_seleccionado = empleado
        self.form_motivo_restriccion = ""
        self.form_notas_restriccion = ""
        self.mostrar_modal_restriccion = True

    def cerrar_modal_restriccion(self):
        """Cierra el modal de restriccion."""
        self.mostrar_modal_restriccion = False
        self.form_motivo_restriccion = ""
        self.form_notas_restriccion = ""

    def abrir_modal_liberacion(self):
        """Abre el modal para liberar restriccion."""
        if not self.empleado_seleccionado:
            return
        self.form_motivo_liberacion = ""
        self.form_notas_liberacion = ""
        self.mostrar_modal_liberacion = True

    def abrir_modal_liberacion_desde_lista(self, empleado: dict):
        """Abre modal de liberacion desde la lista (sin abrir detalle)."""
        if not empleado or not isinstance(empleado, dict):
            return
        self.empleado_seleccionado = empleado
        self.form_motivo_liberacion = ""
        self.form_notas_liberacion = ""
        self.mostrar_modal_liberacion = True

    def cerrar_modal_liberacion(self):
        """Cierra el modal de liberacion."""
        self.mostrar_modal_liberacion = False
        self.form_motivo_liberacion = ""
        self.form_notas_liberacion = ""

    async def abrir_modal_historial(self):
        """Abre el modal de historial y carga los datos."""
        if not self.empleado_seleccionado:
            return

        self.mostrar_modal_historial = True
        self.loading = True

        try:
            from uuid import UUID
            raw_id = str(self.usuario_actual.get('id', '')) if self.usuario_actual else ""
            admin_id = UUID(raw_id) if raw_id else None

            historial = await empleado_service.obtener_historial_restricciones(
                empleado_id=self.empleado_seleccionado["id"],
                admin_user_id=admin_id,
            )

            self.historial_restricciones = [
                {
                    "id": h.id,
                    "accion": h.accion,
                    "motivo": h.motivo,
                    "fecha": h.fecha.strftime("%d/%m/%Y %H:%M") if h.fecha else "",
                    "ejecutado_por_nombre": h.ejecutado_por_nombre,
                    "notas": h.notas or "",
                    "es_restriccion": h.accion == "RESTRICCION",
                }
                for h in historial
            ]

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            self.manejar_error(e, "cargando historial")
        finally:
            self.loading = False

    def cerrar_modal_historial(self):
        """Cierra el modal de historial."""
        self.mostrar_modal_historial = False
        self.historial_restricciones = []

    # ========================
    # OPERACIONES - RESTRICCIONES
    # ========================

    async def confirmar_restriccion(self):
        """Confirma la restriccion del empleado."""
        if not self.empleado_seleccionado:
            return rx.toast.error("No hay empleado seleccionado")

        error_motivo = validar_motivo_restriccion(self.form_motivo_restriccion)
        if error_motivo:
            return rx.toast.error(error_motivo)

        from uuid import UUID
        admin_id = UUID(self.id_usuario) if self.id_usuario else None
        if not admin_id:
            return rx.toast.error("No se pudo obtener el ID del usuario")

        empleado_id = self.empleado_seleccionado["id"]
        motivo = self.form_motivo_restriccion.strip()
        notas = self.form_notas_restriccion.strip() or None

        async def _on_exito():
            self.cerrar_modal_restriccion()
            self.cerrar_modal_detalle()
            await self._fetch_empleados()

        return await self.ejecutar_guardado(
            operacion=lambda: empleado_service.restringir_empleado(
                empleado_id=empleado_id,
                motivo=motivo,
                admin_user_id=admin_id,
                notas=notas,
            ),
            mensaje_exito="Empleado restringido correctamente",
            on_exito=_on_exito,
        )

    async def confirmar_liberacion(self):
        """Confirma la liberacion de la restriccion."""
        if not self.empleado_seleccionado:
            return rx.toast.error("No hay empleado seleccionado")

        error_motivo = validar_motivo_restriccion(self.form_motivo_liberacion)
        if error_motivo:
            return rx.toast.error(error_motivo)

        from uuid import UUID
        admin_id = UUID(self.id_usuario) if self.id_usuario else None
        if not admin_id:
            return rx.toast.error("No se pudo obtener el ID del usuario")

        empleado_id = self.empleado_seleccionado["id"]
        motivo = self.form_motivo_liberacion.strip()
        notas = self.form_notas_liberacion.strip() or None

        async def _on_exito():
            self.cerrar_modal_liberacion()
            self.cerrar_modal_detalle()
            await self._fetch_empleados()

        return await self.ejecutar_guardado(
            operacion=lambda: empleado_service.liberar_empleado(
                empleado_id=empleado_id,
                motivo=motivo,
                admin_user_id=admin_id,
                notas=notas,
            ),
            mensaje_exito="Restriccion liberada correctamente",
            on_exito=_on_exito,
        )

    # ========================
    # OPERACIONES CRUD
    # ========================
    async def guardar_empleado(self):
        """Guarda un empleado (crear o actualizar)"""
        # Validar campos obligatorios
        if not self._validar_formulario():
            return rx.toast.error("Por favor corrija los errores del formulario")

        # Validar que tenemos ID en modo edición
        if self.es_edicion and not self.empleado_id_edicion:
            return rx.toast.error("Error: No se encontró el ID del empleado a editar")

        self.saving = True
        try:
            if self.es_edicion:
                # Actualizar empleado existente
                empleado_update = EmpleadoUpdate(
                    empresa_id=self.parse_id(self.form_empresa_id),
                    rfc=self.form_rfc or None,
                    nss=self.form_nss or None,
                    nombre=self.form_nombre or None,
                    apellido_paterno=self.form_apellido_paterno or None,
                    apellido_materno=self.form_apellido_materno or None,
                    fecha_nacimiento=date.fromisoformat(self.form_fecha_nacimiento) if self.form_fecha_nacimiento else None,
                    genero=self.form_genero or None,
                    telefono=self.form_telefono or None,
                    email=self.form_email or None,
                    direccion=self.form_direccion or None,
                    contacto_emergencia=self.form_contacto_emergencia or None,
                    notas=self.form_notas or None,
                )

                await empleado_service.actualizar(
                    self.empleado_id_edicion,  # Usar ID guardado
                    empleado_update
                )

                self.cerrar_modal_empleado()
                await self._fetch_empleados()
                return rx.toast.success("Empleado actualizado correctamente")

            else:
                # Crear nuevo empleado
                empleado_create = EmpleadoCreate(
                    empresa_id=self.parse_id(self.form_empresa_id),
                    curp=self.form_curp,
                    rfc=self.form_rfc or None,
                    nss=self.form_nss or None,
                    nombre=self.form_nombre,
                    apellido_paterno=self.form_apellido_paterno,
                    apellido_materno=self.form_apellido_materno or None,
                    fecha_nacimiento=date.fromisoformat(self.form_fecha_nacimiento) if self.form_fecha_nacimiento else None,
                    genero=self.form_genero or None,
                    telefono=self.form_telefono or None,
                    email=self.form_email or None,
                    direccion=self.form_direccion or None,
                    contacto_emergencia=self.form_contacto_emergencia or None,
                    notas=self.form_notas or None,
                )

                empleado = await empleado_service.crear(empleado_create)

                self.cerrar_modal_empleado()
                await self._fetch_empleados()
                return rx.toast.success(f"Empleado {empleado.clave} creado correctamente")

        except DuplicateError as e:
            if "curp" in str(e).lower():
                self.error_curp = "Este CURP ya está registrado"
            return rx.toast.error(str(e))
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "guardando empleado")
        finally:
            self.saving = False

    async def dar_de_baja(self):
        """Da de baja al empleado seleccionado"""
        if not self.empleado_seleccionado:
            return rx.toast.error("No hay empleado seleccionado")

        empleado_id = self.empleado_seleccionado.get("id") if isinstance(self.empleado_seleccionado, dict) else None
        if not empleado_id:
            return rx.toast.error("Error: No se pudo obtener el ID del empleado")

        if not self.form_motivo_baja:
            return rx.toast.error("Debe seleccionar un motivo de baja")

        motivo = MotivoBaja(self.form_motivo_baja)

        async def _on_exito():
            self.cerrar_modal_baja()
            self.cerrar_modal_detalle()
            await self._fetch_empleados()

        return await self.ejecutar_guardado(
            operacion=lambda: empleado_service.dar_de_baja(
                empleado_id=empleado_id, motivo=motivo,
            ),
            mensaje_exito="Empleado dado de baja correctamente",
            on_exito=_on_exito,
        )

    async def reactivar_empleado(self):
        """Reactiva al empleado seleccionado"""
        if not self.empleado_seleccionado:
            return rx.toast.error("No hay empleado seleccionado")

        empleado_id = self.empleado_seleccionado.get("id") if isinstance(self.empleado_seleccionado, dict) else None
        if not empleado_id:
            return rx.toast.error("Error: No se pudo obtener el ID del empleado")

        async def _on_exito():
            self.cerrar_modal_detalle()
            await self._fetch_empleados()

        return await self.ejecutar_guardado(
            operacion=lambda: empleado_service.reactivar(empleado_id),
            mensaje_exito="Empleado reactivado correctamente",
            on_exito=_on_exito,
        )

    async def suspender_empleado(self):
        """Suspende al empleado seleccionado"""
        if not self.empleado_seleccionado:
            return rx.toast.error("No hay empleado seleccionado")

        empleado_id = self.empleado_seleccionado.get("id") if isinstance(self.empleado_seleccionado, dict) else None
        if not empleado_id:
            return rx.toast.error("Error: No se pudo obtener el ID del empleado")

        async def _on_exito():
            self.cerrar_modal_detalle()
            await self._fetch_empleados()

        return await self.ejecutar_guardado(
            operacion=lambda: empleado_service.suspender(empleado_id),
            mensaje_exito="Empleado suspendido correctamente",
            on_exito=_on_exito,
        )

    async def suspender_desde_lista(self, empleado_id: int):
        """Suspende un empleado desde la lista (sin modal de detalle)"""
        return await self.ejecutar_guardado(
            operacion=lambda: empleado_service.suspender(empleado_id),
            mensaje_exito="Empleado suspendido correctamente",
            on_exito=self.cargar_empleados,
        )

    async def reactivar_desde_lista(self, empleado_id: int):
        """Reactiva un empleado desde la lista (sin modal de detalle)"""
        return await self.ejecutar_guardado(
            operacion=lambda: empleado_service.reactivar(empleado_id),
            mensaje_exito="Empleado reactivado correctamente",
            on_exito=self.cargar_empleados,
        )

    async def cargar_mas(self):
        """Carga la siguiente pagina de empleados (ver mas)."""
        if not self.hay_mas:
            return

        self.cargando_mas = True
        try:
            self.pagina += 1
            offset = (self.pagina - 1) * self.por_pagina

            empresa_id = None
            if self.filtro_empresa_id and self.filtro_empresa_id not in ("", FILTRO_TODAS):
                empresa_id = int(self.filtro_empresa_id)

            incluir_inactivos = self.filtro_estatus == FILTRO_TODOS

            if empresa_id:
                nuevos = await empleado_service.obtener_por_empresa(
                    empresa_id=empresa_id,
                    incluir_inactivos=incluir_inactivos,
                    limite=self.por_pagina,
                    offset=offset
                )
            else:
                nuevos = await empleado_service.obtener_todos(
                    incluir_inactivos=incluir_inactivos,
                    limite=self.por_pagina,
                    offset=offset
                )

            self.hay_mas = len(nuevos) >= self.por_pagina

            nuevos_dicts = await self._convertir_a_dicts(nuevos)
            self.empleados = self.empleados + nuevos_dicts
            self.total_empleados = len(self.empleados)

        except Exception as e:
            self.manejar_error(e, "cargando más empleados")
            self.pagina -= 1
        finally:
            self.cargando_mas = False

    async def _convertir_a_dicts(self, empleados) -> list:
        """Convierte lista de Empleado a dicts para la UI."""
        empresas_cache = {}
        for emp in empleados:
            if emp.empresa_id is not None and emp.empresa_id not in empresas_cache:
                try:
                    empresa = await empresa_service.obtener_por_id(emp.empresa_id)
                    empresas_cache[emp.empresa_id] = empresa.nombre_comercial
                except NotFoundError:
                    empresas_cache[emp.empresa_id] = "N/A"

        return [
            {
                "id": emp.id,
                "clave": emp.clave,
                "curp": emp.curp,
                "nombre_completo": emp.nombre_completo(),
                "nombre": emp.nombre,
                "apellido_paterno": emp.apellido_paterno,
                "apellido_materno": emp.apellido_materno or "",
                "empresa_id": emp.empresa_id,
                "empresa_nombre": empresas_cache.get(emp.empresa_id, "N/A") if emp.empresa_id is not None else "Sin asignar",
                "estatus": emp.estatus,
                "fecha_ingreso": formatear_fecha(emp.fecha_ingreso) if emp.fecha_ingreso else "",
                "telefono": emp.telefono or "",
                "email": emp.email or "",
                "rfc": emp.rfc or "",
                "nss": emp.nss or "",
                "fecha_nacimiento": emp.fecha_nacimiento.isoformat() if emp.fecha_nacimiento else "",
                "genero": emp.genero or "",
                "direccion": emp.direccion or "",
                "contacto_emergencia": emp.contacto_emergencia or "",
                "notas": emp.notas or "",
                "fecha_baja": formatear_fecha(emp.fecha_baja) if emp.fecha_baja else "",
                "motivo_baja": emp.motivo_baja or "",
                "is_restricted": emp.is_restricted,
                "restriction_reason": emp.restriction_reason or "",
                "restricted_at": emp.restricted_at.isoformat() if emp.restricted_at else "",
                "restricted_by": str(emp.restricted_by) if emp.restricted_by else "",
            }
            for emp in empleados
        ]

    # ========================
    # FILTROS
    # ========================
    async def aplicar_filtros(self):
        """Aplica los filtros y recarga la lista"""
        self.pagina = 1
        async for _ in self._recargar_datos(self._fetch_empleados):
            yield

    async def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.filtro_busqueda = ""
        self.filtro_empresa_id = FILTRO_TODAS
        self.filtro_estatus = FILTRO_TODOS
        self.pagina = 1
        async for _ in self._recargar_datos(self._fetch_empleados):
            yield

    # ========================
    # VERIFICACIÓN DE CURP
    # ========================
    async def verificar_curp_disponible(self):
        """Verifica si el CURP está disponible (para nuevo empleado)"""
        if not self.form_curp or len(self.form_curp) != 18:
            return

        try:
            disponible = await empleado_service.validar_curp_disponible(self.form_curp)
            if not disponible:
                self.error_curp = "Este CURP ya está registrado en el sistema"
            else:
                self.error_curp = ""
        except Exception:
            pass  # Ignorar errores de red en validación en tiempo real

    # ========================
    # MÉTODOS PRIVADOS
    # ========================
    def _limpiar_formulario(self):
        """Limpia el formulario usando configuración del mixin"""
        self.empleado_id_edicion = 0
        self._limpiar_formulario_crud()  # Usa _campos_formulario y _campos_error

    def _validar_formulario(self) -> bool:
        """Valida el formulario completo. Retorna True si es válido."""
        self._limpiar_errores()
        es_valido = True

        # Empresa es opcional - no se valida

        # CURP obligatorio (solo en creación)
        if not self.es_edicion:
            error = validar_curp(self.form_curp)
            if error:
                self.error_curp = error
                es_valido = False

        # Nombre obligatorio
        error = validar_nombre(self.form_nombre)
        if error:
            self.error_nombre = error
            es_valido = False

        # Apellido paterno obligatorio
        error = validar_apellido_paterno(self.form_apellido_paterno)
        if error:
            self.error_apellido_paterno = error
            es_valido = False

        # Validaciones opcionales (solo si tienen valor)
        if self.form_rfc:
            error = validar_rfc(self.form_rfc)
            if error:
                self.error_rfc = error
                es_valido = False

        if self.form_nss:
            error = validar_nss(self.form_nss)
            if error:
                self.error_nss = error
                es_valido = False

        if self.form_email:
            error = validar_email(self.form_email)
            if error:
                self.error_email = error
                es_valido = False

        if self.form_telefono:
            error = validar_telefono(self.form_telefono)
            if error:
                self.error_telefono = error
                es_valido = False

        return es_valido

    # ========================
    # EVENTO ON_MOUNT
    # ========================
    async def on_mount(self):
        """Se ejecuta al montar la página"""
        async for _ in self._montar_pagina(
            self.cargar_empresas,
            self._fetch_empleados,
        ):
            yield
