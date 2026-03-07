"""
State para la pagina Mis Datos del portal (autoservicio empleado).

El empleado accede con su user_id, completa datos personales/bancarios
y sube documentos de su expediente.
"""
import reflex as rx
import logging
from typing import List

from app.core.validation import (
    normalizar_clabe_interbancaria,
    normalizar_cuenta_bancaria,
    normalizar_nombre_banco,
    validar_clabe_empleado,
    validar_cuenta_bancaria_empleado,
)
from app.presentation.portal.state.portal_state import PortalState
from app.services.onboarding_service import onboarding_service
from app.services.empleado_documento_service import empleado_documento_service
from app.core.enums import TipoDocumentoEmpleado
from app.core.exceptions import (
    BusinessRuleError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class MisDatosState(PortalState):
    """State del autoservicio de datos del empleado."""

    # ========================
    # DATOS DEL EMPLEADO
    # ========================
    empleado_data: dict = {}
    estatus_actual: str = ""
    documentos: List[dict] = []
    expediente_status: dict = {}
    empleado_encontrado: bool = False

    # ========================
    # FORM FIELDS
    # ========================
    form_telefono: str = ""
    form_direccion: str = ""
    form_contacto_emergencia: str = ""
    form_entidad_nacimiento: str = ""
    form_cuenta_bancaria: str = ""
    form_banco: str = ""
    form_clabe: str = ""

    # ========================
    # ERRORES INLINE
    # ========================
    error_cuenta_bancaria: str = ""
    error_clabe: str = ""

    # ========================
    # UPLOAD
    # ========================
    tipo_documento_subiendo: str = ""
    subiendo_archivo: bool = False

    # ========================
    # SETTERS EXPLICITOS
    # ========================
    def set_form_telefono(self, value: str):
        self.form_telefono = value

    def set_form_direccion(self, value: str):
        self.form_direccion = value

    def set_form_contacto_emergencia(self, value: str):
        self.form_contacto_emergencia = value

    def set_form_entidad_nacimiento(self, value: str):
        self.form_entidad_nacimiento = value

    def set_form_cuenta_bancaria(self, value: str):
        self.form_cuenta_bancaria = normalizar_cuenta_bancaria(value)
        self.error_cuenta_bancaria = ""

    def set_form_banco(self, value: str):
        self.form_banco = normalizar_nombre_banco(value)

    def set_form_clabe(self, value: str):
        self.form_clabe = normalizar_clabe_interbancaria(value)
        self.error_clabe = ""

    def set_tipo_documento_subiendo(self, value: str):
        self.tipo_documento_subiendo = value

    # ========================
    # VALIDACIONES INLINE
    # ========================
    def validar_cuenta_bancaria_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_cuenta_bancaria,
            validador=validar_cuenta_bancaria_empleado,
            error_attr="error_cuenta_bancaria",
        )

    def validar_clabe_blur(self):
        self.validar_y_asignar_error(
            valor=self.form_clabe,
            validador=validar_clabe_empleado,
            error_attr="error_clabe",
        )

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def puede_editar_datos(self) -> bool:
        """Solo puede editar si estatus es DATOS_PENDIENTES."""
        return self.estatus_actual == "DATOS_PENDIENTES"

    @rx.var
    def puede_subir_docs(self) -> bool:
        """Puede subir docs si DOCUMENTOS_PENDIENTES o RECHAZADO."""
        return self.estatus_actual in ("DOCUMENTOS_PENDIENTES", "RECHAZADO")

    @rx.var
    def puede_enviar_revision(self) -> bool:
        """Puede enviar si tiene todos los docs subidos."""
        if not self.puede_subir_docs:
            return False
        requeridos = self.expediente_status.get("documentos_requeridos", 0)
        subidos = self.expediente_status.get("documentos_subidos", 0)
        return requeridos > 0 and subidos >= requeridos

    @rx.var
    def esta_en_revision(self) -> bool:
        return self.estatus_actual == "EN_REVISION"

    @rx.var
    def esta_aprobado(self) -> bool:
        return self.estatus_actual in ("APROBADO", "ACTIVO_COMPLETO")

    @rx.var
    def porcentaje_expediente(self) -> int:
        return int(self.expediente_status.get("porcentaje_completado", 0))

    @rx.var
    def docs_requeridos(self) -> int:
        return self.expediente_status.get("documentos_requeridos", 0)

    @rx.var
    def docs_subidos(self) -> int:
        return self.expediente_status.get("documentos_subidos", 0)

    @rx.var
    def docs_aprobados(self) -> int:
        return self.expediente_status.get("documentos_aprobados", 0)

    @rx.var
    def docs_rechazados(self) -> int:
        return self.expediente_status.get("documentos_rechazados", 0)

    @rx.var
    def tipos_documento_lista(self) -> List[dict]:
        """Lista de tipos de documento con su estado actual."""
        tipos = []
        for tipo in TipoDocumentoEmpleado:
            doc_existente = None
            for d in self.documentos:
                if d.get("tipo_documento") == tipo.value:
                    doc_existente = d
                    break

            tipos.append({
                **(doc_existente or {}),
                "tipo": tipo.value,
                "nombre": tipo.descripcion,
                "obligatorio": tipo.es_obligatorio,
                "subido": doc_existente is not None,
                "estatus": doc_existente.get("estatus", "") if doc_existente else "",
                "observacion": doc_existente.get("observacion_rechazo", "") if doc_existente else "",
            })
        return tipos

    @rx.var
    def subtitulo_pagina(self) -> str:
        if self.estatus_actual == "DATOS_PENDIENTES":
            return "Complete sus datos personales y bancarios"
        elif self.estatus_actual in ("DOCUMENTOS_PENDIENTES", "RECHAZADO"):
            return "Suba los documentos requeridos para su expediente"
        elif self.estatus_actual == "EN_REVISION":
            return "Su expediente esta siendo revisado"
        elif self.estatus_actual in ("APROBADO", "ACTIVO_COMPLETO"):
            return "Su expediente ha sido aprobado"
        return "Autoservicio del empleado"

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_mis_datos(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.es_empleado_portal:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_empleado):
            yield

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_empleado(self):
        """Busca el empleado vinculado al user_id del usuario logueado."""
        user_id = self.obtener_uuid_usuario_actual()
        if not user_id:
            return

        try:
            from app.services.empleado_service import empleado_service

            empleado = await empleado_service.obtener_por_user_id(user_id)

            if not empleado:
                self.empleado_encontrado = False
                self.empleado_data = {}
                self.estatus_actual = ""
                return

            self.empleado_encontrado = True
            self.empleado_data = empleado.model_dump(mode='json')
            self.estatus_actual = empleado.estatus_onboarding or ""

            # Pre-llenar formulario con datos existentes
            self.form_telefono = empleado.telefono or ""
            self.form_direccion = empleado.direccion or ""
            self.form_contacto_emergencia = empleado.contacto_emergencia or ""
            self.form_entidad_nacimiento = empleado.entidad_nacimiento if hasattr(empleado, 'entidad_nacimiento') and empleado.entidad_nacimiento else ""
            self.form_cuenta_bancaria = normalizar_cuenta_bancaria(empleado.cuenta_bancaria)
            self.form_banco = normalizar_nombre_banco(empleado.banco)
            self.form_clabe = normalizar_clabe_interbancaria(empleado.clabe_interbancaria)
            self.limpiar_errores_campos(["error_cuenta_bancaria", "error_clabe"])

            # Cargar documentos y expediente status
            await self._fetch_documentos(empleado.id)

        except Exception as e:
            logger.error(f"Error cargando datos del empleado: {e}")
            self.mostrar_mensaje(f"Error cargando datos: {e}", "error")
            self.empleado_encontrado = False

    async def _fetch_documentos(self, empleado_id: int):
        """Carga documentos y estado del expediente."""
        try:
            docs = await empleado_documento_service.obtener_documentos_empleado(
                empleado_id=empleado_id,
                solo_vigentes=True,
            )
            self.documentos = [d.model_dump(mode='json') for d in docs]

            expediente = await onboarding_service.obtener_expediente(empleado_id)
            self.expediente_status = expediente.model_dump(mode='json')
        except Exception as e:
            logger.error(f"Error cargando documentos: {e}")
            self.documentos = []
            self.expediente_status = {}

    # ========================
    # GUARDAR DATOS PERSONALES
    # ========================
    def _validar_datos_bancarios(self) -> bool:
        """Ejecuta validación inline de cuenta y CLABE antes de persistir."""
        return all([
            self.validar_y_asignar_error(
                valor=self.form_cuenta_bancaria,
                validador=validar_cuenta_bancaria_empleado,
                error_attr="error_cuenta_bancaria",
            ),
            self.validar_y_asignar_error(
                valor=self.form_clabe,
                validador=validar_clabe_empleado,
                error_attr="error_clabe",
            ),
        ])

    async def guardar_datos_personales(self):
        """Guarda datos personales/bancarios y transiciona estatus."""
        if not self._validar_datos_bancarios():
            return

        self.saving = True
        try:
            from app.entities.onboarding import CompletarDatosEmpleado

            empleado_id = self.empleado_data.get("id")
            if not empleado_id:
                return rx.toast.error("No se encontro el empleado")

            datos = CompletarDatosEmpleado(
                telefono=self.form_telefono or None,
                direccion=self.form_direccion or None,
                contacto_emergencia=self.form_contacto_emergencia or None,
                entidad_nacimiento=self.form_entidad_nacimiento or None,
                cuenta_bancaria=normalizar_cuenta_bancaria(self.form_cuenta_bancaria) or None,
                banco=normalizar_nombre_banco(self.form_banco) or None,
                clabe_interbancaria=normalizar_clabe_interbancaria(self.form_clabe) or None,
            )

            empleado = await onboarding_service.completar_datos(
                empleado_id,
                datos,
                self.obtener_uuid_usuario_actual(),
            )
            self.estatus_actual = empleado.estatus_onboarding or ""
            self.empleado_data = empleado.model_dump(mode='json')

            # Recargar documentos
            await self._fetch_documentos(empleado_id)

            return rx.toast.success("Datos guardados correctamente")

        except (BusinessRuleError, ValidationError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "guardando datos")
        finally:
            self.saving = False

    # ========================
    # SUBIR DOCUMENTO
    # ========================
    async def handle_upload_documento(self, files: list):
        """Maneja la subida de un documento del expediente."""
        if not files or not self.tipo_documento_subiendo:
            return

        self.subiendo_archivo = True
        try:
            from app.entities.empleado_documento import EmpleadoDocumentoCreate

            empleado_id = self.empleado_data.get("id")
            if not empleado_id:
                return rx.toast.error("No se encontro el empleado")

            for file in files:
                upload_data = await file.read()
                nombre = file.filename or "documento"
                tipo_mime = file.content_type or "application/octet-stream"

                datos = EmpleadoDocumentoCreate(
                    empleado_id=empleado_id,
                    tipo_documento=self.tipo_documento_subiendo,
                    subido_por=self.obtener_uuid_usuario_actual(),
                )

                await empleado_documento_service.subir_documento(
                    datos=datos,
                    contenido=upload_data,
                    nombre_archivo=nombre,
                    tipo_mime=tipo_mime,
                )

            # Recargar documentos
            await self._fetch_documentos(empleado_id)
            self.tipo_documento_subiendo = ""

            return rx.toast.success("Documento subido correctamente")

        except (BusinessRuleError, ValidationError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "subiendo documento")
        finally:
            self.subiendo_archivo = False

    # ========================
    # ENVIAR A REVISION
    # ========================
    async def enviar_a_revision(self):
        """Envia el expediente completo para revision."""
        self.saving = True
        try:
            empleado_id = self.empleado_data.get("id")
            if not empleado_id:
                return rx.toast.error("No se encontro el empleado")

            empleado = await onboarding_service.enviar_a_revision(empleado_id)
            self.estatus_actual = empleado.estatus_onboarding or ""
            self.empleado_data = empleado.model_dump(mode='json')

            return rx.toast.success("Expediente enviado a revision")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "enviando a revision")
        finally:
            self.saving = False
