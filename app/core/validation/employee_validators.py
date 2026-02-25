"""Validadores centralizados para campos de empleados (UI)."""
import re
from datetime import date

from .constants import (
    CURP_PATTERN,
    RFC_PERSONA_PATTERN,
    NSS_PATTERN,
    EMAIL_PATTERN,
    CURP_LEN,
    RFC_PERSONA_LEN,
    NSS_LEN,
    NOMBRE_EMPLEADO_MIN,
    NOMBRE_EMPLEADO_MAX,
    APELLIDO_MIN,
    APELLIDO_MAX,
    EMAIL_MAX,
    TELEFONO_DIGITOS,
    TELEFONO_PATTERN,
    MOTIVO_RESTRICCION_MIN,
    NOMBRE_CONTACTO_MAX,
)
from .common_validators import (
    validar_select_requerido,
    validar_fecha_no_futura,
    validar_texto_opcional,
)
from .custom_validators import limpiar_telefono


# =============================================================================
# VALIDADORES BASE (BACKOFFICE + PORTAL)
# =============================================================================


def validar_curp_empleado(curp: str) -> str:
    if not curp:
        return "CURP es obligatorio"

    curp_limpio = curp.strip().upper()

    if len(curp_limpio) != CURP_LEN:
        return f"CURP debe tener {CURP_LEN} caracteres (tiene {len(curp_limpio)})"

    if not re.match(CURP_PATTERN, curp_limpio):
        primeros_4 = curp_limpio[:4]
        if not primeros_4.isalpha():
            return "CURP: Los primeros 4 caracteres deben ser letras"

        fecha = curp_limpio[4:10]
        if not fecha.isdigit():
            return "CURP: Los caracteres 5-10 deben ser números (fecha)"

        sexo = curp_limpio[10] if len(curp_limpio) > 10 else ""
        if sexo not in "HM":
            return "CURP: El carácter 11 debe ser H o M (sexo)"

        estado = curp_limpio[11:13]
        if estado and not estado.isalpha():
            return "CURP: Los caracteres 12-13 deben ser letras (estado)"

        return "CURP con formato inválido"

    return ""


def validar_rfc_empleado(rfc: str) -> str:
    if not rfc:
        return ""  # opcional en backoffice

    rfc_limpio = rfc.strip().upper()

    if len(rfc_limpio) != RFC_PERSONA_LEN:
        return f"RFC debe tener {RFC_PERSONA_LEN} caracteres (tiene {len(rfc_limpio)})"

    if not re.match(RFC_PERSONA_PATTERN, rfc_limpio):
        primeros_4 = rfc_limpio[:4]
        if not all(c.isalpha() or c in '&Ñ' for c in primeros_4):
            return "RFC: Los primeros 4 caracteres deben ser letras"

        fecha = rfc_limpio[4:10]
        if not fecha.isdigit():
            return "RFC: Los caracteres 5-10 deben ser números (fecha)"

        return "RFC con formato inválido"

    return ""


def validar_nss_empleado(nss: str) -> str:
    if not nss:
        return ""  # opcional en backoffice

    nss_limpio = str(nss).strip()
    if not re.match(NSS_PATTERN, nss_limpio):
        if len(nss_limpio) != NSS_LEN:
            return f"NSS debe tener {NSS_LEN} dígitos (tiene {len(nss_limpio)})"
        if not nss_limpio.isdigit():
            return "NSS debe contener solo números"
        return "NSS con formato inválido"

    return ""


def validar_nombre_empleado(nombre: str) -> str:
    if not nombre:
        return "Nombre es obligatorio"

    nombre_limpio = nombre.strip()
    if len(nombre_limpio) < NOMBRE_EMPLEADO_MIN:
        return f"Nombre debe tener al menos {NOMBRE_EMPLEADO_MIN} caracteres"
    if len(nombre_limpio) > NOMBRE_EMPLEADO_MAX:
        return f"Nombre no puede exceder {NOMBRE_EMPLEADO_MAX} caracteres"
    return ""


def validar_apellido_empleado(apellido: str, etiqueta: str = "Apellido") -> str:
    if not apellido:
        return f"{etiqueta} es obligatorio"

    apellido_limpio = apellido.strip()
    if len(apellido_limpio) < APELLIDO_MIN:
        return f"{etiqueta} debe tener al menos {APELLIDO_MIN} caracteres"
    if len(apellido_limpio) > APELLIDO_MAX:
        return f"{etiqueta} no puede exceder {APELLIDO_MAX} caracteres"
    return ""


