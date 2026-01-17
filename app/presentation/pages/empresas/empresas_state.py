"""
Estado para la gestión de empresas.

Refactorizado para usar diccionarios de configuración y reducir código repetitivo.
"""
import reflex as rx
from decimal import Decimal
from typing import List, Callable

from app.presentation.components.shared.base_state import BaseState
from app.services import empresa_service
from app.core.text_utils import normalizar_mayusculas

from app.entities import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
    TipoEmpresa,
    EstatusEmpresa,
)

from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    DatabaseError,
    ValidationError
)

from .empresas_validators import (
    validar_nombre_comercial,
    validar_razon_social,
    validar_rfc,
    validar_email,
    validar_codigo_postal,
    validar_telefono,
    validar_registro_patronal,
    validar_prima_riesgo
)


# ============================================================================
# CONFIGURACIÓN DE CAMPOS VALIDABLES
# ============================================================================
# Mapeo: nombre_campo -> función validadora
CAMPOS_VALIDACION: dict[str, Callable[[str], str]] = {
    "nombre_comercial": validar_nombre_comercial,
    "razon_social": validar_razon_social,
    "rfc": validar_rfc,
    "email": validar_email,
    "codigo_postal": validar_codigo_postal,
    "telefono": validar_telefono,
    "registro_patronal": validar_registro_patronal,
    "prima_riesgo": validar_prima_riesgo,
}

# Campos con sus valores por defecto para limpiar formulario
FORM_DEFAULTS = {
    "nombre_comercial": "",
    "razon_social": "",
    "tipo_empresa": TipoEmpresa.NOMINA.value,
    "rfc": "",
    "direccion": "",
    "codigo_postal": "",
    "telefono": "",
    "email": "",
    "pagina_web": "",
    "estatus": EstatusEmpresa.ACTIVO.value,
    "notas": "",
    "registro_patronal": "",
    "prima_riesgo": "",
}


