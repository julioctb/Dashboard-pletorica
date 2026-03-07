"""
State para la pagina Mis Empleados del portal.
"""
from datetime import date
from typing import List

import reflex as rx

from app.core.enums import GeneroEmpleado
from app.presentation.portal.state.portal_state import PortalState
from app.presentation.components.shared.employee_form_state_mixin import EmployeeFormStateMixin
from app.services import empleado_service
from app.entities import EmpleadoCreate, EmpleadoUpdate
from app.core.exceptions import DuplicateError, BusinessRuleError, NotFoundError
from app.core.ui_helpers import opciones_desde_enum
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

class MisEmpleadosState(PortalState, EmployeeFormStateMixin):
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
    ]

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

    # ========================
    # CREAR EMPLEADO
    # ========================
    async def crear_empleado(self):
        """Crea un nuevo empleado asignado a la empresa del portal."""
        if not self._validar_formulario():
            return rx.toast.error("Por favor corrija los errores del formulario")

        self.saving = True
        try:
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
            }
        )

        self.mostrar_modal_empleado = True

    async def actualizar_empleado(self):
        """Actualiza un empleado existente."""
        if not self._validar_formulario():
            return rx.toast.error("Por favor corrija los errores del formulario")

        self.saving = True
        try:
            empleado_update = EmpleadoUpdate(**self._payload_base_empleado())

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

    def _limpiar_formulario_baja(self) -> None:
        """Resetea el formulario de baja del portal."""
        self.form_motivo_baja = ""
        self.form_fecha_efectiva_baja = ""
        self.form_notas_baja = ""
        self.error_motivo_baja = ""
        self.error_fecha_efectiva_baja = ""

    def _limpiar_formulario(self):
        """Limpia el formulario."""
        self._reset_employee_form_fields(
            error_fields=self._campos_error_formulario,
            extra_defaults={
                "form_motivo_baja": "",
                "form_fecha_efectiva_baja": "",
                "form_notas_baja": "",
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
            ],
        )
