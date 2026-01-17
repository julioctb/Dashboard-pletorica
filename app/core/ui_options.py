"""
Opciones de UI para formularios y componentes.

Centraliza mapeos clave-valor para selects, dropdowns y otros
componentes de interfaz de usuario.

Diferencia con app/core/catalogs/:
- catalogs/ → Constantes fiscales/laborales (IMSS, ISR, UMA, vacaciones)
- ui_options.py → Opciones de display para formularios (estados, tipos de cálculo)

Uso:
    from app.core.ui_options import ESTADOS_DISPLAY, TIPO_SALARIO_CALCULO

    # En formularios Reflex
    rx.select(list(ESTADOS_DISPLAY.values()), ...)
"""

# =============================================================================
# ESTADOS DE MÉXICO (32 estados)
# =============================================================================

ESTADOS_DISPLAY = {
    "aguascalientes": "Aguascalientes",
    "baja_california": "Baja California",
    "baja_california_sur": "Baja California Sur",
    "campeche": "Campeche",
    "chiapas": "Chiapas",
    "chihuahua": "Chihuahua",
    "ciudad_de_mexico": "Ciudad de México",
    "coahuila": "Coahuila",
    "colima": "Colima",
    "durango": "Durango",
    "estado_de_mexico": "Estado de México",
    "guanajuato": "Guanajuato",
    "guerrero": "Guerrero",
    "hidalgo": "Hidalgo",
    "jalisco": "Jalisco",
    "michoacan": "Michoacán",
    "morelos": "Morelos",
    "nayarit": "Nayarit",
    "nuevo_leon": "Nuevo León",
    "oaxaca": "Oaxaca",
    "puebla": "Puebla",
    "queretaro": "Querétaro",
    "quintana_roo": "Quintana Roo",
    "san_luis_potosi": "San Luis Potosí",
    "sinaloa": "Sinaloa",
    "sonora": "Sonora",
    "tabasco": "Tabasco",
    "tamaulipas": "Tamaulipas",
    "tlaxcala": "Tlaxcala",
    "veracruz": "Veracruz",
    "yucatan": "Yucatán",
    "zacatecas": "Zacatecas"
}

# Diccionario inverso: "Puebla" -> "puebla"
_ESTADOS_INVERSO = {v: k for k, v in ESTADOS_DISPLAY.items()}


def obtener_clave_estado(nombre_display: str) -> str | None:
    """
    Convierte nombre display a clave interna.

    Args:
        nombre_display: Nombre visible del estado (ej: "Puebla")

    Returns:
        Clave interna (ej: "puebla") o None si no existe

    Ejemplo:
        >>> obtener_clave_estado("Puebla")
        "puebla"
        >>> obtener_clave_estado("Ciudad de México")
        "ciudad_de_mexico"
    """
    return _ESTADOS_INVERSO.get(nombre_display)


# =============================================================================
# OPCIONES PARA SIMULADOR
# =============================================================================

TIPO_SALARIO_CALCULO = {
    "salario_bruto": "Salario Bruto",
    "salario_neto": "Salario Neto (inverso)",
    "salario_min": "Salario Mínimo"
}
