"""
Pagina Mis Empleados del portal de cliente.

Muestra la lista de empleados de la empresa.
Permite busqueda, filtro por estatus y alta de nuevos empleados.
"""
import reflex as rx
from datetime import date
from typing import List

from app.presentation.portal.state.portal_state import PortalState
from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.components.ui import skeleton_tabla
from app.presentation.theme import Colors, Typography
from app.services import empleado_service
from app.entities import EmpleadoCreate, EmpleadoUpdate
from app.core.exceptions import DatabaseError, DuplicateError, BusinessRuleError, NotFoundError
from app.core.validation import (
    # Patrones regex
    CURP_PATTERN,
    RFC_PERSONA_PATTERN,
    NSS_PATTERN,
    EMAIL_PATTERN,
    TELEFONO_PATTERN,
    # Constantes de longitud
    CURP_LEN,
    RFC_PERSONA_LEN,
    NSS_LEN,
    NOMBRE_EMPLEADO_MIN,
    NOMBRE_EMPLEADO_MAX,
    APELLIDO_MIN,
    APELLIDO_MAX,
    EMAIL_MAX,
    TELEFONO_DIGITOS,
    NOMBRE_CONTACTO_MAX,
    # Validadores comunes
    validar_requerido,
    validar_patron,
    validar_longitud,
    validar_texto_requerido,
    validar_texto_opcional,
    validar_select_requerido,
    validar_fecha_no_futura,
)
import re


# =============================================================================
# VALIDADORES (usan patrones y constantes centralizados de app.core.validation)
# =============================================================================

def _validar_curp(curp: str) -> str:
    """Valida CURP (obligatorio, 18 caracteres, patron CURP_PATTERN)."""
    error = validar_requerido(curp, "CURP")
    if error:
        return error
    curp_limpio = curp.strip().upper()
    error = validar_longitud(curp_limpio, min_len=CURP_LEN, max_len=CURP_LEN, nombre_campo="CURP")
    if error:
        return error
    return validar_patron(curp_limpio, CURP_PATTERN, "CURP con formato invalido")


def _validar_nombre(nombre: str) -> str:
    """Valida nombre (obligatorio, NOMBRE_EMPLEADO_MIN/MAX)."""
    return validar_texto_requerido(
        nombre, "nombre",
        min_length=NOMBRE_EMPLEADO_MIN,
        max_length=NOMBRE_EMPLEADO_MAX,
    )


def _validar_apellido_paterno(apellido: str) -> str:
    """Valida apellido paterno (obligatorio, APELLIDO_MIN/MAX)."""
    return validar_texto_requerido(
        apellido, "apellido paterno",
        min_length=APELLIDO_MIN,
        max_length=APELLIDO_MAX,
    )


def _validar_apellido_materno(apellido: str) -> str:
    """Valida apellido materno (obligatorio en portal, APELLIDO_MIN/MAX)."""
    return validar_texto_requerido(
        apellido, "apellido materno",
        min_length=APELLIDO_MIN,
        max_length=APELLIDO_MAX,
    )


def _validar_rfc_requerido(rfc: str) -> str:
    """Valida RFC persona fisica (obligatorio, RFC_PERSONA_LEN, RFC_PERSONA_PATTERN)."""
    error = validar_requerido(rfc, "RFC")
    if error:
        return error
    rfc_limpio = rfc.strip().upper()
    error = validar_longitud(rfc_limpio, min_len=RFC_PERSONA_LEN, max_len=RFC_PERSONA_LEN, nombre_campo="RFC")
    if error:
        return error
    return validar_patron(rfc_limpio, RFC_PERSONA_PATTERN, "RFC con formato invalido")


def _validar_nss_requerido(nss: str) -> str:
    """Valida NSS (obligatorio, NSS_LEN, NSS_PATTERN)."""
    error = validar_requerido(nss, "NSS")
    if error:
        return error
    nss_limpio = nss.strip()
    error = validar_longitud(nss_limpio, min_len=NSS_LEN, max_len=NSS_LEN, nombre_campo="NSS")
    if error:
        return error
    return validar_patron(nss_limpio, NSS_PATTERN, "NSS debe contener solo numeros")


