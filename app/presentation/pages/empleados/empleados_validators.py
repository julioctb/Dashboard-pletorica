"""
Validadores de formulario para empleados.

Validación frontend sincronizada con las reglas de la entidad Empleado.
Usa patrones y constantes centralizados de app.core.validation.
"""
import re

from app.core.validation import (
    # Patrones
    CURP_PATTERN,
    RFC_PERSONA_PATTERN,
    NSS_PATTERN,
    EMAIL_PATTERN,
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
)


def validar_curp(curp: str) -> str:
    """
    Valida formato de CURP mexicano.

    Formato: AAAA######AAAAAA##
    - Posición 1-4: Letras (apellidos y nombre)
    - Posición 5-10: Fecha nacimiento (AAMMDD)
    - Posición 11: Sexo (H/M)
    - Posición 12-13: Estado (2 letras)
    - Posición 14-16: Consonantes internas
    - Posición 17: Homoclave
    - Posición 18: Dígito verificador

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not curp:
        return "CURP es obligatorio"

    curp_limpio = curp.strip().upper()

    if len(curp_limpio) != CURP_LEN:
        return f"CURP debe tener {CURP_LEN} caracteres (tiene {len(curp_limpio)})"

    if not re.match(CURP_PATTERN, curp_limpio):
        # Validaciones específicas para mejor feedback
        primeros_4 = curp_limpio[:4]
        if not primeros_4.isalpha():
            return "CURP: Los primeros 4 caracteres deben ser letras"

        fecha = curp_limpio[4:10]
        if not fecha.isdigit():
            return "CURP: Los caracteres 5-10 deben ser números (fecha)"

        sexo = curp_limpio[10]
        if sexo not in "HM":
            return "CURP: El carácter 11 debe ser H o M (sexo)"

        estado = curp_limpio[11:13]
        if not estado.isalpha():
            return "CURP: Los caracteres 12-13 deben ser letras (estado)"

        return "CURP con formato inválido"

    return ""


def validar_rfc(rfc: str) -> str:
    """
    Valida formato de RFC persona física (13 caracteres).

    Formato: AAAA######XXX
    - 4 letras (apellidos y nombre)
    - 6 dígitos (fecha nacimiento AAMMDD)
    - 3 caracteres (homoclave)

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not rfc:
        return ""  # RFC es opcional

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


def validar_nss(nss: str) -> str:
    """
    Valida formato de Número de Seguro Social IMSS.

    Debe ser 11 dígitos numéricos.

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not nss:
        return ""  # NSS es opcional

    nss_limpio = nss.strip()

    if not re.match(NSS_PATTERN, nss_limpio):
        if len(nss_limpio) != NSS_LEN:
            return f"NSS debe tener {NSS_LEN} dígitos (tiene {len(nss_limpio)})"
        if not nss_limpio.isdigit():
            return "NSS debe contener solo números"
        return "NSS con formato inválido"

    return ""


def validar_nombre(nombre: str) -> str:
    """
    Valida el nombre del empleado.

    - Obligatorio
    - Mínimo 2 caracteres
    - Máximo 100 caracteres

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not nombre:
        return "Nombre es obligatorio"

    nombre_limpio = nombre.strip()

    if len(nombre_limpio) < NOMBRE_EMPLEADO_MIN:
        return f"Nombre debe tener al menos {NOMBRE_EMPLEADO_MIN} caracteres"

    if len(nombre_limpio) > NOMBRE_EMPLEADO_MAX:
        return f"Nombre no puede exceder {NOMBRE_EMPLEADO_MAX} caracteres"

    return ""


def validar_apellido_paterno(apellido: str) -> str:
    """
    Valida el apellido paterno del empleado.

    - Obligatorio
    - Mínimo 2 caracteres
    - Máximo 100 caracteres

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not apellido:
        return "Apellido paterno es obligatorio"

    apellido_limpio = apellido.strip()

    if len(apellido_limpio) < APELLIDO_MIN:
        return f"Apellido paterno debe tener al menos {APELLIDO_MIN} caracteres"

    if len(apellido_limpio) > APELLIDO_MAX:
        return f"Apellido paterno no puede exceder {APELLIDO_MAX} caracteres"

    return ""


def validar_email(email: str) -> str:
    """
    Valida formato de email.

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not email:
        return ""  # Email es opcional

    email_limpio = email.strip().lower()

    if len(email_limpio) > EMAIL_MAX:
        return f"Email no puede exceder {EMAIL_MAX} caracteres"

    if not re.match(EMAIL_PATTERN, email_limpio):
        return "Email con formato inválido"

    return ""


def validar_telefono(telefono: str) -> str:
    """
    Valida formato de teléfono (10 dígitos).

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not telefono:
        return ""  # Teléfono es opcional

    # Limpiar caracteres no numéricos
    telefono_limpio = re.sub(r'[^0-9]', '', telefono)

    if len(telefono_limpio) != TELEFONO_DIGITOS:
        return f"Teléfono debe tener {TELEFONO_DIGITOS} dígitos (tiene {len(telefono_limpio)})"

    return ""


def validar_fecha_nacimiento(fecha: str) -> str:
    """
    Valida fecha de nacimiento.

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not fecha:
        return ""  # Fecha es opcional

    try:
        from datetime import date
        fecha_obj = date.fromisoformat(fecha)

        hoy = date.today()

        # Validar que no sea fecha futura
        if fecha_obj > hoy:
            return "Fecha de nacimiento no puede ser futura"

        # Validar edad mínima (16 años)
        edad = hoy.year - fecha_obj.year
        if (hoy.month, hoy.day) < (fecha_obj.month, fecha_obj.day):
            edad -= 1

        if edad < 16:
            return "El empleado debe tener al menos 16 años"

        # Validar edad máxima razonable (100 años)
        if edad > 100:
            return "Fecha de nacimiento no parece válida"

    except ValueError:
        return "Fecha con formato inválido"

    return ""


def validar_empresa_seleccionada(empresa_id: str) -> str:
    """
    Valida empresa seleccionada (opcional).

    Returns:
        String vacío - empresa ya no es requerida
    """
    return ""
