"""
State para la pagina Mis Empleados del portal.
"""
import reflex as rx
from typing import List

from app.presentation.portal.state.portal_state import PortalState
from app.services import empleado_service
from app.entities import EmpleadoCreate, EmpleadoUpdate
from app.core.exceptions import DatabaseError, DuplicateError, BusinessRuleError, NotFoundError
from app.core.validation import (
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
    validar_curp,
    validar_nombre,
    validar_apellido_paterno,
    validar_email,
)


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
            self.loading = False
            yield resultado
            return
        if not self.puede_gestionar_personal:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_empleados):
            yield

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_empleados(self):
        """Carga empleados de la empresa del usuario (sin manejo de loading)."""
        if not self.id_empresa_actual:
            return

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

    async def cargar_empleados(self):
        """Recarga empleados con skeleton (filtros)."""
        async for _ in self._recargar_datos(self._fetch_empleados):
            yield

    async def aplicar_filtros_emp(self):
        async for _ in self.cargar_empleados():
            yield

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
            contacto_emergencia = self._construir_contacto_emergencia()

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
            contacto_emergencia = self._construir_contacto_emergencia()

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

    # ========================
    # METODOS PRIVADOS
    # ========================
    def _construir_contacto_emergencia(self) -> str | None:
        """Construye el string de contacto de emergencia desde los campos del form."""
        partes_contacto = [
            self.form_contacto_nombre.strip(),
            self.form_contacto_telefono.strip(),
            self.form_contacto_parentesco,
        ]
        if any(partes_contacto):
            return " / ".join(p for p in partes_contacto if p)
        return None

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
        self.limpiar_errores_campos([
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
        ])

    def _validar_formulario(self) -> bool:
        """Valida el formulario completo. Retorna True si es valido."""
        self._limpiar_errores()
        es_valido = True

        # CURP obligatorio (solo en creacion, inmutable en edicion)
        if not self.es_edicion:
            if not self.validar_y_asignar_error(
                valor=self.form_curp,
                validador=validar_curp,
                error_attr="error_curp",
            ):
                es_valido = False

        if not self.validar_lote_campos([
            ("error_nombre", self.form_nombre, validar_nombre),
            ("error_apellido_paterno", self.form_apellido_paterno, validar_apellido_paterno),
            ("error_apellido_materno", self.form_apellido_materno, validar_apellido_materno_empleado),
            ("error_rfc", self.form_rfc, validar_rfc_empleado_requerido),
            ("error_nss", self.form_nss, validar_nss_empleado_requerido),
            ("error_genero", self.form_genero, validar_genero_empleado_requerido),
            ("error_fecha_nacimiento", self.form_fecha_nacimiento, lambda v: validar_fecha_nacimiento_empleado(v, requerida=True, edad_min=18)),
            ("error_telefono", self.form_telefono, validar_telefono_empleado_requerido),
        ]):
            es_valido = False

        # Email opcional (solo si tiene valor)
        if self.form_email:
            if not self.validar_y_asignar_error(
                valor=self.form_email,
                validador=validar_email,
                error_attr="error_email",
            ):
                es_valido = False

        # Contacto de emergencia opcional (validar formato si tienen valor)
        if self.form_contacto_nombre:
            if not self.validar_y_asignar_error(
                valor=self.form_contacto_nombre,
                validador=validar_contacto_emergencia_nombre,
                error_attr="error_contacto_nombre",
            ):
                es_valido = False

        if self.form_contacto_telefono:
            if not self.validar_y_asignar_error(
                valor=self.form_contacto_telefono,
                validador=validar_contacto_emergencia_telefono,
                error_attr="error_contacto_telefono",
            ):
                es_valido = False

        return es_valido