def _validar_telefono_requerido(telefono: str) -> str:
    """Valida telefono (obligatorio, TELEFONO_DIGITOS, TELEFONO_PATTERN)."""
    error = validar_requerido(telefono, "Telefono")
    if error:
        return error
    telefono_limpio = re.sub(r'[^0-9]', '', telefono)
    if not re.match(TELEFONO_PATTERN, telefono_limpio):
        return f"Telefono debe tener {TELEFONO_DIGITOS} digitos (tiene {len(telefono_limpio)})"
    return ""


def _validar_email_opcional(email: str) -> str:
    """Valida email (opcional, EMAIL_MAX, EMAIL_PATTERN)."""
    if not email:
        return ""
    email_limpio = email.strip().lower()
    error = validar_longitud(email_limpio, max_len=EMAIL_MAX, nombre_campo="Email")
    if error:
        return error
    return validar_patron(email_limpio, EMAIL_PATTERN, "Email con formato invalido")


def _validar_genero(genero: str) -> str:
    """Valida genero (obligatorio, validar_select_requerido)."""
    return validar_select_requerido(genero, "genero")


def _validar_fecha_nacimiento(fecha: str) -> str:
    """Valida fecha de nacimiento (obligatoria, validar_fecha_no_futura + 18 anios)."""
    error = validar_fecha_no_futura(fecha, "fecha de nacimiento")
    if error:
        return error
    fecha_obj = date.fromisoformat(fecha)
    hoy = date.today()
    edad = hoy.year - fecha_obj.year
    if (hoy.month, hoy.day) < (fecha_obj.month, fecha_obj.day):
        edad -= 1
    if edad < 18:
        return "El empleado debe tener al menos 18 anios"
    if edad > 100:
        return "Fecha de nacimiento no parece valida"
    return ""


def _validar_contacto_nombre(nombre: str) -> str:
    """Valida nombre del contacto de emergencia (opcional, NOMBRE_CONTACTO_MAX)."""
    return validar_texto_opcional(nombre, "nombre del contacto", max_length=NOMBRE_CONTACTO_MAX)


def _validar_contacto_telefono(telefono: str) -> str:
    """Valida telefono del contacto de emergencia (opcional, TELEFONO_PATTERN)."""
    if not telefono:
        return ""
    telefono_limpio = re.sub(r'[^0-9]', '', telefono)
    if not re.match(TELEFONO_PATTERN, telefono_limpio):
        return f"Telefono debe tener {TELEFONO_DIGITOS} digitos (tiene {len(telefono_limpio)})"
    return ""


# =============================================================================
# STATE
# =============================================================================