class EmpresasState(BaseState):
    """Estado para la gestión de empresas"""

    # ========================
    # DATOS Y LISTAS
    # ========================
    empresas: List[EmpresaResumen] = []
    empresa_seleccionada: Empresa | None = None

    # ========================
    # FILTROS Y BÚSQUEDA
    # ========================
    filtro_tipo: str = ""
    filtro_busqueda: str = ""
    solo_activas: bool = False

    # ========================
    # ESTADO DE LA UI
    # ========================
    mostrar_modal_empresa: bool = False
    modo_modal_empresa: str = ""  # "crear" | "editar" | ""
    mostrar_modal_detalle: bool = False
    saving: bool = False

    # ========================
    # FORMULARIO DE EMPRESA (Reflex requiere declaración explícita)
    # ========================
    form_nombre_comercial: str = ""
    form_razon_social: str = ""
    form_tipo_empresa: str = TipoEmpresa.NOMINA.value
    form_rfc: str = ""
    form_direccion: str = ""
    form_codigo_postal: str = ""
    form_telefono: str = ""
    form_email: str = ""
    form_pagina_web: str = ""
    form_estatus: str = EstatusEmpresa.ACTIVO.value
    form_notas: str = ""
    form_registro_patronal: str = ""
    form_prima_riesgo: str = ""

    # ========================
    # ERRORES DE VALIDACIÓN (Reflex requiere declaración explícita)
    # ========================
    error_nombre_comercial: str = ""
    error_razon_social: str = ""
    error_rfc: str = ""
    error_email: str = ""
    error_codigo_postal: str = ""
    error_telefono: str = ""
    error_registro_patronal: str = ""
    error_prima_riesgo: str = ""

    # ========================
    # SETTERS DE FILTROS
    # ========================
    def set_filtro_tipo(self, value: str):
        self.filtro_tipo = value

    def set_filtro_busqueda(self, value: str):
        self.filtro_busqueda = value

    def set_solo_activas(self, value: bool):
        self.solo_activas = value

    # ========================
    # SETTERS DE FORMULARIO (Reflex v0.8.9+ requiere explícitos)
    # ========================
    def set_form_nombre_comercial(self, value: str):
        self.form_nombre_comercial = value

    def set_form_razon_social(self, value: str):
        self.form_razon_social = value

    def set_form_tipo_empresa(self, value: str):
        self.form_tipo_empresa = value

    def set_form_rfc(self, value: str):
        self.form_rfc = value.upper() if value else ""

    def set_form_direccion(self, value: str):
        self.form_direccion = value

    def set_form_codigo_postal(self, value: str):
        self.form_codigo_postal = value

    def set_form_telefono(self, value: str):
        self.form_telefono = value

    def set_form_email(self, value: str):
        self.form_email = value

    def set_form_pagina_web(self, value: str):
        self.form_pagina_web = value

    def set_form_estatus(self, value: str):
        self.form_estatus = value

    def set_form_notas(self, value: str):
        self.form_notas = value

    def set_form_registro_patronal(self, value: str):
        self.form_registro_patronal = value

    def set_form_prima_riesgo(self, value: str):
        self.form_prima_riesgo = value

    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def cargar_empresas(self):
        """Cargar empresas con filtros aplicados en BD"""
        self.loading = True
        try:
            self.empresas = await empresa_service.buscar_con_filtros(
                texto=self.filtro_busqueda or None,
                tipo_empresa=self.filtro_tipo or None,
                estatus="ACTIVO" if self.solo_activas else None,
                incluir_inactivas=not self.solo_activas,
                limite=100,
                offset=0
            )
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error de base de datos: {e}", "error")
            self.empresas = []
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.empresas = []
        finally:
            self.loading = False

    async def crear_empresa(self):
        """Crear una nueva empresa"""
        self._validar_todos_los_campos()
        if self.tiene_errores_formulario:
            return

        self.saving = True
        try:
            nueva_empresa = self._preparar_empresa_desde_formulario(es_actualizacion=False)
            empresa_creada = await empresa_service.crear(nueva_empresa)

            self.cerrar_modal_empresa()
            await self.cargar_empresas()

            return rx.toast.success(
                f"Empresa '{empresa_creada.nombre_comercial}' creada exitosamente",
                position="top-center",
                duration=4000
            )
        except Exception as e:
            self._manejar_error(e, "crear empresa")
        finally:
            self.saving = False

    async def actualizar_empresa(self):
        """Actualizar empresa existente"""
        self._validar_todos_los_campos()
        if self.tiene_errores_formulario:
            return

        if not self.empresa_seleccionada:
            self.mostrar_mensaje("No hay empresa seleccionada", "error")
            return

        self.saving = True
        try:
            update_data = self._preparar_empresa_desde_formulario(es_actualizacion=True)
            empresa_actualizada = await empresa_service.actualizar(
                self.empresa_seleccionada.id, update_data
            )

            self.cerrar_modal_empresa()
            await self.cargar_empresas()

            return rx.toast.success(
                f"Empresa '{empresa_actualizada.nombre_comercial}' actualizada",
                position="top-center",
                duration=4000
            )
        except Exception as e:
            self._manejar_error(e, "actualizar empresa")
        finally:
            self.saving = False

    async def cambiar_estatus_empresa(self, empresa_id: int, nuevo_estatus: EstatusEmpresa):
        """Cambiar estatus de una empresa"""
        try:
            await empresa_service.cambiar_estatus(empresa_id, nuevo_estatus)
            await self.cargar_empresas()
            return rx.toast.success(f"Estatus cambiado a {nuevo_estatus.value}")
        except Exception as e:
            self._manejar_error(e, "cambiar estatus")

    # ========================
    # OPERACIONES DE MODALES
    # ========================
    def abrir_modal_crear(self):
        """Abrir modal en modo crear"""
        self._limpiar_formulario()
        self.limpiar_mensajes()
        self.modo_modal_empresa = "crear"
        self.mostrar_modal_empresa = True

    async def abrir_modal_editar(self, empresa_id: int):
        """Abrir modal en modo editar"""
        try:
            self.limpiar_mensajes()
            self.mostrar_modal_detalle = False

            empresa = await empresa_service.obtener_por_id(empresa_id)
            self._cargar_empresa_en_formulario(empresa)

            self.empresa_seleccionada = empresa
            self.modo_modal_empresa = "editar"
            self.mostrar_modal_empresa = True
        except Exception as e:
            self._manejar_error(e, "abrir modal de edición")

    def cerrar_modal_empresa(self):
        """Cerrar modal crear/editar"""
        self.mostrar_modal_empresa = False
        self.modo_modal_empresa = ""
        self.empresa_seleccionada = None
        self._limpiar_formulario()
        self.limpiar_mensajes()

    async def abrir_modal_detalle(self, empresa_id: int):
        """Abrir modal de detalles"""
        try:
            self.empresa_seleccionada = await empresa_service.obtener_por_id(empresa_id)
            self.mostrar_modal_detalle = True
        except Exception as e:
            self._manejar_error(e, "abrir detalles")

    def cerrar_modal_detalle(self):
        """Cerrar modal de detalles"""
        self.mostrar_modal_detalle = False
        self.empresa_seleccionada = None

    # ========================
    # OPERACIONES DE FILTROS
    # ========================
    async def aplicar_filtros(self):
        await self.cargar_empresas()

    async def limpiar_filtros(self):
        self.filtro_tipo = ""
        self.filtro_busqueda = ""
        self.solo_activas = False
        await self.cargar_empresas()

    # ========================
    # VALIDACIÓN - Métodos individuales para on_blur
    # ========================
    def validar_nombre_comercial_campo(self):
        self._validar_campo("nombre_comercial")

    def validar_razon_social_campo(self):
        self._validar_campo("razon_social")

    def validar_rfc_campo(self):
        self._validar_campo("rfc")

    def validar_email_campo(self):
        self._validar_campo("email")

    def validar_codigo_postal_campo(self):
        self._validar_campo("codigo_postal")

    def validar_telefono_campo(self):
        self._validar_campo("telefono")

    def validar_registro_patronal_campo(self):
        self._validar_campo("registro_patronal")

    def validar_prima_riesgo_campo(self):
        self._validar_campo("prima_riesgo")

    def _validar_campo(self, campo: str):
        """Valida un campo usando el diccionario de validadores"""
        if campo in CAMPOS_VALIDACION:
            valor = getattr(self, f"form_{campo}")
            error = CAMPOS_VALIDACION[campo](valor)
            setattr(self, f"error_{campo}", error)

    def _validar_todos_los_campos(self):
        """Valida todos los campos del formulario"""
        for campo in CAMPOS_VALIDACION:
            self._validar_campo(campo)

    @rx.var
    def tiene_errores_formulario(self) -> bool:
        """Verifica si hay errores de validación"""
        return any(
            getattr(self, f"error_{campo}")
            for campo in CAMPOS_VALIDACION
        )

    @rx.var
    def tiene_filtros_activos(self) -> bool:
        return bool(self.filtro_busqueda or self.filtro_tipo or self.solo_activas)

    @rx.var
    def cantidad_filtros_activos(self) -> int:
        return sum([
            bool(self.filtro_busqueda),
            bool(self.filtro_tipo),
            self.solo_activas
        ])

    # ========================
    # MÉTODOS HELPER PRIVADOS
    # ========================
    def _manejar_error(self, error: Exception, operacion: str = "") -> None:
        """Maneja errores de forma centralizada"""
        contexto = f" al {operacion}" if operacion else ""

        if isinstance(error, NotFoundError):
            self.mostrar_mensaje(f"Empresa no encontrada{contexto}", "error")
        elif isinstance(error, DuplicateError):
            self.mostrar_mensaje(f"RFC duplicado: ya existe en el sistema", "error")
        elif isinstance(error, ValidationError):
            self.mostrar_mensaje(f"Error de validación{contexto}: {error}", "error")
        elif isinstance(error, DatabaseError):
            self.mostrar_mensaje(f"Error de base de datos{contexto}", "error")
        else:
            self.mostrar_mensaje(f"Error inesperado{contexto}: {error}", "error")

    def _limpiar_formulario(self):
        """Limpia campos del formulario usando diccionario de defaults"""
        for campo, default in FORM_DEFAULTS.items():
            setattr(self, f"form_{campo}", default)
        self._limpiar_errores()

    def _limpiar_errores(self):
        """Limpia todos los errores de validación"""
        for campo in CAMPOS_VALIDACION:
            setattr(self, f"error_{campo}", "")

    def _cargar_empresa_en_formulario(self, empresa: Empresa):
        """Carga datos de empresa en el formulario"""
        self.form_nombre_comercial = empresa.nombre_comercial
        self.form_razon_social = empresa.razon_social
        self.form_tipo_empresa = str(empresa.tipo_empresa)
        self.form_rfc = empresa.rfc
        self.form_direccion = empresa.direccion or ""
        self.form_codigo_postal = empresa.codigo_postal or ""
        self.form_telefono = empresa.telefono or ""
        self.form_email = empresa.email or ""
        self.form_pagina_web = empresa.pagina_web or ""
        self.form_estatus = str(empresa.estatus)
        self.form_notas = empresa.notas or ""
        self.form_registro_patronal = empresa.registro_patronal or ""
        self.form_prima_riesgo = str(empresa.get_prima_riesgo_porcentaje()) if empresa.prima_riesgo else ""

    def _preparar_empresa_desde_formulario(self, es_actualizacion: bool = False) -> EmpresaCreate | EmpresaUpdate:
        """Prepara objeto Empresa desde formulario"""
        datos = {
            "nombre_comercial": normalizar_mayusculas(self.form_nombre_comercial) or None,
            "razon_social": normalizar_mayusculas(self.form_razon_social) or None,
            "rfc": normalizar_mayusculas(self.form_rfc) or None,
            "tipo_empresa": TipoEmpresa(self.form_tipo_empresa) if self.form_tipo_empresa else None,
            "direccion": self.form_direccion.strip() or None,
            "codigo_postal": self.form_codigo_postal.strip() or None,
            "telefono": self.form_telefono.strip() or None,
            "email": self.form_email.strip() or None,
            "pagina_web": self.form_pagina_web.strip() or None,
            "estatus": EstatusEmpresa(self.form_estatus) if self.form_estatus else None,
            "notas": self.form_notas.strip() or None,
            "registro_patronal": self.form_registro_patronal.strip() or None,
            "prima_riesgo": Decimal(self.form_prima_riesgo) if self.form_prima_riesgo.strip() else None,
        }

        if es_actualizacion:
            return EmpresaUpdate(**datos)
        return EmpresaCreate(**datos)

    # ========================
    # COMPATIBILIDAD (métodos públicos usados por otros módulos)
    # ========================
    def limpiar_formulario(self):
        """Alias público para compatibilidad"""
        self._limpiar_formulario()

    def limpiar_errores_validacion(self):
        """Alias público para compatibilidad"""
        self._limpiar_errores()

    def validar_todos_los_campos(self):
        """Alias público para compatibilidad"""
        self._validar_todos_los_campos()

    async def handle_key_down(self, key):
        """Manejar Enter en búsqueda"""
        if key == "Enter":
            await self.aplicar_filtros()
