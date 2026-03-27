"""
Página Mi Empresa del portal de cliente.

Refactor visual alineado al resto de la app:
- header con PageHeader y metadata compacta
- secciones sin cards innecesarias
- edición centralizada en modal para admins de empresa
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import reflex as rx
from pydantic import ValidationError as PydanticValidationError

from app.domain.enums import RolEmpresa
from app.core.text_utils import (
    capitalizar_con_preposiciones,
    capitalizar_palabras,
    capitalizar_razon_social,
    construir_mailto_href,
    construir_url_publica,
    formatear_porcentaje,
    formatear_telefono,
    formatear_url_display,
    normalizar_email,
    normalizar_mayusculas,
    obtener_iniciales,
)
from app.core.validation import (
    CAMPO_CODIGO_CORTO_EMPRESA,
    CAMPO_CODIGO_POSTAL,
    CAMPO_DIRECCION,
    CAMPO_EMAIL,
    CAMPO_NOMBRE_COMERCIAL,
    CAMPO_PAGINA_WEB,
    CAMPO_PRIMA_RIESGO,
    CAMPO_RAZON_SOCIAL,
    CAMPO_REGISTRO_PATRONAL,
    CAMPO_RFC,
    CAMPO_TELEFONO,
    CODIGO_CORTO_LEN,
    validar_email_usuario as validar_email_usuario,
    validar_nombre_completo_usuario as validar_nombre_contacto,
    validar_telefono_usuario as validar_telefono_usuario,
)
from app.core.validation.empresa_form_validators import (
    validar_codigo_corto_empresa as validar_codigo_corto,
    validar_codigo_postal_empresa as validar_codigo_postal,
    validar_email_empresa as validar_email,
    validar_prima_riesgo_empresa as validar_prima_riesgo,
    validar_registro_patronal_empresa as validar_registro_patronal,
    validar_telefono_empresa as validar_telefono,
)
from app.domain.models import EmpresaUpdate
from app.domain.models.user_profile import UserProfileUpdate
from app.presentation.components.ui import (
    detail_link_item,
    detail_text_item,
    form_input,
    metadata_divider,
    metadata_item,
    modal_formulario,
    modal_section_label,
    section_title,
)
from app.presentation.layouts.backoffice import page_header, page_layout
from app.presentation.pages.portal.state.portal_state import PortalState
from app.presentation.theme import Colors, Radius, Spacing, Typography
from app.modules.application import empresa_service, user_service


_NO_DISPONIBLE = "No disponible"

_VALIDADORES_FORMULARIO_MI_EMPRESA = {
    "codigo_corto": validar_codigo_corto,
    "telefono": validar_telefono,
    "email": validar_email,
    "codigo_postal": validar_codigo_postal,
    "registro_patronal": validar_registro_patronal,
    "prima_riesgo": validar_prima_riesgo,
    "contacto_nombre": validar_nombre_contacto,
    "contacto_telefono": validar_telefono_usuario,
    "contacto_email": validar_email_usuario,
}

_CAMPOS_ERROR_FORMULARIO_MI_EMPRESA = tuple(_VALIDADORES_FORMULARIO_MI_EMPRESA)


def _rol_empresa_label(valor: str | None) -> str:
    if not valor:
        return "Sin rol asignado"
    try:
        return RolEmpresa(valor).descripcion
    except ValueError:
        return capitalizar_con_preposiciones(valor.replace("_", " "))


def _parse_uuid(valor: str | None) -> UUID | None:
    if not valor:
        return None
    try:
        return UUID(str(valor))
    except (TypeError, ValueError):
        return None


class MiEmpresaState(PortalState):
    """State para la pantalla Mi Empresa."""

    mostrar_modal_edicion: bool = False
    saving_empresa: bool = False

    contacto_principal: dict = {}

    form_codigo_corto: str = ""
    form_telefono: str = ""
    form_email: str = ""
    form_pagina_web: str = ""
    form_direccion: str = ""
    form_codigo_postal: str = ""
    form_registro_patronal: str = ""
    form_prima_riesgo: str = ""
    form_contacto_nombre: str = ""
    form_contacto_cargo: str = ""
    form_contacto_telefono: str = ""
    form_contacto_email: str = ""

    error_codigo_corto: str = ""
    error_telefono: str = ""
    error_email: str = ""
    error_codigo_postal: str = ""
    error_registro_patronal: str = ""
    error_prima_riesgo: str = ""
    error_contacto_nombre: str = ""
    error_contacto_telefono: str = ""
    error_contacto_email: str = ""

    async def on_mount_mi_empresa(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.mostrar_seccion_empresa:
            yield rx.redirect("/portal")
            return
        if not self.usuario_actual.get("email"):
            await self._enriquecer_email_usuario_desde_token()
        async for _ in self._montar_pagina(self._fetch_mi_empresa):
            yield

    async def _fetch_mi_empresa(self):
        await self._cargar_datos_empresa_presentacion()
        await self._cargar_contacto_principal()

    async def _cargar_datos_empresa_presentacion(self):
        if not self.id_empresa_actual:
            self.datos_empresa = {}
            return

        try:
            empresa = await empresa_service.obtener_por_id(self.id_empresa_actual)
            prima_porcentaje = (
                Decimal(str(empresa.get_prima_riesgo_porcentaje()))
                if empresa.prima_riesgo is not None
                else None
            )
            estatus_raw = str(empresa.estatus or "")
            esta_activa = estatus_raw == "ACTIVO"

            self.datos_empresa = {
                "nombre_comercial": empresa.nombre_comercial or "",
                "nombre_comercial_display": capitalizar_palabras(empresa.nombre_comercial),
                "razon_social": empresa.razon_social or "",
                "razon_social_display": capitalizar_razon_social(empresa.razon_social),
                "rfc": normalizar_mayusculas(empresa.rfc),
                "codigo_corto": normalizar_mayusculas(empresa.codigo_corto or ""),
                "telefono": empresa.telefono or "",
                "telefono_display": formatear_telefono(empresa.telefono),
                "email": normalizar_email(empresa.email),
                "email_href": construir_mailto_href(empresa.email),
                "pagina_web": empresa.pagina_web or "",
                "pagina_web_display": formatear_url_display(empresa.pagina_web),
                "pagina_web_href": construir_url_publica(empresa.pagina_web),
                "direccion": empresa.direccion or "",
                "direccion_display": capitalizar_con_preposiciones(empresa.direccion),
                "codigo_postal": (empresa.codigo_postal or "").strip(),
                "registro_patronal": empresa.registro_patronal or "",
                "prima_riesgo": str(prima_porcentaje or ""),
                "prima_riesgo_display": formatear_porcentaje(prima_porcentaje),
                "estatus_badge_label": "Activo" if esta_activa else "Inactivo",
                "estatus_badge_scheme": "green" if esta_activa else "red",
            }
        except Exception as e:
            self.datos_empresa = {}
            self.manejar_error(e, "cargando datos de la empresa")

    async def _cargar_contacto_principal(self):
        usuarios: list[dict] = []
        if self.id_empresa_actual:
            try:
                usuarios = await user_service.listar_usuarios_empresa(self.id_empresa_actual)
            except Exception:
                usuarios = []

        contacto = self._seleccionar_contacto_principal(usuarios)
        self.contacto_principal = {
            "user_id": str(contacto.get("user_id", "") or ""),
            "nombre": contacto.get("nombre_completo", "") or "",
            "nombre_display": capitalizar_palabras(contacto.get("nombre_completo", "")),
            "cargo": _rol_empresa_label(contacto.get("rol_empresa", self.rol_empresa_actual)),
            "telefono": contacto.get("telefono", "") or "",
            "telefono_display": formatear_telefono(contacto.get("telefono", "")),
            "email": normalizar_email(contacto.get("email", "")),
            "email_href": construir_mailto_href(contacto.get("email", "")),
            "avatar_initials": obtener_iniciales(contacto.get("nombre_completo", "")),
        }

    def _seleccionar_contacto_principal(self, usuarios: list[dict]) -> dict:
        if not usuarios:
            return {
                "user_id": self.id_usuario,
                "nombre_completo": self.usuario_actual.get("nombre_completo", self.nombre_usuario),
                "telefono": self.usuario_actual.get("telefono", ""),
                "email": self.usuario_actual.get("email", ""),
                "rol_empresa": self.rol_empresa_actual,
            }

        activos = [
            usuario
            for usuario in usuarios
            if usuario.get("activo_empresa", True) and usuario.get("activo_perfil", True)
        ] or usuarios

        return sorted(
            activos,
            key=lambda usuario: (
                0 if usuario.get("es_principal") else 1,
                0 if usuario.get("rol_empresa") == "admin_empresa" else 1,
                0 if str(usuario.get("user_id", "")) == self.id_usuario else 1,
                (usuario.get("nombre_completo") or "").lower(),
            ),
        )[0]

    @rx.var
    def puede_editar_empresa(self) -> bool:
        return bool(self.es_admin_empresa and self.id_empresa_actual)

    def set_mostrar_modal_edicion(self, value: bool):
        self.mostrar_modal_edicion = bool(value)
        if not value:
            self._limpiar_errores_formulario()

    def set_form_codigo_corto(self, value: str):
        self.set_form_value(
            "codigo_corto",
            value,
            normalizador=normalizar_mayusculas,
            max_length=CODIGO_CORTO_LEN,
        )

    def set_form_telefono(self, value: str):
        self.set_form_value("telefono", value)

    def set_form_email(self, value: str):
        self.set_form_value("email", value)

    def set_form_pagina_web(self, value: str):
        self.set_form_value("pagina_web", value)

    def set_form_direccion(self, value: str):
        self.set_form_value("direccion", value)

    def set_form_codigo_postal(self, value: str):
        self.set_form_value("codigo_postal", value)

    def set_form_registro_patronal(self, value: str):
        self.set_form_value("registro_patronal", value)

    def set_form_prima_riesgo(self, value: str):
        self.set_form_value(
            "prima_riesgo",
            value,
            normalizador=lambda valor: (valor or "").replace("%", ""),
        )

    def set_form_contacto_nombre(self, value: str):
        self.set_form_value("contacto_nombre", value)

    def set_form_contacto_telefono(self, value: str):
        self.set_form_value("contacto_telefono", value)

    def set_form_contacto_email(self, value: str):
        self.set_form_value("contacto_email", value, normalizador=normalizar_email)

    def validar_campo_codigo_corto(self):
        self._validar_campo("codigo_corto")

    def validar_campo_telefono(self, _value: str = ""):
        self._validar_campo("telefono")

    def validar_campo_email(self, _value: str = ""):
        self._validar_campo("email")

    def validar_campo_codigo_postal(self, _value: str = ""):
        self._validar_campo("codigo_postal")

    def validar_campo_registro_patronal(self, _value: str = ""):
        self._validar_campo("registro_patronal")

    def validar_campo_prima_riesgo(self, _value: str = ""):
        self._validar_campo("prima_riesgo")

    def validar_campo_contacto_nombre(self):
        self._validar_campo("contacto_nombre")

    def validar_campo_contacto_telefono(self):
        self._validar_campo("contacto_telefono")

    def validar_campo_contacto_email(self):
        self._validar_campo("contacto_email")

    def _validar_campo(self, campo: str):
        validador = _VALIDADORES_FORMULARIO_MI_EMPRESA.get(campo)
        if not validador:
            return

        self.validar_y_asignar_error(
            valor=getattr(self, f"form_{campo}"),
            validador=validador,
            error_attr=f"error_{campo}",
        )

    def _validar_todos_los_campos(self) -> bool:
        return self.validar_lote_campos(
            [
                (
                    f"error_{campo}",
                    getattr(self, f"form_{campo}"),
                    _VALIDADORES_FORMULARIO_MI_EMPRESA[campo],
                )
                for campo in _VALIDADORES_FORMULARIO_MI_EMPRESA
            ]
        )

    def _limpiar_errores_formulario(self):
        self.limpiar_errores_campos(list(_CAMPOS_ERROR_FORMULARIO_MI_EMPRESA))

    def abrir_modal_edicion(self):
        if not self.puede_editar_empresa:
            return

        datos = self.datos_empresa
        contacto = self.contacto_principal

        self.form_codigo_corto = datos.get("codigo_corto", "") or ""
        self.form_telefono = datos.get("telefono", "") or ""
        self.form_email = datos.get("email", "") or ""
        self.form_pagina_web = datos.get("pagina_web", "") or ""
        self.form_direccion = capitalizar_con_preposiciones(datos.get("direccion", ""))
        self.form_codigo_postal = datos.get("codigo_postal", "") or ""
        self.form_registro_patronal = datos.get("registro_patronal", "") or ""
        self.form_prima_riesgo = datos.get("prima_riesgo", "") or ""
        self.form_contacto_nombre = contacto.get("nombre", "") or ""
        self.form_contacto_cargo = contacto.get("cargo", "") or ""
        self.form_contacto_telefono = contacto.get("telefono", "") or ""
        self.form_contacto_email = contacto.get("email", "") or ""

        self._limpiar_errores_formulario()
        self.mostrar_modal_edicion = True

    def cancelar_edicion(self):
        self.mostrar_modal_edicion = False
        self._limpiar_errores_formulario()

    def _validar_formulario(self) -> tuple[EmpresaUpdate, UserProfileUpdate, str] | None:
        if not self._validar_todos_los_campos():
            return None

        try:
            empresa_payload = EmpresaUpdate(
                codigo_corto=normalizar_mayusculas(self.form_codigo_corto) or None,
                telefono=self.form_telefono.strip() or None,
                email=normalizar_email(self.form_email) or None,
                pagina_web=self.form_pagina_web.strip() or None,
                direccion=self.form_direccion.strip() or None,
                codigo_postal=self.form_codigo_postal.strip() or None,
                registro_patronal=self.form_registro_patronal.strip() or None,
                prima_riesgo=Decimal(self.form_prima_riesgo.strip())
                if self.form_prima_riesgo.strip()
                else None,
            )
            contacto_payload = UserProfileUpdate(
                nombre_completo=self.form_contacto_nombre.strip() or None,
                telefono=self.form_contacto_telefono.strip() or None,
            )
            return (
                empresa_payload,
                contacto_payload,
                normalizar_email(self.form_contacto_email),
            )
        except PydanticValidationError as e:
            self.aplicar_errores_validacion(e, fallback_attr="error_codigo_corto")
            if not self.tiene_errores_en_campos(list(_CAMPOS_ERROR_FORMULARIO_MI_EMPRESA)):
                self.error_codigo_corto = "Revise los datos capturados"
            return None

    async def guardar_edicion(self):
        if not self.puede_editar_empresa:
            return rx.toast.error("No tienes permisos para editar la empresa")

        validacion = self._validar_formulario()
        if not validacion:
            return rx.toast.error("Revise los campos del formulario", position="top-center")

        empresa_payload, contacto_payload, nuevo_email_contacto = validacion
        contacto_user_id = _parse_uuid(self.contacto_principal.get("user_id") or self.id_usuario)

        self.saving_empresa = True
        try:
            await empresa_service.actualizar(self.id_empresa_actual, empresa_payload)

            if contacto_user_id:
                await user_service.actualizar_perfil(contacto_user_id, contacto_payload)

                email_actual = normalizar_email(self.contacto_principal.get("email", ""))
                if nuevo_email_contacto != email_actual:
                    await user_service.actualizar_email_usuario(contacto_user_id, nuevo_email_contacto)

                if str(contacto_user_id) == self.id_usuario:
                    self.usuario_actual = {
                        **self.usuario_actual,
                        "nombre_completo": contacto_payload.nombre_completo
                        or self.usuario_actual.get("nombre_completo", ""),
                        "telefono": contacto_payload.telefono
                        or self.usuario_actual.get("telefono", ""),
                        "email": nuevo_email_contacto or self.usuario_actual.get("email", ""),
                    }

            await self._fetch_mi_empresa()
            self.mostrar_modal_edicion = False
            self._limpiar_errores_formulario()
            return rx.toast.success("Empresa actualizada", position="top-center")
        except Exception as e:
            return self.manejar_error_con_toast(e, "al guardar la empresa")
        finally:
            self.saving_empresa = False


def _header_title() -> rx.Component:
    datos = MiEmpresaState.datos_empresa
    return rx.hstack(
        rx.text(
            datos["nombre_comercial_display"],
            size="6",
            weight="bold",
            color=Colors.TEXT_PRIMARY,
        ),
        rx.badge(
            datos["estatus_badge_label"],
            color_scheme=datos["estatus_badge_scheme"],
            variant="soft",
            size="1",
        ),
        spacing="3",
        align="center",
        wrap="wrap",
    )


def _header_subtitle() -> rx.Component:
    return rx.text(
        MiEmpresaState.datos_empresa["razon_social_display"],
        font_size="13px",
        color=Colors.TEXT_MUTED,
    )


def _header_actions() -> rx.Component:
    return rx.cond(
        MiEmpresaState.puede_editar_empresa,
        rx.button(
            rx.icon("pencil", size=16),
            "Editar",
            variant="outline",
            color_scheme="gray",
            size="2",
            on_click=MiEmpresaState.abrir_modal_edicion,
        ),
        rx.fragment(),
    )


def _metadata_strip() -> rx.Component:
    datos = MiEmpresaState.datos_empresa
    return rx.box(
        rx.flex(
            metadata_item(CAMPO_RFC.nombre, datos["rfc"]),
            metadata_divider(),
            metadata_item(CAMPO_CODIGO_CORTO_EMPRESA.nombre, datos["codigo_corto"]),
            width="100%",
            wrap="wrap",
            align="stretch",
            column_gap=Spacing.MD,
            row_gap=Spacing.SM,
        ),
        width="100%",
        padding_y=Spacing.SM,
        border_bottom=f"1px solid {Colors.BORDER}",
    )


def _seccion_contacto() -> rx.Component:
    datos = MiEmpresaState.datos_empresa
    return rx.vstack(
        section_title("Contacto"),
        rx.grid(
            detail_text_item(CAMPO_TELEFONO.nombre, datos["telefono_display"], fallback=_NO_DISPONIBLE),
            detail_link_item(CAMPO_EMAIL.nombre, datos["email"], datos["email_href"], fallback=_NO_DISPONIBLE),
            detail_link_item(
                CAMPO_PAGINA_WEB.nombre,
                datos["pagina_web_display"],
                datos["pagina_web_href"],
                external=True,
                fallback=_NO_DISPONIBLE,
            ),
            detail_text_item(CAMPO_DIRECCION.nombre, datos["direccion_display"], fallback=_NO_DISPONIBLE),
            detail_text_item(CAMPO_CODIGO_POSTAL.nombre, datos["codigo_postal"], fallback=_NO_DISPONIBLE),
            columns=rx.breakpoints(initial="1", md="2"),
            gap=Spacing.LG,
            width="100%",
        ),
        width="100%",
        gap=Spacing.MD,
        margin_bottom=Spacing.LG,
    )


def _seccion_imss() -> rx.Component:
    datos = MiEmpresaState.datos_empresa
    return rx.vstack(
        section_title("Configuración IMSS"),
        rx.grid(
            detail_text_item(
                CAMPO_REGISTRO_PATRONAL.nombre,
                datos["registro_patronal"],
                weight=Typography.WEIGHT_MEDIUM,
                fallback=_NO_DISPONIBLE,
            ),
            detail_text_item(
                CAMPO_PRIMA_RIESGO.nombre,
                datos["prima_riesgo_display"],
                weight=Typography.WEIGHT_MEDIUM,
                fallback=_NO_DISPONIBLE,
            ),
            columns=rx.breakpoints(initial="1", md="2"),
            gap=Spacing.LG,
            width="100%",
        ),
        width="100%",
        gap=Spacing.MD,
        margin_bottom=Spacing.LG,
    )


def _contacto_inline(
    texto,
    *,
    href="",
    icon_name="phone",
    as_link: bool = False,
) -> rx.Component:
    contenido = rx.hstack(
        rx.icon(icon_name, size=14, color=Colors.TEXT_SECONDARY),
        rx.cond(
            texto != "",
            rx.text(
                texto,
                font_size="12px",
                color=Colors.INFO if as_link else Colors.TEXT_SECONDARY,
            ),
            rx.text(
                _NO_DISPONIBLE,
                font_size="12px",
                color=Colors.TEXT_MUTED,
            ),
        ),
        spacing="2",
        align="center",
    )
    if not as_link:
        return contenido
    return rx.link(
        contenido,
        href=href,
        underline="none",
    )


def _seccion_contacto_principal() -> rx.Component:
    contacto = MiEmpresaState.contacto_principal
    return rx.vstack(
        section_title("Contacto principal"),
        rx.box(
            rx.flex(
                rx.center(
                    rx.text(
                        contacto["avatar_initials"],
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_SEMIBOLD,
                        color=Colors.INFO,
                    ),
                    width="40px",
                    height="40px",
                    border_radius=Radius.FULL,
                    background=Colors.INFO_LIGHT,
                    flex_shrink="0",
                ),
                rx.vstack(
                    rx.text(
                        contacto["nombre_display"],
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    rx.text(
                        contacto["cargo"],
                        font_size="12px",
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.flex(
                        _contacto_inline(contacto["telefono_display"], icon_name="phone"),
                        _contacto_inline(
                            contacto["email"],
                            href=contacto["email_href"],
                            icon_name="mail",
                            as_link=True,
                        ),
                        wrap="wrap",
                        align="center",
                        gap=Spacing.MD,
                        margin_top=Spacing.SM,
                        width="100%",
                    ),
                    spacing="0",
                    align="start",
                    width="100%",
                    flex="1",
                ),
                width="100%",
                align="center",
                wrap="wrap",
                gap=Spacing.MD,
            ),
            width="100%",
            padding=Spacing.LG,
            background=Colors.SECONDARY_LIGHT,
            border_radius=Radius.XL,
        ),
        width="100%",
        gap=Spacing.MD,
        margin_bottom=Spacing.LG,
    )


def _contenido_empresa() -> rx.Component:
    return rx.vstack(
        _metadata_strip(),
        _seccion_contacto(),
        _seccion_imss(),
        _seccion_contacto_principal(),
        width="100%",
        max_width="800px",
        spacing="0",
    )


def _modal_edicion_empresa() -> rx.Component:
    datos = MiEmpresaState.datos_empresa

    _disabled = {
        "disabled": True,
        "read_only": True,
        "background": Colors.SECONDARY_LIGHT,
        "color": Colors.TEXT_SECONDARY,
        "cursor": "not-allowed",
    }

    def _divider() -> rx.Component:
        return rx.box(
            height="1px",
            background=Colors.BORDER,
            margin_y=Spacing.BASE,
            width="100%",
        )

    contenido = rx.vstack(
        # -- Datos de empresa --
        modal_section_label("DATOS DE EMPRESA"),
        rx.grid(
            form_input(
                label=CAMPO_NOMBRE_COMERCIAL.nombre,
                value=datos["nombre_comercial_display"],
                label_variant="portal",
                style_variant="portal",
                **_disabled,
            ),
            form_input(
                label=CAMPO_RFC.nombre,
                value=datos["rfc"],
                label_variant="portal",
                style_variant="portal",
                **_disabled,
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        form_input(
            label=CAMPO_RAZON_SOCIAL.nombre,
            value=datos["razon_social_display"],
            label_variant="portal",
            style_variant="portal",
            **_disabled,
        ),
        rx.box(
            form_input(
                label=CAMPO_CODIGO_CORTO_EMPRESA.nombre,
                value=datos["codigo_corto"],
                hint=CAMPO_CODIGO_CORTO_EMPRESA.hint,
                label_variant="portal",
                style_variant="portal",
                **_disabled,
            ),
            max_width="120px",
        ),
        _divider(),
        # -- Contacto --
        modal_section_label("CONTACTO"),
        rx.grid(
            form_input(
                label=CAMPO_TELEFONO.nombre,
                placeholder=CAMPO_TELEFONO.placeholder,
                hint=CAMPO_TELEFONO.hint,
                value=MiEmpresaState.form_telefono,
                on_change=MiEmpresaState.set_form_telefono,
                on_blur=MiEmpresaState.validar_campo_telefono,
                error=MiEmpresaState.error_telefono,
                max_length=15,
                label_variant="portal",
                style_variant="portal",
            ),
            form_input(
                label=CAMPO_EMAIL.nombre,
                placeholder=CAMPO_EMAIL.placeholder,
                value=MiEmpresaState.form_email,
                on_change=MiEmpresaState.set_form_email,
                on_blur=MiEmpresaState.validar_campo_email,
                error=MiEmpresaState.error_email,
                label_variant="portal",
                style_variant="portal",
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        rx.grid(
            form_input(
                label=CAMPO_PAGINA_WEB.nombre,
                placeholder=CAMPO_PAGINA_WEB.placeholder,
                value=MiEmpresaState.form_pagina_web,
                on_change=MiEmpresaState.set_form_pagina_web,
                label_variant="portal",
                style_variant="portal",
            ),
            form_input(
                label=CAMPO_CODIGO_POSTAL.nombre,
                placeholder=CAMPO_CODIGO_POSTAL.placeholder,
                hint=CAMPO_CODIGO_POSTAL.hint,
                value=MiEmpresaState.form_codigo_postal,
                on_change=MiEmpresaState.set_form_codigo_postal,
                on_blur=MiEmpresaState.validar_campo_codigo_postal,
                error=MiEmpresaState.error_codigo_postal,
                max_length=5,
                label_variant="portal",
                style_variant="portal",
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        form_input(
            label=CAMPO_DIRECCION.nombre,
            placeholder=CAMPO_DIRECCION.placeholder,
            value=MiEmpresaState.form_direccion,
            on_change=MiEmpresaState.set_form_direccion,
            label_variant="portal",
            style_variant="portal",
        ),
        _divider(),
        # -- Configuracion IMSS --
        modal_section_label("CONFIGURACION IMSS"),
        rx.grid(
            form_input(
                label=CAMPO_REGISTRO_PATRONAL.nombre,
                placeholder=CAMPO_REGISTRO_PATRONAL.placeholder,
                hint=CAMPO_REGISTRO_PATRONAL.hint,
                value=MiEmpresaState.form_registro_patronal,
                on_change=MiEmpresaState.set_form_registro_patronal,
                on_blur=MiEmpresaState.validar_campo_registro_patronal,
                error=MiEmpresaState.error_registro_patronal,
                label_variant="portal",
                style_variant="portal",
            ),
            form_input(
                label=CAMPO_PRIMA_RIESGO.label,
                placeholder=CAMPO_PRIMA_RIESGO.placeholder,
                hint=CAMPO_PRIMA_RIESGO.hint,
                value=MiEmpresaState.form_prima_riesgo,
                on_change=MiEmpresaState.set_form_prima_riesgo,
                on_blur=MiEmpresaState.validar_campo_prima_riesgo,
                error=MiEmpresaState.error_prima_riesgo,
                label_variant="portal",
                style_variant="portal",
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        _divider(),
        # -- Contacto principal --
        modal_section_label("CONTACTO PRINCIPAL"),
        rx.grid(
            form_input(
                label="Nombre",
                value=MiEmpresaState.form_contacto_nombre,
                on_change=MiEmpresaState.set_form_contacto_nombre,
                on_blur=MiEmpresaState.validar_campo_contacto_nombre,
                error=MiEmpresaState.error_contacto_nombre,
                label_variant="portal",
                style_variant="portal",
            ),
            form_input(
                label="Cargo / puesto",
                value=MiEmpresaState.form_contacto_cargo,
                hint="Se deriva del rol actual del usuario.",
                label_variant="portal",
                style_variant="portal",
                **_disabled,
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        rx.grid(
            form_input(
                label="Telefono",
                value=MiEmpresaState.form_contacto_telefono,
                on_change=MiEmpresaState.set_form_contacto_telefono,
                on_blur=MiEmpresaState.validar_campo_contacto_telefono,
                error=MiEmpresaState.error_contacto_telefono,
                max_length=10,
                label_variant="portal",
                style_variant="portal",
            ),
            form_input(
                label="Email",
                value=MiEmpresaState.form_contacto_email,
                label_variant="portal",
                style_variant="portal",
                **_disabled,
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )

    return modal_formulario(
        open=MiEmpresaState.mostrar_modal_edicion,
        titulo="Editar empresa",
        descripcion="Nombre comercial, razon social, RFC y codigo corto se administran desde la configuracion general.",
        contenido=contenido,
        on_guardar=MiEmpresaState.guardar_edicion,
        on_cancelar=MiEmpresaState.cancelar_edicion,
        loading=MiEmpresaState.saving_empresa,
        icono="building",
        color_icono="teal",
        color_guardar="teal",
        texto_guardar="Guardar cambios",
        texto_guardando="Guardando...",
        scroll_body=True,
        max_width="760px",
    )


def mi_empresa_page() -> rx.Component:
    """Página del perfil de empresa en el portal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="",
                subtitulo="",
                titulo_compuesto=_header_title(),
                subtitulo_compuesto=_header_subtitle(),
                icono="building-2",
                accion_principal=_header_actions(),
                show_divider=False,
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
            ),
            toolbar=rx.fragment(),
            content=rx.cond(
                MiEmpresaState.loading,
                rx.center(rx.spinner(size="3"), padding_y="60px"),
                rx.cond(
                    MiEmpresaState.datos_empresa,
                    rx.vstack(
                        _contenido_empresa(),
                        _modal_edicion_empresa(),
                        width="100%",
                        spacing="0",
                    ),
                    rx.center(
                        rx.text(
                            "No se encontraron datos de la empresa",
                            color=Colors.TEXT_SECONDARY,
                        ),
                        padding_y="60px",
                    ),
                ),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MiEmpresaState.on_mount_mi_empresa,
    )