class MisEmpleadosState(PortalState):
    """State para la lista de empleados del portal."""

    empleados: List[dict] = []
    total_empleados_lista: int = 0

    # Filtros
    filtro_busqueda_emp: str = ""
    filtro_estatus_emp: str = "ACTIVO"

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
    form_notas: str = ""

    # Contacto de emergencia (3 campos)
    form_contacto_nombre: str = ""
    form_contacto_telefono: str = ""
    form_contacto_parentesco: str = ""

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

    # ========================
    # SETTERS DE FILTROS
    # ========================
    def set_filtro_busqueda_emp(self, value: str):
        self.filtro_busqueda_emp = value

    def set_filtro_estatus_emp(self, value: str):
        self.filtro_estatus_emp = value

    # ========================
    # SETTERS DE FORMULARIO
    # ========================
    def set_form_curp(self, value: str):
        self.form_curp = value.upper() if value else ""

    def set_form_nombre(self, value: str):
        self.form_nombre = value.upper() if value else ""

    def set_form_apellido_paterno(self, value: str):
        self.form_apellido_paterno = value.upper() if value else ""

    def set_form_apellido_materno(self, value: str):
        self.form_apellido_materno = value.upper() if value else ""

    def set_form_rfc(self, value: str):
        self.form_rfc = value.upper() if value else ""

    def set_form_nss(self, value: str):
        self.form_nss = value if value else ""

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

    def set_form_notas(self, value: str):
        self.form_notas = value if value else ""

    def set_form_contacto_nombre(self, value: str):
        self.form_contacto_nombre = value if value else ""

    def set_form_contacto_telefono(self, value: str):
        self.form_contacto_telefono = value if value else ""

    def set_form_contacto_parentesco(self, value: str):
        self.form_contacto_parentesco = value if value else ""

    # ========================
    # VALIDADORES ON_BLUR
    # ========================
    def validar_curp_blur(self):
        self.error_curp = _validar_curp(self.form_curp)

    def validar_nombre_blur(self):
        self.error_nombre = _validar_nombre(self.form_nombre)

    def validar_apellido_paterno_blur(self):
        self.error_apellido_paterno = _validar_apellido_paterno(self.form_apellido_paterno)

    def validar_apellido_materno_blur(self):
        self.error_apellido_materno = _validar_apellido_materno(self.form_apellido_materno)

    def validar_rfc_blur(self):
        self.error_rfc = _validar_rfc_requerido(self.form_rfc)

    def validar_nss_blur(self):
        self.error_nss = _validar_nss_requerido(self.form_nss)

    def validar_fecha_nacimiento_blur(self):
        self.error_fecha_nacimiento = _validar_fecha_nacimiento(self.form_fecha_nacimiento)

    def validar_genero_blur(self):
        self.error_genero = _validar_genero(self.form_genero)

    def validar_email_blur(self):
        self.error_email = _validar_email_opcional(self.form_email)

    def validar_telefono_blur(self):
        self.error_telefono = _validar_telefono_requerido(self.form_telefono)

    def validar_contacto_nombre_blur(self):
        self.error_contacto_nombre = _validar_contacto_nombre(self.form_contacto_nombre)

    def validar_contacto_telefono_blur(self):
        self.error_contacto_telefono = _validar_contacto_telefono(self.form_contacto_telefono)

    def validar_contacto_parentesco_blur(self):
        self.error_contacto_parentesco = _validar_contacto_parentesco(self.form_contacto_parentesco)

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def opciones_genero(self) -> List[dict]:
        """Opciones para el select de genero."""
        return [
            {"value": "MASCULINO", "label": "Masculino"},
            {"value": "FEMENINO", "label": "Femenino"},
        ]

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

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_empleados(self):
        resultado = await self.on_mount_portal()
        if resultado:
            return resultado
        await self.cargar_empleados()

    # ========================
    # CARGA DE DATOS
    # ========================
    async def cargar_empleados(self):
        """Carga empleados de la empresa del usuario."""
        if not self.id_empresa_actual:
            return

        self.loading = True
        try:
            incluir_inactivos = self.filtro_estatus_emp != "ACTIVO"
            empleados = await empleado_service.obtener_resumen_por_empresa(
                empresa_id=self.id_empresa_actual,
                incluir_inactivos=incluir_inactivos,
                limite=200,
            )
            self.empleados = [e.model_dump(mode='json') if hasattr(e, 'model_dump') else e for e in empleados]
            self.total_empleados_lista = len(self.empleados)
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando empleados: {e}", "error")
            self.empleados = []
            self.total_empleados_lista = 0
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.empleados = []
            self.total_empleados_lista = 0
        finally:
            self.loading = False

    async def aplicar_filtros_emp(self):
        await self.cargar_empleados()

    # ========================
    # ACCIONES DE MODAL
    # ========================
    def abrir_modal_crear(self):
        """Abre el modal para crear un nuevo empleado."""
        self._limpiar_formulario()
        self.mostrar_modal_empleado = True

    def cerrar_modal_empleado(self):
        """Cierra el modal de empleado."""
        self.mostrar_modal_empleado = False
        self._limpiar_formulario()

    # ========================
    # CREAR EMPLEADO
    # ========================
    async def crear_empleado(self):
        """Crea un nuevo empleado asignado a la empresa del portal."""
        if not self._validar_formulario():
            return rx.toast.error("Por favor corrija los errores del formulario")

        self.saving = True
        try:
            # Combinar contacto de emergencia (opcional)
            contacto_emergencia = None
            partes_contacto = [
                self.form_contacto_nombre.strip(),
                self.form_contacto_telefono.strip(),
                self.form_contacto_parentesco,
            ]
            if any(partes_contacto):
                contacto_emergencia = " / ".join(p for p in partes_contacto if p)

            empleado_create = EmpleadoCreate(
                empresa_id=self.id_empresa_actual,
                curp=self.form_curp,
                rfc=self.form_rfc,
                nss=self.form_nss,
                nombre=self.form_nombre,
                apellido_paterno=self.form_apellido_paterno,
                apellido_materno=self.form_apellido_materno,
                fecha_nacimiento=date.fromisoformat(self.form_fecha_nacimiento),
                genero=self.form_genero,
                telefono=self.form_telefono,
                email=self.form_email or None,
                direccion=self.form_direccion or None,
                contacto_emergencia=contacto_emergencia,
                notas=self.form_notas or None,
            )

            empleado = await empleado_service.crear(empleado_create)

            self.cerrar_modal_empleado()
            await self.cargar_empleados()
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
        self.form_curp = empleado.curp or ""
        self.form_nombre = empleado.nombre or ""
        self.form_apellido_paterno = empleado.apellido_paterno or ""
        self.form_apellido_materno = empleado.apellido_materno or ""
        self.form_rfc = empleado.rfc or ""
        self.form_nss = empleado.nss or ""
        self.form_fecha_nacimiento = str(empleado.fecha_nacimiento) if empleado.fecha_nacimiento else ""
        self.form_genero = empleado.genero or ""
        self.form_telefono = empleado.telefono or ""
        self.form_email = empleado.email or ""
        self.form_direccion = empleado.direccion or ""
        self.form_notas = empleado.notas or ""

        # Descomponer contacto_emergencia
        if empleado.contacto_emergencia:
            partes = empleado.contacto_emergencia.split(" / ")
            self.form_contacto_nombre = partes[0] if len(partes) > 0 else ""
            self.form_contacto_telefono = partes[1] if len(partes) > 1 else ""
            self.form_contacto_parentesco = partes[2] if len(partes) > 2 else ""
        else:
            self.form_contacto_nombre = ""
            self.form_contacto_telefono = ""
            self.form_contacto_parentesco = ""

        self.mostrar_modal_empleado = True

    async def actualizar_empleado(self):
        """Actualiza un empleado existente."""
        if not self._validar_formulario():
            return rx.toast.error("Por favor corrija los errores del formulario")

        self.saving = True
        try:
            # Combinar contacto de emergencia (opcional)
            contacto_emergencia = None
            partes_contacto = [
                self.form_contacto_nombre.strip(),
                self.form_contacto_telefono.strip(),
                self.form_contacto_parentesco,
            ]
            if any(partes_contacto):
                contacto_emergencia = " / ".join(p for p in partes_contacto if p)

            empleado_update = EmpleadoUpdate(
                nombre=self.form_nombre,
                apellido_paterno=self.form_apellido_paterno,
                apellido_materno=self.form_apellido_materno or None,
                rfc=self.form_rfc or None,
                nss=self.form_nss or None,
                fecha_nacimiento=date.fromisoformat(self.form_fecha_nacimiento) if self.form_fecha_nacimiento else None,
                genero=self.form_genero or None,
                telefono=self.form_telefono or None,
                email=self.form_email or None,
                direccion=self.form_direccion or None,
                contacto_emergencia=contacto_emergencia,
                notas=self.form_notas or None,
            )

            empleado = await empleado_service.actualizar(self.empleado_editando_id, empleado_update)

            self.cerrar_modal_empleado()
            await self.cargar_empleados()
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

    # ========================
    # METODOS PRIVADOS
    # ========================
    def _limpiar_formulario(self):
        """Limpia el formulario."""
        self.es_edicion = False
        self.empleado_editando_id = 0
        self.form_curp = ""
        self.form_nombre = ""
        self.form_apellido_paterno = ""
        self.form_apellido_materno = ""
        self.form_rfc = ""
        self.form_nss = ""
        self.form_fecha_nacimiento = ""
        self.form_genero = ""
        self.form_telefono = ""
        self.form_email = ""
        self.form_direccion = ""
        self.form_notas = ""
        self.form_contacto_nombre = ""
        self.form_contacto_telefono = ""
        self.form_contacto_parentesco = ""
        self._limpiar_errores()

    def _limpiar_errores(self):
        """Limpia los errores de validacion."""
        self.error_curp = ""
        self.error_nombre = ""
        self.error_apellido_paterno = ""
        self.error_apellido_materno = ""
        self.error_rfc = ""
        self.error_nss = ""
        self.error_genero = ""
        self.error_fecha_nacimiento = ""
        self.error_email = ""
        self.error_telefono = ""
        self.error_contacto_nombre = ""
        self.error_contacto_telefono = ""
        self.error_contacto_parentesco = ""

    def _validar_formulario(self) -> bool:
        """Valida el formulario completo. Retorna True si es valido."""
        self._limpiar_errores()
        es_valido = True

        # CURP obligatorio (solo en creacion, inmutable en edicion)
        if not self.es_edicion:
            error = _validar_curp(self.form_curp)
            if error:
                self.error_curp = error
                es_valido = False

        # Nombre obligatorio
        error = _validar_nombre(self.form_nombre)
        if error:
            self.error_nombre = error
            es_valido = False

        # Apellido paterno obligatorio
        error = _validar_apellido_paterno(self.form_apellido_paterno)
        if error:
            self.error_apellido_paterno = error
            es_valido = False

        # Apellido materno obligatorio
        error = _validar_apellido_materno(self.form_apellido_materno)
        if error:
            self.error_apellido_materno = error
            es_valido = False

        # RFC obligatorio
        error = _validar_rfc_requerido(self.form_rfc)
        if error:
            self.error_rfc = error
            es_valido = False

        # NSS obligatorio
        error = _validar_nss_requerido(self.form_nss)
        if error:
            self.error_nss = error
            es_valido = False

        # Genero obligatorio
        error = _validar_genero(self.form_genero)
        if error:
            self.error_genero = error
            es_valido = False

        # Fecha de nacimiento obligatoria (18+ anios)
        error = _validar_fecha_nacimiento(self.form_fecha_nacimiento)
        if error:
            self.error_fecha_nacimiento = error
            es_valido = False

        # Telefono obligatorio
        error = _validar_telefono_requerido(self.form_telefono)
        if error:
            self.error_telefono = error
            es_valido = False

        # Email opcional (solo si tiene valor)
        if self.form_email:
            error = _validar_email_opcional(self.form_email)
            if error:
                self.error_email = error
                es_valido = False

        # Contacto de emergencia opcional (validar formato si tienen valor)
        if self.form_contacto_nombre:
            error = _validar_contacto_nombre(self.form_contacto_nombre)
            if error:
                self.error_contacto_nombre = error
                es_valido = False

        if self.form_contacto_telefono:
            error = _validar_contacto_telefono(self.form_contacto_telefono)
            if error:
                self.error_contacto_telefono = error
                es_valido = False

        return es_valido


