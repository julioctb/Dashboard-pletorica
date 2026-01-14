"""
Validadores de formulario para empresas.
Funciones puras que retornan mensaje de error o string vacío si es válido.
"""
import re


def validar_nombre_comercial(nombre: str) -> str:
    """
    Valida nombre comercial.

    Args:
        nombre: Nombre comercial a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not nombre or not nombre.strip():
        return "Nombre comercial es obligatorio"

    if len(nombre.strip()) < 2:
        return "Debe tener al menos 2 caracteres"

    if len(nombre.strip()) > 100:
        return "Máximo 100 caracteres"

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
        return "Razón social es obligatoria"

    if len(razon.strip()) < 2:
        return "Debe tener al menos 2 caracteres"

    if len(razon.strip()) > 100:
        return "Máximo 100 caracteres"

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
        return "RFC es obligatorio"

    rfc_limpio = rfc.strip().upper()

    # Validar longitud
    if len(rfc_limpio) < 12 or len(rfc_limpio) > 13:
        return f"RFC debe tener 12 o 13 caracteres (tiene {len(rfc_limpio)})"

    # Patrón del SAT: 3-4 letras + 6 dígitos (fecha) + 3 caracteres (homoclave)
    # Homoclave: [A-V1-9][A-Z1-9][0-9A]
    patron = r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$'

    if not re.match(patron, rfc_limpio):
        # Identificar qué parte está mal para dar feedback específico
        if not re.match(r'^[A-Z&Ñ]{3,4}', rfc_limpio[:4]):
            return "Las primeras 3-4 letras son inválidas"

        inicio = 4 if len(rfc_limpio) == 13 else 3
        fecha = rfc_limpio[inicio:inicio+6]

        if not re.match(r'^[0-9]{6}$', fecha):
            return "La fecha (6 dígitos) es inválida"

        # Si llegamos aquí, es la homoclave
        return f"La homoclave '{rfc_limpio[-3:]}' no cumple el formato del SAT"

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

    # Patrón básico de email
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(patron, email_limpio):
        return "Formato de email inválido (ejemplo: usuario@dominio.com)"

    if len(email_limpio) > 100:
        return "Email demasiado largo (máximo 100 caracteres)"

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
        return "Solo números permitidos"

    if len(cp_limpio) != 5:
        return f"Debe tener 5 dígitos (tiene {len(cp_limpio)})"

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
        return "Solo números (puede usar espacios, guiones o paréntesis)"

    if len(tel_solo_digitos) != 10:
        return f"Debe tener 10 dígitos (tiene {len(tel_solo_digitos)})"

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
        return f"Campos obligatorios faltantes: {', '.join(faltantes)}"

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
    
    # Limpiar: quitar guiones, espacios, convertir a mayúsculas
    limpio = valor.strip().upper().replace("-", "").replace(" ", "")
    
    # Validar longitud
    if len(limpio) != 11:
        return f"Debe tener 11 caracteres (tiene {len(limpio)})"
    
    # Validar formato: letra + 10 dígitos
    if not limpio[0].isalpha():
        return "Debe iniciar con una letra"
    
    if not limpio[1:].isdigit():
        return "Después de la letra deben ser 10 dígitos"
    
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
        return "Debe ser un número válido (ejemplo: 2.598)"
    
    if numero < 0.5:
        return "Mínimo 0.5%"
    
    if numero > 15:
        return "Máximo 15%"
    
    return ""
