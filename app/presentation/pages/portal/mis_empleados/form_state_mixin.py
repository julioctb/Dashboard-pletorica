"""Reusable form behavior for the portal employee management state."""

from __future__ import annotations

from datetime import date
from typing import List

import reflex as rx

from app.core.ui_helpers import opciones_desde_enum
from app.core.utils import normalize_date_input
from app.core.validation import (
    normalizar_clabe_interbancaria,
    normalizar_cuenta_bancaria,
    validar_apellido_materno_empleado,
    validar_apellido_paterno_empleado as validar_apellido_paterno,
    validar_banco_empleado as validar_banco,
    validar_clabe_empleado as validar_clabe,
    validar_contacto_emergencia_nombre,
    validar_contacto_emergencia_telefono,
    validar_cuenta_bancaria_empleado as validar_cuenta_bancaria,
    validar_curp_empleado as validar_curp,
    validar_email_empleado as validar_email,
    validar_fecha_nacimiento_empleado,
    validar_genero_empleado_requerido,
    validar_nombre_empleado as validar_nombre,
    validar_nss_empleado_requerido,
    validar_rfc_empleado_requerido,
    validar_telefono_empleado_requerido,
    normalizar_nombre_banco as normalizar_banco,
)
from app.modules.empleados.domain.enums import GeneroEmpleado


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


class MisEmpleadosFormStateMixin:
    """Setters, validators and computed vars for employee form handling."""

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
        tiene_datos = any(
            [
                str(snapshot.get("cuenta_bancaria", "") or ""),
                str(snapshot.get("banco", "") or ""),
                str(snapshot.get("clabe_interbancaria", "") or ""),
            ]
        )
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