# =============================================================================
# COMPONENTES
# =============================================================================

def _badge_estatus(estatus: str) -> rx.Component:
    """Badge de estatus del empleado."""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("Activo", color_scheme="green", variant="soft", size="1")),
        ("INACTIVO", rx.badge("Inactivo", color_scheme="red", variant="soft", size="1")),
        ("SUSPENDIDO", rx.badge("Suspendido", color_scheme="orange", variant="soft", size="1")),
        rx.badge(estatus, size="1"),
    )


def _fila_empleado(emp: dict) -> rx.Component:
    """Fila de la tabla de empleados."""
    # Editable: ACTIVO y no restringido
    puede_editar = (emp["estatus"] == "ACTIVO") & (~emp["is_restricted"])
    return rx.table.row(
        rx.table.cell(
            rx.text(emp["clave"], size="2", weight="medium", color="var(--teal-11)"),
        ),
        rx.table.cell(
            rx.text(emp["nombre_completo"], size="2", weight="medium"),
        ),
        rx.table.cell(
            rx.text(emp["curp"], size="2", color="gray"),
        ),
        rx.table.cell(
            _badge_estatus(emp["estatus"]),
        ),
        rx.table.cell(
            rx.cond(
                puede_editar,
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    variant="ghost",
                    size="1",
                    color_scheme="teal",
                    cursor="pointer",
                    on_click=MisEmpleadosState.abrir_modal_editar(emp),
                ),
                rx.fragment(),
            ),
        ),
    )


