"""Helpers compartidos para formularios de empleados en states de Reflex."""

from __future__ import annotations

from datetime import date
from typing import Any, Callable, Sequence

from core.core.utils import normalize_date_input, parse_date_input
from core.core.validation import (
    normalizar_clabe_interbancaria,
    normalizar_cuenta_bancaria,
    normalizar_nombre_banco,
)
from core.domain.models.empleado_descuento_recurrente import (
    DESCUENTOS_RECURRENTES_CONFIG,
    DESCUENTOS_RECURRENTES_POR_FORM_KEY,
    EmpleadoDescuentoRecurrenteCreate,
)

_EMPLOYEE_RECURRENT_DISCOUNT_FORM_DEFAULTS = {}
for _meta_descuento in DESCUENTOS_RECURRENTES_CONFIG:
    _form_key = _meta_descuento["form_key"]
    _EMPLOYEE_RECURRENT_DISCOUNT_FORM_DEFAULTS.update(
        {
            f"form_descuento_{_form_key}_monto": "",
            f"form_descuento_{_form_key}_inicio": "",
            f"form_descuento_{_form_key}_fin": "",
            f"form_descuento_{_form_key}_notas": "",
        }
    )


class EmployeeFormStateMixin:
    """Lógica compartida para formulario/validación de empleados.

    No declara vars de Reflex. Solo concentra helpers reutilizables para
    states que ya exponen explícitamente `form_*` y `error_*`.
    """

    _EMPLOYEE_COMMON_FORM_DEFAULTS = {
        "form_curp": "",
        "form_nombre": "",
        "form_apellido_paterno": "",
        "form_apellido_materno": "",
        "form_rfc": "",
        "form_nss": "",
        "form_fecha_ingreso": "",
        "form_fecha_nacimiento": "",
        "form_genero": "",
        "form_telefono": "",
        "form_email": "",
        "form_direccion": "",
        "form_cuenta_bancaria": "",
        "form_banco": "",
        "form_clabe": "",
        "form_notas": "",
    }

    _EMPLOYEE_SPLIT_CONTACT_FORM_DEFAULTS = {
        "form_contacto_nombre": "",
        "form_contacto_telefono": "",
        "form_contacto_parentesco": "",
    }

    def _set_form_upper_field(self, attr: str, value: str) -> None:
        setattr(self, attr, value.upper() if value else "")

    def _set_form_lower_field(self, attr: str, value: str) -> None:
        setattr(self, attr, value.lower() if value else "")

    def _set_form_plain_field(self, attr: str, value: str) -> None:
        setattr(self, attr, value if value else "")

    @staticmethod
    def _split_contacto_emergencia(value: str | None) -> tuple[str, str, str]:
        """Descompone `Nombre / Telefono / Parentesco` a campos separados."""
        if not value:
            return "", "", ""
        partes = [parte.strip() for parte in value.split(" / ")]
        nombre = partes[0] if len(partes) > 0 else ""
        telefono = partes[1] if len(partes) > 1 else ""
        parentesco = partes[2] if len(partes) > 2 else ""
        return nombre, telefono, parentesco

    def _construir_contacto_emergencia_compartido(self) -> str | None:
        """Construye el valor de contacto según el modo del state."""
        if hasattr(self, "form_contacto_emergencia"):
            valor = getattr(self, "form_contacto_emergencia", "")
            return valor.strip() or None

        partes = [
            getattr(self, "form_contacto_nombre", "").strip(),
            getattr(self, "form_contacto_telefono", "").strip(),
            getattr(self, "form_contacto_parentesco", "").strip(),
        ]
        if any(partes):
            return " / ".join(parte for parte in partes if parte)
        return None

    def _reset_employee_form_fields(
        self,
        *,
        error_fields: Sequence[str],
        extra_defaults: dict[str, Any] | None = None,
    ) -> None:
        """Limpia los campos comunes del formulario de empleado."""
        defaults = dict(self._EMPLOYEE_COMMON_FORM_DEFAULTS)
        if hasattr(self, "form_contacto_emergencia"):
            defaults["form_contacto_emergencia"] = ""
        else:
            defaults.update(self._EMPLOYEE_SPLIT_CONTACT_FORM_DEFAULTS)
        defaults["form_fecha_ingreso"] = date.today().isoformat()
        defaults.update(_EMPLOYEE_RECURRENT_DISCOUNT_FORM_DEFAULTS)

        if extra_defaults:
            defaults.update(extra_defaults)

        for attr, default in defaults.items():
            if hasattr(self, attr):
                setattr(self, attr, default)

        if hasattr(self, "es_edicion"):
            self.es_edicion = False
        if hasattr(self, "empleado_id_edicion"):
            self.empleado_id_edicion = 0
        if hasattr(self, "empleado_editando_id"):
            self.empleado_editando_id = 0

        self.limpiar_errores_campos(list(error_fields))

    def _llenar_formulario_empleado_compartido(self, empleado: dict) -> None:
        """Carga en el formulario los campos comunes de un empleado."""
        if hasattr(self, "form_empresa_id"):
            empresa_id = empleado.get("empresa_id")
            self.form_empresa_id = str(empresa_id) if empresa_id else ""

        self.form_curp = empleado.get("curp", "") or ""
        self.form_nombre = empleado.get("nombre", "") or ""
        self.form_apellido_paterno = empleado.get("apellido_paterno", "") or ""
        self.form_apellido_materno = empleado.get("apellido_materno", "") or ""
        self.form_rfc = empleado.get("rfc", "") or ""
        self.form_nss = empleado.get("nss", "") or ""
        self.form_fecha_ingreso = (
            empleado.get("fecha_ingreso_iso", "")
            or empleado.get("fecha_ingreso", "")
            or date.today().isoformat()
        )
        self.form_fecha_nacimiento = (
            empleado.get("fecha_nacimiento_iso", "")
            or empleado.get("fecha_nacimiento", "")
            or ""
        )
        self.form_genero = empleado.get("genero", "") or ""
        self.form_telefono = empleado.get("telefono", "") or ""
        self.form_email = empleado.get("email", "") or ""
        self.form_direccion = empleado.get("direccion", "") or ""
        if hasattr(self, "form_cuenta_bancaria"):
            self.form_cuenta_bancaria = normalizar_cuenta_bancaria(
                empleado.get("cuenta_bancaria", "")
            )
        if hasattr(self, "form_banco"):
            self.form_banco = normalizar_nombre_banco(empleado.get("banco", ""))
        if hasattr(self, "form_clabe"):
            self.form_clabe = normalizar_clabe_interbancaria(
                empleado.get("clabe_interbancaria", "")
            )
        self.form_notas = empleado.get("notas", "") or ""

        contacto = empleado.get("contacto_emergencia", "") or ""
        if hasattr(self, "form_contacto_emergencia"):
            self.form_contacto_emergencia = contacto
        else:
            (
                self.form_contacto_nombre,
                self.form_contacto_telefono,
                self.form_contacto_parentesco,
            ) = self._split_contacto_emergencia(contacto)

        self._llenar_formulario_descuentos_recurrentes(
            empleado.get("descuentos_configurados", []) or []
        )

    def _payload_base_empleado(self) -> dict[str, Any]:
        """Construye el payload común para create/update de empleado."""
        payload = {
            "rfc": self.form_rfc or None,
            "nss": self.form_nss or None,
            "nombre": self.form_nombre or None,
            "apellido_paterno": self.form_apellido_paterno or None,
            "apellido_materno": self.form_apellido_materno or None,
            "fecha_ingreso": (
                parse_date_input(self.form_fecha_ingreso)
                if self.form_fecha_ingreso
                else None
            ),
            "fecha_nacimiento": (
                parse_date_input(self.form_fecha_nacimiento)
                if self.form_fecha_nacimiento
                else None
            ),
            "genero": self.form_genero or None,
            "telefono": self.form_telefono or None,
            "email": self.form_email or None,
            "direccion": self.form_direccion or None,
            "contacto_emergencia": self._construir_contacto_emergencia_compartido(),
            "notas": self.form_notas or None,
        }
        if hasattr(self, "form_cuenta_bancaria"):
            payload["cuenta_bancaria"] = normalizar_cuenta_bancaria(
                getattr(self, "form_cuenta_bancaria", "")
            ) or None
        if hasattr(self, "form_banco"):
            payload["banco"] = normalizar_nombre_banco(
                getattr(self, "form_banco", "")
            ) or None
        if hasattr(self, "form_clabe"):
            payload["clabe_interbancaria"] = normalizar_clabe_interbancaria(
                getattr(self, "form_clabe", "")
            ) or None
        return payload

    def _validar_formulario_empleado_compartido(
        self,
        *,
        error_fields: Sequence[str],
        required_validations: Sequence[tuple[str, Any, Callable[[Any], str]]],
        optional_validations: Sequence[tuple[str, Any, Callable[[Any], str]]],
        curp_validator: Callable[[Any], str] | None = None,
    ) -> bool:
        """Ejecuta validación declarativa del formulario de empleado."""
        self.limpiar_errores_campos(list(error_fields))
        es_valido = True

        if curp_validator and not getattr(self, "es_edicion", False):
            if not self.validar_y_asignar_error(
                valor=getattr(self, "form_curp", ""),
                validador=curp_validator,
                error_attr="error_curp",
            ):
                es_valido = False

        if required_validations and not self.validar_lote_campos(list(required_validations)):
            es_valido = False

        for error_attr, valor, validador in optional_validations:
            if valor and not self.validar_y_asignar_error(
                valor=valor,
                validador=validador,
                error_attr=error_attr,
            ):
                es_valido = False

        return es_valido

    def _set_form_fecha_ingreso_value(self, value: str) -> None:
        """Actualiza fecha_ingreso y conserva el prefilling de descuentos nuevos."""
        self.form_fecha_ingreso = normalize_date_input(value)
        if hasattr(self, "error_fecha_ingreso"):
            self.error_fecha_ingreso = ""

        for meta in DESCUENTOS_RECURRENTES_CONFIG:
            monto_attr = f'form_descuento_{meta["form_key"]}_monto'
            inicio_attr = f'form_descuento_{meta["form_key"]}_inicio'
            if (
                hasattr(self, monto_attr)
                and hasattr(self, inicio_attr)
                and getattr(self, monto_attr, "").strip()
                and not getattr(self, inicio_attr, "").strip()
            ):
                setattr(self, inicio_attr, self.form_fecha_ingreso)

    def _set_form_descuento_recurrente_field(
        self,
        form_key: str,
        field_name: str,
        value: str,
    ) -> None:
        """Set genérico de campos de descuentos recurrentes."""
        if form_key not in DESCUENTOS_RECURRENTES_POR_FORM_KEY:
            return

        attr = f"form_descuento_{form_key}_{field_name}"
        if not hasattr(self, attr):
            return

        if field_name in {"inicio", "fin"}:
            setattr(self, attr, normalize_date_input(value))
        else:
            setattr(self, attr, value if value else "")
        if hasattr(self, "error_descuentos_recurrentes"):
            self.error_descuentos_recurrentes = ""

        if field_name == "monto" and str(value or "").strip():
            inicio_attr = f"form_descuento_{form_key}_inicio"
            if hasattr(self, inicio_attr) and not getattr(self, inicio_attr, "").strip():
                setattr(
                    self,
                    inicio_attr,
                    getattr(self, "form_fecha_ingreso", "") or date.today().isoformat(),
                )

    def _llenar_formulario_descuentos_recurrentes(
        self,
        descuentos_configurados: list[dict],
    ) -> None:
        """Carga descuentos recurrentes ya configurados en el formulario."""
        for attr, default in _EMPLOYEE_RECURRENT_DISCOUNT_FORM_DEFAULTS.items():
            if hasattr(self, attr):
                setattr(self, attr, default)

        for descuento in descuentos_configurados:
            meta = DESCUENTOS_RECURRENTES_POR_FORM_KEY.get(
                descuento.get("form_key", "")
            )
            if meta is None:
                meta = next(
                    (
                        item
                        for item in DESCUENTOS_RECURRENTES_CONFIG
                        if item["concepto_clave"] == descuento.get("concepto_clave")
                    ),
                    None,
                )
            if meta is None:
                continue

            form_key = meta["form_key"]
            monto = descuento.get("monto_periodico")
            monto_value = ""
            if monto not in (None, ""):
                monto_value = f"{float(monto):.2f}"

            setattr(self, f"form_descuento_{form_key}_monto", monto_value)
            setattr(
                self,
                f"form_descuento_{form_key}_inicio",
                descuento.get("fecha_inicio", "") or "",
            )
            setattr(
                self,
                f"form_descuento_{form_key}_fin",
                descuento.get("fecha_fin", "") or "",
            )
            setattr(
                self,
                f"form_descuento_{form_key}_notas",
                descuento.get("notas", "") or "",
            )

    def _validar_fecha_ingreso_form(
        self,
        *,
        error_attr: str = "error_fecha_ingreso",
    ) -> bool:
        """Valida fecha_ingreso como dato maestro obligatorio."""
        if hasattr(self, error_attr):
            setattr(self, error_attr, "")

        if not getattr(self, "form_fecha_ingreso", "").strip():
            if hasattr(self, error_attr):
                setattr(self, error_attr, "La fecha de ingreso es obligatoria")
            return False

        if parse_date_input(self.form_fecha_ingreso) is None:
            if hasattr(self, error_attr):
                setattr(self, error_attr, "La fecha de ingreso no es válida")
            return False

        return True

    def _construir_descuentos_recurrentes_form(
        self,
        *,
        empleado_id: int = 0,
        error_attr: str = "error_descuentos_recurrentes",
    ) -> list[EmpleadoDescuentoRecurrenteCreate] | None:
        """Normaliza la sección de descuentos recurrentes del formulario."""
        if hasattr(self, error_attr):
            setattr(self, error_attr, "")

        descuentos: list[EmpleadoDescuentoRecurrenteCreate] = []
        fecha_ingreso_default = getattr(self, "form_fecha_ingreso", "").strip()

        for meta in DESCUENTOS_RECURRENTES_CONFIG:
            form_key = meta["form_key"]
            monto = getattr(self, f"form_descuento_{form_key}_monto", "").strip()
            fecha_inicio = getattr(self, f"form_descuento_{form_key}_inicio", "").strip()
            fecha_fin = getattr(self, f"form_descuento_{form_key}_fin", "").strip()
            notas = getattr(self, f"form_descuento_{form_key}_notas", "").strip()

            if not any([monto, fecha_inicio, fecha_fin, notas]):
                continue

            if not monto:
                if hasattr(self, error_attr):
                    setattr(
                        self,
                        error_attr,
                        f'Capture un monto para {meta["label"]}.',
                    )
                return None

            fecha_inicio_valor = fecha_inicio or fecha_ingreso_default
            if not fecha_inicio_valor:
                if hasattr(self, error_attr):
                    setattr(
                        self,
                        error_attr,
                        f'Capture una fecha de inicio para {meta["label"]}.',
                    )
                return None

            try:
                descuentos.append(
                    EmpleadoDescuentoRecurrenteCreate(
                        empleado_id=empleado_id,
                        concepto_clave=meta["concepto_clave"],
                        monto_periodico=monto,
                        fecha_inicio=parse_date_input(fecha_inicio_valor),
                        fecha_fin=(
                            parse_date_input(fecha_fin)
                            if fecha_fin
                            else None
                        ),
                        notas=notas or None,
                    )
                )
            except Exception as exc:
                if hasattr(self, error_attr):
                    setattr(
                        self,
                        error_attr,
                        f'{meta["label"]}: {exc}',
                    )
                return None

        return descuentos