def validar_apellido_paterno_empleado(apellido: str) -> str:
    return validar_apellido_empleado(apellido, "Apellido paterno")


def validar_apellido_materno_empleado(apellido: str) -> str:
    return validar_apellido_empleado(apellido, "Apellido materno")


def validar_email_empleado(email: str) -> str:
    if not email:
        return ""

    email_limpio = email.strip().lower()
    if len(email_limpio) > EMAIL_MAX:
        return f"Email no puede exceder {EMAIL_MAX} caracteres"
    if not re.match(EMAIL_PATTERN, email_limpio):
        return "Email con formato inválido"
    return ""


def validar_telefono_empleado(telefono: str) -> str:
    if not telefono:
        return ""

    telefono_limpio = limpiar_telefono(telefono)
    if len(telefono_limpio) != TELEFONO_DIGITOS:
        return f"Teléfono debe tener {TELEFONO_DIGITOS} dígitos (tiene {len(telefono_limpio)})"
    return ""


def validar_fecha_nacimiento_empleado(
    fecha: str,
    *,
    requerida: bool = False,
    edad_min: int = 16,
    edad_max: int = 100,
) -> str:
    if not fecha:
        return "Fecha de nacimiento es obligatoria" if requerida else ""

    error = validar_fecha_no_futura(fecha, "fecha de nacimiento")
    if error:
        return error

    try:
        fecha_obj = date.fromisoformat(fecha)
        hoy = date.today()
        edad = hoy.year - fecha_obj.year
        if (hoy.month, hoy.day) < (fecha_obj.month, fecha_obj.day):
            edad -= 1

        if edad < edad_min:
            return f"El empleado debe tener al menos {edad_min} años"
        if edad > edad_max:
            return "Fecha de nacimiento no parece válida"
    except ValueError:
        return "Fecha con formato inválido"

    return ""


def validar_empresa_seleccionada_empleado(_empresa_id: str) -> str:
    """Empresa ya no es requerida en este flujo."""
    return ""


def validar_motivo_restriccion_empleado(motivo: str) -> str:
    if not motivo:
        return "El motivo es obligatorio"

    motivo_limpio = motivo.strip()
    if len(motivo_limpio) < MOTIVO_RESTRICCION_MIN:
        return f"El motivo debe tener al menos {MOTIVO_RESTRICCION_MIN} caracteres"
    return ""


# =============================================================================
# VARIANTES PORTAL (obligatorias / específicas)
# =============================================================================


def validar_rfc_empleado_requerido(rfc: str) -> str:
    if not rfc:
        return "RFC es obligatorio"
    return validar_rfc_empleado(rfc)


def validar_nss_empleado_requerido(nss: str) -> str:
    if not nss:
        return "NSS es obligatorio"
    return validar_nss_empleado(nss)


def validar_telefono_empleado_requerido(telefono: str) -> str:
    if not telefono:
        return "Telefono es obligatorio"
    return validar_telefono_empleado(telefono)


def validar_genero_empleado_requerido(genero: str) -> str:
    return validar_select_requerido(genero, "genero")


def validar_contacto_emergencia_nombre(nombre: str) -> str:
    return validar_texto_opcional(nombre, "nombre del contacto", max_length=NOMBRE_CONTACTO_MAX)


def validar_contacto_emergencia_telefono(telefono: str) -> str:
    if not telefono:
        return ""
    telefono_limpio = limpiar_telefono(telefono)
    if not re.match(TELEFONO_PATTERN, telefono_limpio):
        return f"Telefono debe tener {TELEFONO_DIGITOS} digitos (tiene {len(telefono_limpio)})"
    return ""


__all__ = [
    "validar_curp_empleado",
    "validar_rfc_empleado",
    "validar_nss_empleado",
    "validar_nombre_empleado",
    "validar_apellido_empleado",
    "validar_apellido_paterno_empleado",
    "validar_apellido_materno_empleado",
    "validar_email_empleado",
    "validar_telefono_empleado",
    "validar_fecha_nacimiento_empleado",
    "validar_empresa_seleccionada_empleado",
    "validar_motivo_restriccion_empleado",
    "validar_rfc_empleado_requerido",
    "validar_nss_empleado_requerido",
    "validar_telefono_empleado_requerido",
    "validar_genero_empleado_requerido",
    "validar_contacto_emergencia_nombre",
    "validar_contacto_emergencia_telefono",
]