ENCABEZADOS_EMPLEADOS = [
    {"nombre": "Clave", "ancho": "120px"},
    {"nombre": "Nombre", "ancho": "auto"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "80px"},
]


def _tabla_empleados() -> rx.Component:
    """Tabla de empleados."""
    return rx.cond(
        MisEmpleadosState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_EMPLEADOS, filas=5),
        rx.cond(
            MisEmpleadosState.total_empleados_lista > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_EMPLEADOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            MisEmpleadosState.empleados_filtrados,
                            _fila_empleado,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.text(
                    "Mostrando ",
                    MisEmpleadosState.total_empleados_lista,
                    " empleado(s)",
                    size="2",
                    color="gray",
                ),
                width="100%",
                spacing="3",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("users", size=48, color="var(--gray-6)"),
                    rx.text("No hay empleados registrados", color="gray", size="3"),
                    spacing="3",
                    align="center",
                ),
                padding="12",
            ),
        ),
    )


def _filtros_empleados() -> rx.Component:
    """Filtros de la tabla de empleados."""
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(placeholder="Estatus"),
            rx.select.content(
                rx.select.item("Activos", value="ACTIVO"),
                rx.select.item("Todos", value="TODOS"),
            ),
            value=MisEmpleadosState.filtro_estatus_emp,
            on_change=MisEmpleadosState.set_filtro_estatus_emp,
            size="2",
        ),
        rx.button(
            rx.icon("filter", size=14),
            "Filtrar",
            on_click=MisEmpleadosState.aplicar_filtros_emp,
            variant="soft",
            size="2",
        ),
        spacing="3",
        align="center",
    )


