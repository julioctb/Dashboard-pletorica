"""
Validadores de formulario para empresas.
Funciones puras que retornan mensaje de error o string vacío si es válido.
"""
import re

from app.core.text_utils import normalizar_mayusculas, limpiar_alfanumerico
from app.core.validation_patterns import (
    RFC_PATTERN,
    RFC_PREFIX_PATTERN,
    RFC_FECHA_PATTERN,
    EMAIL_PATTERN,
    NOMBRE_COMERCIAL_MIN,
    NOMBRE_COMERCIAL_MAX,
    RAZON_SOCIAL_MIN,
    RAZON_SOCIAL_MAX,
    EMAIL_MAX,
    TELEFONO_DIGITOS,
    CODIGO_POSTAL_LEN,
)
from app.core.error_messages import (
    msg_campo_obligatorio,
    msg_campo_obligatoria,
    msg_min_caracteres,
    msg_max_caracteres,
    msg_campos_faltantes,
    MSG_RFC_OBLIGATORIO,
    msg_rfc_longitud,
    MSG_RFC_LETRAS_INVALIDAS,
    MSG_RFC_FECHA_INVALIDA,
    msg_rfc_homoclave_invalida,
    MSG_EMAIL_FORMATO_INVALIDO,
    msg_email_max_longitud,
    MSG_CP_SOLO_NUMEROS,
    msg_cp_digitos,
    MSG_TELEFONO_SOLO_NUMEROS,
    msg_telefono_digitos,
    msg_registro_patronal_longitud,
    MSG_REGISTRO_PATRONAL_INICIO,
    MSG_REGISTRO_PATRONAL_FORMATO,
    MSG_PRIMA_RIESGO_NUMERO,
    MSG_PRIMA_RIESGO_MIN,
    MSG_PRIMA_RIESGO_MAX,
)


def validar_nombre_comercial(nombre: str) -> str:
    """
    Valida nombre comercial.

    Args:
        nombre: Nombre comercial a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not nombre or not nombre.strip():
        return msg_campo_obligatorio("Nombre comercial")

    if len(nombre.strip()) < NOMBRE_COMERCIAL_MIN:
        return msg_min_caracteres(NOMBRE_COMERCIAL_MIN)

    if len(nombre.strip()) > NOMBRE_COMERCIAL_MAX:
        return msg_max_caracteres(NOMBRE_COMERCIAL_MAX)

    return ""


def validar_razon_social(razon: str) -> str:
    """
    Valida razón social.

    Args:
        razon: Razón social a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not razon or not razon.strip():
        return msg_campo_obligatoria("Razón social")

    if len(razon.strip()) < RAZON_SOCIAL_MIN:
        return msg_min_caracteres(RAZON_SOCIAL_MIN)

    if len(razon.strip()) > RAZON_SOCIAL_MAX:
        return msg_max_caracteres(RAZON_SOCIAL_MAX)

    return ""


def validar_rfc(rfc: str) -> str:
    """
    Valida RFC mexicano con homoclave.

    Args:
        rfc: RFC a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not rfc or not rfc.strip():
        return MSG_RFC_OBLIGATORIO

    rfc_limpio = normalizar_mayusculas(rfc)

    # Validar longitud
    if len(rfc_limpio) < 12 or len(rfc_limpio) > 13:
        return msg_rfc_longitud(len(rfc_limpio))

    if not re.match(RFC_PATTERN, rfc_limpio):
        # Identificar qué parte está mal para dar feedback específico
        if not re.match(RFC_PREFIX_PATTERN, rfc_limpio[:4]):
            return MSG_RFC_LETRAS_INVALIDAS

        inicio = 4 if len(rfc_limpio) == 13 else 3
        fecha = rfc_limpio[inicio:inicio+6]

        if not re.match(RFC_FECHA_PATTERN, fecha):
            return MSG_RFC_FECHA_INVALIDA

        # Si llegamos aquí, es la homoclave
        return msg_rfc_homoclave_invalida(rfc_limpio[-3:])

    return ""


def validar_email(email: str) -> str:
    """
    Valida formato de email.

    Args:
        email: Email a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not email or not email.strip():
        return ""  # Email es opcional

    email_limpio = email.strip()

    if not re.match(EMAIL_PATTERN, email_limpio):
        return MSG_EMAIL_FORMATO_INVALIDO

    if len(email_limpio) > EMAIL_MAX:
        return msg_email_max_longitud(EMAIL_MAX)

    return ""


