"""
Estado de Reflex para el módulo de Empleados.
Maneja el estado de la UI y las operaciones del módulo.
"""
import reflex as rx
from typing import List, Optional
from datetime import date

from app.presentation.components.shared.base_state import BaseState
from app.services import empleado_service, empresa_service
from app.core.text_utils import formatear_fecha

from app.entities import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
    EstatusEmpleado,
    GeneroEmpleado,
    MotivoBaja,
    EmpresaResumen,
)

from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    DatabaseError,
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
)


class EmpleadosState(BaseState):
    """Estado para el módulo de Empleados"""

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
    por_pagina: int = 20

    # Catálogos
    empresas: List[dict] = []

    # ========================
    # FILTROS
    # ========================
    filtro_empresa_id: str = "TODAS"  # String para el select
    filtro_estatus: str = "TODOS"
    search: str = ""

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_empleado: bool = False
    mostrar_modal_detalle: bool = False
    mostrar_modal_baja: bool = False
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
    def set_search(self, value: str):
        self.search = value if value else ""

    def set_filtro_empresa_id(self, value: str):
        self.filtro_empresa_id = value if value else "TODAS"

    def set_filtro_estatus(self, value: str):
        self.filtro_estatus = value if value else "TODOS"

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
        return [
            {"value": "TODOS", "label": "Todos"},
            {"value": "ACTIVO", "label": "Activo"},
            {"value": "INACTIVO", "label": "Inactivo"},
            {"value": "SUSPENDIDO", "label": "Suspendido"},
        ]

    @rx.var
    def opciones_genero(self) -> List[dict]:
        """Opciones para el select de género"""
        return [
            {"value": "MASCULINO", "label": "Masculino"},
            {"value": "FEMENINO", "label": "Femenino"},
        ]

    @rx.var
    def opciones_motivo_baja(self) -> List[dict]:
        """Opciones para el select de motivo de baja"""
        return [
            {"value": "RENUNCIA", "label": "Renuncia voluntaria"},
            {"value": "DESPIDO", "label": "Despido"},
            {"value": "FIN_CONTRATO", "label": "Fin de contrato"},
            {"value": "JUBILACION", "label": "Jubilación"},
            {"value": "FALLECIMIENTO", "label": "Fallecimiento"},
            {"value": "OTRO", "label": "Otro motivo"},
        ]

    @rx.var
    def empleados_filtrados(self) -> List[dict]:
        """Empleados filtrados por búsqueda local (adicional al filtro de BD)"""
        if not self.search:
            return self.empleados

        termino = self.search.lower()
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
    # CARGA DE DATOS
    # ========================
    async def cargar_empleados(self):
        """Carga la lista de empleados con filtros aplicados"""
        self.loading = True
        try:
            # Determinar empresa_id para filtro
            empresa_id = None
            if self.filtro_empresa_id and self.filtro_empresa_id not in ("", "TODAS"):
                empresa_id = int(self.filtro_empresa_id)

            # Determinar estatus para filtro
            estatus = None
            incluir_inactivos = False
            if self.filtro_estatus == "TODOS":
                incluir_inactivos = True
            elif self.filtro_estatus:
                estatus = self.filtro_estatus

            # Buscar empleados
            if self.search and len(self.search) >= 2:
                empleados = await empleado_service.buscar(
                    texto=self.search,
                    empresa_id=empresa_id,
                    limite=50
                )
            elif empresa_id:
                empleados = await empleado_service.obtener_por_empresa(
                    empresa_id=empresa_id,
                    incluir_inactivos=incluir_inactivos,
                    limite=self.por_pagina,
                    offset=(self.pagina - 1) * self.por_pagina
                )
            else:
                empleados = await empleado_service.obtener_todos(
                    incluir_inactivos=incluir_inactivos,
                    limite=self.por_pagina,
                    offset=(self.pagina - 1) * self.por_pagina
                )

            # Obtener nombres de empresas
            empresas_cache = {}
            for emp in empleados:
                if emp.empresa_id is not None and emp.empresa_id not in empresas_cache:
                    try:
                        empresa = await empresa_service.obtener_por_id(emp.empresa_id)
                        empresas_cache[emp.empresa_id] = empresa.nombre_comercial
                    except NotFoundError:
                        empresas_cache[emp.empresa_id] = "N/A"

            # Convertir a diccionarios para la UI
            self.empleados = [
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
                }
                for emp in empleados
            ]

            self.total_empleados = len(self.empleados)

        except Exception as e:
            self.manejar_error(e, "cargando empleados")
            self.empleados = []
        finally:
            self.loading = False

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
                    empresa_id=int(self.form_empresa_id) if self.form_empresa_id else None,
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
                await self.cargar_empleados()
                return rx.toast.success("Empleado actualizado correctamente")

            else:
                # Crear nuevo empleado
                empleado_create = EmpleadoCreate(
                    empresa_id=int(self.form_empresa_id) if self.form_empresa_id else None,
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
                await self.cargar_empleados()
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

        self.saving = True
        try:
            await empleado_service.dar_de_baja(
                empleado_id=empleado_id,
                motivo=MotivoBaja(self.form_motivo_baja),
            )

            self.cerrar_modal_baja()
            self.cerrar_modal_detalle()
            await self.cargar_empleados()
            return rx.toast.success("Empleado dado de baja correctamente")

        except Exception as e:
            return self.manejar_error_con_toast(e, "dando de baja")
        finally:
            self.saving = False

    async def reactivar_empleado(self):
        """Reactiva al empleado seleccionado"""
        if not self.empleado_seleccionado:
            return rx.toast.error("No hay empleado seleccionado")

        empleado_id = self.empleado_seleccionado.get("id") if isinstance(self.empleado_seleccionado, dict) else None
        if not empleado_id:
            return rx.toast.error("Error: No se pudo obtener el ID del empleado")

        self.saving = True
        try:
            await empleado_service.reactivar(empleado_id)

            self.cerrar_modal_detalle()
            await self.cargar_empleados()
            return rx.toast.success("Empleado reactivado correctamente")

        except Exception as e:
            return self.manejar_error_con_toast(e, "reactivando empleado")
        finally:
            self.saving = False

    async def suspender_empleado(self):
        """Suspende al empleado seleccionado"""
        if not self.empleado_seleccionado:
            return rx.toast.error("No hay empleado seleccionado")

        empleado_id = self.empleado_seleccionado.get("id") if isinstance(self.empleado_seleccionado, dict) else None
        if not empleado_id:
            return rx.toast.error("Error: No se pudo obtener el ID del empleado")

        self.saving = True
        try:
            await empleado_service.suspender(empleado_id)

            self.cerrar_modal_detalle()
            await self.cargar_empleados()
            return rx.toast.success("Empleado suspendido correctamente")

        except Exception as e:
            return self.manejar_error_con_toast(e, "suspendiendo empleado")
        finally:
            self.saving = False

    async def suspender_desde_lista(self, empleado_id: int):
        """Suspende un empleado desde la lista (sin modal de detalle)"""
        self.saving = True
        try:
            await empleado_service.suspender(empleado_id)
            await self.cargar_empleados()
            return rx.toast.success("Empleado suspendido correctamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "suspendiendo empleado")
        finally:
            self.saving = False

    async def reactivar_desde_lista(self, empleado_id: int):
        """Reactiva un empleado desde la lista (sin modal de detalle)"""
        self.saving = True
        try:
            await empleado_service.reactivar(empleado_id)
            await self.cargar_empleados()
            return rx.toast.success("Empleado reactivado correctamente")
        except Exception as e:
            return self.manejar_error_con_toast(e, "reactivando empleado")
        finally:
            self.saving = False

    # ========================
    # FILTROS
    # ========================
    async def aplicar_filtros(self):
        """Aplica los filtros y recarga la lista"""
        self.pagina = 1
        await self.cargar_empleados()

    async def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.search = ""
        self.filtro_empresa_id = "TODAS"
        self.filtro_estatus = "TODOS"
        self.pagina = 1
        await self.cargar_empleados()

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
        """Limpia el formulario"""
        self.empleado_id_edicion = 0
        self.form_empresa_id = ""
        self.form_curp = ""
        self.form_rfc = ""
        self.form_nss = ""
        self.form_nombre = ""
        self.form_apellido_paterno = ""
        self.form_apellido_materno = ""
        self.form_fecha_nacimiento = ""
        self.form_genero = ""
        self.form_telefono = ""
        self.form_email = ""
        self.form_direccion = ""
        self.form_contacto_emergencia = ""
        self.form_notas = ""
        self._limpiar_errores()

    def _limpiar_errores(self):
        """Limpia los errores de validación"""
        self.error_curp = ""
        self.error_rfc = ""
        self.error_nss = ""
        self.error_nombre = ""
        self.error_apellido_paterno = ""
        self.error_email = ""
        self.error_telefono = ""
        self.error_empresa_id = ""

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
        await self.cargar_empresas()
        await self.cargar_empleados()