def _modal_empleado() -> rx.Component:
    """Modal para crear o editar un empleado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    MisEmpleadosState.es_edicion,
                    "Editar Empleado",
                    "Nuevo Empleado",
                ),
            ),
            rx.dialog.description(
                rx.cond(
                    MisEmpleadosState.es_edicion,
                    rx.text("Modifique los datos del empleado. El CURP no se puede cambiar."),
                    rx.text(
                        "El empleado se asignara a ",
                        rx.text(
                            MisEmpleadosState.nombre_empresa_actual,
                            weight="bold",
                            as_="span",
                        ),
                    ),
                ),
            ),

            rx.vstack(
                # CURP (obligatorio en creacion, inmutable en edicion)
                rx.vstack(
                    rx.text("CURP *", size="2", weight="medium"),
                    rx.input(
                        value=MisEmpleadosState.form_curp,
                        on_change=MisEmpleadosState.set_form_curp,
                        on_blur=MisEmpleadosState.validar_curp_blur,
                        placeholder="18 caracteres",
                        max_length=18,
                        width="100%",
                        disabled=MisEmpleadosState.es_edicion,
                    ),
                    rx.cond(
                        MisEmpleadosState.error_curp != "",
                        rx.text(MisEmpleadosState.error_curp, size="1", color="red"),
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Nombre y apellidos
                rx.hstack(
                    rx.vstack(
                        rx.text("Nombre *", size="2", weight="medium"),
                        rx.input(
                            value=MisEmpleadosState.form_nombre,
                            on_change=MisEmpleadosState.set_form_nombre,
                            on_blur=MisEmpleadosState.validar_nombre_blur,
                            placeholder="Nombre(s)",
                            width="100%",
                        ),
                        rx.cond(
                            MisEmpleadosState.error_nombre != "",
                            rx.text(MisEmpleadosState.error_nombre, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Ap. Paterno *", size="2", weight="medium"),
                        rx.input(
                            value=MisEmpleadosState.form_apellido_paterno,
                            on_change=MisEmpleadosState.set_form_apellido_paterno,
                            on_blur=MisEmpleadosState.validar_apellido_paterno_blur,
                            placeholder="Apellido paterno",
                            width="100%",
                        ),
                        rx.cond(
                            MisEmpleadosState.error_apellido_paterno != "",
                            rx.text(MisEmpleadosState.error_apellido_paterno, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Ap. Materno *", size="2", weight="medium"),
                        rx.input(
                            value=MisEmpleadosState.form_apellido_materno,
                            on_change=MisEmpleadosState.set_form_apellido_materno,
                            on_blur=MisEmpleadosState.validar_apellido_materno_blur,
                            placeholder="Apellido materno",
                            width="100%",
                        ),
                        rx.cond(
                            MisEmpleadosState.error_apellido_materno != "",
                            rx.text(MisEmpleadosState.error_apellido_materno, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # RFC y NSS (obligatorios)
                rx.hstack(
                    rx.vstack(
                        rx.text("RFC *", size="2", weight="medium"),
                        rx.input(
                            value=MisEmpleadosState.form_rfc,
                            on_change=MisEmpleadosState.set_form_rfc,
                            on_blur=MisEmpleadosState.validar_rfc_blur,
                            placeholder="13 caracteres",
                            max_length=13,
                            width="100%",
                        ),
                        rx.cond(
                            MisEmpleadosState.error_rfc != "",
                            rx.text(MisEmpleadosState.error_rfc, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("NSS *", size="2", weight="medium"),
                        rx.input(
                            value=MisEmpleadosState.form_nss,
                            on_change=MisEmpleadosState.set_form_nss,
                            on_blur=MisEmpleadosState.validar_nss_blur,
                            placeholder="11 digitos",
                            max_length=11,
                            width="100%",
                        ),
                        rx.cond(
                            MisEmpleadosState.error_nss != "",
                            rx.text(MisEmpleadosState.error_nss, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Fecha nacimiento y genero (obligatorios)
                rx.hstack(
                    rx.vstack(
                        rx.text("Fecha de Nacimiento *", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=MisEmpleadosState.form_fecha_nacimiento,
                            on_change=MisEmpleadosState.set_form_fecha_nacimiento,
                            on_blur=MisEmpleadosState.validar_fecha_nacimiento_blur,
                            width="100%",
                        ),
                        rx.cond(
                            MisEmpleadosState.error_fecha_nacimiento != "",
                            rx.text(MisEmpleadosState.error_fecha_nacimiento, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Genero *", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(
                                placeholder="Seleccionar...",
                                width="100%",
                            ),
                            rx.select.content(
                                rx.foreach(
                                    MisEmpleadosState.opciones_genero,
                                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                                ),
                            ),
                            value=MisEmpleadosState.form_genero,
                            on_change=MisEmpleadosState.set_form_genero,
                        ),
                        rx.cond(
                            MisEmpleadosState.error_genero != "",
                            rx.text(MisEmpleadosState.error_genero, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Telefono (obligatorio) y email (opcional)
                rx.hstack(
                    rx.vstack(
                        rx.text("Telefono *", size="2", weight="medium"),
                        rx.input(
                            value=MisEmpleadosState.form_telefono,
                            on_change=MisEmpleadosState.set_form_telefono,
                            on_blur=MisEmpleadosState.validar_telefono_blur,
                            placeholder="10 digitos",
                            max_length=15,
                            width="100%",
                        ),
                        rx.cond(
                            MisEmpleadosState.error_telefono != "",
                            rx.text(MisEmpleadosState.error_telefono, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Email", size="2", weight="medium"),
                        rx.input(
                            value=MisEmpleadosState.form_email,
                            on_change=MisEmpleadosState.set_form_email,
                            on_blur=MisEmpleadosState.validar_email_blur,
                            placeholder="correo@ejemplo.com",
                            width="100%",
                        ),
                        rx.cond(
                            MisEmpleadosState.error_email != "",
                            rx.text(MisEmpleadosState.error_email, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Direccion
                rx.vstack(
                    rx.text("Direccion", size="2", weight="medium"),
                    rx.text_area(
                        value=MisEmpleadosState.form_direccion,
                        on_change=MisEmpleadosState.set_form_direccion,
                        placeholder="Direccion completa",
                        width="100%",
                        rows="2",
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Contacto de emergencia (3 campos)
                rx.vstack(
                    rx.text("Contacto de Emergencia", size="2", weight="bold"),
                    rx.hstack(
                        rx.vstack(
                            rx.text("Nombre", size="2", weight="medium"),
                            rx.input(
                                value=MisEmpleadosState.form_contacto_nombre,
                                on_change=MisEmpleadosState.set_form_contacto_nombre,
                                on_blur=MisEmpleadosState.validar_contacto_nombre_blur,
                                placeholder="Nombre completo",
                                width="100%",
                            ),
                            rx.cond(
                                MisEmpleadosState.error_contacto_nombre != "",
                                rx.text(MisEmpleadosState.error_contacto_nombre, size="1", color="red"),
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Telefono", size="2", weight="medium"),
                            rx.input(
                                value=MisEmpleadosState.form_contacto_telefono,
                                on_change=MisEmpleadosState.set_form_contacto_telefono,
                                on_blur=MisEmpleadosState.validar_contacto_telefono_blur,
                                placeholder="10 digitos",
                                max_length=15,
                                width="100%",
                            ),
                            rx.cond(
                                MisEmpleadosState.error_contacto_telefono != "",
                                rx.text(MisEmpleadosState.error_contacto_telefono, size="1", color="red"),
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Parentesco", size="2", weight="medium"),
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Seleccionar...",
                                    width="100%",
                                ),
                                rx.select.content(
                                    rx.foreach(
                                        MisEmpleadosState.opciones_parentesco,
                                        lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                                    ),
                                ),
                                value=MisEmpleadosState.form_contacto_parentesco,
                                on_change=MisEmpleadosState.set_form_contacto_parentesco,
                            ),
                            rx.cond(
                                MisEmpleadosState.error_contacto_parentesco != "",
                                rx.text(MisEmpleadosState.error_contacto_parentesco, size="1", color="red"),
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    width="100%",
                    spacing="2",
                    padding="3",
                    border="1px solid var(--gray-5)",
                    border_radius="var(--radius-2)",
                ),

                # Notas
                rx.vstack(
                    rx.text("Notas", size="2", weight="medium"),
                    rx.text_area(
                        value=MisEmpleadosState.form_notas,
                        on_change=MisEmpleadosState.set_form_notas,
                        placeholder="Observaciones adicionales",
                        width="100%",
                        rows="2",
                    ),
                    width="100%",
                    spacing="1",
                ),

                spacing="4",
                width="100%",
                padding_y="4",
            ),

            # Botones de accion
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=MisEmpleadosState.cerrar_modal_empleado,
                    ),
                ),
                rx.button(
                    rx.cond(
                        MisEmpleadosState.saving,
                        rx.spinner(size="1"),
                        rx.icon("save", size=16),
                    ),
                    "Guardar",
                    on_click=MisEmpleadosState.guardar_empleado,
                    disabled=MisEmpleadosState.saving,
                    color_scheme="teal",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),

            max_width="600px",
        ),
        open=MisEmpleadosState.mostrar_modal_empleado,
        on_open_change=lambda open: rx.cond(~open, MisEmpleadosState.cerrar_modal_empleado(), None),
    )


# =============================================================================
# PAGINA
# =============================================================================

def mis_empleados_page() -> rx.Component:
    """Pagina de lista de empleados del portal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Empleados",
                subtitulo="Empleados de la empresa",
                icono="users",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo Empleado",
                    on_click=MisEmpleadosState.abrir_modal_crear,
                    color_scheme="teal",
                ),
            ),
            toolbar=page_toolbar(
                search_value=MisEmpleadosState.filtro_busqueda_emp,
                search_placeholder="Buscar por nombre, clave o CURP...",
                on_search_change=MisEmpleadosState.set_filtro_busqueda_emp,
                on_search_clear=lambda: MisEmpleadosState.set_filtro_busqueda_emp(""),
                show_view_toggle=False,
                filters=_filtros_empleados(),
            ),
            content=rx.vstack(
                _tabla_empleados(),
                _modal_empleado(),
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MisEmpleadosState.on_mount_empleados,
    )