def validar_codigo_postal(cp: str) -> str:
    """
    Valida código postal mexicano (5 dígitos).

    Args:
        cp: Código postal a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not cp or not cp.strip():
        return ""  # CP es opcional

    cp_limpio = cp.strip()

    if not cp_limpio.isdigit():
        return MSG_CP_SOLO_NUMEROS

    if len(cp_limpio) != CODIGO_POSTAL_LEN:
        return msg_cp_digitos(CODIGO_POSTAL_LEN, len(cp_limpio))

    return ""


def validar_telefono(telefono: str) -> str:
    """
    Valida teléfono mexicano (10 dígitos).
    Permite espacios, guiones y paréntesis como separadores.

    Args:
        telefono: Teléfono a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not telefono or not telefono.strip():
        return ""  # Teléfono es opcional

    tel_limpio = telefono.strip()

    # Remover caracteres permitidos para separación
    tel_solo_digitos = (
        tel_limpio
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
        .replace("+", "")
    )

    if not tel_solo_digitos.isdigit():
        return MSG_TELEFONO_SOLO_NUMEROS

    if len(tel_solo_digitos) != TELEFONO_DIGITOS:
        return msg_telefono_digitos(TELEFONO_DIGITOS, len(tel_solo_digitos))

    return ""


def validar_campos_requeridos(nombre_comercial: str, razon_social: str, rfc: str) -> str:
    """
    Valida que todos los campos obligatorios estén presentes.

    Args:
        nombre_comercial: Nombre comercial
        razon_social: Razón social
        rfc: RFC

    Returns:
        Mensaje de error general o string vacío si todos están presentes
    """
    faltantes = []

    if not nombre_comercial or not nombre_comercial.strip():
        faltantes.append("Nombre comercial")

    if not razon_social or not razon_social.strip():
        faltantes.append("Razón social")

    if not rfc or not rfc.strip():
        faltantes.append("RFC")

    if faltantes:
        return msg_campos_faltantes(faltantes)

    return ""

def validar_registro_patronal(valor: str) -> str:
    """
    Valida registro patronal IMSS.
    Formato esperado: Y12-34567-10-1 (11 caracteres sin guiones)

    Args:
        valor: Registro patronal a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not valor or not valor.strip():
        return ""  # Campo opcional

    # Limpiar: solo alfanuméricos en mayúsculas
    limpio = limpiar_alfanumerico(valor)

    # Validar longitud
    if len(limpio) != 11:
        return msg_registro_patronal_longitud(11, len(limpio))

    # Validar formato: letra + 10 dígitos
    if not limpio[0].isalpha():
        return MSG_REGISTRO_PATRONAL_INICIO

    if not limpio[1:].isdigit():
        return MSG_REGISTRO_PATRONAL_FORMATO

    return ""


def validar_prima_riesgo(valor: str) -> str:
    """
    Valida prima de riesgo de trabajo.
    Rango válido: 0.5% a 15%

    Args:
        valor: Prima de riesgo a validar (como porcentaje)

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not valor or not valor.strip():
        return ""  # Campo opcional

    valor_limpio = valor.strip()

    try:
        numero = float(valor_limpio)
    except ValueError:
        return MSG_PRIMA_RIESGO_NUMERO

    if numero < 0.5:
        return MSG_PRIMA_RIESGO_MIN

    if numero > 15:
        return MSG_PRIMA_RIESGO_MAX

    return ""
